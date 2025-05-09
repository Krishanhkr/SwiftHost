#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ZTNA Authentication Routes
--------------------------
Provides authentication endpoints for the honeypot's zero trust security model.
"""

import os
import json
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, g, make_response, session
from werkzeug.security import generate_password_hash, check_password_hash

from .zero_trust import ztna_manager, ztna_login_required, ztna_role_required

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('ztna_auth')

# Create Blueprint for auth routes
auth_bp = Blueprint('auth', __name__)

# Simple user database for demo purposes
# In production, this would be a proper database
USERS = {
    "admin": {
        "username": "admin",
        "password_hash": generate_password_hash("admin_password"),
        "roles": ["admin"],
        "email": "admin@example.com",
        "created_at": datetime.now().isoformat()
    },
    "analyst": {
        "username": "analyst",
        "password_hash": generate_password_hash("analyst_password"),
        "roles": ["security_analyst"],
        "email": "analyst@example.com",
        "created_at": datetime.now().isoformat()
    },
    "hunter": {
        "username": "hunter",
        "password_hash": generate_password_hash("hunter_password"),
        "roles": ["threat_hunter"],
        "email": "hunter@example.com",
        "created_at": datetime.now().isoformat()
    }
}

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate a user and issue a ZTNA token"""
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Username and password required", "code": "MISSING_CREDENTIALS"}), 400
    
    username = data['username']
    password = data['password']
    
    # Check for account lockout
    if ztna_manager.check_account_lockout(username):
        lockout = USERS.get(username, {}).get('lockout_until')
        return jsonify({
            "error": "Account temporarily locked due to multiple failed attempts", 
            "code": "ACCOUNT_LOCKED",
            "lockout_until": lockout
        }), 403
    
    # Authenticate user
    user = USERS.get(username)
    if not user or not check_password_hash(user['password_hash'], password):
        # Track failed authentication
        ztna_manager.track_failed_authentication(username)
        
        return jsonify({"error": "Invalid username or password", "code": "INVALID_CREDENTIALS"}), 401
    
    # Get device fingerprint
    fingerprint = ztna_manager.generate_device_fingerprint(request)
    
    # Create user data for token
    user_data = {
        "id": username,
        "username": username,
        "roles": user['roles'],
        "fingerprint": fingerprint
    }
    
    # Generate token
    token = ztna_manager.generate_token(user_data)
    
    # Reset failed authentication attempts
    ztna_manager.reset_failed_attempts(username)
    
    # Create response
    response = jsonify({
        "message": "Login successful",
        "user": {
            "username": username,
            "roles": user['roles'],
            "email": user['email']
        }
    })
    
    # Set token as cookie
    response.set_cookie(
        'ztna_token', 
        token, 
        httponly=True, 
        secure=request.is_secure,
        samesite='Strict',
        max_age=3600  # 1 hour
    )
    
    return response

@auth_bp.route('/logout', methods=['POST'])
@ztna_login_required
def logout():
    """Log out a user by revoking their token"""
    token = ztna_manager.extract_token(request)
    
    if token:
        # Revoke the token
        ztna_manager.revoke_token(token)
    
    # Create response
    response = jsonify({"message": "Logout successful"})
    
    # Clear the token cookie
    response.set_cookie('ztna_token', '', expires=0)
    
    return response

@auth_bp.route('/refresh-token', methods=['POST'])
@ztna_login_required
def refresh_token():
    """Refresh an existing valid token"""
    user = g.user
    
    # Create new user data from existing user info
    user_data = {
        "id": user.get('sub'),
        "username": user.get('username'),
        "roles": user.get('roles', []),
        "fingerprint": user.get('fingerprint')
    }
    
    # Generate new token
    new_token = ztna_manager.generate_token(user_data)
    
    # Revoke old token
    old_token = ztna_manager.extract_token(request)
    if old_token:
        ztna_manager.revoke_token(old_token)
    
    # Create response
    response = jsonify({"message": "Token refreshed successfully"})
    
    # Set new token as cookie
    response.set_cookie(
        'ztna_token', 
        new_token, 
        httponly=True, 
        secure=request.is_secure,
        samesite='Strict',
        max_age=3600  # 1 hour
    )
    
    return response

@auth_bp.route('/user', methods=['GET'])
@ztna_login_required
def get_user_info():
    """Get current user information"""
    user = g.user
    
    # Check if token needs refresh and set header if it does
    response = jsonify({
        "user": {
            "username": user.get('username'),
            "roles": user.get('roles', []),
            "sub": user.get('sub')
        },
        "token_needs_refresh": g.get('token_needs_refresh', False)
    })
    
    if g.get('token_needs_refresh'):
        response.headers['X-Token-Refresh-Required'] = 'true'
    
    return response

@auth_bp.route('/users', methods=['GET'])
@ztna_login_required
@ztna_role_required(['admin'])
def list_users():
    """Admin endpoint to list all users"""
    users_list = []
    for username, user_data in USERS.items():
        user_info = {
            "username": username,
            "roles": user_data.get('roles', []),
            "email": user_data.get('email'),
            "created_at": user_data.get('created_at')
        }
        users_list.append(user_info)
    
    return jsonify({"users": users_list})

@auth_bp.route('/check-access', methods=['POST'])
@ztna_login_required
def check_access():
    """Check if user has access to a specific resource"""
    data = request.get_json()
    
    if not data or 'resource' not in data:
        return jsonify({"error": "Resource path required", "code": "MISSING_RESOURCE"}), 400
    
    resource = data['resource']
    
    # Check authorization for the resource
    has_access = False
    
    # Admin access check
    if resource.startswith('/admin'):
        has_access = ztna_manager.has_role('admin')
    
    # Security analyst access check
    elif resource.startswith('/analytics') or resource.startswith('/threat-intel'):
        has_access = ztna_manager.has_role('security_analyst') or ztna_manager.has_role('admin')
    
    # Threat hunter access check
    elif resource.startswith('/deception') or resource.startswith('/services'):
        has_access = ztna_manager.has_role('threat_hunter') or ztna_manager.has_role('admin')
    
    # Default access for authenticated users
    else:
        has_access = True
    
    return jsonify({
        "resource": resource,
        "has_access": has_access,
        "user": g.user.get('username')
    }) 