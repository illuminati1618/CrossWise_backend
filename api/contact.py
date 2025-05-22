from flask import Blueprint, request, jsonify
from flask_restful import Api, Resource
import os
from datetime import datetime
import json

# Create Blueprint
contact_api = Blueprint('contact_api', __name__, url_prefix='/api/contact')
api = Api(contact_api)

# File path for storing contact data
CONTACT_FILE = 'data/contacts.txt'
CONTACT_JSON = 'data/contacts.json'

def ensure_data_directory():
    """Ensure the data directory exists"""
    os.makedirs('data', exist_ok=True)

def validate_contact_data(data):
    """Validate the contact form data"""
    errors = []
    
    # Required fields
    if not data.get('name', '').strip():
        errors.append('Name is required')
    
    if not data.get('email', '').strip():
        errors.append('Email is required')
    
    # Basic email validation
    email = data.get('email', '').strip()
    if email and '@' not in email:
        errors.append('Invalid email format')
    
    # Phone number validation (if provided)
    phone = data.get('phone', '').strip()
    if phone and len(phone) < 10:
        errors.append('Phone number must be at least 10 digits')
    
    return errors

class ContactAPI:
    class _Signup(Resource):
        def post(self):
            try:
                # Ensure data directory exists
                ensure_data_directory()
                
                # Get JSON data from request
                data = request.get_json()
                
                if not data:
                    return {'error': 'No data provided'}, 400
                
                # Validate the data
                validation_errors = validate_contact_data(data)
                if validation_errors:
                    return {'error': '; '.join(validation_errors)}, 400
                
                # Clean and prepare the data
                contact_info = {
                    'name': data.get('name', '').strip(),
                    'email': data.get('email', '').strip().lower(),
                    'phone': data.get('phone', '').strip(),
                    'wants_updates': data.get('updates', False),
                    'timestamp': data.get('timestamp', datetime.now().isoformat()),
                    'ip_address': request.remote_addr
                }
                
                # Check for duplicate email (optional)
                if os.path.exists(CONTACT_JSON):
                    try:
                        with open(CONTACT_JSON, 'r', encoding='utf-8') as f:
                            existing_contacts = json.load(f)
                        
                        # Check if email already exists
                        for contact in existing_contacts:
                            if contact.get('email') == contact_info['email']:
                                return {
                                    'message': 'Email already registered',
                                    'status': 'duplicate'
                                }, 200
                    except (json.JSONDecodeError, FileNotFoundError):
                        existing_contacts = []
                else:
                    existing_contacts = []
                
                # Append to text file (human-readable format)
                with open(CONTACT_FILE, 'a', encoding='utf-8') as f:
                    f.write(f"--- New Contact ---\n")
                    f.write(f"Date: {contact_info['timestamp']}\n")
                    f.write(f"Name: {contact_info['name']}\n")
                    f.write(f"Email: {contact_info['email']}\n")
                    f.write(f"Phone: {contact_info['phone'] or 'Not provided'}\n")
                    f.write(f"Wants Updates: {'Yes' if contact_info['wants_updates'] else 'No'}\n")
                    f.write(f"IP Address: {contact_info['ip_address']}\n")
                    f.write(f"{'='*50}\n\n")
                
                # Also save to JSON file for easier processing
                existing_contacts.append(contact_info)
                with open(CONTACT_JSON, 'w', encoding='utf-8') as f:
                    json.dump(existing_contacts, f, indent=2, ensure_ascii=False)
                
                return {
                    'message': 'Contact information saved successfully',
                    'status': 'success',
                    'id': len(existing_contacts)
                }, 200
                
            except Exception as e:
                print(f"Error saving contact: {str(e)}")
                return {
                    'error': 'Internal server error',
                    'message': 'Failed to save contact information'
                }, 500
    
    class _GetContacts(Resource):
        def get(self):
            """Get all contacts (admin only - you might want to add authentication)"""
            try:
                ensure_data_directory()
                
                if not os.path.exists(CONTACT_JSON):
                    return {'contacts': [], 'count': 0}, 200
                
                with open(CONTACT_JSON, 'r', encoding='utf-8') as f:
                    contacts = json.load(f)
                
                # Remove sensitive info for security
                safe_contacts = []
                for contact in contacts:
                    safe_contact = {
                        'name': contact.get('name'),
                        'email': contact.get('email'),
                        'has_phone': bool(contact.get('phone')),
                        'wants_updates': contact.get('wants_updates'),
                        'timestamp': contact.get('timestamp')
                    }
                    safe_contacts.append(safe_contact)
                
                return {
                    'contacts': safe_contacts,
                    'count': len(safe_contacts)
                }, 200
                
            except Exception as e:
                print(f"Error retrieving contacts: {str(e)}")
                return {
                    'error': 'Failed to retrieve contacts'
                }, 500
    
    class _Stats(Resource):
        def get(self):
            """Get contact statistics"""
            try:
                ensure_data_directory()
                
                if not os.path.exists(CONTACT_JSON):
                    return {
                        'total_contacts': 0,
                        'contacts_with_phone': 0,
                        'wants_updates': 0,
                        'latest_signup': None
                    }, 200
                
                with open(CONTACT_JSON, 'r', encoding='utf-8') as f:
                    contacts = json.load(f)
                
                stats = {
                    'total_contacts': len(contacts),
                    'contacts_with_phone': sum(1 for c in contacts if c.get('phone')),
                    'wants_updates': sum(1 for c in contacts if c.get('wants_updates')),
                    'latest_signup': max(contacts, key=lambda x: x.get('timestamp', ''))['timestamp'] if contacts else None
                }
                
                return stats, 200
                
            except Exception as e:
                print(f"Error getting stats: {str(e)}")
                return {
                    'error': 'Failed to get statistics'
                }, 500

    # Register API routes
    api.add_resource(_Signup, '/signup')
    api.add_resource(_GetContacts, '/list')
    api.add_resource(_Stats, '/stats')