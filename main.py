# imports from flask
import json
import os
from urllib.parse import urljoin, urlparse
from flask import abort, redirect, render_template, request, send_from_directory, url_for, jsonify
from flask_login import current_user, login_user, logout_user
from flask.cli import AppGroup
from flask_login import current_user, login_required
from flask import current_app, send_file
from werkzeug.security import generate_password_hash
import shutil
from functools import wraps
import requests
from api.border_checker import start_checker  # Import the border checker
import threading
# import "objects" from "this" project
from __init__ import app, db, login_manager  # Key Flask objects 
# API endpoints
from api.user import user_api 
from api.pfp import pfp_api
from api.post import post_api
from api.channel import channel_api
from api.group import group_api
from api.section import section_api
from api.chat import chat_api
from api.interests import interests_api  # Import the new interests API
from api.chat_met import chat_met_api
from api.usettings import settings_api
from api.user_met import user_met_api
from api.post_met import post_met_api
from api.health import health_api
from api.accident import accident_api
from api.cancer import cancer_api
from api.estonia import estonia_api
from api.titanic import titanic_api
from api.border import border_api
from api.timelapse import timelapse_api
from api.user_facial import facial_api
from api.historicalgraph_api import historicalgraph_api
from api.border_email import border_email_api
from api.border_sms import sms_api
from api.weather_api import weather_api
from api.traffic_report import traffic_report_api
from api.border_feedback import border_feedback_api
from api.contact import contact_api
from api.twitter_search import run_border_queries

# database Initialization functions
from model.user import User, initUsers
from model.section import Section, initSections
from model.group import Group, initGroups
from model.channel import Channel, initChannels
from model.post import Post, initPosts
from model.vote import Vote, initVotes
from model.player import Player, initPlayers
from model.poll import Poll, initPolls
from model.school_classes import SchoolClass, initSchoolClasses
from model.language import Language, initLanguages
from model.chat import Chat, initChats
from model.help_request import HelpRequest, initHelpRequests
from model.timelapse import TimelapseModel
from model.facial_encoding import FacialEncoding5c


from model.topusers import TopUser
from model.usettings import Settings  # Import the Settings model
from model.accident import AccidentModel
from model.cancer import CancerModel
from model.estonia import EstoniaModel
from model.help_request import HelpRequest
from model.titanic import TitanicModel
from model.traffic_report import TrafficReport, initTrafficReports

# server only Views

# register URIs for api endpoints
app.register_blueprint(user_api)
app.register_blueprint(pfp_api) 
app.register_blueprint(post_api)
app.register_blueprint(channel_api)
app.register_blueprint(group_api)
app.register_blueprint(section_api)
app.register_blueprint(weather_api)
app.register_blueprint(chat_api)
app.register_blueprint(interests_api)
app.register_blueprint(chat_met_api)
app.register_blueprint(timelapse_api)
app.register_blueprint(user_met_api)
app.register_blueprint(post_met_api)
app.register_blueprint(health_api)
app.register_blueprint(accident_api)
app.register_blueprint(cancer_api)
app.register_blueprint(estonia_api)
app.register_blueprint(titanic_api)
app.register_blueprint(border_api)
app.register_blueprint(facial_api)
app.register_blueprint(historicalgraph_api)  # Register the new historical graph API
app.register_blueprint(border_email_api)
app.register_blueprint(sms_api)
app.register_blueprint(border_feedback_api)
app.register_blueprint(traffic_report_api)
app.register_blueprint(contact_api)
# Tell Flask-Login the view function name of your login route
login_manager.login_view = "login"

@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect(url_for('login', next=request.path))

# register URIs for server pages
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_user():
    return dict(current_user=current_user)

# Helper function to check if the URL is safe for redirects
def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'Admin':
            return redirect(url_for('unauthorized'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    next_page = request.args.get('next', '') or request.form.get('next', '')
    if request.method == 'POST':
        user = User.query.filter_by(_uid=request.form['username']).first()
        if user and user.is_password(request.form['password']):
            login_user(user)
            if not is_safe_url(next_page):
                return abort(400)
            if user.role == 'Admin':
                return redirect(next_page or url_for('index'))
            else:
                return redirect(next_page or url_for('user_index'))
        else:
            error = 'Invalid username or password.'
    return render_template("login.html", error=error, next=next_page)
    
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.errorhandler(404)  # catch for URL not found
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404

@app.route('/')  # connects default URL to index() function
def index():
    if current_user.is_authenticated and current_user.role == 'Admin':
        return render_template("index.html")
    elif current_user.is_authenticated:
        return render_template("user_index.html")
    return render_template("login.html")

@app.route('/unauthorized')
def unauthorized():
    return render_template('unauthorized.html'), 401

@app.route('/user_index')
@login_required
def user_index():
    return render_template("user_index.html")

@app.route('/users/table')
@login_required
def utable():
    users = User.query.all()
    return render_template("utable.html", user_data=users)

@app.route('/users/table2')
@login_required
def u2table():
    users = User.query.all()
    return render_template("u2table.html", user_data=users)

@app.route('/users/bordernotifs')
@login_required
def bordernotifs():
    users = User.query.all()
    return render_template("bordernotifs.html", user_data=users)

@app.route("/data/weather")
def get_weather_csv():
    return send_file("datasets/san_diego_weather.csv", mimetype="text/csv")

@app.route('/data/<month>')
def get_month_data(month):
    path_map = {
        "january": "datasets/january.json",
        "february": "datasets/february.json",
        "march": "datasets/march.json",
        "april": "datasets/april.json"
    }

    if month not in path_map:
        return jsonify({"error": "Invalid month"}), 404

    try:
        with open(path_map[month], 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/users/data_dashboard')
def data_dashboard():
    return render_template("data_dashboard.html")

@app.route('/users/votedata')
@admin_required
@login_required
def uvote():
    users = User.query.all()
    return render_template("uvote.html", user_data=users)

@app.route('/postdata')
@admin_required
@login_required
def postData():
    users = User.query.all()
    return render_template("postData.html", user_data=users)

@app.route('/chatdata')
@admin_required
@login_required
def chatData():
    users = User.query.all()
    return render_template("chatData.html", user_data=users)

@app.route('/languagedata')
@admin_required
@login_required
def languageData():
    users = User.query.all()
    return render_template("languageData.html", user_data=users)

@app.route('/pollData')
@admin_required
@login_required
def pollData():
    users = User.query.all()
    return render_template("pollData.html", user_data=users)

@app.route('/users/settings')
@admin_required
@login_required
def usettings():
    users = User.query.all()
    return render_template("usettings.html", user_data=users)

@app.route('/users/reports')
@admin_required
@login_required
def ureports():
    users = User.query.all()
    return render_template("ureports.html", user_data=users)

@app.route('/api/proxy/waittimes')
def proxy_waittimes():
    try:
        response = requests.get('https://bwt.cbp.gov/api/waittimes')
        response.raise_for_status()
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/users/health', methods=['GET'])
@admin_required
@login_required
def uhealth():
    users = User.query.all()
    return render_template("uhealth.html", user_data=users)

@app.route("/users/help", methods=["GET"])
@admin_required
@login_required
def uhelp():
    users = HelpRequest.query.all()
    print(users[0])
    return render_template("uhelp.html", user_data=users)

@app.route('/general-settings', methods=['GET', 'POST'])
@login_required
@admin_required
def general_settings():
    settings = Settings.query.first()
    if request.method == 'POST':
        settings.description = request.form['description']
        settings.contact_email = request.form['contact_email']
        settings.contact_phone = request.form['contact_phone']
        db.session.commit()
        return redirect(url_for('general_settings'))
    return render_template('ugeneralsettings.html', settings=settings)

# Helper function to extract uploads for a user (ie PFP image)
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
 
@app.route('/users/delete/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        user.delete()
        return jsonify({'message': 'User deleted successfully'}), 200
    return jsonify({'error': 'User not found'}), 404

@app.route('/users/reset_password/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def reset_password(user_id):
    if current_user.role != 'Admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Set the new password
    if user.update({"password": app.config['DEFAULT_PASSWORD']}):
        return jsonify({'message': 'Password reset successfully'}), 200
    return jsonify({'error': 'Password reset failed'}), 500

# Create an AppGroup for custom commands
custom_cli = AppGroup('custom', help='Custom commands')

# Define a command to run the data generation functions
@custom_cli.command('generate_data')
def generate_data():
    initUsers()
    initSections()
    initGroups()
    initChannels()
    initPosts()
    initChats()
    initVotes()
    initSchoolClasses()
    initPlayers()
    initLanguages()
    initPolls()
    initHelpRequests()
    initTrafficReports()


# Backup the old database
def backup_database(db_uri, backup_uri):
    """Backup the current database."""
    if backup_uri:
        db_path = db_uri.replace('sqlite:///', 'instance/')
        backup_path = backup_uri.replace('sqlite:///', 'instance/')
        shutil.copyfile(db_path, backup_path)
        print(f"Database backed up to {backup_path}")
    else:
        print("Backup not supported for production database.")

# Extract data from the existing database
def extract_data():
    data = {}
    with app.app_context():
        data['users'] = [user.read() for user in User.query.all()]
        data['sections'] = [section.read() for section in Section.query.all()]
        data['groups'] = [group.read() for group in Group.query.all()]
        data['channels'] = [channel.read() for channel in Channel.query.all()]
        data['school_classes'] = [school_class.read() for school_class in SchoolClass.query.all()]
        data['chat'] = [chat.read() for chat in Chat.query.all()]
        data['votes'] = [vote.read() for vote in Vote.query.all()]
        data['languages'] = [language.read() for language in Language.query.all()]
        data['polls'] = [poll.read() for poll in Poll.query.all()]
    return data

# Save extracted data to JSON files
def save_data_to_json(data, directory='backup'):
    if not os.path.exists(directory):
        os.makedirs(directory)
    for table, records in data.items():
        with open(os.path.join(directory, f'{table}.json'), 'w') as f:
            json.dump(records, f)
    print(f"Data backed up to {directory} directory.")

# Load data from JSON files
def load_data_from_json(directory='backup'):
    data = {}
    for table in ['polls', 'users', 'sections', 'groups', 'channels', 'school_classes', 'votes', 'team_members', 'top_interests', 'chat', 'languages']:
        with open(os.path.join(directory, f'{table}.json'), 'r') as f:
            data[table] = json.load(f)
    return data

def restore_data(data):
    with app.app_context():
        users = User.restore(data['users'])
        _ = Section.restore(data['sections'])
        _ = Group.restore(data['groups'], users)
        _ = Channel.restore(data['channels'])
        _ = SchoolClass.restore(data['school_classes'])
        _ = Poll.restore(data['polls'])
        _ = Vote.restore(data['votes'])
        _ = Chat.restore(data['chat'])
        # _ = Player.restore(data['player'])
        _ = Language.restore(data['languages'])
    print("Data restored to the new database.")

# Define a command to backup data
@custom_cli.command('backup_data')
def backup_data():
    data = extract_data()
    save_data_to_json(data)
    backup_database(app.config['SQLALCHEMY_DATABASE_URI'], app.config['SQLALCHEMY_BACKUP_URI'])

# Define a command to restore data
@custom_cli.command('restore_data')
def restore_data_command():
    data = load_data_from_json()
    restore_data(data)
    
# Register the custom command group with the Flask application
app.cli.add_command(custom_cli)
        
# this runs the flask application on the development server
if __name__ == "__main__":
    # Start Twitter scraper in background
    def twitter_scraper_thread():
        with app.app_context():
            print("🚀 [Startup] Running Twitter scraper background task...")
            run_border_queries()
            print("✅ [Startup] Twitter scrape completed.")

    threading.Thread(target=twitter_scraper_thread).start()

    app.run(debug=True, host="0.0.0.0", port="3167")
