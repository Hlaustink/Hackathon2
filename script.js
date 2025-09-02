// DOM Elements
const darkModeToggle = document.getElementById('dark-mode-toggle');
const body = document.body;
const hamburger = document.querySelector('.hamburger');
const navMenu = document.querySelector('.nav-menu');
const loginBtn = document.getElementById('login-btn');
const registerBtn = document.getElementById('register-btn');
const heroRegisterBtn = document.getElementById('hero-register-btn');
const heroLearnMore = document.getElementById('hero-learn-more');
const ctaRegisterBtn = document.getElementById('cta-register-btn');
const loginModal = document.getElementById('login-modal');
const registerModal = document.getElementById('register-modal');
const modalCloseButtons = document.querySelectorAll('.modal-close');
const switchToRegister = document.getElementById('switch-to-register');
const switchToLogin = document.getElementById('switch-to-login');

// Dark Mode Toggle
function enableDarkMode() {
    body.classList.add('dark-mode');
    localStorage.setItem('darkMode', 'enabled');
}

function disableDarkMode() {
    body.classList.remove('dark-mode');
    localStorage.setItem('darkMode', 'disabled');
}

// Check for saved dark mode preference
if (localStorage.getItem('darkMode') === 'enabled') {
    enableDarkMode();
    darkModeToggle.checked = true;
}

// Toggle dark mode
darkModeToggle.addEventListener('change', () => {
    if (darkModeToggle.checked) {
        enableDarkMode();
    } else {
        disableDarkMode();
    }
});

// Mobile Menu Toggle
hamburger.addEventListener('click', () => {
    hamburger.classList.toggle('active');
    navMenu.classList.toggle('active');
});

// Close mobile menu when clicking on a nav link
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', () => {
        hamburger.classList.remove('active');
        navMenu.classList.remove('active');
    });
});

// Modal Functions
function openModal(modal) {
    modal.classList.add('active');
    document.body.style.overflow = 'hidden'; // Prevent scrolling
}

function closeModal(modal) {
    modal.classList.remove('active');
    document.body.style.overflow = 'auto'; // Enable scrolling
}

// Event Listeners for Modals
loginBtn.addEventListener('click', () => openModal(loginModal));
registerBtn.addEventListener('click', () => openModal(registerModal));
heroRegisterBtn.addEventListener('click', () => openModal(registerModal));
ctaRegisterBtn.addEventListener('click', () => openModal(registerModal));

heroLearnMore.addEventListener('click', () => {
    document.getElementById('features').scrollIntoView({ behavior: 'smooth' });
});

// Close modals when clicking on close button
modalCloseButtons.forEach(button => {
    button.addEventListener('click', () => {
        const modal = button.closest('.modal');
        closeModal(modal);
    });
});

// Close modals when clicking outside
document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal(modal);
        }
    });
});

// Switch between login and register modals
switchToRegister.addEventListener('click', (e) => {
    e.preventDefault();
    closeModal(loginModal);
    openModal(registerModal);
});

switchToLogin.addEventListener('click', (e) => {
    e.preventDefault();
    closeModal(registerModal);
    openModal(loginModal);
});

// Form Submissions
document.querySelectorAll('.auth-form').forEach(form => {
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        
        if (form.parentElement.id === 'login-modal') {
            // Login form submission
            const email = document.getElementById('login-email').value;
            const password = document.getElementById('login-password').value;
            
            // Simulate login process
            console.log('Login attempt with:', { email, password });
            
            // In a real application, you would send this data to your backend
            alert('Login functionality would connect to your backend API.');
            
        } else if (form.parentElement.id === 'register-modal') {
            // Registration form submission
            const name = document.getElementById('register-name').value;
            const email = document.getElementById('register-email').value;
            const password = document.getElementById('register-password').value;
            const confirmPassword = document.getElementById('register-confirm').value;
            
            // Simple validation
            if (password !== confirmPassword) {
                alert('Passwords do not match!');
                return;
            }
            
            // Simulate registration process
            console.log('Registration attempt with:', { name, email, password });
            
            // In a real application, you would send this data to your backend
            alert('Registration functionality would connect to your backend API.');
        }
        
        // Close the modal after submission
        const modal = form.closest('.modal');
        closeModal(modal);
    });
});

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        
        const targetId = this.getAttribute('href');
        if (targetId === '#') return;
        
        const targetElement = document.querySelector(targetId);
        if (targetElement) {
            targetElement.scrollIntoView({
                behavior: 'smooth'
            });
        }
    });
});

// Animation on scroll
function animateOnScroll() {
    const elements = document.querySelectorAll('.feature-card, .pricing-card, .step');
    
    elements.forEach(element => {
        const elementPosition = element.getBoundingClientRect().top;
        const screenPosition = window.innerHeight / 1.3;
        
        if (elementPosition < screenPosition) {
            element.style.opacity = 1;
            element.style.transform = 'translateY(0)';
        }
    });
}

// Initialize elements for animation
document.querySelectorAll('.feature-card, .pricing-card, .step').forEach(element => {
    element.style.opacity = 0;
    element.style.transform = 'translateY(20px)';
    element.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
});

// Listen for scroll events
window.addEventListener('scroll', animateOnScroll);
// Initial check in case elements are already in view
window.addEventListener('load', animateOnScroll);

// Process payment with IntaSend
function processPayment() {
    const modal = document.getElementById('payment-modal');
    const context = modal.dataset.context;
    const token = localStorage.getItem('authToken');
    
    if (!token) {
        alert('Authentication required. Please try again.');
        return;
    }
    
    // Show loading state
    const confirmBtn = document.getElementById('payment-confirm');
    const originalText = confirmBtn.innerHTML;
    confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating payment...';
    confirmBtn.disabled = true;
    
    // Create payment intent with IntaSend
    fetch('/create-payment-intent', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Redirect to IntaSend payment page
        window.location.href = data.payment_url;
        
        // Poll for payment completion (simplified version)
        pollPaymentStatus(data.invoice_id, context);
    })
    .catch(error => {
        console.error('Payment error:', error);
        alert('Payment setup failed: ' + error.message);
        
        // Reset button
        confirmBtn.innerHTML = originalText;
        confirmBtn.disabled = false;
    });
}

function pollPaymentStatus(invoiceId, context) {
    const token = localStorage.getItem('authToken');
    const maxAttempts = 30; // 3 minutes at 6-second intervals
    let attempts = 0;
    
    const checkStatus = setInterval(() => {
        attempts++;
        
        if (attempts > maxAttempts) {
            clearInterval(checkStatus);
            alert('Payment verification timeout. Please contact support if payment was made.');
            return;
        }
        
        fetch('/verify-payment', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ invoice_id: invoiceId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                clearInterval(checkStatus);
                
                // Update token and user data
                localStorage.setItem('authToken', data.token);
                const userData = JSON.parse(localStorage.getItem('userData') || '{}');
                userData.tier = data.tier;
                localStorage.setItem('userData', JSON.stringify(userData));
                
                // Close modal
                document.getElementById('payment-modal').classList.remove('active');
                
                if (context === 'register') {
                    // Redirect to AI app
                    window.location.href = 'ai-app.html';
                } else {
                    // Retry the action that required payment
                    alert('Payment successful! You now have premium access.');
                }
            } else if (data.error && data.status === 'FAILED') {
                clearInterval(checkStatus);
                alert('Payment failed. Please try again.');
            }
            // If payment is still pending, continue polling
        })
        .catch(error => {
            console.error('Status check error:', error);
        });
    }, 6000); // Check every 6 seconds
}

// Update the completeRegistrationWithPayment function
function completeRegistrationWithPayment() {
    const name = document.getElementById('register-name').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    
    // For IntaSend integration, we'll handle registration after payment
    // Store registration data temporarily
    localStorage.setItem('pendingRegistration', JSON.stringify({
        name: name,
        email: email,
        password: password
    }));
    
    // Show payment modal
    showPaymentRequiredModal('register');
}

                // Authentication flow
// After successful registration/login in index.html
function handleAuthenticationSuccess(response) {
    // Store token and user info
    localStorage.setItem('authToken', response.token);
    localStorage.setItem('userData', JSON.stringify(response.user));
    
    // Redirect to AI application
    window.location.href = 'ai-app.html';
}

        //STILL AUTHENTICATION
// Check if user is already logged in when index.html loads
document.addEventListener('DOMContentLoaded', function() {
    const token = localStorage.getItem('authToken');
    const userData = JSON.parse(localStorage.getItem('userData') || '{}');
    
    if (token && userData.id) {
        // User is already logged in, show "Go to App" button
        showAppNavigation();
    }
});

function showAppNavigation() {
    // Replace login/register buttons with "Go to App" button
    const navMenu = document.querySelector('.nav-menu');
    const loginBtn = document.getElementById('login-btn');
    const registerBtn = document.getElementById('register-btn');
    
    if (loginBtn && registerBtn) {
        loginBtn.style.display = 'none';
        registerBtn.style.display = 'none';
        
        const goToAppBtn = document.createElement('button');
        goToAppBtn.className = 'btn-primary';
        goToAppBtn.textContent = 'Go to App';
        goToAppBtn.addEventListener('click', function() {
            window.location.href = 'ai-app.html';
        });
        
        navMenu.insertBefore(goToAppBtn, document.querySelector('.theme-toggle'));
    }
}

        //PAYMENT FLOW CONNECTION
// Check for payment completion when index.html loads
document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    const paymentStatus = urlParams.get('payment');
    const invoiceId = urlParams.get('invoice_id');
    
    if (paymentStatus === 'success' && invoiceId) {
        verifyPaymentAndRedirect(invoiceId);
    }
});

function verifyPaymentAndRedirect(invoiceId) {
    fetch('/verify-payment', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ invoice_id: invoiceId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Store token and user info
            localStorage.setItem('authToken', data.token);
            localStorage.setItem('userData', JSON.stringify(data.user));
            
            // Redirect to AI app
            window.location.href = 'ai-app.html';
        } else {
            alert('Payment verification failed: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Verification error:', error);
        alert('Payment verification failed. Please contact support if payment was made.');
    });
}

        //ERROR HANDLING
// Handle authentication errors
function handleAuthError(error) {
    console.error('Authentication error:', error);
    localStorage.removeItem('authToken');
    localStorage.removeItem('userData');
    window.location.href = 'index.html';
}

// Example usage in API calls
fetch('/some-protected-endpoint', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('authToken')}`
    }
})
.then(response => {
    if (response.status === 401) {
        handleAuthError('Token expired or invalid');
    }
    return response.json();
})
.catch(error => {
    handleAuthError(error);
});

