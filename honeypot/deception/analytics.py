#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Deception Technology Analytics
------------------------------
This module analyzes interactions with deception endpoints to identify and
profile attacker behavior, track stolen credentials, and generate alerts.
"""

import os
import json
import logging
import time
from datetime import datetime, timedelta
from collections import defaultdict
import ipaddress

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('deception_analytics')

class DeceptionAnalytics:
    """Analyzes interactions with deception endpoints"""
    def __init__(self):
        self.interactions = {}
        self.tracked_payloads = {}
        self.alerts = []
        
        # Directory for storing analytics
        self.analytics_dir = 'analytics/deception'
        os.makedirs(self.analytics_dir, exist_ok=True)
    
    def update_interactions(self, new_interactions):
        """Update interaction database with new interactions"""
        # Merge new interactions with existing ones
        for ip, interactions in new_interactions.items():
            if ip not in self.interactions:
                self.interactions[ip] = []
            
            # Add new interactions
            for interaction in interactions:
                # Check if this interaction already exists (by tracking_id)
                if not any(i.get('tracking_id') == interaction.get('tracking_id') 
                           for i in self.interactions[ip]):
                    self.interactions[ip].append(interaction)
                    
                    # Track any embedded tracking payloads
                    if '_tracker' in interaction.get('data', {}):
                        self.tracked_payloads[interaction['data']['_tracker']] = {
                            'ip': ip,
                            'timestamp': interaction['timestamp'],
                            'endpoint': interaction['endpoint']
                        }
                        
        logger.info(f"Updated interactions database - now tracking {len(self.interactions)} IPs")
    
    def analyze_attacker_behavior(self):
        """
        Analyze attacker behavior based on interactions
        Returns profiles of attacker behavior
        """
        profiles = {}
        
        for ip, interactions in self.interactions.items():
            # Skip if no interactions
            if not interactions:
                continue
                
            # Basic profile structure
            profile = {
                'ip': ip,
                'first_seen': min(i['timestamp'] for i in interactions),
                'last_seen': max(i['timestamp'] for i in interactions),
                'interaction_count': len(interactions),
                'accessed_endpoints': defaultdict(int),
                'api_types': set(),
                'user_agents': set(),
                'methods': set(),
                'sophistication_score': 0.0,
                'extracted_credentials': False,
                'lateral_movement': False,
                'tracking_payloads': []
            }
            
            # Process each interaction
            for interaction in interactions:
                # Track endpoints accessed
                profile['accessed_endpoints'][interaction['endpoint']] += 1
                
                # Track API types
                if '/redis/' in interaction['endpoint']:
                    profile['api_types'].add('redis')
                elif '/mysql/' in interaction['endpoint']:
                    profile['api_types'].add('mysql')
                elif '/aws/' in interaction['endpoint']:
                    profile['api_types'].add('aws')
                
                # Track user agents and methods
                profile['user_agents'].add(interaction.get('user_agent', 'unknown'))
                profile['methods'].add(interaction.get('method', 'GET'))
                
                # Check for credential extraction
                if any(endpoint in interaction['endpoint'] for endpoint in 
                      ['/redis/config', '/mysql/connection', '/aws/s3/config']):
                    profile['extracted_credentials'] = True
                
                # Check for lateral movement attempts
                if interaction['endpoint'] == '/mysql/connection' and interaction.get('method') == 'POST':
                    profile['lateral_movement'] = True
                
                # Track any tracking IDs
                if '_tracker_id' in interaction.get('data', {}):
                    profile['tracking_payloads'].append(interaction['data']['_tracker_id'])
            
            # Calculate sophistication score
            profile['sophistication_score'] = self._calculate_sophistication(profile)
            
            # Convert sets to lists for JSON serialization
            profile['api_types'] = list(profile['api_types'])
            profile['user_agents'] = list(profile['user_agents'])
            profile['methods'] = list(profile['methods'])
            
            # Store in profiles dict
            profiles[ip] = profile
        
        # Save profiles to file
        self._save_profiles(profiles)
        
        return profiles
    
    def detect_tracked_payload_usage(self, request_data):
        """
        Check if any of our tracked payloads appear in incoming requests
        This allows us to detect when attackers use stolen credentials
        
        Args:
            request_data: The incoming request data to check
            
        Returns:
            detection: Dict with tracking info if found, None otherwise
        """
        # Convert request data to string for searching
        if isinstance(request_data, bytes):
            request_str = request_data.decode('utf-8', errors='ignore')
        elif isinstance(request_data, dict):
            request_str = json.dumps(request_data)
        else:
            request_str = str(request_data)
        
        # Check for any tracked payloads
        for tracker, info in self.tracked_payloads.items():
            if tracker in request_str:
                detection = {
                    'tracker': tracker,
                    'original_ip': info['ip'],
                    'original_timestamp': info['original_timestamp'],
                    'original_endpoint': info['endpoint'],
                    'detection_timestamp': datetime.now().isoformat()
                }
                
                # Generate alert
                self._generate_alert(
                    'CREDENTIAL_REUSE',
                    f"Tracked payload {tracker} detected in request",
                    detection
                )
                
                return detection
                
        return None
    
    def _calculate_sophistication(self, profile):
        """Calculate a sophistication score for an attacker based on behavior"""
        score = 0.0
        
        # Base score based on number of different API types accessed
        score += len(profile['api_types']) * 0.2
        
        # Higher score if credentials were extracted
        if profile['extracted_credentials']:
            score += 0.3
            
        # Higher score if lateral movement was attempted
        if profile['lateral_movement']:
            score += 0.4
            
        # Higher score based on number of endpoints accessed
        endpoint_score = min(0.3, len(profile['accessed_endpoints']) * 0.05)
        score += endpoint_score
        
        # Cap at 1.0
        return min(1.0, score)
    
    def _generate_alert(self, alert_type, message, details=None):
        """Generate an alert based on suspicious activity"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'type': alert_type,
            'message': message,
            'details': details or {}
        }
        
        self.alerts.append(alert)
        logger.warning(f"ALERT: {alert_type} - {message}")
        
        return alert
    
    def _save_profiles(self, profiles):
        """Save attacker profiles to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save to file
        with open(f'{self.analytics_dir}/attacker_profiles_{timestamp}.json', 'w') as f:
            json.dump(profiles, f, indent=2)
            
        logger.info(f"Saved {len(profiles)} attacker profiles to {self.analytics_dir}")
    
    def generate_credential_tracking_report(self):
        """
        Generate a report on tracked credentials and their usage
        This shows which fake credentials were accessed and potentially used
        
        Returns:
            report: Dictionary with credential tracking information
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'tracked_payloads': len(self.tracked_payloads),
            'usage_detections': 0,
            'payloads': []
        }
        
        # Process each tracked payload
        for tracker, info in self.tracked_payloads.items():
            payload_info = {
                'tracker': tracker,
                'ip': info['ip'],
                'first_seen': info['timestamp'],
                'endpoint': info['endpoint'],
                'detections': []
            }
            
            # Add any detections from alerts
            for alert in self.alerts:
                if (alert['type'] == 'CREDENTIAL_REUSE' and 
                    alert['details'].get('tracker') == tracker):
                    payload_info['detections'].append({
                        'timestamp': alert['details'].get('detection_timestamp'),
                        'context': alert['message']
                    })
            
            report['usage_detections'] += len(payload_info['detections'])
            report['payloads'].append(payload_info)
        
        # Save report
        with open(f'{self.analytics_dir}/credential_tracking_report.json', 'w') as f:
            json.dump(report, f, indent=2)
            
        return report
    
    def identify_data_exfiltration(self):
        """
        Identify potential data exfiltration patterns in interactions
        
        Returns:
            exfil_data: List of potential data exfiltration attempts
        """
        exfil_attempts = []
        
        # Look for patterns suggesting data exfiltration
        for ip, interactions in self.interactions.items():
            # Group interactions by time windows (5 minute windows)
            time_windows = defaultdict(list)
            
            for interaction in interactions:
                try:
                    timestamp = datetime.fromisoformat(interaction['timestamp'])
                    window_key = timestamp.strftime("%Y-%m-%d %H:%M")
                    time_windows[window_key].append(interaction)
                except (ValueError, TypeError):
                    continue
            
            # Check each time window for potential exfiltration patterns
            for window, window_interactions in time_windows.items():
                # If multiple sensitive endpoints were accessed in a short time
                sensitive_endpoints = [i for i in window_interactions 
                                     if '/download/' in i['endpoint'] or 
                                        '/backup' in i['endpoint'] or
                                        '/config' in i['endpoint']]
                
                if len(sensitive_endpoints) >= 2:
                    # Potential exfiltration
                    data_size = sum(
                        len(json.dumps(i.get('data', ''))) 
                        for i in sensitive_endpoints
                    )
                    
                    exfil_attempts.append({
                        'ip': ip,
                        'timestamp': window,
                        'endpoints_accessed': [i['endpoint'] for i in sensitive_endpoints],
                        'data_size_bytes': data_size,
                        'interaction_count': len(window_interactions),
                        'tracking_ids': [i.get('tracking_id') for i in sensitive_endpoints]
                    })
        
        # Generate alerts for exfiltration attempts
        for attempt in exfil_attempts:
            self._generate_alert(
                'DATA_EXFILTRATION',
                f"Potential data exfiltration from IP {attempt['ip']}",
                attempt
            )
        
        return exfil_attempts 