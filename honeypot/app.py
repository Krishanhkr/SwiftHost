from flask import Flask, jsonify, request, render_template, redirect, url_for, send_from_directory
import logging
import random
import time
import uuid
import os
import json
from datetime import datetime

# Import our custom modules
from data_generator import HoneypotData
from analytics import AttackDetector
from utils.geolocation import IPGeolocation
from threat_intelligence.misp_integration import ThreatIntelSender
from analytics.attacker_profiling import AttackerProfiler
from forensics.blockchain_evidence import BlockchainLogger, log_attack_evidence
# Import deception technology module
from deception import deception_bp, DeceptionAnalytics
# Import Zero Trust security module
from security import ztna_manager, auth_bp, ztna_login_required, ztna_role_required

app = Flask(__name__)

# Set a secret key for session management
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'honeypot_secret_key_change_in_production')

# Register the deception blueprint
app.register_blueprint(deception_bp, url_prefix='/services')
# Register the authentication blueprint
app.register_blueprint(auth_bp, url_prefix='/auth')

# Initialize the Zero Trust manager
ztna_manager.init_app(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('honeypot.log'),
        logging.StreamHandler()
    ]
)

# Initialize our modules
honeypot_data = HoneypotData()
attack_detector = AttackDetector()
geo_locator = IPGeolocation()
threat_intel = ThreatIntelSender()
attacker_profiler = AttackerProfiler()
blockchain_logger = BlockchainLogger()
# Initialize deception analytics
deception_analytics = DeceptionAnalytics()

# Create directories for static content
os.makedirs('static/js', exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/img', exist_ok=True)

# Create a dictionary to track attacker IPs and their behavior
attackers = {}

# Add random delay to simulate real server
def add_random_delay():
    time.sleep(random.uniform(0.5, 2))

# Track and log suspicious activity with our new analytics
def log_suspicious_activity(route, request):
    # Use our new attack detector to analyze the request
    log_entry = attack_detector.analyze_request(request)
    
    # Log the activity
    logging.info(f"HONEYPOT ACTIVITY: {json.dumps(log_entry)}")
    
    return log_entry["threat_level"]

# Middleware to check for deception tracking payloads
@app.before_request
def check_tracked_payloads():
    # Skip for static files
    if request.path.startswith('/static/'):
        return None
        
    # Get request data for checking
    request_data = {}
    if request.is_json:
        request_data = request.get_json()
    elif request.form:
        request_data = request.form.to_dict()
    elif request.args:
        request_data = request.args.to_dict()
        
    # Also check headers and cookies
    headers_dict = {k: v for k, v in request.headers.items()}
    cookies_dict = request.cookies.to_dict() if hasattr(request.cookies, 'to_dict') else dict(request.cookies)
    
    # Combine all data for checking
    all_data = {
        'body': request_data,
        'headers': headers_dict,
        'cookies': cookies_dict,
        'path': request.path
    }
    
    # Check if any tracked payload is in the request
    detection = deception_analytics.detect_tracked_payload_usage(all_data)
    
    if detection:
        # Log the detection
        tracking_info = {
            'route': request.path,
            'method': request.method,
            'ip': request.remote_addr,
            'tracking_info': detection
        }
        logging.warning(f"TRACKED PAYLOAD DETECTED: {json.dumps(tracking_info)}")
        
        # Create a blockchain record of the tracked payload usage
        log_attack_evidence({
            'ip': request.remote_addr,
            'path': request.path,
            'method': request.method,
            'attack_types': ['CREDENTIAL_REUSE', 'TRACKING_PAYLOAD'],
            'threat_score': 0.95,  # High score for credential reuse
            'tracking_info': detection
        }, blockchain_logger)
        
    return None

# Root route - nothing suspicious here
@app.route('/')
def index():
    return render_template('index.html')

# Fake login endpoint
@app.route('/api/login', methods=['POST'])
def fake_login():
    add_random_delay()
    threat_level = log_suspicious_activity('/api/login', request)
    
    # If the attacker has been making many requests, slow them down more
    if threat_level == "MEDIUM":
        time.sleep(random.uniform(3, 5))
    elif threat_level == "HIGH":
        time.sleep(random.uniform(8, 10))
    
    return jsonify({
        "success": False,
        "message": "Invalid credentials"
    }), 401

# Fake users endpoint
@app.route('/api/v1/users')
def fake_users():
    add_random_delay()
    threat_level = log_suspicious_activity('/api/v1/users', request)
    
    # If the attacker has been making many requests, slow them down more
    if threat_level == "MEDIUM":
        time.sleep(random.uniform(3, 5))
    elif threat_level == "HIGH":
        time.sleep(random.uniform(8, 10))
    
    return jsonify({
        "users": honeypot_data.generate_users(50),
        "pagination": {
            "next": f"/api/v1/users?page={random.randint(2,5)}",
            "total": random.randint(1000, 5000)
        },
        "rate_limit": f"{random.randint(90, 100)}/100"
    })

# Fake admin endpoint
@app.route('/admin')
def fake_admin():
    add_random_delay()
    log_suspicious_activity('/admin', request)
    
    return redirect(url_for('fake_login_page'))

# Fake login page
@app.route('/login')
def fake_login_page():
    return render_template('login.html')

# Secure admin login page
@app.route('/secure-login')
def secure_login_page():
    return render_template('secure_login.html')

# Fake transactions endpoint
@app.route('/api/v1/transactions')
def fake_transactions():
    add_random_delay()
    log_suspicious_activity('/api/v1/transactions', request)
    
    return jsonify(honeypot_data.generate_financial_data(20))

# Fake .env file - looks like it leaked into public directory
@app.route('/.env')
def fake_env():
    add_random_delay()
    log_suspicious_activity('/.env', request)
    
    return """
    # Production Environment Variables
    DB_CONNECTION=mysql
    DB_HOST=db.internal.example.com
    DB_PORT=3306
    DB_DATABASE=production_db
    DB_USERNAME=db_user
    DB_PASSWORD=verystr0ngp@ss!
    
    # AWS Configuration
    AWS_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE
    AWS_SECRET_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
    
    # Application
    APP_ENV=production
    APP_KEY=base64:rSVTexa1UwCIwWUJ8oZEhK1+nGEUZqKtw86EO5M2nBk=
    APP_DEBUG=false
    APP_URL=https://example.com
    """

# Fake backup file with "sensitive" data
@app.route('/backup.sql')
def fake_backup():
    add_random_delay()
    log_suspicious_activity('/backup.sql', request)
    
    return """
    -- MySQL dump 10.13  Distrib 5.7.33, for Linux (x86_64)
    --
    -- Database: honeypot_fake_data
    
    CREATE TABLE `users` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `username` varchar(255) NOT NULL,
      `password` varchar(255) NOT NULL,
      `email` varchar(255) NOT NULL,
      PRIMARY KEY (`id`)
    );
    
    INSERT INTO `users` VALUES 
    (1,'admin','$2a$12$fakeHash1','admin@example.com'),
    (2,'john.doe','$2a$12$fakeHash2','john@example.com');
    """

# NEW: Git HEAD endpoint
@app.route('/.git/HEAD')
def fake_git():
    add_random_delay()
    log_suspicious_activity('/.git/HEAD', request)
    
    return "ref: refs/heads/development\n"

# NEW: WordPress config 
@app.route('/wp-admin/config.json')
def fake_wordpress():
    add_random_delay()
    log_suspicious_activity('/wp-admin/config.json', request)
    
    return jsonify({
        "db_creds": honeypot_data.generate_fake_credentials(),
        "admin_user": "wp_admin",
        "admin_hash": "$P$B7fakedhashfakehash12345"
    })

# NEW: System logs endpoint
@app.route('/api/v1/logs')
def fake_logs():
    add_random_delay()
    log_suspicious_activity('/api/v1/logs', request)
    
    return jsonify({
        "logs": honeypot_data.generate_system_logs(30),
        "total": random.randint(500, 2000)
    })

# NEW: User profile image generator
@app.route('/api/v1/users/<user_id>/avatar')
def fake_user_avatar(user_id):
    add_random_delay()
    log_suspicious_activity(f'/api/v1/users/{user_id}/avatar', request)
    
    # Use our DeepFake image generator - would return an actual image in production
    image_data = honeypot_data.generate_deepfake_image()
    
    return jsonify({
        "image_url": f"https://example.com/images/users/{user_id}.jpg",
        "generated": True,
        "metadata": image_data
    })

# Analytics dashboard - would normally be protected
@app.route('/admin/dashboard')
@ztna_login_required
@ztna_role_required(['admin'])
def analytics_dashboard():
    add_random_delay()
    log_suspicious_activity('/admin/dashboard', request)
    
    return render_template('dashboard.html', 
                          analytics=attack_detector.get_attack_analytics())

# 404 handler
@app.errorhandler(404)
def page_not_found(e):
    log_suspicious_activity(request.path, request)
    
    return render_template('404.html'), 404

# Deception analytics dashboard
@app.route('/admin/deception-analytics')
@ztna_login_required
@ztna_role_required(['admin', 'threat_hunter'])
def deception_dashboard():
    # Get attack interaction stats
    attacker_profiles = deception_analytics.analyze_attacker_behavior()
    
    # Get credential tracking report
    tracking_report = deception_analytics.generate_credential_tracking_report()
    
    # Get potential data exfiltration attempts
    exfil_attempts = deception_analytics.identify_data_exfiltration()
    
    return render_template(
        'deception_dashboard.html',
        profiles=attacker_profiles,
        tracking_report=tracking_report,
        exfil_attempts=exfil_attempts,
        stats={
            'total_attackers': len(attacker_profiles),
            'tracked_payloads': len(tracking_report.get('payloads', [])),
            'exfil_attempts': len(exfil_attempts)
        }
    )

# ZTNA Security Dashboard
@app.route('/admin/security/ztna')
@ztna_login_required
@ztna_role_required(['admin'])
def ztna_dashboard():
    # Get all device fingerprints
    device_data = ztna_manager.device_fingerprints
    
    # Get recent access logs (last 100)
    recent_logs = access_logs[-100:] if len(access_logs) > 0 else []
    
    # Count denied vs allowed access attempts
    denied_count = sum(1 for log in recent_logs if not log.get('success', False))
    allowed_count = sum(1 for log in recent_logs if log.get('success', True))
    
    # Group by reason for denial
    denial_reasons = {}
    for log in recent_logs:
        if not log.get('success', False):
            reason = log.get('reason', 'Unknown')
            denial_reasons[reason] = denial_reasons.get(reason, 0) + 1
    
    # Get user login status
    user_sessions = {}
    for username, data in failed_authentication.items():
        user_sessions[username] = {
            'failed_attempts': data.get('count', 0),
            'lockout_until': data.get('lockout_until'),
            'status': 'Locked' if data.get('lockout_until') and data.get('lockout_until') > datetime.now() else 'Active'
        }
    
    return render_template(
        'ztna_dashboard.html',
        device_count=len(device_data),
        access_logs=recent_logs,
        denied_count=denied_count,
        allowed_count=allowed_count,
        denial_reasons=denial_reasons,
        user_sessions=user_sessions,
        device_data=device_data
    )

# ZTNA Policy Management
@app.route('/admin/security/policies')
@ztna_login_required
@ztna_role_required(['admin'])
def ztna_policies():
    return render_template(
        'ztna_policies.html',
        config=ZTNA_CONFIG
    )

# ZTNA Device Management
@app.route('/admin/security/devices')
@ztna_login_required
@ztna_role_required(['admin'])
def ztna_devices():
    # Sort devices by trust score
    sorted_devices = sorted(
        ztna_manager.device_fingerprints.items(),
        key=lambda x: x[1].get('trust_score', 0),
        reverse=True
    )
    
    return render_template(
        'ztna_devices.html',
        devices=sorted_devices
    )

# ZTNA User Management
@app.route('/admin/security/users')
@ztna_login_required
@ztna_role_required(['admin'])
def ztna_users():
    return render_template(
        'ztna_users.html',
        users=USERS,
        failed_auth=failed_authentication
    )

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Create basic templates for the honeypot
    with open('templates/index.html', 'w') as f:
        f.write("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Example Company</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                .container { max-width: 800px; margin: 0 auto; }
                .header { border-bottom: 1px solid #eee; padding-bottom: 20px; margin-bottom: 20px; }
                .footer { border-top: 1px solid #eee; padding-top: 20px; margin-top: 20px; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Example Company</h1>
                    <p>Innovative solutions for modern challenges</p>
                </div>
                <div class="content">
                    <h2>Welcome to Our Website</h2>
                    <p>This is a demonstration website. Our company specializes in providing cutting-edge solutions to meet your business needs.</p>
                    <p>Please <a href="/login">login</a> to access your account.</p>
                </div>
                <div class="footer">
                    <p>&copy; 2023 Example Company. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """)
    
    with open('templates/login.html', 'w') as f:
        f.write("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login - Example Company</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                .container { max-width: 400px; margin: 0 auto; }
                .header { border-bottom: 1px solid #eee; padding-bottom: 20px; margin-bottom: 20px; }
                .footer { border-top: 1px solid #eee; padding-top: 20px; margin-top: 20px; font-size: 12px; }
                .form-group { margin-bottom: 15px; }
                label { display: block; margin-bottom: 5px; }
                input[type="text"], input[type="password"] { width: 100%; padding: 8px; box-sizing: border-box; }
                button { padding: 10px 15px; background-color: #4CAF50; color: white; border: none; cursor: pointer; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Login</h1>
                    <p>Please enter your credentials to access your account.</p>
                </div>
                <div class="content">
                    <form id="login-form" onsubmit="return false;">
                        <div class="form-group">
                            <label for="username">Username:</label>
                            <input type="text" id="username" name="username" required>
                        </div>
                        <div class="form-group">
                            <label for="password">Password:</label>
                            <input type="password" id="password" name="password" required>
                        </div>
                        <button type="button" onclick="attemptLogin()">Login</button>
                    </form>
                    <p id="error-message" style="color: red; display: none;">Invalid username or password.</p>
                </div>
                <div class="footer">
                    <p>&copy; 2023 Example Company. All rights reserved.</p>
                </div>
            </div>
            <script>
            function attemptLogin() {
                document.getElementById('error-message').style.display = 'block';
                fetch('/api/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        username: document.getElementById('username').value,
                        password: document.getElementById('password').value
                    })
                });
            }
            </script>
        </body>
        </html>
        """)
    
    with open('templates/404.html', 'w') as f:
        f.write("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>404 - Page Not Found</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                .container { max-width: 800px; margin: 0 auto; text-align: center; }
                .error-code { font-size: 120px; margin-bottom: 0; color: #e74c3c; }
                .error-message { font-size: 24px; margin-top: 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="error-code">404</h1>
                <p class="error-message">Page Not Found</p>
                <p>The page you are looking for does not exist or has been moved.</p>
                <p><a href="/">Return to Home</a></p>
            </div>
        </body>
        </html>
        """)

    # Create dashboard template
    with open('templates/dashboard.html', 'w') as f:
        f.write("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Security Dashboard - Example Company</title>
            <link rel="stylesheet" href="/static/css/attack-map.css">
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; }
                .header { background-color: #333; color: white; padding: 20px; border-radius: 5px 5px 0 0; }
                .dashboard { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-top: 20px; }
                .card { background-color: white; border-radius: 5px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .card h3 { margin-top: 0; color: #333; border-bottom: 1px solid #eee; padding-bottom: 10px; }
                .metric { font-size: 24px; font-weight: bold; margin: 10px 0; }
                .table { width: 100%; border-collapse: collapse; }
                .table th, .table td { padding: 8px; text-align: left; border-bottom: 1px solid #eee; }
                .table th { background-color: #f9f9f9; }
                .high { color: #e74c3c; }
                .medium { color: #f39c12; }
                .low { color: #3498db; }
                .full-width { grid-column: span 2; }
                .tabs { display: flex; border-bottom: 1px solid #ddd; margin-bottom: 20px; }
                .tab { padding: 10px 15px; cursor: pointer; margin-right: 5px; }
                .tab.active { border-bottom: 3px solid #3498db; font-weight: bold; }
                .tab-content { display: none; }
                .tab-content.active { display: block; }
                .flex-container { display: flex; justify-content: space-between; }
                .profile-badge { 
                    padding: 10px; 
                    border-radius: 5px; 
                    margin-bottom: 10px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .profile-badge.script-kiddie { background-color: rgba(52, 152, 219, 0.1); border-left: 4px solid #3498db; }
                .profile-badge.opportunistic { background-color: rgba(243, 156, 18, 0.1); border-left: 4px solid #f39c12; }
                .profile-badge.advanced { background-color: rgba(231, 76, 60, 0.1); border-left: 4px solid #e74c3c; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Security Dashboard</h1>
                    <p>Honeypot Attack Analytics</p>
                </div>
                
                <div class="tabs">
                    <div class="tab active" data-tab="overview">Overview</div>
                    <div class="tab" data-tab="attack-map">Attack Map</div>
                    <div class="tab" data-tab="profiles">Attacker Profiles</div>
                    <div class="tab" data-tab="forensics">Forensic Evidence</div>
                </div>
                
                <!-- Overview Tab -->
                <div class="tab-content active" id="overview">
                    <div class="dashboard">
                        <div class="card">
                            <h3>Attack Overview</h3>
                            <div class="metric">Total Attackers: {{ analytics.total_attackers }}</div>
                            <div class="metric">High Threat Attackers: <span class="high">{{ analytics.high_threat_attackers }}</span></div>
                        </div>
                        
                        <div class="card">
                            <h3>Top Attack Types</h3>
                            <table class="table">
                                <thead>
                                    <tr>
                                        <th>Attack Type</th>
                                        <th>Count</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for attack_type, count in analytics.top_attack_types %}
                                    <tr>
                                        <td>{{ attack_type }}</td>
                                        <td>{{ count }}</td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                        
                        <div class="card">
                            <h3>Most Targeted Resources</h3>
                            <table class="table">
                                <thead>
                                    <tr>
                                        <th>Path</th>
                                        <th>Hits</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for path, count in analytics.top_requested_paths %}
                                    <tr>
                                        <td>{{ path }}</td>
                                        <td>{{ count }}</td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                        
                        <div class="card">
                            <h3>Recent High Threat Activity</h3>
                            <table class="table">
                                <thead>
                                    <tr>
                                        <th>Time</th>
                                        <th>Threat Score</th>
                                        <th>Attack Types</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for attack in analytics.recent_attacks %}
                                    <tr>
                                        <td>{{ attack.last_seen }}</td>
                                        <td class="{% if attack.threat_score > 0.7 %}high{% elif attack.threat_score > 0.4 %}medium{% else %}low{% endif %}">
                                            {{ "%.2f"|format(attack.threat_score) }}
                                        </td>
                                        <td>{{ attack.attack_types|join(', ') }}</td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                
                <!-- Attack Map Tab -->
                <div class="tab-content" id="attack-map">
                    <div class="dashboard">
                        <div class="card full-width">
                            <h3>Attack Geolocation Map</h3>
                            <div id="map-container"></div>
                        </div>
                        
                        <div class="card">
                            <h3>Top Origin Countries</h3>
                            <div id="country-stats">Loading...</div>
                        </div>
                        
                        <div class="card">
                            <h3>Realtime Attacks</h3>
                            <div id="realtime-attacks">Loading...</div>
                        </div>
                    </div>
                </div>
                
                <!-- Attacker Profiles Tab -->
                <div class="tab-content" id="profiles">
                    <div class="dashboard">
                        <div class="card">
                            <h3>Attacker Classification</h3>
                            <div class="metric">Script Kiddies: <span class="low">{{ profiles.stats.script_kiddies_pct|round|int }}%</span></div>
                            <div class="metric">Opportunistic: <span class="medium">{{ profiles.stats.opportunistic_pct|round|int }}%</span></div>
                            <div class="metric">Advanced Attackers: <span class="high">{{ profiles.stats.advanced_attackers_pct|round|int }}%</span></div>
                        </div>
                        
                        <div class="card">
                            <h3>Advanced Attacker Profiles</h3>
                            <div id="advanced-attackers">
                                {% for ip in profiles.advanced_attackers[:5] %}
                                <div class="profile-badge advanced">
                                    <span>{{ ip }}</span>
                                    <span class="high">Advanced</span>
                                </div>
                                {% else %}
                                <p>No advanced attackers detected</p>
                                {% endfor %}
                            </div>
                        </div>
                        
                        <div class="card">
                            <h3>Opportunistic Attacker Profiles</h3>
                            <div id="opportunistic-attackers">
                                {% for ip in profiles.opportunistic[:5] %}
                                <div class="profile-badge opportunistic">
                                    <span>{{ ip }}</span>
                                    <span class="medium">Opportunistic</span>
                                </div>
                                {% else %}
                                <p>No opportunistic attackers detected</p>
                                {% endfor %}
                            </div>
                        </div>
                        
                        <div class="card">
                            <h3>Script Kiddie Profiles</h3>
                            <div id="script-kiddies">
                                {% for ip in profiles.script_kiddies[:5] %}
                                <div class="profile-badge script-kiddie">
                                    <span>{{ ip }}</span>
                                    <span class="low">Script Kiddie</span>
                                </div>
                                {% else %}
                                <p>No script kiddies detected</p>
                                {% endfor %}
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Forensic Evidence Tab -->
                <div class="tab-content" id="forensics">
                    <div class="dashboard">
                        <div class="card full-width">
                            <h3>Blockchain-Verified Forensic Evidence</h3>
                            <div id="blockchain-evidence">Loading evidence...</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <script src="/static/js/attackMap.js"></script>
            <script>
                // Initialize tabs
                document.querySelectorAll('.tab').forEach(tab => {
                    tab.addEventListener('click', () => {
                        // Remove active class from all tabs and content
                        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                        
                        // Add active class to clicked tab and corresponding content
                        tab.classList.add('active');
                        document.getElementById(tab.dataset.tab).classList.add('active');
                    });
                });
                
                // Load attack map data
                fetch('/api/attack-map')
                    .then(response => response.json())
                    .then(data => {
                        // Initialize map with data
                        const map = new AttackMap('map-container');
                        map.updateAttacks(data);
                        
                        // Update country stats
                        const countryStats = document.getElementById('country-stats');
                        const countries = {};
                        
                        data.forEach(attack => {
                            if (attack.country) {
                                countries[attack.country] = (countries[attack.country] || 0) + 1;
                            }
                        });
                        
                        const countryList = Object.entries(countries)
                            .sort((a, b) => b[1] - a[1])
                            .map(([country, count]) => `<div>${country}: ${count}</div>`)
                            .join('');
                            
                        countryStats.innerHTML = countryList || 'No country data available';
                        
                        // Update realtime attacks
                        const realtimeAttacks = document.getElementById('realtime-attacks');
                        const recentAttacks = data
                            .sort((a, b) => b.threat_score - a.threat_score)
                            .slice(0, 5)
                            .map(attack => {
                                const threatClass = attack.threat_score > 0.7 ? 'high' : 
                                                  attack.threat_score > 0.4 ? 'medium' : 'low';
                                return `
                                    <div class="profile-badge ${threatClass === 'high' ? 'advanced' : threatClass === 'medium' ? 'opportunistic' : 'script-kiddie'}">
                                        <span>${attack.ip} (${attack.country || 'Unknown'})</span>
                                        <span class="${threatClass}">${attack.threat_score.toFixed(2)}</span>
                                    </div>
                                `;
                            })
                            .join('');
                            
                        realtimeAttacks.innerHTML = recentAttacks || 'No recent attacks';
                    });
                
                // Load forensic evidence
                fetch('/api/forensic-evidence')
                    .then(response => response.json())
                    .then(data => {
                        const evidenceContainer = document.getElementById('blockchain-evidence');
                        
                        if (data.length === 0) {
                            evidenceContainer.innerHTML = 'No forensic evidence recorded yet';
                            return;
                        }
                        
                        // Create evidence table
                        let evidenceHtml = `
                            <table class="table">
                                <thead>
                                    <tr>
                                        <th>Evidence ID</th>
                                        <th>Attacker IP</th>
                                        <th>Type</th>
                                        <th>Timestamp</th>
                                        <th>Block #</th>
                                        <th>Action</th>
                                    </tr>
                                </thead>
                                <tbody>
                        `;
                        
                        data.forEach(evidence => {
                            evidenceHtml += `
                                <tr>
                                    <td>${evidence.evidence_id}</td>
                                    <td>${evidence.attack_ip}</td>
                                    <td>${evidence.evidence_type}</td>
                                    <td>${evidence.timestamp}</td>
                                    <td>${evidence.block_index}</td>
                                    <td><button onclick="verifyEvidence('${evidence.evidence_id}')">Verify</button></td>
                                </tr>
                            `;
                        });
                        
                        evidenceHtml += `
                                </tbody>
                            </table>
                            <div id="verification-result"></div>
                        `;
                        
                        evidenceContainer.innerHTML = evidenceHtml;
                    });
                    
                // Function to verify evidence
                function verifyEvidence(evidenceId) {
                    fetch(`/api/forensic-evidence/${evidenceId}/verify`)
                        .then(response => response.json())
                        .then(data => {
                            const resultContainer = document.getElementById('verification-result');
                            
                            if (data.verified) {
                                resultContainer.innerHTML = `
                                    <div style="margin-top: 20px; padding: 10px; background-color: #d4edda; border-radius: 5px; border-left: 4px solid #28a745;">
                                        <strong>Verification Successful:</strong> Evidence ${evidenceId} integrity verified with blockchain.
                                    </div>
                                `;
                            } else {
                                resultContainer.innerHTML = `
                                    <div style="margin-top: 20px; padding: 10px; background-color: #f8d7da; border-radius: 5px; border-left: 4px solid #dc3545;">
                                        <strong>Verification Failed:</strong> ${data.error}
                                    </div>
                                `;
                            }
                        });
                }
            </script>
        </body>
        </html>
        """)
    
    # Copy attack map JS to static directory
    with open('static/js/attackMap.js', 'w') as f:
        f.write("""// Attack Map Visualization
// This will be loaded by the dashboard to show geolocation of attacks

class AttackMap {
  constructor(elementId) {
    this.mapElement = document.getElementById(elementId);
    this.attacks = [];
    this.map = null;
    this.markers = [];
    
    // Initialize the map
    this.initMap();
  }
  
  initMap() {
    // Create a basic world map using Leaflet.js
    // Note: In a production environment, you would use the actual Leaflet library
    // This is a simplified version for demonstration purposes
    this.mapElement.innerHTML = `
      <div class="attack-map-container">
        <div class="map-overlay">
          <h3>Live Attack Map</h3>
          <div class="map-stats">
            <span id="active-attackers">0</span> active attackers
          </div>
        </div>
        <div id="map-canvas" class="map-canvas"></div>
      </div>
    `;
    
    // In a real implementation, you would initialize the map here
    // For example: this.map = L.map('map-canvas').setView([0, 0], 2);
    console.log("Map initialized");
  }
  
  async updateAttacks(attacks) {
    this.attacks = attacks;
    
    // Clear existing markers
    this.markers = [];
    
    // In a real implementation, you would:
    // 1. Geolocate IPs that haven't been geolocated yet
    // 2. Add markers for each attack
    // 3. Create heatmap overlays for attack hotspots
    
    document.getElementById('active-attackers').textContent = attacks.length;
    
    // Log for demonstration
    console.log(`Updated map with ${attacks.length} attacks`);
    
    // Simulate rendering of attacks
    this.renderAttackList();
    this.renderMockMarkers();
  }
  
  renderAttackList() {
    // Create a simple list of attacks below the map for demonstration
    let listHTML = '<div class="attack-list"><h4>Recent Attacks</h4><ul>';
    
    this.attacks.slice(0, 5).forEach(attack => {
      const threatClass = attack.threat_score > 0.7 ? 'high-threat' : 
                          attack.threat_score > 0.4 ? 'medium-threat' : 'low-threat';
      
      listHTML += `
        <li class="${threatClass}">
          <span class="attack-ip">${attack.ip}</span>
          <span class="attack-country">${attack.country || 'Unknown'}</span>
          <span class="attack-score">Score: ${attack.threat_score.toFixed(2)}</span>
        </li>
      `;
    });
    
    listHTML += '</ul></div>';
    
    // Append to map container
    const listContainer = document.createElement('div');
    listContainer.innerHTML = listHTML;
    
    // Remove existing list if present
    const existingList = this.mapElement.querySelector('.attack-list');
    if (existingList) {
      existingList.remove();
    }
    
    this.mapElement.appendChild(listContainer);
  }
  
  renderMockMarkers() {
    // Create mock markers on the map canvas
    const canvas = document.getElementById('map-canvas');
    
    // Clear existing markers
    const existingMarkers = canvas.querySelectorAll('.map-marker');
    existingMarkers.forEach(marker => marker.remove());
    
    // Add markers for each attack
    this.attacks.forEach(attack => {
      if (attack.latitude && attack.longitude) {
        // Calculate position on the map
        // This is a very simple mapping from lat/long to pixels
        // In a real implementation, use a proper mapping library
        const x = ((attack.longitude + 180) / 360) * canvas.offsetWidth;
        const y = ((90 - attack.latitude) / 180) * canvas.offsetHeight;
        
        // Create marker element
        const marker = document.createElement('div');
        marker.className = 'map-marker';
        marker.classList.add(attack.threat_score > 0.7 ? 'high' : 
                            attack.threat_score > 0.4 ? 'medium' : 'low');
        marker.style.left = `${x}px`;
        marker.style.top = `${y}px`;
        
        // Add tooltip
        marker.title = `${attack.ip} (${attack.country || 'Unknown'})
Score: ${attack.threat_score.toFixed(2)}
Attacks: ${attack.count}`;
        
        canvas.appendChild(marker);
      }
    });
  }
  
  // Helper function to get color based on threat score
  getThreatColor(score) {
    if (score > 0.7) return '#EF4444'; // Red for high threat
    if (score > 0.4) return '#F59E0B'; // Orange for medium threat
    return '#3B82F6'; // Blue for low threat
  }
}

// Make available globally
window.AttackMap = AttackMap;""")
    
    # Copy attack map CSS to static directory
    with open('static/css/attack-map.css', 'w') as f:
        f.write(""".attack-map-container {
    position: relative;
    width: 100%;
    height: 400px;
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 20px;
    border: 1px solid #ddd;
    background-color: #f8f9fa;
}

.map-canvas {
    width: 100%;
    height: 100%;
    background-image: url('https://openlayers.org/en/latest/examples/data/crossorigin.jpg');
    background-size: cover;
    background-position: center;
    position: relative;
}

.map-overlay {
    position: absolute;
    top: 10px;
    left: 10px;
    z-index: 1000;
    background-color: rgba(255, 255, 255, 0.8);
    padding: 10px;
    border-radius: 4px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.map-stats {
    margin-top: 5px;
    font-size: 14px;
}

#active-attackers {
    font-weight: bold;
    color: #e74c3c;
}

.attack-list {
    margin-top: 20px;
    background: white;
    border-radius: 8px;
    padding: 15px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.attack-list h4 {
    margin-top: 0;
    border-bottom: 1px solid #eee;
    padding-bottom: 10px;
}

.attack-list ul {
    list-style: none;
    padding: 0;
    margin: 0;
}

.attack-list li {
    padding: 8px 10px;
    margin-bottom: 5px;
    border-left: 4px solid #ccc;
    display: flex;
    justify-content: space-between;
}

.attack-list li.high-threat {
    border-left-color: #e74c3c;
    background-color: rgba(231, 76, 60, 0.1);
}

.attack-list li.medium-threat {
    border-left-color: #f39c12;
    background-color: rgba(243, 156, 18, 0.1);
}

.attack-list li.low-threat {
    border-left-color: #3498db;
    background-color: rgba(52, 152, 219, 0.1);
}

.attack-ip {
    font-family: monospace;
    font-weight: bold;
}

.attack-country {
    color: #555;
}

.attack-score {
    font-weight: bold;
}

.high-threat .attack-score {
    color: #e74c3c;
}

.medium-threat .attack-score {
    color: #f39c12;
}

.low-threat .attack-score {
    color: #3498db;
}

/* Map marker animation */
@keyframes pulse {
    0% {
        transform: scale(1);
        opacity: 1;
    }
    50% {
        transform: scale(1.5);
        opacity: 0.7;
    }
    100% {
        transform: scale(1);
        opacity: 1;
    }
}

.map-marker {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    position: absolute;
    transform: translate(-50%, -50%);
}

.map-marker.high {
    background-color: #e74c3c;
    box-shadow: 0 0 10px #e74c3c;
    animation: pulse 1.5s infinite;
}

.map-marker.medium {
    background-color: #f39c12;
    box-shadow: 0 0 8px #f39c12;
    animation: pulse 2s infinite;
}

.map-marker.low {
    background-color: #3498db;
    box-shadow: 0 0 6px #3498db;
    animation: pulse 2.5s infinite;
}""")
    
    # Create a simple world map image placeholder
    os.makedirs('static/img', exist_ok=True)
    
    app.run(host='0.0.0.0', port=5000, debug=True) 