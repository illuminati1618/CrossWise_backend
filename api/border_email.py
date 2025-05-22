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
border_email_api = Blueprint('border_email_api', __name__, url_prefix='/api/border_email')

# Database path
DB_PATH = 'instance/border_notifications.db'

# Gmail API configuration
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_CLIENT_ID = os.getenv('EMAIL_CLIENT_ID')
EMAIL_CLIENT_SECRET = os.getenv('EMAIL_CLIENT_SECRET')
GOOGLE_REFRESH_TOKEN = os.getenv('GOOGLE_REFRESH_TOKEN')

def init_db():
    """Initialize the database if it doesn't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create notifications table with sms_email field
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS border_notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        condition TEXT NOT NULL,
        wait_time INTEGER NOT NULL,
        email TEXT NOT NULL,
        sms_email TEXT,
        active BOOLEAN DEFAULT 1,
        created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get a database connection with row factory"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_credentials():
    """Get valid credentials for Gmail API using refresh token"""
    try:
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
    except Exception as e:
        print(f"Error getting credentials: {str(e)}")
        print(traceback.format_exc())
        raise e

def create_message(sender, to, subject, message_text, html=True):
    """Create a message for an email"""
    if html:
        message = MIMEText(message_text, 'html')
    else:
        message = MIMEText(message_text, 'plain')
    
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    
    # Encode the message in base64url format
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw}

def send_message(service, user_id, message):
    """Send an email message"""
    try:
        message = service.users().messages().send(userId=user_id, body=message).execute()
        return message
    except HttpError as error:
        print(f'An error occurred: {error}')
        print(traceback.format_exc())
        raise error

@border_email_api.route('/send', methods=['POST'])
def send_email():
    try:
        # Parse request body
        data = request.get_json()
        email = data.get('email')
        subject = data.get('subject')
        message = data.get('message')
        
        if not email or not subject or not message:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: email, subject, and message are required'
            }), 400
        
        # Get Gmail API credentials
        creds = get_credentials()
        
        # Create Gmail API service
        service = build('gmail', 'v1', credentials=creds)
        
        # Create and send the email
        email_from = f'"Border Alerts" <{EMAIL_USER}>'
        email_message = create_message(email_from, email, subject, message, html=True)
        result = send_message(service, 'me', email_message)
        
        return jsonify({
            'success': True,
            'messageId': result['id'],
            'message': f'Email sent successfully to {email}'
        })
    
    except Exception as e:
        print("======== EMAIL ERROR ========")
        print(f"Error message: {str(e)}")
        print(f"Stack trace: {traceback.format_exc()}")
        print("=============================")
        
        return jsonify({
            'success': False,
            'error': str(e) or 'Failed to send email',
            'details': 'Check server logs for more details'
        }), 500

@border_email_api.route('/notifications', methods=['POST'])
def create_notification():
    # Initialize the database if it doesn't exist
    init_db()
    
    try:
        # Get data from request
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['type', 'condition', 'waitTime', 'email']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Validate email
        if not data.get('email') or '@' not in data.get('email', ''):
            return jsonify({
                'success': False,
                'error': 'Valid email address is required for notifications'
            }), 400
        
        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check for sms_email in request
        sms_email = data.get('smsEmail', None)
        
        # Insert the notification
        cursor.execute('''
            INSERT INTO border_notifications 
            (type, condition, wait_time, email, sms_email, created)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data['type'],
            data['condition'],
            data['waitTime'],
            data['email'],
            sms_email,
            datetime.now().isoformat()
        ))
        
        notification_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Create and send a confirmation email
        try:
            # Get wait time type label
            type_labels = {
                'standard': 'Standard Vehicles',
                'sentri': 'SENTRI Lanes',
                'pedestrian': 'Pedestrian'
            }
            
            type_label = type_labels.get(data['type'], data['type'])
            condition_text = 'falls below' if data['condition'] == 'below' else 'rises above'
            
            # Email content
            subject = f"Border Alert Notification Created"
            html_message = f"""
            <div style="font-family: 'Inter', sans-serif; color: #121212; padding: 20px; background-color: #f0f4f8; border-radius: 10px;">
                <h2 style="color: #4285F4;">Border Alert Created</h2>
                <p>You have successfully created a border wait time alert.</p>
                <p><strong>Details:</strong></p>
                <ul>
                    <li><strong>Type:</strong> {type_label}</li>
                    <li><strong>Condition:</strong> When wait time {condition_text} {data['waitTime']} minutes</li>
                    <li><strong>Email:</strong> {data['email']}</li>
                    <li><strong>Created:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                </ul>
                <p>You will receive an alert when the specified condition is met.</p>
                <p><a href="http://localhost:3167/users/bordernotifs" style="color: #4285F4;">View your notifications</a></p>
            </div>
            """
            
            # Get Gmail API credentials
            creds = get_credentials()
            
            # Create Gmail API service
            service = build('gmail', 'v1', credentials=creds)
            
            # Create and send the email
            email_from = f'"Border Alerts" <{EMAIL_USER}>'
            email_message = create_message(email_from, data['email'], subject, html_message, html=True)
            send_message(service, 'me', email_message)
            
        except Exception as e:
            print(f"Warning: Confirmation email could not be sent: {str(e)}")
            print(traceback.format_exc())
            # Continue with the notification creation even if email sending fails
        
        return jsonify({
            'success': True,
            'message': 'Notification created successfully',
            'id': notification_id
        })
        
    except Exception as e:
        print(f"Error creating notification: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to create notification'
        }), 500

@border_email_api.route('/notifications', methods=['GET'])
def get_notifications():
    # Initialize the database if it doesn't exist
    init_db()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all active notifications
        cursor.execute('SELECT * FROM border_notifications WHERE active = 1 ORDER BY created DESC')
        notifications = cursor.fetchall()
        
        # Convert to list of dictionaries
        result = []
        for notification in notifications:
            notification_data = {
                'id': notification['id'],
                'type': notification['type'],
                'condition': notification['condition'],
                'waitTime': notification['wait_time'],
                'email': notification['email'],
                'created': notification['created']
            }
            
            # Include SMS email if present
            if notification['sms_email']:
                notification_data['smsEmail'] = notification['sms_email']
                
            result.append(notification_data)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'notifications': result
        })
        
    except Exception as e:
        print(f"Error fetching notifications: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to fetch notifications'
        }), 500

@border_email_api.route('/notifications/<int:notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    # Initialize the database if it doesn't exist
    init_db()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if notification exists
        cursor.execute('SELECT id FROM border_notifications WHERE id = ?', (notification_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Notification not found'
            }), 404
        
        # Delete or deactivate the notification
        cursor.execute('UPDATE border_notifications SET active = 0 WHERE id = ?', (notification_id,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Notification deleted successfully'
        })
        
    except Exception as e:
        print(f"Error deleting notification: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to delete notification'
        }), 500

# Fixed endpoint for test emails
@border_email_api.route('/test_email', methods=['POST'])
def test_email():
    """Endpoint to test email sending functionality"""
    try:
        print("Test email endpoint called")
        # Parse request body
        data = request.get_json()
        if not data:
            print("No JSON data received")
            return jsonify({
                'success': False,
                'error': 'No JSON data received'
            }), 400
            
        email = data.get('email')
        
        if not email:
            print("Missing email field")
            return jsonify({
                'success': False,
                'error': 'Missing required email field'
            }), 400
        
        print(f"Sending test email to: {email}")
        
        # Email content
        subject = "Border Alert System Test Email"
        html_message = """
        <div style="font-family: 'Inter', sans-serif; color: #121212; padding: 20px; background-color: #f0f4f8; border-radius: 10px;">
            <h2 style="color: #4285F4;">Border Alert System Test</h2>
            <p>This is a test email from the Border Alert System.</p>
            <p>If you're receiving this email, it means the email notification system is working correctly.</p>
            <p><a href="http://localhost:3167/users/bordernotifs" style="color: #4285F4;">Go to Border Alerts</a></p>
        </div>
        """
        
        # Get Gmail API credentials
        creds = get_credentials()
        
        # Create Gmail API service
        service = build('gmail', 'v1', credentials=creds)
        
        # Create and send the email
        email_from = f'"Border Alerts" <{EMAIL_USER}>'
        email_message = create_message(email_from, email, subject, html_message, html=True)
        result = send_message(service, 'me', email_message)
        
        print(f"Test email sent successfully, message ID: {result['id']}")
        
        return jsonify({
            'success': True,
            'messageId': result['id'],
            'message': f'Test email sent successfully to {email}'
        })
    
    except Exception as e:
        print("======== TEST EMAIL ERROR ========")
        print(f"Error message: {str(e)}")
        print(traceback.format_exc())
        print("==================================")
        
        return jsonify({
            'success': False,
            'error': str(e) or 'Failed to send test email',
            'details': 'Check server logs for more details'
        }), 500