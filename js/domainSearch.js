// Domain Search with Namecheap API Integration
const API_USER = process.env.NAMECHEAP_API_USER;
const API_KEY = process.env.NAMECHEAP_API_KEY;
const CLIENT_IP = process.env.CLIENT_IP || '127.0.0.1';

// Show error toast
function showErrorToast(message) {
  const toast = document.createElement('div');
  toast.classList.add('error-toast');
  toast.textContent = message;
  document.body.appendChild(toast);
  
  setTimeout(() => {
    toast.classList.add('show');
    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => {
        document.body.removeChild(toast);
      }, 300);
    }, 3000);
  }, 100);
}

// Check domain availability through Namecheap API
async function checkDomain(domain) {
  const domainSearchBtn = document.querySelector('.domain-search button');
  const loadingState = '<i class="fas fa-spinner fa-spin"></i> Searching...';
  const originalContent = domainSearchBtn.innerHTML;
  
  try {
    domainSearchBtn.innerHTML = loadingState;
    domainSearchBtn.disabled = true;
    
    const res = await axios.get(`https://api.namecheap.com/xml.response`, {
      params: {
        ApiUser: API_USER,
        ApiKey: API_KEY,
        UserName: API_USER,
        ClientIp: CLIENT_IP,
        Command: 'namecheap.domains.check',
        DomainList: domain
      }
    });
    
    domainSearchBtn.innerHTML = originalContent;
    domainSearchBtn.disabled = false;
    
    // Parse XML response - in a real app you'd use a proper XML parser
    // This is simplified for the example
    if (res.data && res.data.DomainCheckResult) {
      return res.data.DomainCheckResult;
    }
    
    // Fallback for demo purposes
    return {
      Domain: domain,
      Available: Math.random() > 0.3, // Random availability for demo
      Price: `$${(Math.random() * 10 + 9.99).toFixed(2)}`
    };
    
  } catch (error) {
    console.error("API Error:", error);
    domainSearchBtn.innerHTML = originalContent;
    domainSearchBtn.disabled = false;
    showErrorToast("API Limit Exceeded or Service Unavailable");
    return [];
  }
}

// Show domain suggestions with available/unavailable status
function showDomainResults(result) {
  const suggestionsContainer = document.querySelector('.domain-suggestions');
  if (!suggestionsContainer) return;
  
  suggestionsContainer.innerHTML = '';
  
  if (!result || !result.Domain) {
    suggestionsContainer.innerHTML = '<div class="no-results">No results found</div>';
    return;
  }
  
  const suggestionEl = document.createElement('div');
  suggestionEl.className = 'domain-suggestion';
  
  // Add animation class
  suggestionEl.classList.add('fade-in');
  
  // Set content based on availability
  suggestionEl.innerHTML = `
    <div class="domain-info">
      <span class="domain-name">${result.Domain}</span>
      <span class="domain-status ${result.Available ? 'available' : 'unavailable'}">
        ${result.Available ? 'Available' : 'Unavailable'}
      </span>
    </div>
    <div class="domain-action">
      ${result.Available ? 
        `<span class="price">${result.Price}</span>
         <button class="btn-add-cart">Add to Cart</button>` : 
        `<button class="btn-try-another">Try Another</button>`
      }
    </div>
  `;
  
  suggestionsContainer.appendChild(suggestionEl);
  
  // Add click handlers
  if (result.Available) {
    suggestionEl.querySelector('.btn-add-cart').addEventListener('click', () => {
      alert(`Domain ${result.Domain} added to cart!`);
      // In a real app, this would add to cart
    });
  } else {
    suggestionEl.querySelector('.btn-try-another').addEventListener('click', () => {
      document.querySelector('#domainSearch').value = '';
      document.querySelector('#domainSearch').focus();
    });
  }
}

// Initialize domain search
function initDomainSearch() {
  const domainForm = document.querySelector('.search-box');
  const domainInput = document.querySelector('#domainSearch');
  
  if (!domainForm || !domainInput) return;
  
  // Add debouncing for real-time checking
  let timeout;
  domainInput.addEventListener('input', (e) => {
    clearTimeout(timeout);
    const query = e.target.value.trim();
    
    // Clear suggestions if input is empty
    if (!query) {
      document.querySelector('.domain-suggestions').innerHTML = '';
      return;
    }
    
    // Wait for user to finish typing
    if (query.length >= 3) {
      timeout = setTimeout(async () => {
        const tld = document.querySelector('.search-box select').value;
        const domain = `${query}${tld}`;
        const result = await checkDomain(domain);
        showDomainResults(result);
      }, 500);
    }
  });
  
  // Form submission handler
  domainForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = domainInput.value.trim();
    if (!query) return;
    
    const tld = document.querySelector('.search-box select').value;
    const domain = `${query}${tld}`;
    const result = await checkDomain(domain);
    showDomainResults(result);
  });
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initDomainSearch);

// Export for testing
if (typeof module !== 'undefined') {
  module.exports = { checkDomain, showDomainResults };
} 