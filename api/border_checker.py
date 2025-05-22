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

# Enhanced logging configuration
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

# Track checker statistics
checker_stats = {
    'total_checks': 0,
    'successful_checks': 0,
    'failed_checks': 0,
    'notifications_sent': 0,
    'start_time': None,
    'last_successful_check': None,
    'last_error': None
}

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
        logger.info("🌐 Fetching border wait times from CBP API...")
        response = requests.get('https://bwt.cbp.gov/api/waittimes', timeout=10)
        
        if response.status_code != 200:
            logger.error(f"❌ API request failed with status code {response.status_code}")
            return None
        
        data = response.json()
        logger.info(f"✅ Successfully received API response with {len(data)} ports")
        
        # Find San Ysidro port
        san_ysidro = next((port for port in data if 
                         port.get('port_name') == 'San Ysidro' and 
                         port.get('border') == 'Mexican Border'), None)
        
        if not san_ysidro:
            logger.error("❌ San Ysidro port data not found in API response")
            return None
        
        # Log current wait times for visibility
        try:
            standard_wait = san_ysidro['passenger_vehicle_lanes']['standard_lanes']['delay_minutes']
            sentri_wait = san_ysidro['passenger_vehicle_lanes']['NEXUS_SENTRI_lanes']['delay_minutes']
            pedestrian_wait = san_ysidro['pedestrian_lanes']['standard_lanes']['delay_minutes']
            
            logger.info(f"📊 Current wait times - Standard: {standard_wait}min, SENTRI: {sentri_wait}min, Pedestrian: {pedestrian_wait}min")
        except KeyError as e:
            logger.warning(f"⚠️ Could not extract wait time details: {e}")
            
        return san_ysidro
        
    except requests.exceptions.Timeout:
        logger.error("⏱️ API request timed out after 10 seconds")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"🌐 Network error fetching border wait times: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected error fetching border wait times: {str(e)}")
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
        
        logger.info(f"📋 Found {len(notifications)} active notifications in database")
        return notifications
        
    except Exception as e:
        logger.error(f"🗄️ Error retrieving notifications from database: {str(e)}")
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
        logger.debug(f"✅ Notification {notification_id} approved for sending")
        return True
    
    time_since_last = (now - last_notifications[notification_id]).total_seconds()
    logger.debug(f"⏭️ Skipping notification {notification_id} - sent {time_since_last/60:.1f} minutes ago")
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
        logger.info(f"⏭️ Skipping notification {notification['id']} - already sent recently")
        return
        
    try:
        logger.info(f"📧 Preparing to send email notification {notification['id']}")
        
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
        
        logger.info(f"✅ Email notification sent successfully to {notification['email']} for {type_label}")
        
        # Update global statistics
        checker_stats['notifications_sent'] += 1
        
        # Log notification time
        last_notifications[notification['id']] = datetime.now()
        
    except Exception as e:
        logger.error(f"❌ Error sending email notification: {str(e)}")
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
        logger.debug(f"⏭️ No SMS email configured for notification {notification['id']}")
        return
        
    try:
        logger.info(f"📱 Preparing to send SMS notification {notification['id']}")
        
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
        
        logger.info(f"✅ SMS notification sent successfully to {notification['sms_email']}")
        
        # Update global statistics
        checker_stats['notifications_sent'] += 1
        
    except Exception as e:
        logger.error(f"❌ Error sending SMS notification: {str(e)}")
        logger.error(traceback.format_exc())

def check_notifications(port_data):
    """
    Check all active notifications against current wait times
    
    Args:
        port_data: Port data from API
    """
    if not port_data:
        logger.error("❌ No port data available to check notifications")
        return
        
    notifications = get_active_notifications()
    logger.info(f"🔍 Checking {len(notifications)} active notifications against current wait times")
    
    conditions_met = 0
    
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
                logger.warning(f"⚠️ Unknown notification type: {notification['type']}")
                continue
                
            # Convert to integer if needed
            if isinstance(current_wait_time, str):
                current_wait_time = int(current_wait_time)
                
            # Check if condition is met
            threshold = notification['wait_time']
            condition_met = False
            
            if notification['condition'] == 'below' and current_wait_time <= threshold:
                condition_met = True
                logger.info(f"🎯 Condition MET: {notification['type']} wait time {current_wait_time} minutes is below threshold {threshold}")
            elif notification['condition'] == 'above' and current_wait_time >= threshold:
                condition_met = True
                logger.info(f"🎯 Condition MET: {notification['type']} wait time {current_wait_time} minutes is above threshold {threshold}")
            else:
                logger.debug(f"📋 Condition not met for notification {notification['id']}: {current_wait_time}min vs {threshold}min threshold ({notification['condition']})")
                
            # Send notification if condition is met
            if condition_met:
                conditions_met += 1
                send_notification(notification, current_wait_time, port_data)
                
                # Check if this notification has an SMS email
                if 'sms_email' in notification and notification['sms_email']:
                    send_sms_notification(notification, current_wait_time)
                
        except Exception as e:
            logger.error(f"❌ Error processing notification {notification['id']}: {str(e)}")
            logger.error(traceback.format_exc())
    
    if conditions_met == 0:
        logger.info("✅ No notification conditions met this check")
    else:
        logger.info(f"🔔 {conditions_met} notification condition(s) met and processed")

def log_checker_stats():
    """Log current checker statistics"""
    if checker_stats['start_time']:
        uptime = datetime.now() - checker_stats['start_time']
        uptime_str = f"{uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m"
        
        success_rate = 0
        if checker_stats['total_checks'] > 0:
            success_rate = (checker_stats['successful_checks'] / checker_stats['total_checks']) * 100
        
        logger.info(f"📈 Checker Stats - Uptime: {uptime_str}, "
                   f"Total checks: {checker_stats['total_checks']}, "
                   f"Success rate: {success_rate:.1f}%, "
                   f"Notifications sent: {checker_stats['notifications_sent']}")

def checker_worker():
    """
    Main worker function that runs checks at regular intervals.
    """
    global checker_stats
    
    logger.info("🚀 Border checker worker starting up...")
    checker_stats['start_time'] = datetime.now()
    
    # Log startup information
    logger.info(f"⚙️ Configuration - Check interval: {CHECK_INTERVAL} seconds ({CHECK_INTERVAL/60} minutes)")
    logger.info(f"🗄️ Database path: {DB_PATH}")
    
    while True:
        try:
            # Update statistics
            checker_stats['total_checks'] += 1
            
            # Log start of check cycle
            check_start_time = datetime.now()
            logger.info(f"🔄 === Starting border wait time check cycle #{checker_stats['total_checks']} at {check_start_time.strftime('%Y-%m-%d %H:%M:%S')} ===")
            
            # Fetch current wait times
            logger.info("📡 Step 1: Fetching current border wait times...")
            port_data = fetch_border_wait_times()
            
            # Check notifications against current wait times
            if port_data:
                logger.info("✅ Step 2: Port data received, checking notifications...")
                check_notifications(port_data)
                checker_stats['successful_checks'] += 1
                checker_stats['last_successful_check'] = datetime.now()
                checker_stats['last_error'] = None
            else:
                logger.warning("⚠️ Step 2: No port data available, skipping notification check")
                checker_stats['failed_checks'] += 1
                checker_stats['last_error'] = "No port data received"
            
            # Log completion of check cycle
            check_end_time = datetime.now()
            check_duration = (check_end_time - check_start_time).total_seconds()
            logger.info(f"✅ === Completed border wait time check cycle #{checker_stats['total_checks']} in {check_duration:.2f} seconds ===")
            
            # Log stats every 10 checks
            if checker_stats['total_checks'] % 10 == 0:
                log_checker_stats()
            
            # Sleep until next check
            logger.info(f"⏰ Sleeping for {CHECK_INTERVAL} seconds until next check...")
            logger.info(f"⏰ Next check scheduled for: {datetime.fromtimestamp(time.time() + CHECK_INTERVAL).strftime('%Y-%m-%d %H:%M:%S')}")
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            logger.info("🛑 Border checker stopped by user (Ctrl+C)")
            break
        except Exception as e:
            checker_stats['failed_checks'] += 1
            checker_stats['last_error'] = str(e)
            
            logger.error(f"❌ Unexpected error in checker worker: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Continue checking even after errors, but log the issue
            logger.info(f"🔄 Continuing checks despite error. Sleeping for {CHECK_INTERVAL} seconds...")
            time.sleep(CHECK_INTERVAL)

def init_db():
    """Initialize the database if it doesn't exist"""
    logger.info("🗄️ Initializing database...")
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
    logger.info("✅ Database initialization completed")

def start_checker():
    """
    Start the border checker in a separate thread
    """
    # Create database tables if they don't exist yet
    init_db()
    
    logger.info("🎬 Starting border checker thread...")
    checker_thread = threading.Thread(target=checker_worker, daemon=True)
    checker_thread.start()
    logger.info("✅ Border checker thread started successfully")
    return checker_thread

# This allows the module to be imported without starting the checker
if __name__ == "__main__":
    print("🎯 Starting Border Checker in standalone mode...")
    thread = start_checker()
    # Keep the main thread alive
    try:
        while thread.is_alive():
            thread.join(1)
    except KeyboardInterrupt:
        logger.info("🛑 Border checker stopped by user")
        print("\n👋 Border checker shut down gracefully")