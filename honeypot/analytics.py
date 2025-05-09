from datetime import datetime
import json
import re
import os
import logging
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('analytics.log'),
        logging.StreamHandler()
    ]
)

class AttackDetector:
    # Common patterns that indicate malicious activity
    MALICIOUS_PATTERNS = [
        ("sqlmap", 0.95),
        ("nmap", 0.85),
        ("wp-login.php", 0.75),
        ("admin", 0.35),
        ("config", 0.40),
        (".git", 0.60),
        (".env", 0.70),
        ("passwd", 0.80),
        ("backup", 0.50),
        ("shell", 0.65)
    ]
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(?:\'|\%27)(?:--|\%2D\%2D|%23|\#)",  # Basic SQL injection
        r"(?:select|union|insert|update|delete|drop).*(?:from|into|where)",  # SQL keywords
        r"(?:AND|OR)[^\w]+\d+[^\w]+[=<>]",  # Boolean-based SQL injection
        r"(?:SLEEP|BENCHMARK|WAIT FOR DELAY)\s*\(\s*\d+\s*\)",  # Time-based SQL injection
    ]
    
    # Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r"(?:;|\||\|\||&&)\s*(?:cat|ls|dir|cd|pwd|echo|wget|curl)",
        r"(?:\/bin\/(?:bash|sh)|cmd\.exe|powershell\.exe)",
    ]
    
    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r"(?:\.\.|%2e%2e)(?:\/|%2f)",
    ]
    
    def __init__(self):
        self.attackers = defaultdict(lambda: {
            "first_seen": datetime.utcnow().isoformat(),
            "last_seen": datetime.utcnow().isoformat(),
            "count": 0,
            "paths": [],
            "user_agents": set(),
            "threat_score": 0.0,
            "attack_types": set()
        })
        
        # Create the analytics directory if it doesn't exist
        os.makedirs('analytics', exist_ok=True)
        
    def analyze_request(self, request):
        """
        Analyze a request for potential threats
        Returns a log entry with threat analysis
        """
        ip = request.remote_addr
        user_agent = request.headers.get("User-Agent", "")
        path = request.path
        query_params = dict(request.args)
        method = request.method
        body = request.get_json(silent=True) or {}
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "ip": ip,
            "user_agent": user_agent,
            "method": method,
            "path": path,
            "params": query_params,
            "body": body,
            "threat_indicators": [],
            "attack_types": []
        }
        
        # Initialize threat score
        threat_score = 0.0
        
        # Check for malicious patterns in path
        for pattern, score in self.MALICIOUS_PATTERNS:
            if pattern.lower() in path.lower():
                threat_score += score
                log_entry["threat_indicators"].append(pattern)
        
        # Check query parameters for SQL injection
        param_data = json.dumps(query_params)
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, param_data, re.IGNORECASE):
                threat_score += 0.9
                log_entry["threat_indicators"].append("SQL Injection")
                log_entry["attack_types"].append("SQL Injection")
                break
        
        # Check body for command injection
        body_data = json.dumps(body)
        for pattern in self.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, body_data, re.IGNORECASE):
                threat_score += 0.95
                log_entry["threat_indicators"].append("Command Injection")
                log_entry["attack_types"].append("Command Injection")
                break
        
        # Check for path traversal
        for pattern in self.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, path, re.IGNORECASE):
                threat_score += 0.85
                log_entry["threat_indicators"].append("Path Traversal")
                log_entry["attack_types"].append("Path Traversal")
                break
        
        # Check for unusual user agents (common scanners/bots)
        scanner_agents = ["nmap", "sqlmap", "nikto", "burpsuite", "zgrab", "dirbuster"]
        for agent in scanner_agents:
            if agent.lower() in user_agent.lower():
                threat_score += 0.8
                log_entry["threat_indicators"].append(f"Scanner: {agent}")
                log_entry["attack_types"].append("Scanner")
        
        # Calculate final threat score (max 1.0)
        threat_score = min(threat_score, 1.0)
        log_entry["threat_score"] = threat_score
        
        # Determine threat level based on score
        if threat_score < 0.3:
            log_entry["threat_level"] = "LOW"
        elif threat_score < 0.6:
            log_entry["threat_level"] = "MEDIUM" 
        else:
            log_entry["threat_level"] = "HIGH"
        
        # Update attacker profile
        self._update_attacker_profile(ip, log_entry)
        
        return log_entry
    
    def _update_attacker_profile(self, ip, log_entry):
        """
        Update the profile for an attacker based on their request
        """
        attacker = self.attackers[ip]
        attacker["count"] += 1
        attacker["last_seen"] = log_entry["timestamp"]
        attacker["paths"].append(log_entry["path"])
        attacker["user_agents"].add(log_entry["user_agent"])
        
        # Moving average for threat score with more weight on higher scores
        if log_entry["threat_score"] > attacker["threat_score"]:
            # Higher threat scores get more weight
            attacker["threat_score"] = (attacker["threat_score"] * 0.7) + (log_entry["threat_score"] * 0.3)
        else:
            attacker["threat_score"] = (attacker["threat_score"] * 0.9) + (log_entry["threat_score"] * 0.1)
        
        # Add attack types
        for attack_type in log_entry.get("attack_types", []):
            attacker["attack_types"].add(attack_type)
        
        # Log if this is a high-threat attacker
        if attacker["threat_score"] > 0.7 and attacker["count"] > 5:
            logging.warning(f"HIGH THREAT ATTACKER: {ip} Score: {attacker['threat_score']:.2f} Attacks: {list(attacker['attack_types'])}")
        
        # Save attacker profiles periodically
        if attacker["count"] % 10 == 0:
            self.save_attacker_profiles()
    
    def save_attacker_profiles(self):
        """
        Save attacker profiles to a file for later analysis
        """
        # Convert sets to lists for JSON serialization
        serializable_attackers = {}
        for ip, profile in self.attackers.items():
            serializable_profile = profile.copy()
            serializable_profile["user_agents"] = list(profile["user_agents"])
            serializable_profile["attack_types"] = list(profile["attack_types"])
            serializable_attackers[ip] = serializable_profile
        
        with open('analytics/attacker_profiles.json', 'w') as f:
            json.dump(serializable_attackers, f, indent=2)
    
    def get_attack_analytics(self):
        """
        Get statistics and analytics about attacks
        """
        total_attackers = len(self.attackers)
        high_threat_attackers = sum(1 for profile in self.attackers.values() if profile["threat_score"] > 0.7)
        
        # Count attack types
        attack_types = defaultdict(int)
        for profile in self.attackers.values():
            for attack_type in profile["attack_types"]:
                attack_types[attack_type] += 1
        
        # Get most requested paths
        all_paths = []
        for profile in self.attackers.values():
            all_paths.extend(profile["paths"])
        
        path_counts = defaultdict(int)
        for path in all_paths:
            path_counts[path] += 1
        
        # Sort by count
        top_paths = sorted(path_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        top_attack_types = sorted(attack_types.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "total_attackers": total_attackers,
            "high_threat_attackers": high_threat_attackers,
            "top_attack_types": top_attack_types,
            "top_requested_paths": top_paths,
            "recent_attacks": sorted(
                [p for p in self.attackers.values() if p["threat_score"] > 0.5],
                key=lambda x: x["last_seen"],
                reverse=True
            )[:5]
        }
        
    def generate_report(self):
        """
        Generate a comprehensive report of attack patterns
        """
        analytics = self.get_attack_analytics()
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_attackers": analytics["total_attackers"],
                "high_threat_attackers": analytics["high_threat_attackers"],
                "attack_types": dict(analytics["top_attack_types"]),
                "most_targeted_resources": dict(analytics["top_requested_paths"])
            },
            "top_attackers": sorted(
                [{"ip": ip, **profile} for ip, profile in self.attackers.items()],
                key=lambda x: x["threat_score"],
                reverse=True
            )[:10]
        }
        
        # Save report to file
        with open(f'analytics/attack_report_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
            json.dump(report, f, indent=2)
            
        return report 