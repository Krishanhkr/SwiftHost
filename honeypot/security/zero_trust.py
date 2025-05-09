#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Zero Trust Network Access (ZTNA) Module
--------------------------------------
Implements ZTNA principles for honeypot security: continuous verification,
least privilege access, and encrypted micro-segmentation.
"""

import os
import json
import time
import uuid
import logging
import hashlib
import ipaddress
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, session, g, redirect, url_for
import jwt
import requests

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('ztna_security')

# Configuration - would typically be loaded from environment or config file
ZTNA_CONFIG = {
    "token_secret": os.getenv("ZTNA_TOKEN_SECRET", "honeypot_ztna_secret_key"),
    "token_expiry": int(os.getenv("ZTNA_TOKEN_EXPIRY", "1800")),  # 30 minutes
    "allowed_networks": os.getenv("ZTNA_ALLOWED_NETWORKS", "10.0.0.0/8,172.16.0.0/12,192.168.0.0/16").split(","),
    "high_risk_countries": os.getenv("ZTNA_HIGH_RISK_COUNTRIES", "").split(","),
    "enforce_device_verification": os.getenv("ZTNA_ENFORCE_DEVICE", "false").lower() == "true",
    "privileged_roles": ["admin", "security_analyst", "threat_hunter"],
    "service_mesh_enabled": os.getenv("ZTNA_SERVICE_MESH", "false").lower() == "true",
    "max_failed_attempts": int(os.getenv("ZTNA_MAX_FAILED_ATTEMPTS", "5")),
    "lockout_duration": int(os.getenv("ZTNA_LOCKOUT_DURATION", "1800")),  # 30 minutes
}

# Track security-related data
device_fingerprints = {}  # Map of device fingerprints to trust scores
failed_authentication = {}  # Track failed auth attempts
access_logs = []  # Store ZTNA access logs
blocked_tokens = set()  # Revoked tokens

class ZeroTrustManager:
    """Manages ZTNA policies and enforcement"""
    
    def __init__(self, app=None):
        self.app = app
        self.device_trust_threshold = 0.5
        self.trusted_device_threshold = 0.8
        
        # Initialize storage for access logs
        self.logs_dir = 'security/ztna_logs'
        os.makedirs(self.logs_dir, exist_ok=True)
        
        if app is not None:
            self.init_app(app)
            
    def init_app(self, app):
        """Initialize the ZTNA manager with a Flask app"""
        self.app = app
        
        # Register before_request handler
        app.before_request(self.ztna_request_handler)
        
        # Register error handler
        app.errorhandler(403)(self.ztna_access_denied_handler)
        
        logger.info("ZTNA security layer initialized")
    
    def ztna_request_handler(self):
        """Main ZTNA request handler executed before each request"""
        # Skip for static files and whitelisted paths
        if request.path.startswith('/static/') or request.path in ['/login', '/']:
            return None
            
        # 1. Device Fingerprinting and Verification
        device_fingerprint = self.generate_device_fingerprint(request)
        g.device_fingerprint = device_fingerprint
        
        if ZTNA_CONFIG['enforce_device_verification']:
            device_trust_score = self.evaluate_device_trust(device_fingerprint)
            g.device_trust_score = device_trust_score
            
            if device_trust_score < self.device_trust_threshold:
                self.log_access_attempt(request, False, "Low device trust score")
                return jsonify({"error": "Device verification failed", "code": "DEVICE_VERIFICATION_FAILED"}), 403
        
        # 2. Network Context Verification
        client_ip = request.remote_addr
        if not self.verify_network_context(client_ip):
            self.log_access_attempt(request, False, "Network context verification failed")
            return jsonify({"error": "Access denied from your network location", "code": "NETWORK_VERIFICATION_FAILED"}), 403
        
        # 3. Token Verification & Continuous Authentication
        token = self.extract_token(request)
        if token:
            try:
                # Verify and decode the token
                payload = jwt.decode(token, ZTNA_CONFIG['token_secret'], algorithms=['HS256'])
                
                # Check if token is blocked/revoked
                if token in blocked_tokens:
                    self.log_access_attempt(request, False, "Using revoked token")
                    return jsonify({"error": "Authentication token revoked", "code": "TOKEN_REVOKED"}), 403
                
                # Store user info in g for access in route handlers
                g.user = payload
                g.authenticated = True
                
                # Check if token needs refresh (approaching expiry)
                if self.should_refresh_token(payload):
                    g.token_needs_refresh = True
                
            except jwt.ExpiredSignatureError:
                self.log_access_attempt(request, False, "Expired token")
                return jsonify({"error": "Authentication token expired", "code": "TOKEN_EXPIRED"}), 401
                
            except jwt.InvalidTokenError:
                self.log_access_attempt(request, False, "Invalid token")
                return jsonify({"error": "Invalid authentication token", "code": "TOKEN_INVALID"}), 401
        else:
            # Default to unauthenticated if no token
            g.authenticated = False
            g.user = None
        
        # 4. Authorization - Least Privilege Access
        if not self.authorize_access(request):
            self.log_access_attempt(request, False, "Unauthorized access attempt")
            return jsonify({"error": "You don't have permission to access this resource", "code": "AUTHORIZATION_FAILED"}), 403
        
        # 5. Micro-segmentation (service routing if needed)
        if ZTNA_CONFIG['service_mesh_enabled']:
            self.apply_service_routing(request)
        
        # Log successful access attempt
        self.log_access_attempt(request, True, "Access granted")
        
        # Continue with the request
        return None
    
    def ztna_access_denied_handler(self, error):
        """Custom handler for 403 access denied errors"""
        return jsonify({
            "error": "Access Denied",
            "message": str(error),
            "code": "ACCESS_DENIED"
        }), 403
    
    def generate_device_fingerprint(self, request):
        """
        Generate a unique device fingerprint based on request attributes
        Uses browser/client characteristics to identify the device
        """
        # Collect device characteristics
        fingerprint_data = {
            'user_agent': request.headers.get('User-Agent', ''),
            'accept_language': request.headers.get('Accept-Language', ''),
            'accept_encoding': request.headers.get('Accept-Encoding', ''),
            'accept': request.headers.get('Accept', ''),
            'ip': request.remote_addr,
            # Add more indicators as needed
        }
        
        # Generate a hash as the fingerprint
        fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
        fingerprint = hashlib.sha256(fingerprint_str.encode()).hexdigest()
        
        # Track this fingerprint
        if fingerprint not in device_fingerprints:
            device_fingerprints[fingerprint] = {
                'first_seen': datetime.now().isoformat(),
                'last_seen': datetime.now().isoformat(),
                'count': 1,
                'characteristics': fingerprint_data,
                'trust_score': 0.5  # Initial neutral score
            }
        else:
            device_fingerprints[fingerprint]['count'] += 1
            device_fingerprints[fingerprint]['last_seen'] = datetime.now().isoformat()
        
        return fingerprint
    
    def evaluate_device_trust(self, fingerprint):
        """Evaluate the trust score for a device fingerprint"""
        if fingerprint not in device_fingerprints:
            return 0.0  # Unknown device
        
        device_data = device_fingerprints[fingerprint]
        
        # Base score from existing data
        trust_score = device_data.get('trust_score', 0.5)
        
        # Adjust score based on factors
        
        # 1. Interaction frequency increases trust
        count = device_data.get('count', 1)
        if count > 100:
            trust_score += 0.2
        elif count > 50:
            trust_score += 0.1
        elif count > 10:
            trust_score += 0.05
            
        # 2. User-agent analysis (simplified example)
        user_agent = device_data.get('characteristics', {}).get('user_agent', '').lower()
        if 'bot' in user_agent or 'crawler' in user_agent:
            trust_score -= 0.2
        
        # 3. If previously marked as suspicious
        if device_data.get('marked_suspicious', False):
            trust_score -= 0.3
            
        # Ensure score stays within 0-1 range
        trust_score = max(0.0, min(1.0, trust_score))
        
        # Update the stored score
        device_fingerprints[fingerprint]['trust_score'] = trust_score
        
        return trust_score
    
    def verify_network_context(self, client_ip):
        """
        Verify the network context of the request
        Checks IP against allowed networks and risk categories
        """
        # Always allow local development
        if client_ip == '127.0.0.1' or client_ip == 'localhost':
            return True
            
        # Check if IP is in allowed networks
        if ZTNA_CONFIG['allowed_networks']:
            for network in ZTNA_CONFIG['allowed_networks']:
                try:
                    if ipaddress.ip_address(client_ip) in ipaddress.ip_network(network):
                        return True
                except ValueError:
                    # Invalid IP or network format
                    continue
        
        # For external honeypot deployments, this would check geographical restrictions
        # and other network risk factors
        
        # For demo purposes, we'll allow all IPs to access the honeypot
        # In a real ZTNA setup, we'd be more restrictive
        return True
    
    def extract_token(self, request):
        """Extract authentication token from request"""
        # Check Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            return auth_header.split(' ')[1]
            
        # Check for token in cookies
        token = request.cookies.get('ztna_token')
        if token:
            return token
            
        # Check for token in query parameters (not recommended for production)
        token = request.args.get('token')
        if token:
            return token
            
        return None
    
    def should_refresh_token(self, payload):
        """Check if token should be refreshed (approaching expiry)"""
        if 'exp' in payload:
            exp_time = datetime.fromtimestamp(payload['exp'])
            # If token expires in less than 10 minutes
            if exp_time - datetime.now() < timedelta(minutes=10):
                return True
        return False
    
    def generate_token(self, user_data, expiry=None):
        """Generate a new ZTNA authentication token"""
        if not expiry:
            expiry = ZTNA_CONFIG['token_expiry']
            
        payload = {
            'sub': user_data.get('id') or str(uuid.uuid4()),
            'username': user_data.get('username', 'anonymous'),
            'roles': user_data.get('roles', []),
            'fingerprint': user_data.get('fingerprint', ''),
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(seconds=expiry)
        }
        
        token = jwt.encode(payload, ZTNA_CONFIG['token_secret'], algorithm='HS256')
        return token
    
    def revoke_token(self, token):
        """Revoke a token by adding it to the blocked list"""
        blocked_tokens.add(token)
        logger.info(f"Token revoked: {token[:10]}...")
        
        # In a production system, we'd persist this to a database
        return True
    
    def authorize_access(self, request):
        """
        Authorize access based on least privilege principle
        Checks if the user has sufficient permissions for the requested resource
        """
        # Public resources are accessible without authentication
        if request.path in ['/login', '/', '/static'] or request.path.startswith('/static/'):
            return True
            
        # If no authentication required for this endpoint
        if not self.requires_authentication(request.path):
            return True
            
        # Check if user is authenticated
        if not g.get('authenticated', False):
            return False
            
        # Admin paths require admin role
        if request.path.startswith('/admin'):
            return self.has_role('admin')
            
        # Security analyst paths
        if request.path.startswith('/analytics') or request.path.startswith('/threat-intel'):
            return self.has_role('security_analyst') or self.has_role('admin')
            
        # Threat hunter paths
        if request.path.startswith('/deception') or request.path.startswith('/services'):
            return self.has_role('threat_hunter') or self.has_role('admin')
            
        # Default allow for authenticated users on other paths
        return True
    
    def requires_authentication(self, path):
        """Check if a path requires authentication"""
        # List of paths that don't require authentication
        public_paths = ['/', '/login', '/api/login']
        
        # Check if path is public
        if path in public_paths or path.startswith('/static/'):
            return False
            
        # All other paths require authentication
        return True
    
    def has_role(self, role):
        """Check if the authenticated user has a specific role"""
        user = g.get('user', {})
        roles = user.get('roles', [])
        return role in roles
    
    def apply_service_routing(self, request):
        """
        Apply micro-segmentation by routing the request through appropriate service mesh
        This would typically integrate with a service mesh like Istio, Linkerd, or Consul
        """
        # For honeypot purposes, we'll just simulate service mesh routing
        service_routes = {
            '/api': 'api-gateway',
            '/admin': 'admin-service',
            '/services': 'deception-service',
            '/analytics': 'analytics-service'
        }
        
        # Find appropriate service for this path
        for path_prefix, service in service_routes.items():
            if request.path.startswith(path_prefix):
                g.routed_service = service
                logger.debug(f"Request routed through service mesh to: {service}")
                break
    
    def log_access_attempt(self, request, success, reason):
        """Log access attempt details for audit and threat analysis"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'ip': request.remote_addr,
            'path': request.path,
            'method': request.method,
            'user_agent': request.headers.get('User-Agent'),
            'success': success,
            'reason': reason,
            'user': g.get('user', {}).get('username', 'anonymous') if g.get('user') else 'anonymous',
            'fingerprint': g.get('device_fingerprint', 'unknown'),
            'trust_score': g.get('device_trust_score', 0)
        }
        
        access_logs.append(log_entry)
        
        # In a production system, we'd probably use a proper log storage system
        # For now, we'll periodically write to a JSON file
        self._maybe_persist_logs()
        
        # Log security-relevant events
        if not success:
            logger.warning(f"ZTNA access denied: {reason} for {request.path} from {request.remote_addr}")
        elif request.path.startswith('/admin'):
            logger.info(f"ZTNA admin access granted to {g.get('user', {}).get('username', 'anonymous')} for {request.path}")
    
    def _maybe_persist_logs(self):
        """Periodically persist logs to a file"""
        # Only persist logs when they reach a certain size
        if len(access_logs) >= 100:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.logs_dir}/ztna_access_{timestamp}.json"
            
            try:
                with open(filename, 'w') as f:
                    json.dump(access_logs[:100], f, indent=2)
                    
                # Remove persisted logs
                del access_logs[:100]
                logger.info(f"Persisted ZTNA access logs to {filename}")
            except Exception as e:
                logger.error(f"Failed to persist ZTNA logs: {e}")
    
    def track_failed_authentication(self, username):
        """Track failed authentication attempts to prevent brute force attacks"""
        timestamp = datetime.now()
        
        if username not in failed_authentication:
            failed_authentication[username] = {
                'count': 1,
                'first_attempt': timestamp,
                'last_attempt': timestamp,
                'lockout_until': None
            }
        else:
            # Update existing record
            failed_authentication[username]['count'] += 1
            failed_authentication[username]['last_attempt'] = timestamp
            
            # Check if we need to lockout the account
            if failed_authentication[username]['count'] >= ZTNA_CONFIG['max_failed_attempts']:
                lockout_until = timestamp + timedelta(seconds=ZTNA_CONFIG['lockout_duration'])
                failed_authentication[username]['lockout_until'] = lockout_until
                logger.warning(f"Account locked out due to failed attempts: {username} until {lockout_until}")
    
    def check_account_lockout(self, username):
        """Check if an account is locked out due to failed authentication attempts"""
        if username not in failed_authentication:
            return False
            
        lockout_until = failed_authentication[username].get('lockout_until')
        if lockout_until and datetime.now() < lockout_until:
            return True
        
        # If lockout has expired, reset the count
        if lockout_until and datetime.now() >= lockout_until:
            failed_authentication[username]['count'] = 0
            failed_authentication[username]['lockout_until'] = None
            
        return False
    
    def reset_failed_attempts(self, username):
        """Reset failed authentication attempts after successful login"""
        if username in failed_authentication:
            failed_authentication[username]['count'] = 0
            failed_authentication[username]['lockout_until'] = None

# Authentication decorator for route handlers
def ztna_login_required(f):
    """Decorator to require ZTNA authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.get('authenticated', False):
            return jsonify({"error": "Authentication required", "code": "AUTHENTICATION_REQUIRED"}), 401
        return f(*args, **kwargs)
    return decorated_function

# Role-based access control decorator
def ztna_role_required(roles):
    """Decorator to require specific roles for routes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not g.get('authenticated', False):
                return jsonify({"error": "Authentication required", "code": "AUTHENTICATION_REQUIRED"}), 401
                
            user_roles = g.get('user', {}).get('roles', [])
            if not any(role in user_roles for role in roles):
                return jsonify({"error": "Insufficient permissions", "code": "AUTHORIZATION_FAILED"}), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Create an instance for import
ztna_manager = ZeroTrustManager() 