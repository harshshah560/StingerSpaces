// Supabase configuration
const SUPABASE_URL = 'https://dbkmzqknpvzumthytnyw.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRia216cWtucHZ6dW10aHl0bnl3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg5MzUyNzQsImV4cCI6MjA3NDUxMTI3NH0.B0wXbXmKHW1iJzmMfOsi4_-fnl_qZUduE2CYn2AOlKE'
// Initialize Supabase client and make it globally available
const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
window.supabaseClient = supabase;

// Auth state management
class AuthManager {
    constructor() {
        this.currentUser = null;
        this.init();
    }

    async init() {
        try {
            // Check if user is already logged in
            const { data: { user } } = await supabase.auth.getUser();
            this.currentUser = user;
            console.log('AuthManager initialized with user:', user?.email || 'none');
        } catch (error) {
            console.error('Error getting user during init:', error);
            this.currentUser = null;
        }
        
        // Listen for auth changes
        supabase.auth.onAuthStateChange((event, session) => {
            console.log('Auth state change event:', event, 'User:', session?.user?.email || 'none');
            this.currentUser = session?.user || null;
            this.handleAuthStateChange(event, session);
        });
    }

    handleAuthStateChange(event, session) {
        if (event === 'SIGNED_IN') {
            console.log('User signed in:', session.user);
            // After login, check if user wanted to make a review
            const currentPath = window.location.pathname;
            console.log('Current path during sign in:', currentPath);
            
            // Only redirect if we're on the landing page
            if (currentPath.includes('landing.html')) {
                // Check if user came to login to make a review
                if (sessionStorage.getItem('pendingReview') === 'true') {
                    sessionStorage.removeItem('pendingReview');
                    console.log('Redirecting to review page');
                    window.location.href = 'apartment-review.html';
                } else {
                    console.log('Redirecting to main page');
                    window.location.href = 'index.html';
                }
            } else {
                console.log('Already on correct page, not redirecting');
            }
        } else if (event === 'SIGNED_OUT') {
            console.log('User signed out');
            this.currentUser = null;
        }
    }

    async signUp(email, password, userData = {}) {
        try {
            // Validate Georgia Tech email domain
            if (!email.toLowerCase().endsWith('@gatech.edu')) {
                throw new Error('Only Georgia Tech email addresses (@gatech.edu) are allowed');
            }

            const { data, error } = await supabase.auth.signUp({
                email: email,
                password: password,
                options: {
                    data: userData
                }
            });

            if (error) throw error;
            return { success: true, data };
        } catch (error) {
            console.error('Sign up error:', error);
            return { success: false, error: error.message };
        }
    }

    async signIn(email, password) {
        try {
            // Validate Georgia Tech email domain
            if (!email.toLowerCase().endsWith('@gatech.edu')) {
                throw new Error('Only Georgia Tech email addresses (@gatech.edu) are allowed');
            }

            const { data, error } = await supabase.auth.signInWithPassword({
                email: email,
                password: password
            });

            if (error) throw error;
            return { success: true, data };
        } catch (error) {
            console.error('Sign in error:', error);
            return { success: false, error: error.message };
        }
    }

    async signOut() {
        try {
            const { error } = await supabase.auth.signOut();
            if (error) throw error;
            return { success: true };
        } catch (error) {
            console.error('Sign out error:', error);
            return { success: false, error: error.message };
        }
    }

    isAuthenticated() {
        return this.currentUser !== null;
    }

    getCurrentUser() {
        return this.currentUser;
    }
}

// Create global auth instance
window.authManager = new AuthManager();
