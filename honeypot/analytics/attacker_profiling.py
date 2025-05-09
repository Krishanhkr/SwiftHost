import numpy as np
import logging
import json
import os
from datetime import datetime
from collections import defaultdict

# These imports would be used in a real implementation
# In this mock version, we'll implement simplified versions of these algorithms
# from sklearn.cluster import DBSCAN
# from sklearn.preprocessing import StandardScaler
# import matplotlib.pyplot as plt
# import plotly.express as px

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AttackerProfiler:
    def __init__(self):
        # In a real implementation:
        # self.scaler = StandardScaler()
        # self.model = DBSCAN(eps=0.5, min_samples=5)
        
        # For mock implementation
        self.clusters = []
        self.profiles = {}
        self.profiling_dir = 'analytics/profiles'
        os.makedirs(self.profiling_dir, exist_ok=True)
    
    def _extract_features(self, attacks):
        """
        Extract relevant features from attack data for clustering
        
        Args:
            attacks: List of attack data dictionaries
            
        Returns:
            features: Numpy array of features for each attack
        """
        logger.info(f"Extracting features from {len(attacks)} attacks")
        
        # Calculate features for each attacker
        features = []
        for attacker in attacks:
            # Basic features
            request_count = attacker.get('count', 0)
            distinct_paths = len(set(attacker.get('paths', [])))
            path_variety = distinct_paths / max(request_count, 1)  # Normalize by request count
            
            # Calculate error rate (% of 4xx/5xx responses if status codes available)
            error_count = sum(1 for path in attacker.get('status_codes', {}).values() 
                             if path >= 400)
            error_rate = error_count / max(request_count, 1)
            
            # Calculate time-based features
            if 'first_seen' in attacker and 'last_seen' in attacker:
                try:
                    first_seen = datetime.fromisoformat(attacker['first_seen'])
                    last_seen = datetime.fromisoformat(attacker['last_seen'])
                    duration_seconds = (last_seen - first_seen).total_seconds()
                    requests_per_minute = (request_count / max(duration_seconds, 60)) * 60
                except (ValueError, TypeError):
                    requests_per_minute = 0
            else:
                requests_per_minute = 0
            
            # Attack sophistication score based on attack types
            attack_types = attacker.get('attack_types', [])
            sophistication_score = 0
            if 'SQL Injection' in attack_types:
                sophistication_score += 0.7
            if 'Command Injection' in attack_types:
                sophistication_score += 0.8
            if 'Path Traversal' in attack_types:
                sophistication_score += 0.6
            if 'Scanner' in attack_types:
                sophistication_score += 0.4
                
            # Normalize sophistication score to [0,1]
            sophistication_score = min(sophistication_score, 1.0)
            
            # Create feature vector
            feature_vector = [
                requests_per_minute,
                path_variety,
                error_rate,
                sophistication_score,
                attacker.get('threat_score', 0)
            ]
            
            features.append(feature_vector)
        
        return np.array(features)
    
    def _mock_clustering(self, features):
        """
        Mock implementation of DBSCAN clustering
        
        Args:
            features: Feature array for clustering
            
        Returns:
            clusters: Cluster labels for each attacker
        """
        # Very simple mock clustering - just divide into 3 groups based on threat score
        # In a real implementation, use DBSCAN or another clustering algorithm
        n_samples = features.shape[0]
        
        # Use the threat score (features[:, 4]) to divide into groups
        clusters = np.zeros(n_samples, dtype=int)
        
        for i in range(n_samples):
            threat_score = features[i, 4]
            sophistication = features[i, 3]
            
            if threat_score > 0.7 and sophistication > 0.7:
                # Advanced attacker
                clusters[i] = 2
            elif threat_score > 0.4 or sophistication > 0.5:
                # Intermediate attacker
                clusters[i] = 1
            else:
                # Basic attacker / scanner
                clusters[i] = 0
        
        return clusters
    
    def analyze_attackers(self, attackers):
        """
        Analyze attackers to identify clusters and behaviors
        
        Args:
            attackers: Dictionary of attacker profiles
            
        Returns:
            profiles: Dictionary with attacker profiles
        """
        logger.info(f"Analyzing {len(attackers)} attackers")
        
        # Convert to list for processing
        attacker_list = []
        for ip, data in attackers.items():
            attacker_data = data.copy()
            attacker_data['ip'] = ip
            attacker_list.append(attacker_data)
        
        # Extract features for clustering
        features = self._extract_features(attacker_list)
        
        # Skip clustering if too few samples
        if len(attacker_list) < 3:
            logger.warning("Too few attackers for meaningful clustering")
            return {
                "script_kiddies": [a['ip'] for a in attacker_list if a.get('threat_score', 0) <= 0.4],
                "advanced_attackers": [a['ip'] for a in attacker_list if a.get('threat_score', 0) > 0.7],
                "opportunistic": [a['ip'] for a in attacker_list if 0.4 < a.get('threat_score', 0) <= 0.7]
            }
        
        # Perform clustering (mock implementation)
        clusters = self._mock_clustering(features)
        self.clusters = clusters
        
        # Generate profiles for each cluster
        script_kiddies = []
        opportunistic = []
        advanced_attackers = []
        
        for i, (attacker, cluster) in enumerate(zip(attacker_list, clusters)):
            if cluster == 0:
                script_kiddies.append(attacker['ip'])
            elif cluster == 1:
                opportunistic.append(attacker['ip'])
            elif cluster == 2:
                advanced_attackers.append(attacker['ip'])
        
        # Create profile results
        profiles = {
            "script_kiddies": script_kiddies,
            "opportunistic": opportunistic,
            "advanced_attackers": advanced_attackers,
            "stats": {
                "total_attackers": len(attacker_list),
                "script_kiddies_pct": len(script_kiddies) / max(len(attacker_list), 1) * 100,
                "opportunistic_pct": len(opportunistic) / max(len(attacker_list), 1) * 100,
                "advanced_attackers_pct": len(advanced_attackers) / max(len(attacker_list), 1) * 100
            }
        }
        
        # Save the analysis
        self._save_profiles(profiles, attacker_list, features)
        
        self.profiles = profiles
        return profiles
    
    def _save_profiles(self, profiles, attackers, features):
        """
        Save attacker profiles to file
        
        Args:
            profiles: Dictionary of profiles
            attackers: List of attacker data
            features: Feature array
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create detailed profile with feature data
        detailed_profiles = {
            "timestamp": datetime.now().isoformat(),
            "summary": profiles['stats'],
            "clusters": {
                "script_kiddies": profiles['script_kiddies'],
                "opportunistic": profiles['opportunistic'],
                "advanced_attackers": profiles['advanced_attackers']
            },
            "attackers": {}
        }
        
        # Add detailed attacker data
        for i, attacker in enumerate(attackers):
            ip = attacker['ip']
            
            # Find which cluster this IP belongs to
            if ip in profiles['script_kiddies']:
                cluster = "script_kiddies"
            elif ip in profiles['opportunistic']:
                cluster = "opportunistic"
            elif ip in profiles['advanced_attackers']:
                cluster = "advanced_attackers"
            else:
                cluster = "unknown"
            
            # Create attacker profile with features
            detailed_profiles['attackers'][ip] = {
                "cluster": cluster,
                "features": {
                    "requests_per_minute": float(features[i, 0]),
                    "path_variety": float(features[i, 1]),
                    "error_rate": float(features[i, 2]),
                    "sophistication": float(features[i, 3]),
                    "threat_score": float(features[i, 4])
                },
                "attack_types": list(attacker.get('attack_types', [])),
                "paths": attacker.get('paths', [])[:10],  # Include up to 10 sample paths
                "first_seen": attacker.get('first_seen', ""),
                "last_seen": attacker.get('last_seen', ""),
                "request_count": attacker.get('count', 0)
            }
        
        # Save to file
        with open(f'{self.profiling_dir}/attacker_profiles_{timestamp}.json', 'w') as f:
            json.dump(detailed_profiles, f, indent=2)
            
        logger.info(f"Saved attacker profiles to {self.profiling_dir}/attacker_profiles_{timestamp}.json")
    
    def plot_clusters_3d(self, attackers=None):
        """
        Generate a visualization of attacker clusters
        In a real implementation, this would use Plotly to create an interactive 3D visualization
        
        Args:
            attackers: Dictionary of attacker profiles (optional, uses stored data if None)
            
        Returns:
            plot_data: Data structure representing the plot (for mock implementation)
        """
        logger.info("Generating 3D cluster visualization (mock implementation)")
        
        # In a real implementation with Plotly:
        """
        fig = px.scatter_3d(
            x=features[:, 0],  # requests_per_minute
            y=features[:, 1],  # path_variety
            z=features[:, 4],  # threat_score
            color=clusters,
            labels={'x': 'Requests/min', 'y': 'Path Variety', 'z': 'Threat Score'}
        )
        
        fig.update_layout(
            title="Attacker Behavioral Clusters",
            margin=dict(l=20, r=20, t=30, b=20)
        )
        
        fig.write_html(f'{self.profiling_dir}/attacker_clusters_3d.html')
        """
        
        # Mock implementation - just return cluster data
        plot_data = {
            "title": "Attacker Behavioral Clusters",
            "clusters": {
                "script_kiddies": len(self.profiles.get('script_kiddies', [])),
                "opportunistic": len(self.profiles.get('opportunistic', [])),
                "advanced_attackers": len(self.profiles.get('advanced_attackers', []))
            },
            "axes": ["Requests/min", "Path Variety", "Threat Score"]
        }
        
        # Save mock plot data
        with open(f'{self.profiling_dir}/cluster_visualization_mock.json', 'w') as f:
            json.dump(plot_data, f, indent=2)
            
        return plot_data
    
    def generate_attack_timeline(self, attackers):
        """
        Generate a timeline of attack events
        
        Args:
            attackers: Dictionary of attacker profiles
            
        Returns:
            timeline: List of timeline events
        """
        logger.info("Generating attack timeline")
        
        timeline = []
        
        # Process each attacker
        for ip, data in attackers.items():
            # Add first seen event
            if 'first_seen' in data:
                timeline.append({
                    "timestamp": data['first_seen'],
                    "ip": ip,
                    "event": "first_activity",
                    "threat_score": data.get('threat_score', 0)
                })
            
            # Add last seen event
            if 'last_seen' in data:
                timeline.append({
                    "timestamp": data['last_seen'],
                    "ip": ip,
                    "event": "last_activity",
                    "threat_score": data.get('threat_score', 0)
                })
            
            # Add high threat events
            if data.get('threat_score', 0) > 0.7:
                # Use an intermediate timestamp if available
                if 'first_seen' in data and 'last_seen' in data:
                    try:
                        first = datetime.fromisoformat(data['first_seen'])
                        last = datetime.fromisoformat(data['last_seen'])
                        mid = first + (last - first) / 2
                        mid_timestamp = mid.isoformat()
                    except (ValueError, TypeError):
                        mid_timestamp = data.get('last_seen', datetime.now().isoformat())
                else:
                    mid_timestamp = data.get('last_seen', datetime.now().isoformat())
                
                timeline.append({
                    "timestamp": mid_timestamp,
                    "ip": ip,
                    "event": "high_threat_activity",
                    "threat_score": data.get('threat_score', 0),
                    "attack_types": list(data.get('attack_types', []))
                })
        
        # Sort timeline by timestamp
        timeline.sort(key=lambda x: x['timestamp'])
        
        # Save timeline
        with open(f'{self.profiling_dir}/attack_timeline.json', 'w') as f:
            json.dump(timeline, f, indent=2)
            
        return timeline 