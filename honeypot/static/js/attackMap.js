// Attack Map Visualization
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
  
  // Helper function to get color based on threat score
  getThreatColor(score) {
    if (score > 0.7) return '#EF4444'; // Red for high threat
    if (score > 0.4) return '#F59E0B'; // Orange for medium threat
    return '#3B82F6'; // Blue for low threat
  }
  
  // Mock function for IP geolocation
  // In a real implementation, this would call an API like IPStack
  async geoLocateIP(ip) {
    // Mock implementation - in production use actual API
    console.log(`Geolocating IP: ${ip}`);
    
    // Simulate API response
    return {
      latitude: (Math.random() * 180) - 90,
      longitude: (Math.random() * 360) - 180,
      country_name: "Mock Country"
    };
  }
}

// Make available globally
window.AttackMap = AttackMap; 