from flask import Blueprint, request, jsonify
import os
import base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import sqlite3
from datetime import datetime
import traceback

# Create Blueprint
sms_api = Blueprint('sms_api', __name__, url_prefix='/api/border_notifications')

# Gmail API Configuration
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_CLIENT_ID = os.getenv('EMAIL_CLIENT_ID')
EMAIL_CLIENT_SECRET = os.getenv('EMAIL_CLIENT_SECRET')
GOOGLE_REFRESH_TOKEN = os.getenv('GOOGLE_REFRESH_TOKEN')

# SMS message template
template = "Border Alert: {label} wait time {direction} {threshold} minutes."

# Function to get Gmail credentials
def get_credentials():
    creds = Credentials(
        None,
        refresh_token=GOOGLE_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=EMAIL_CLIENT_ID,
        client_secret=EMAIL_CLIENT_SECRET,
        scopes=SCOPES
    )
    creds.refresh(Request())
    return creds

# Function to send message via Gmail API
def create_message(sender, to, subject, message_text):
    message = MIMEText(message_text, 'plain')
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw}

def send_message(service, user_id, message):
    return service.users().messages().send(userId=user_id, body=message).execute()

@sms_api.route('/test_sms', methods=['POST'])
def test_sms():
    try:
        data = request.get_json()
        phone = data.get('phone')
        if not phone:
            return jsonify({
                'success': False,
                'error': 'Missing phone field'
            }), 400

        # Compose message
        subject = "Border Alert Test"
        message_text = "This is a test SMS from the Border Alert System. If you received this, it works."

        creds = get_credentials()
        service = build('gmail', 'v1', credentials=creds)
        email_message = create_message(f"Border Alerts <{EMAIL_USER}>", phone, subject, message_text)
        result = send_message(service, 'me', email_message)

        return jsonify({
            'success': True,
            'messageId': result['id'],
            'message': f'Test SMS sent successfully to {phone}'
        })
    
    except Exception as e:
        print(f"Error sending SMS: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@sms_api.route('/create_sms', methods=['POST'])
def create_sms_notification():
    try:
        data = request.get_json()
        required = ['type', 'condition', 'waitTime', 'smsEmail']
        for field in required:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing field: {field}'
                }), 400

        # First store notification in database for background checker
        try:
            conn = sqlite3.connect('instance/border_notifications.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO border_notifications 
                (type, condition, wait_time, email, sms_email, created)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                data['type'],
                data['condition'],
                data['waitTime'],
                '',  # Email is empty for SMS-only notifications
                data['smsEmail'],
                datetime.now().isoformat()
            ))
            
            notification_id = cursor.lastrowid
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error storing SMS notification in database: {str(e)}")
            print(traceback.format_exc())
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

        # Get wait time type label
        type_labels = {
            'standard': 'Standard Vehicles',
            'sentri': 'SENTRI Lanes',
            'pedestrian': 'Pedestrian'
        }

        label = type_labels.get(data['type'], data['type'])
        direction = 'falls below' if data['condition'] == 'below' else 'rises above'
        threshold = data['waitTime']

        subject = "Border Alert Notification"
        message_text = template.format(label=label, direction=direction, threshold=threshold)

        creds = get_credentials()
        service = build('gmail', 'v1', credentials=creds)
        email_message = create_message(f"Border Alerts <{EMAIL_USER}>", data['smsEmail'], subject, message_text)
        result = send_message(service, 'me', email_message)

        return jsonify({
            'success': True,
            'message': f'SMS notification created successfully for {data["smsEmail"]}',
            'messageId': result['id'],
            'notification_id': notification_id
        })
    except Exception as e:
        print(f"Error creating SMS notification: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500