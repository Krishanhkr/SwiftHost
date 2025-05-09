// Hamburger menu toggle
document.querySelector('.hamburger').addEventListener('click', () => {
  const navLinks = document.querySelector('.nav-links');
  navLinks.style.display = navLinks.style.display === 'flex' ? 'none' : 'flex';
});

// Smooth scroll
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    e.preventDefault();
    document.querySelector(this.getAttribute('href')).scrollIntoView({
      behavior: 'smooth'
    });
  });
});

// Page transitions
document.addEventListener('DOMContentLoaded', () => {
  // Simple fade in
  document.body.style.opacity = 0;
  setTimeout(() => {
    document.body.style.transition = 'opacity 0.5s ease-in-out';
    document.body.style.opacity = 1;
  }, 100);
  
  // Initialize GSAP animations later, after ensuring GSAP is loaded
  setTimeout(() => {
    if (typeof gsap !== 'undefined') {
      initGSAPAnimations();
    }
  }, 300);
  
  // Initialize domain search
  initDomainSearch();
});

// Initialize GSAP animations
function initGSAPAnimations() {
  // Safety check for GSAP
  if (typeof gsap === 'undefined') {
    console.warn('GSAP not loaded, skipping animations');
    return;
  }
  
  try {
    // Pricing card hover animations
    const pricingCards = document.querySelectorAll('.pricing-card');
    
    if (pricingCards.length > 0) {
      pricingCards.forEach(card => {
        // Simple hover effect instead of timeline
        card.addEventListener('mouseenter', () => {
          gsap.to(card, {
            scale: 1.03,
            boxShadow: '0 15px 30px -5px rgba(59, 130, 246, 0.4)',
            duration: 0.3,
            ease: 'power2.out'
          });
        });
        
        card.addEventListener('mouseleave', () => {
          gsap.to(card, {
            scale: 1,
            boxShadow: '0 5px 15px rgba(0,0,0,0.1)',
            duration: 0.3,
            ease: 'power2.out'
          });
        });
      });
      
      // Simple fade-in animation for cards
      gsap.from(pricingCards, {
        y: 30,
        opacity: 0,
        stagger: 0.1,
        duration: 0.8,
        ease: 'power1.out',
        delay: 0.2
      });
    }
    
    // Animate feature cards - simplified
    const featureCards = document.querySelectorAll('.feature-card');
    if (featureCards.length > 0) {
      gsap.from(featureCards, {
        y: 30,
        opacity: 0,
        stagger: 0.1,
        duration: 0.6,
        ease: 'power1.out',
        delay: 0.3
      });
    }
  } catch (error) {
    console.error('Error initializing GSAP animations:', error);
  }
}

// Generate CSRF Token
function generateCSRF() {
  return Math.random().toString(36).substring(2, 15) + 
         Math.random().toString(36).substring(2, 15);
}

// Domain Search Functionality
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
      const suggestionsContainer = document.querySelector('.domain-suggestions');
      if (suggestionsContainer) {
        suggestionsContainer.innerHTML = '';
      }
      return;
    }
    
    // Wait for user to finish typing
    if (query.length >= 3) {
      timeout = setTimeout(() => {
        const select = document.querySelector('.search-box select');
        if (!select) return;
        
        const tld = select.value;
        const domain = `${query}${tld}`;
        checkDomain(domain);
      }, 500);
    }
  });
  
  // Form submission handler
  domainForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const query = domainInput.value.trim();
    if (!query) return;
    
    const select = document.querySelector('.search-box select');
    if (!select) return;
    
    const tld = select.value;
    const domain = `${query}${tld}`;
    checkDomain(domain);
  });
}

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

// Check domain availability
async function checkDomain(domain) {
  const domainSearchBtn = document.querySelector('.domain-search button');
  if (!domainSearchBtn) return;
  
  const loadingState = '<i class="fas fa-spinner fa-spin"></i> Searching...';
  const originalContent = domainSearchBtn.innerHTML;
  
  try {
    domainSearchBtn.innerHTML = loadingState;
    domainSearchBtn.disabled = true;
    
    // Simple local "API" call
    await new Promise(resolve => setTimeout(resolve, 800));
    
    // Simulate random availability
    const isAvailable = Math.random() > 0.3;
    const price = `$${(Math.random() * 10 + 9.99).toFixed(2)}`;
    
    const result = {
      domain: domain,
      available: isAvailable,
      price: price
    };
    
    domainSearchBtn.innerHTML = originalContent;
    domainSearchBtn.disabled = false;
    
    showDomainResult(result);
  } catch (error) {
    console.error("Error checking domain:", error);
    domainSearchBtn.innerHTML = originalContent;
    domainSearchBtn.disabled = false;
    showErrorToast("An error occurred while checking domain");
  }
}

// Show domain result
function showDomainResult(result) {
  const suggestionsContainer = document.querySelector('.domain-suggestions');
  if (!suggestionsContainer) return;
  
  suggestionsContainer.innerHTML = '';
  
  const suggestionEl = document.createElement('div');
  suggestionEl.className = 'domain-suggestion';
  
  suggestionEl.innerHTML = `
    <div>
      <span>${result.domain}</span>
      <span style="color: ${result.available ? 'green' : 'red'}">
        ${result.available ? '✓ Available' : '✗ Unavailable'}
      </span>
    </div>
    <div>
      ${result.available ? 
        `<span class="price">${result.price}</span>
         <button class="btn-add-cart">Add to Cart</button>` : 
        `<button class="btn-try-another">Try Another</button>`
      }
    </div>
  `;
  
  suggestionsContainer.appendChild(suggestionEl);
  
  // Add click handlers
  if (result.available) {
    const addBtn = suggestionEl.querySelector('.btn-add-cart');
    if (addBtn) {
      addBtn.addEventListener('click', () => {
        alert(`Domain ${result.domain} added to cart!`);
      });
    }
  } else {
    const tryBtn = suggestionEl.querySelector('.btn-try-another');
    if (tryBtn) {
      tryBtn.addEventListener('click', () => {
        const domainInput = document.querySelector('#domainSearch');
        if (domainInput) {
          domainInput.value = '';
          domainInput.focus();
          suggestionsContainer.innerHTML = '';
        }
      });
    }
  }
  
  // Animate with GSAP if available
  if (typeof gsap !== 'undefined') {
    gsap.from(suggestionEl, {
      y: 20,
      opacity: 0,
      duration: 0.4,
      ease: 'power1.out'
    });
  }
}

// Contact form with security features
document.addEventListener('DOMContentLoaded', () => {
  const contactForm = document.querySelector('.contact-form');
  if(contactForm) {
    // Add CSRF token and honeypot field
    contactForm.insertAdjacentHTML('beforeend', `
      <input type="text" name="honeypot" style="display:none;">
      <input type="hidden" name="_csrf" value="${generateCSRF()}">
    `);
    
    contactForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      // Check honeypot field (bot protection)
      const honeypot = contactForm.querySelector('[name="honeypot"]');
      if (honeypot && honeypot.value) {
        console.log('Bot detected');
        return;
      }
      
      const submitBtn = contactForm.querySelector('button[type="submit"]');
      const successMsg = document.querySelector('.success-message');
      
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
      
      try {
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        // Show success message
        if (successMsg) {
          successMsg.style.display = 'block';
          setTimeout(() => {
            successMsg.style.display = 'none';
          }, 5000);
        }
        
        contactForm.reset();
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Send';
      } catch (error) {
        console.error('Error submitting form:', error);
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Send';
        alert('An error occurred. Please try again.');
      }
    });
  }
}); 