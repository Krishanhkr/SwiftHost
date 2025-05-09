#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Deception Technology API Endpoints
----------------------------------
This module implements fake microservices mimicking Redis, MySQL, and AWS S3 APIs 
that log attacker behavior and inject tracking payloads.
"""

import os
import time
import json
import logging
import hashlib
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, Response, make_response
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('decoy_api')

# Create Flask Blueprint for the deception endpoints
deception_bp = Blueprint('deception', __name__)

# Configure fake credentials and endpoints
FAKE_CREDS = {
    "redis": {
        "url": "redis://admin:Pa$$w0rd123@decoy-redis.internal:6379",
        "master_auth": "S3cr3tRedisAuth!",
        "max_memory": "4gb",
        "replicas": ["10.0.2.33", "10.0.2.34"]
    },
    "mysql": {
        "host": "db-master.internal",
        "user": "dbadmin",
        "password": "MyS3cr3tP@ssw0rd!",
        "database": "production",
        "port": 3306,
        "allow_remote": True,
        "ssl_disabled": True
    },
    "aws": {
        "access_key": "AKIAIOSFODNN7EXAMPLE",
        "secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "region": "us-west-2",
        "bucket": "company-backups",
        "objects": ["customer_data.sql", "financial_records.xlsx", "credentials.json"]
    }
}

# Track interactions for later analysis
attacker_interactions = {}

def log_interaction(endpoint, attacker_ip, data=None, method=None):
    """Log and record interaction with deception APIs"""
    timestamp = datetime.now().isoformat()
    tracking_id = str(uuid.uuid4())
    
    # Record interaction for later analysis
    if attacker_ip not in attacker_interactions:
        attacker_interactions[attacker_ip] = []
        
    interaction = {
        'timestamp': timestamp,
        'endpoint': endpoint,
        'tracking_id': tracking_id,
        'method': method or request.method,
        'data': data,
        'headers': {k: v for k, v in request.headers.items()},
        'user_agent': request.headers.get('User-Agent'),
    }
    
    attacker_interactions[attacker_ip].append(interaction)
    
    # Log the interaction
    logger.warning(
        f"Deception endpoint accessed | {endpoint} | {attacker_ip} | {tracking_id}"
    )
    
    return tracking_id

def embed_tracking_payload(data, attacker_ip):
    """Generate and embed a tracking payload in the JSON response"""
    tracking_id = f"TRACKER_{attacker_ip}_{int(time.time())}"
    tracking_hash = hashlib.sha256(tracking_id.encode()).hexdigest()[:12]
    
    # If data is a dict, add tracking info
    if isinstance(data, dict):
        data['_tracker'] = tracking_hash
    
    return data, tracking_hash

# Redis API endpoints
@deception_bp.route('/redis/config', methods=['GET'])
def fake_redis_config():
    """Fake Redis configuration endpoint"""
    attacker_ip = request.remote_addr
    tracking_id = log_interaction('/redis/config', attacker_ip)
    
    # Prepare response data with embedded tracking
    response_data = {
        "config": FAKE_CREDS['redis'],
        "_comment": "DEV: Remember to disable backup replication in production",
        "_tracker_id": tracking_id
    }
    
    return jsonify(response_data)

@deception_bp.route('/redis/master/auth', methods=['GET', 'POST'])
def fake_redis_auth():
    """Fake Redis authentication endpoint"""
    attacker_ip = request.remote_addr
    data = request.get_json() if request.is_json else {}
    tracking_id = log_interaction('/redis/master/auth', attacker_ip, data)
    
    # Always act like authentication succeeded
    response_data = {
        "status": "success",
        "message": "Redis master auth configured",
        "auth_key": FAKE_CREDS['redis']['master_auth'],
        "_tracker_id": tracking_id
    }
    
    return jsonify(response_data)

# MySQL API endpoints
@deception_bp.route('/mysql/connection', methods=['GET', 'POST'])
def fake_mysql_connection():
    """Fake MySQL connection information endpoint"""
    attacker_ip = request.remote_addr
    data = request.get_json() if request.is_json else {}
    tracking_id = log_interaction('/mysql/connection', attacker_ip, data)
    
    # Generate connectionString with tracking id embedded
    connection_string = (
        f"mysql://{FAKE_CREDS['mysql']['user']}:{FAKE_CREDS['mysql']['password']}"
        f"@{FAKE_CREDS['mysql']['host']}:{FAKE_CREDS['mysql']['port']}/"
        f"{FAKE_CREDS['mysql']['database']}?tracking={tracking_id}"
    )
    
    response_data = {
        "connection": FAKE_CREDS['mysql'],
        "connectionString": connection_string,
        "allowedIPs": ["0.0.0.0/0"],  # Intentionally insecure
        "note": "TODO: Restrict access before going to production"
    }
    
    return jsonify(response_data)

@deception_bp.route('/mysql/backup', methods=['GET'])
def fake_mysql_backup():
    """Fake MySQL backup endpoint with SQL dump"""
    attacker_ip = request.remote_addr
    tracking_id = log_interaction('/mysql/backup', attacker_ip)
    
    # Generate fake SQL content with tracking info embedded as a comment
    sql_content = f"""-- MySQL dump 10.13  Distrib 8.0.28, for Linux (x86_64)
-- Host: {FAKE_CREDS['mysql']['host']}    Database: {FAKE_CREDS['mysql']['database']}
-- ------------------------------------------------------
-- Server version       8.0.28
-- Tracking: {tracking_id}

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;

-- Table structure for table `users`
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `email` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=289 DEFAULT CHARSET=utf8mb4;

-- Dumping data for table `users`
INSERT INTO `users` VALUES 
(1,'admin','$2a$12$KhDr4xj/dCJIf/XkVpCEIeQHiEm.LrGh2M/caeP2DM4QzlPpn7JLi','admin@example.com'),
(2,'john.doe','$2a$12$k8B1C2T.page5eQrxR7eme8kNbNXf/NVEOlqvYcWaVHAIQb7xQdQe','john@example.com');

-- End of MySQL dump (tracking: {tracking_id})
"""
    
    # Return SQL file
    response = make_response(sql_content)
    response.headers['Content-Type'] = 'text/plain'
    response.headers['Content-Disposition'] = f'attachment; filename=backup_{datetime.now().strftime("%Y%m%d")}.sql'
    return response

# AWS S3 API endpoints
@deception_bp.route('/aws/s3/config', methods=['GET'])
def fake_aws_s3_config():
    """Fake AWS S3 configuration endpoint"""
    attacker_ip = request.remote_addr
    tracking_id = log_interaction('/aws/s3/config', attacker_ip)
    
    response_data = {
        "accessKey": FAKE_CREDS['aws']['access_key'],
        "secretKey": FAKE_CREDS['aws']['secret_key'],
        "region": FAKE_CREDS['aws']['region'],
        "defaultBucket": FAKE_CREDS['aws']['bucket']
    }
    
    # Embed tracking info
    response_data, tracking_hash = embed_tracking_payload(response_data, attacker_ip)
    
    return jsonify(response_data)

@deception_bp.route('/aws/s3/list', methods=['GET'])
def fake_aws_s3_list():
    """Fake AWS S3 bucket listing endpoint"""
    attacker_ip = request.remote_addr
    tracking_id = log_interaction('/aws/s3/list', attacker_ip)
    
    # Generate fake object listing with tracking info
    objects = []
    for obj_name in FAKE_CREDS['aws']['objects']:
        # Generate fake file metadata
        timestamp = int(time.time() - (86400 * (hash(obj_name) % 30)))  # Random date in last 30 days
        size = (hash(obj_name) % 100) * 1024 * 1024  # Random size 0-100 MB
        
        objects.append({
            "Key": obj_name,
            "LastModified": datetime.fromtimestamp(timestamp).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "ETag": f"\"{hashlib.md5((obj_name + tracking_id).encode()).hexdigest()}\"",
            "Size": size,
            "StorageClass": "STANDARD"
        })
    
    response_data = {
        "Name": FAKE_CREDS['aws']['bucket'],
        "Prefix": "",
        "MaxKeys": 1000,
        "IsTruncated": False,
        "Contents": objects
    }
    
    return jsonify(response_data)

@deception_bp.route('/aws/s3/download/<path:key>', methods=['GET'])
def fake_aws_s3_download(key):
    """Fake AWS S3 file download endpoint"""
    attacker_ip = request.remote_addr
    tracking_id = log_interaction(f'/aws/s3/download/{key}', attacker_ip)
    
    # Check if requested file is in our fake list
    if key not in FAKE_CREDS['aws']['objects']:
        return jsonify({"error": "AccessDenied", "message": "Access Denied"}), 403
    
    # Generate fake content based on file type
    content = ""
    if key.endswith('.json'):
        # Generate fake JSON
        fake_data = {
            "api_keys": [
                {"service": "mailchimp", "key": "abcd1234-mock-key-5678", "active": True},
                {"service": "stripe", "key": "sk_test_mockKeyWithTracker" + tracking_id, "active": True},
            ],
            "tracker": tracking_id  # Add tracker directly
        }
        content = json.dumps(fake_data, indent=2)
        mimetype = 'application/json'
        
    elif key.endswith('.sql'):
        # Generate fake SQL dump with embedded tracker
        content = f"""-- SQL Dump with tracking ID: {tracking_id}
CREATE TABLE accounts (id INT, username VARCHAR(100), password VARCHAR(100));
INSERT INTO accounts VALUES (1, 'system_admin', 'S3cr3tP@ss!');
-- End tracked dump {tracking_id}
"""
        mimetype = 'text/plain'
        
    elif key.endswith('.xlsx'):
        # For binary files like XLSX, just return a text representation
        content = f"[This would be an Excel file in production. Tracking ID: {tracking_id}]"
        mimetype = 'text/plain'
    
    # Return the fake content
    response = make_response(content)
    response.headers['Content-Type'] = mimetype
    response.headers['ETag'] = f"\"{hashlib.md5(content.encode()).hexdigest()}\""
    response.headers['X-Tracker'] = tracking_id  # Add tracker in header
    return response

# Endpoint to retrieve all recorded interactions (admin only)
@deception_bp.route('/admin/interactions', methods=['GET'])
def get_interactions():
    """Admin endpoint to retrieve recorded interactions"""
    # In a real system, this would require authentication
    # For demo purposes, we're making it accessible
    
    # Format the attacker interactions for display
    formatted_interactions = {
        ip: interactions for ip, interactions in attacker_interactions.items()
    }
    
    return jsonify({
        "total_attackers": len(attacker_interactions),
        "total_interactions": sum(len(interactions) for interactions in attacker_interactions.values()),
        "interactions": formatted_interactions
    })

# Error handling
@deception_bp.errorhandler(Exception)
def handle_error(error):
    """Handle exceptions in the deception module"""
    logger.error(f"Error in deception API: {error}")
    logger.error(traceback.format_exc())
    
    # Return a generic error to avoid revealing information
    return jsonify({
        "error": "Internal Server Error",
        "message": "The server encountered an unexpected condition"
    }), 500 