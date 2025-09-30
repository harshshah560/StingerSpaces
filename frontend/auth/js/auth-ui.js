// Authentication form handlers
class AuthUI {
    constructor() {
        this.loginTab = document.getElementById('login-tab');
        this.signupTab = document.getElementById('signup-tab');
        this.loginForm = document.getElementById('login-form');
        this.signupForm = document.getElementById('signup-form');
        this.errorMessage = document.getElementById('error-message');
        this.successMessage = document.getElementById('success-message');
        
        this.init();
    }

    init() {
        // Tab switching
        this.loginTab.addEventListener('click', () => this.switchTab('login'));
        this.signupTab.addEventListener('click', () => this.switchTab('signup'));

        // Form submissions
        this.loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        this.signupForm.addEventListener('submit', (e) => this.handleSignup(e));

        // Default to login tab
        this.switchTab('login');
    }

    switchTab(tab) {
        if (tab === 'login') {
            this.loginTab.classList.add('active');
            this.signupTab.classList.remove('active');
            this.loginForm.classList.add('active');
            this.signupForm.classList.remove('active');
        } else {
            this.signupTab.classList.add('active');
            this.loginTab.classList.remove('active');
            this.signupForm.classList.add('active');
            this.loginForm.classList.remove('active');
        }
        this.clearMessages();
    }

    async handleLogin(e) {
        e.preventDefault();
        
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;

        if (!this.validateEmail(email)) {
            this.showError('Please enter a valid Georgia Tech email address (@gatech.edu)');
            return;
        }

        if (!password) {
            this.showError('Please enter your password');
            return;
        }

        this.setLoading(true, 'login');
        this.clearMessages();

        const result = await window.authManager.signIn(email, password);

        if (result.success) {
            this.showSuccess('Login successful! Redirecting...');
            // Redirect will be handled by auth state change
        } else {
            this.showError(result.error);
        }

        this.setLoading(false, 'login');
    }

    async handleSignup(e) {
        e.preventDefault();
        
        const email = document.getElementById('signup-email').value;
        const password = document.getElementById('signup-password').value;
        const confirmPassword = document.getElementById('signup-confirm-password').value;
        const fullName = document.getElementById('signup-name').value;

        if (!this.validateEmail(email)) {
            this.showError('Please enter a valid Georgia Tech email address (@gatech.edu)');
            return;
        }

        if (!fullName.trim()) {
            this.showError('Please enter your full name');
            return;
        }

        if (password.length < 6) {
            this.showError('Password must be at least 6 characters long');
            return;
        }

        if (password !== confirmPassword) {
            this.showError('Passwords do not match');
            return;
        }

        this.setLoading(true, 'signup');
        this.clearMessages();

        const userData = {
            full_name: fullName
        };

        const result = await window.authManager.signUp(email, password, userData);

        if (result.success) {
            this.showSuccess('🎉 Welcome to StingerSpaces! Your account has been created successfully. Please check your email to verify your account and start exploring apartments.');
            // Clear form
            this.signupForm.reset();
        } else {
            this.showError(result.error);
        }

        this.setLoading(false, 'signup');
    }

    validateEmail(email) {
        // Only allow @gatech.edu email addresses
        const gatechEmailRegex = /^[^\s@]+@gatech\.edu$/i;
        return gatechEmailRegex.test(email);
    }

    showError(message) {
        this.errorMessage.textContent = message;
        this.errorMessage.style.display = 'block';
        this.successMessage.style.display = 'none';
    }

    showSuccess(message) {
        this.successMessage.textContent = message;
        this.successMessage.style.display = 'block';
        this.errorMessage.style.display = 'none';
        
        // Scroll to top so user sees the success message
        this.successMessage.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        // Add a slight pulse effect
        this.successMessage.style.transform = 'scale(1.02)';
        setTimeout(() => {
            this.successMessage.style.transform = 'scale(1)';
        }, 200);
    }

    clearMessages() {
        this.errorMessage.style.display = 'none';
        this.successMessage.style.display = 'none';
    }

    setLoading(loading, formType) {
        const button = document.getElementById(`${formType}-button`);
        const spinner = button.querySelector('.loading-spinner');
        const buttonText = button.querySelector('.button-text');

        if (loading) {
            button.disabled = true;
            spinner.style.display = 'inline-block';
            buttonText.textContent = formType === 'login' ? 'Signing In...' : 'Creating Account...';
        } else {
            button.disabled = false;
            spinner.style.display = 'none';
            buttonText.textContent = formType === 'login' ? 'Sign In' : 'Create Account';
        }
    }
}

// Initialize auth UI when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // First check if user is already authenticated
    checkExistingAuth().then(() => {
        new AuthUI();
    });
});

// Check if user is already authenticated and redirect accordingly
async function checkExistingAuth() {
    // Wait for auth services to be available
    const waitForAuth = () => {
        return new Promise((resolve) => {
            const checkAuth = () => {
                if (window.authManager && window.supabaseClient) {
                    resolve();
                } else {
                    setTimeout(checkAuth, 100);
                }
            };
            checkAuth();
        });
    };

    await waitForAuth();

    try {
        // Check authentication status directly from Supabase
        const { data: { session }, error } = await window.supabaseClient.auth.getSession();
        
        if (error) {
            console.error('Error checking auth status on landing page:', error);
            return; // Stay on landing page
        }

        if (session && session.user) {
            console.log('User already authenticated on landing page:', session.user.email);
            
            // Check if user came to login to make a review
            if (sessionStorage.getItem('pendingReview') === 'true') {
                sessionStorage.removeItem('pendingReview');
                console.log('Redirecting authenticated user to review page');
                window.location.href = 'apartment-review.html';
            } else {
                console.log('Redirecting authenticated user to main page');
                window.location.href = 'index.html';
            }
        } else {
            console.log('User not authenticated, staying on landing page');
        }
    } catch (error) {
        console.error('Unexpected error checking authentication on landing page:', error);
        // Stay on landing page on error
    }
}
