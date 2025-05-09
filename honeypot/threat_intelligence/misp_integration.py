import os
import json
import logging
import requests
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MISPEvent:
    """Simple mock of PyMISP MISPEvent class"""
    def __init__(self):
        self.info = ""
        self.attributes = []
        self.tags = []
        
    def add_attribute(self, attribute):
        self.attributes.append(attribute)
        
    def add_tag(self, tag):
        self.tags.append(tag)
        
    def to_dict(self):
        return {
            "info": self.info,
            "attributes": [attr.to_dict() for attr in self.attributes],
            "tags": self.tags
        }

class MISPAttribute:
    """Simple mock of PyMISP MISPAttribute class"""
    def __init__(self):
        self.type = ""
        self.value = ""
        self.comment = ""
        self.tags = []
        
    def add_tag(self, tag):
        self.tags.append(tag)
        
    def to_dict(self):
        return {
            "type": self.type,
            "value": self.value,
            "comment": self.comment,
            "tags": self.tags
        }

class ThreatIntelSender:
    def __init__(self, misp_url=None, misp_key=None, abuseipdb_key=None):
        self.misp_url = misp_url or os.getenv('MISP_URL', 'https://misp.example.com')
        self.misp_key = misp_key or os.getenv('MISP_KEY', 'demo_key')
        self.abuseipdb_key = abuseipdb_key or os.getenv('ABUSEIPDB_KEY', 'demo_key')
        
        # In a real implementation, use PyMISP
        # self.misp = ExpandedPyMISP(url=self.misp_url, key=self.misp_key, ssl=False)
        
        # Directory for storing shared threat intel
        os.makedirs('threat_intel', exist_ok=True)
    
    def create_event(self, attack_data):
        """
        Create a MISP event for a detected attack
        
        Args:
            attack_data: Dictionary containing attack information
        
        Returns:
            event_id: ID of the created event
        """
        logger.info(f"Creating MISP event for attack from {attack_data['ip']}")
        
        try:
            # Create MISP event
            event = MISPEvent()
            event.info = f"Honeypot Attack: {attack_data['ip']}"
            
            # Add IP as IOC
            attr_ip = MISPAttribute()
            attr_ip.type = "ip-dst"
            attr_ip.value = attack_data['ip']
            attr_ip.comment = f"Source IP of attack with threat score {attack_data.get('threat_score', 0)}"
            
            # Add tags based on threat score
            if attack_data.get('threat_score', 0) > 0.7:
                attr_ip.add_tag("tlp:amber")
                attr_ip.add_tag("honeypot:high-threat")
            else:
                attr_ip.add_tag("tlp:white")
                attr_ip.add_tag("honeypot:low-threat")
                
            event.add_attribute(attr_ip)
            
            # Add user-agent if available
            if attack_data.get('user_agent'):
                attr_ua = MISPAttribute()
                attr_ua.type = "user-agent"
                attr_ua.value = attack_data['user_agent']
                event.add_attribute(attr_ua)
            
            # Add HTTP method and path if available
            if attack_data.get('method') and attack_data.get('path'):
                attr_http = MISPAttribute()
                attr_http.type = "http-method"
                attr_http.value = f"{attack_data['method']} {attack_data['path']}"
                event.add_attribute(attr_http)
            
            # Add attack types
            for attack_type in attack_data.get('attack_types', []):
                event.add_tag(f"attack-type:{attack_type}")
            
            # In a real implementation, we would submit this to MISP
            # event_id = self.misp.add_event(event)
            
            # For demo, save to file
            event_id = self._mock_submit_event(event, attack_data)
            
            # Report to AbuseIPDB if appropriate
            if attack_data.get('threat_score', 0) > 0.5:
                self.report_to_abuseipdb(attack_data)
            
            return event_id
            
        except Exception as e:
            logger.error(f"Error creating MISP event: {e}")
            return None
    
    def _mock_submit_event(self, event, attack_data):
        """Mock submission to MISP by saving to a file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        event_id = f"mock_event_{timestamp}_{attack_data['ip'].replace('.', '_')}"
        
        # Convert event to dict for serialization
        event_dict = event.to_dict()
        
        # Add additional honeypot specific data
        event_dict['honeypot_data'] = {
            "threat_score": attack_data.get('threat_score', 0),
            "timestamp": datetime.now().isoformat(),
            "threat_indicators": attack_data.get('threat_indicators', []),
            "attack_types": attack_data.get('attack_types', [])
        }
        
        # Save to file
        with open(f'threat_intel/misp_event_{event_id}.json', 'w') as f:
            json.dump(event_dict, f, indent=2)
            
        logger.info(f"Saved mock MISP event {event_id}")
        return event_id
    
    def report_to_abuseipdb(self, attack_data):
        """
        Report malicious IP to AbuseIPDB
        
        Args:
            attack_data: Dictionary containing attack information
        """
        if self.abuseipdb_key == 'demo_key':
            logger.info(f"Mock reporting IP {attack_data['ip']} to AbuseIPDB")
            return
        
        try:
            # Map attack types to AbuseIPDB categories
            # See: https://www.abuseipdb.com/categories
            category_map = {
                'SQL Injection': 14,  # Cross Site Scripting
                'Command Injection': 21,  # Hacking
                'Path Traversal': 21,  # Hacking
                'Scanner': 15,  # Port Scan
            }
            
            # Build categories list
            categories = [15]  # Default to port scan
            for attack_type in attack_data.get('attack_types', []):
                if attack_type in category_map:
                    categories.append(category_map[attack_type])
            
            # Remove duplicates and convert to comma-separated string
            categories = list(set(categories))
            categories_str = ','.join(map(str, categories))
            
            # Create comment from attack data
            comment = f"Honeypot detection: {', '.join(attack_data.get('attack_types', ['Suspicious Activity']))}"
            if attack_data.get('path'):
                comment += f", targeting {attack_data['path']}"
            
            # Submit to AbuseIPDB
            response = requests.post(
                'https://api.abuseipdb.com/api/v2/report',
                headers={
                    'Key': self.abuseipdb_key,
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                data={
                    'ip': attack_data['ip'],
                    'categories': categories_str,
                    'comment': comment
                }
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully reported {attack_data['ip']} to AbuseIPDB")
            else:
                logger.warning(f"Failed to report to AbuseIPDB: {response.status_code} {response.text}")
                
        except Exception as e:
            logger.error(f"Error reporting to AbuseIPDB: {e}")
    
    def export_stix(self, attack_data):
        """
        Export attack data in STIX format
        
        Args:
            attack_data: Dictionary containing attack information
            
        Returns:
            stix_data: Dictionary in STIX format
        """
        # In a real implementation, use the stix2 library
        # Here we implement a simple mock
        
        timestamp = datetime.now().isoformat()
        
        # Create STIX Indicator
        stix_data = {
            "type": "indicator",
            "id": f"indicator--{attack_data['ip'].replace('.', '-')}",
            "created": timestamp,
            "modified": timestamp,
            "name": f"Malicious IP: {attack_data['ip']}",
            "description": f"IP address observed conducting suspicious activities against honeypot",
            "indicator_types": ["malicious-activity"],
            "pattern": f"[ipv4-addr:value = '{attack_data['ip']}']",
            "pattern_type": "stix",
            "valid_from": timestamp,
            "labels": attack_data.get('attack_types', ["suspicious-activity"]),
            "confidence": int(attack_data.get('threat_score', 0.5) * 100),
            "object_marking_refs": [
                "marking-definition--613f2e26-407d-48c7-9eca-b8e91df99dc9" # TLP:GREEN
            ]
        }
        
        # Save to file
        with open(f'threat_intel/stix_{attack_data["ip"].replace(".", "_")}.json', 'w') as f:
            json.dump(stix_data, f, indent=2)
            
        logger.info(f"Saved STIX data for {attack_data['ip']}")
        return stix_data 