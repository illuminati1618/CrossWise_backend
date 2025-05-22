import time
import threading
import requests
import sqlite3
import traceback
import os
import logging
from datetime import datetime
import json
from googleapiclient.discovery import build

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("border_checker.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("border_checker")

# Database path
DB_PATH = 'instance/border_notifications.db'

# Sleep interval in seconds (5 minutes)
CHECK_INTERVAL = 300

# Track notifications to avoid sending duplicates
# Format: {notification_id: last_notification_time}
last_notifications = {}

def get_db_connection():
    """Get a database connection with row factory"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_border_wait_times():
    """
    Fetch current border wait times from CBP API
    Returns:
        dict: Border wait time data for San Ysidro port
    """
    try:
        response = requests.get('https://bwt.cbp.gov/api/waittimes')
        if response.status_code != 200:
            logger.error(f"API request failed with status code {response.status_code}")
            return None
        
        data = response.json()
        
        # Find San Ysidro port
        san_ysidro = next((port for port in data if 
                         port.get('port_name') == 'San Ysidro' and 
                         port.get('border') == 'Mexican Border'), None)
        
        if not san_ysidro:
            logger.error("San Ysidro port data not found in API response")
            return None
            
        return san_ysidro
    except Exception as e:
        logger.error(f"Error fetching border wait times: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def get_active_notifications():
    """
    Retrieve all active notifications from database
    
    Returns:
        list: Active notifications 
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM border_notifications WHERE active = 1')
        notifications = cursor.fetchall()
        conn.close()
        return notifications
    except Exception as e:
        logger.error(f"Error retrieving notifications: {str(e)}")
        logger.error(traceback.format_exc())
        return []

def should_send_notification(notification_id):
    """
    Determine if we should send a notification (avoid spam)
    Only send once per hour for the same notification
    
    Args:
        notification_id: ID of the notification
        
    Returns:
        bool: True if notification should be sent
    """
    global last_notifications
    
    now = datetime.now()
    
    # If no record or last notification was more than 1 hour ago
    if notification_id not in last_notifications or \
       (now - last_notifications[notification_id]).total_seconds() > 3600:
        last_notifications[notification_id] = now
        return True
        
    return False

def send_notification(notification, wait_time, port_data):
    """
    Send email notification when conditions are met
    
    Args:
        notification: Notification record
        wait_time: Current wait time
        port_data: Port data from API
    """
    # First check if we should send this notification (avoid spam)
    if not should_send_notification(notification['id']):
        logger.info(f"Skipping notification {notification['id']} - already sent recently")
        return
        
    try:
        # Import here to avoid circular imports
        from api.border_email import get_credentials, create_message, send_message
        
        # Get type label
        type_labels = {
            'standard': 'Standard Vehicles',
            'sentri': 'SENTRI Lanes',
            'pedestrian': 'Pedestrian'
        }
        
        type_label = type_labels.get(notification['type'], notification['type'])
        condition_text = 'below' if notification['condition'] == 'below' else 'above'
        
        # Create email subject
        subject = f"Border Alert: {type_label} Wait Time is now {wait_time} minutes"
        
        # Create email content
        email_from = f'"Border Alerts" <{os.getenv("EMAIL_USER")}>'
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        html_message = f"""
        <div style="font-family: 'Inter', sans-serif; color: #121212; padding: 20px; background-color: #f0f4f8; border-radius: 10px;">
            <h2 style="color: #4285F4;">Border Alert Notification</h2>
            <p>Your border wait time alert condition has been met.</p>
            <p><strong>Details:</strong></p>
            <ul>
                <li><strong>Border Crossing:</strong> San Ysidro</li>
                <li><strong>Type:</strong> {type_label}</li>
                <li><strong>Current Wait Time:</strong> {wait_time} minutes</li>
                <li><strong>Your Alert Condition:</strong> When wait time is {condition_text} {notification['wait_time']} minutes</li>
                <li><strong>Check Time:</strong> {now}</li>
            </ul>
            <p>To view current wait times, visit <a href="http://localhost:3167/users/bordernotifs" style="color: #4285F4;">Border Alerts Dashboard</a></p>
        </div>
        """
        
        # Get Gmail API credentials
        creds = get_credentials()
        
        # Create Gmail API service
        service = build('gmail', 'v1', credentials=creds)
        
        # Create and send the email
        email_message = create_message(email_from, notification['email'], subject, html_message, html=True)
        send_message(service, 'me', email_message)
        
        logger.info(f"Notification sent to {notification['email']} for {type_label}")
        
        # Log notification time
        last_notifications[notification['id']] = datetime.now()
        
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        logger.error(traceback.format_exc())

def send_sms_notification(notification, wait_time):
    """
    Send SMS notification when conditions are met
    
    Args:
        notification: Notification record
        wait_time: Current wait time
    """
    # Skip if no SMS email is defined
    if not notification.get('sms_email'):
        return
        
    try:
        # Import here to avoid circular imports
        from api.border_email import get_credentials
        from api.border_sms import create_message, send_message
        
        # Get type label
        type_labels = {
            'standard': 'Standard Vehicles',
            'sentri': 'SENTRI Lanes',
            'pedestrian': 'Pedestrian'
        }
        
        type_label = type_labels.get(notification['type'], notification['type'])
        condition_text = 'below' if notification['condition'] == 'below' else 'above'
        
        # Create subject and message (keep very short for SMS)
        subject = "Border Alert"
        message_text = f"Border Alert: {type_label} wait time is now {wait_time} minutes ({condition_text} {notification['wait_time']} min threshold)."
        
        # Get Gmail API credentials
        creds = get_credentials()
        
        # Create Gmail API service
        service = build('gmail', 'v1', credentials=creds)
        
        # Create and send the SMS
        email_from = f"Border Alerts <{os.getenv('EMAIL_USER')}>"
        email_message = create_message(email_from, notification['sms_email'], subject, message_text)
        send_message(service, 'me', email_message)
        
        logger.info(f"SMS notification sent to {notification['sms_email']}")
        
    except Exception as e:
        logger.error(f"Error sending SMS notification: {str(e)}")
        logger.error(traceback.format_exc())

def check_notifications(port_data):
    """
    Check all active notifications against current wait times
    
    Args:
        port_data: Port data from API
    """
    if not port_data:
        logger.error("No port data available to check notifications")
        return
        
    notifications = get_active_notifications()
    logger.info(f"Checking {len(notifications)} active notifications")
    
    for notification in notifications:
        try:
            # Get current wait time based on notification type
            current_wait_time = None
            
            if notification['type'] == 'standard':
                current_wait_time = port_data['passenger_vehicle_lanes']['standard_lanes']['delay_minutes']
            elif notification['type'] == 'sentri':
                current_wait_time = port_data['passenger_vehicle_lanes']['NEXUS_SENTRI_lanes']['delay_minutes']
            elif notification['type'] == 'pedestrian':
                current_wait_time = port_data['pedestrian_lanes']['standard_lanes']['delay_minutes']
            else:
                logger.warning(f"Unknown notification type: {notification['type']}")
                continue
                
            # Convert to integer if needed
            if isinstance(current_wait_time, str):
                current_wait_time = int(current_wait_time)
                
            # Check if condition is met
            threshold = notification['wait_time']
            condition_met = False
            
            if notification['condition'] == 'below' and current_wait_time <= threshold:
                condition_met = True
                logger.info(f"Condition met: {notification['type']} wait time {current_wait_time} minutes is below threshold {threshold}")
            elif notification['condition'] == 'above' and current_wait_time >= threshold:
                condition_met = True
                logger.info(f"Condition met: {notification['type']} wait time {current_wait_time} minutes is above threshold {threshold}")
                
            # Send notification if condition is met
            if condition_met:
                send_notification(notification, current_wait_time, port_data)
                
                # Check if this notification has an SMS email
                if 'sms_email' in notification and notification['sms_email']:
                    send_sms_notification(notification, current_wait_time)
                
        except Exception as e:
            logger.error(f"Error processing notification {notification['id']}: {str(e)}")
            logger.error(traceback.format_exc())

def checker_worker():
    """
    Main worker function that runs checks at regular intervals.
    """
    logger.info("Border checker worker started")
    
    while True:
        try:
            # Log start of check
            logger.info(f"Running border wait time check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Fetch current wait times
            port_data = fetch_border_wait_times()
            
            # Check notifications against current wait times
            if port_data:
                check_notifications(port_data)
            else:
                logger.warning("No port data available, skipping notification check")
                
            # Log completion of check
            logger.info(f"Completed border wait time check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Sleep until next check
            time.sleep(CHECK_INTERVAL)
            
        except Exception as e:
            logger.error(f"Error in checker worker: {str(e)}")
            logger.error(traceback.format_exc())
            # Continue checking even after errors
            time.sleep(CHECK_INTERVAL)

def init_db():
    """Initialize the database if it doesn't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create notifications table if it doesn't exist
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

def start_checker():
    """
    Start the border checker in a separate thread
    """
    # Create database tables if they don't exist yet
    init_db()
    
    checker_thread = threading.Thread(target=checker_worker, daemon=True)
    checker_thread.start()
    logger.info("Border checker thread started")
    return checker_thread

# This allows the module to be imported without starting the checker
if __name__ == "__main__":
    thread = start_checker()
    # Keep the main thread alive
    try:
        while thread.is_alive():
            thread.join(1)
    except KeyboardInterrupt:
        logger.info("Border checker stopped by user")