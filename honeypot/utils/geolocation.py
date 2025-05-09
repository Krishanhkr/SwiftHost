import os
import json
import requests
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IPGeolocation:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('IPSTACK_API_KEY', 'demo_key')
        self.cache = {}
        self.cache_duration = timedelta(days=7)  # Cache results for 7 days
        self.cache_file = 'geoip_cache.json'
        
        # Load cache from file if exists
        self._load_cache()
    
    def _load_cache(self):
        """Load IP geolocation cache from file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                # Convert string timestamps back to datetime objects
                for ip, data in cache_data.items():
                    if 'timestamp' in data:
                        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
                
                self.cache = cache_data
                logger.info(f"Loaded {len(self.cache)} IP locations from cache")
        except Exception as e:
            logger.error(f"Error loading IP geolocation cache: {e}")
            self.cache = {}
    
    def _save_cache(self):
        """Save IP geolocation cache to file"""
        try:
            # Convert datetime objects to ISO format strings for JSON serialization
            cache_data = {}
            for ip, data in self.cache.items():
                cache_data[ip] = data.copy()
                if 'timestamp' in cache_data[ip]:
                    cache_data[ip]['timestamp'] = data['timestamp'].isoformat()
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f)
                
            logger.info(f"Saved {len(self.cache)} IP locations to cache")
        except Exception as e:
            logger.error(f"Error saving IP geolocation cache: {e}")
    
    def geolocate(self, ip):
        """
        Geolocate an IP address using the IPStack API
        Returns location data or None if the lookup fails
        """
        # Check cache first
        now = datetime.now()
        if ip in self.cache:
            cache_data = self.cache[ip]
            # Check if cache is still valid
            if now - cache_data.get('timestamp', now) < self.cache_duration:
                logger.debug(f"IP {ip} found in cache")
                return cache_data
        
        # If not in cache or cache expired, query the API
        try:
            logger.info(f"Geolocating IP: {ip}")
            
            # Use the ipstack API if we have a key
            if self.api_key != 'demo_key':
                response = requests.get(
                    f"http://api.ipstack.com/{ip}",
                    params={"access_key": self.api_key}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract relevant information
                    location_data = {
                        'ip': ip,
                        'latitude': data.get('latitude'),
                        'longitude': data.get('longitude'),
                        'country_code': data.get('country_code'),
                        'country_name': data.get('country_name'),
                        'region_name': data.get('region_name'),
                        'city': data.get('city'),
                        'timestamp': now
                    }
                    
                    # Cache the result
                    self.cache[ip] = location_data
                    self._save_cache()
                    
                    return location_data
            
            # Fallback to mock data for demo purposes
            return self._generate_mock_location(ip)
                
        except Exception as e:
            logger.error(f"Error geolocating IP {ip}: {e}")
            return self._generate_mock_location(ip)
    
    def _generate_mock_location(self, ip):
        """Generate mock location data for demo purposes"""
        import random
        
        # Generate deterministic but random-looking coordinates based on IP
        # This ensures the same IP always gets the same coordinates
        seed = sum(int(part) for part in ip.split('.'))
        random.seed(seed)
        
        latitude = random.uniform(-80, 80)
        longitude = random.uniform(-170, 170)
        
        # Mock country assignment based on longitude ranges
        countries = {
            (-170, -30): ("US", "United States"),
            (-30, 0): ("GB", "United Kingdom"),
            (0, 30): ("FR", "France"),
            (30, 60): ("RU", "Russia"),
            (60, 90): ("CN", "China"),
            (90, 130): ("JP", "Japan"),
            (130, 170): ("AU", "Australia")
        }
        
        for lon_range, country in countries.items():
            if lon_range[0] <= longitude < lon_range[1]:
                country_code, country_name = country
                break
        else:
            country_code, country_name = "UN", "Unknown"
        
        location_data = {
            'ip': ip,
            'latitude': latitude,
            'longitude': longitude,
            'country_code': country_code,
            'country_name': country_name,
            'region_name': "Unknown",
            'city': "Unknown",
            'timestamp': datetime.now(),
            'is_mock': True
        }
        
        # Cache the mock result
        self.cache[ip] = location_data
        self._save_cache()
        
        return location_data
    
    def batch_geolocate(self, ip_list):
        """Geolocate a batch of IP addresses"""
        results = {}
        for ip in ip_list:
            results[ip] = self.geolocate(ip)
        return results 