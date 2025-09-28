// Review Popup Manager
class ReviewPopupManager {
    constructor() {
        this.popup = null;
        this.userPreferences = null;
        this.currentUser = null;
        this.init();
    }

    async init() {
        this.popup = document.getElementById('review-popup');
        this.setupEventListeners();
        
        // Wait for auth to be ready and check if we should show popup
        await this.checkShouldShowPopup();
    }

    async checkShouldShowPopup() {
        // Wait for auth services to be ready
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
            // Check if user is authenticated
            const { data: { session }, error } = await window.supabaseClient.auth.getSession();
            
            if (error || !session || !session.user) {
                // Not authenticated - show popup after delay for anonymous users
                setTimeout(() => {
                    this.showPopup();
                }, 3000);
                return;
            }

            this.currentUser = session.user;
            
            // Get user preferences from database
            const preferences = await this.getUserPreferences();
            
            if (preferences && !preferences.show_review_popup) {
                // User has dismissed popup permanently, don't show
                console.log('User has dismissed review popup, not showing');
                return;
            }

            // Show popup after delay for authenticated users who haven't dismissed it
            setTimeout(() => {
                this.showPopup();
            }, 2000);

        } catch (error) {
            console.error('Error checking popup preferences:', error);
            // On error, show popup anyway
            setTimeout(() => {
                this.showPopup();
            }, 3000);
        }
    }

    async getUserPreferences() {
        if (!this.currentUser) return null;

        try {
            const { data, error } = await window.supabaseClient
                .from('user_preferences')
                .select('*')
                .eq('user_id', this.currentUser.id)
                .single();

            if (error && error.code !== 'PGRST116') { // PGRST116 = no rows found
                console.error('Error fetching user preferences:', error);
                return null;
            }

            this.userPreferences = data;
            return data;
        } catch (error) {
            console.error('Unexpected error fetching user preferences:', error);
            return null;
        }
    }

    async updateUserPreferences(updates) {
        if (!this.currentUser) return false;

        try {
            const { data, error } = await window.supabaseClient
                .from('user_preferences')
                .upsert({
                    user_id: this.currentUser.id,
                    ...updates,
                    updated_at: new Date().toISOString()
                }, {
                    onConflict: 'user_id'
                });

            if (error) {
                console.error('Error updating user preferences:', error);
                return false;
            }

            console.log('User preferences updated successfully');
            return true;
        } catch (error) {
            console.error('Unexpected error updating user preferences:', error);
            return false;
        }
    }

    setupEventListeners() {
        // Close popup button
        document.getElementById('popup-close').addEventListener('click', () => {
            this.handlePopupClose();
        });

        // Make a review button
        document.getElementById('make-review-btn').addEventListener('click', () => {
            this.handleMakeReview();
        });

        // Continue browsing button
        document.getElementById('continue-browsing-btn').addEventListener('click', () => {
            this.handleContinueBrowsing();
        });

        // Close popup when clicking outside
        this.popup.addEventListener('click', (e) => {
            if (e.target === this.popup) {
                this.handlePopupClose();
            }
        });

        // Close popup with Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.popup.classList.contains('show')) {
                this.handlePopupClose();
            }
        });
    }

    showPopup() {
        if (this.popup) {
            this.popup.classList.add('show');
        }
    }

    hidePopup() {
        if (this.popup) {
            this.popup.classList.remove('show');
        }
    }

    async handlePopupClose() {
        this.hidePopup();
        // Don't update preferences just for closing - only for explicit actions
    }

    async handleContinueBrowsing() {
        this.hidePopup();
        
        // Update user preferences to not show popup again
        if (this.currentUser) {
            await this.updateUserPreferences({
                has_dismissed_review_popup: true,
                show_review_popup: false
            });
        }
    }

    async handleMakeReview() {
        this.hidePopup();
        
        // Wait for auth manager to be ready
        if (!window.authManager || !window.supabaseClient) {
            console.log('Auth services not ready, redirecting to login');
            sessionStorage.setItem('pendingReview', 'true');
            window.location.href = 'landing.html';
            return;
        }

        try {
            // Check authentication status directly from Supabase
            const { data: { session }, error } = await window.supabaseClient.auth.getSession();
            
            if (error) {
                console.error('Error checking auth status:', error);
                // On error, redirect to login to be safe
                sessionStorage.setItem('pendingReview', 'true');
                window.location.href = 'landing.html';
                return;
            }

            if (session && session.user) {
                // User is authenticated, update preferences and go to review page
                await this.updateUserPreferences({
                    show_review_popup: false // Don't show popup again after they've started a review
                });
                
                console.log('User authenticated, redirecting to review page');
                window.location.href = 'apartment-review.html';
            } else {
                // User not authenticated, redirect to login with return URL
                console.log('User not authenticated, redirecting to login');
                sessionStorage.setItem('pendingReview', 'true');
                window.location.href = 'landing.html';
            }
        } catch (error) {
            console.error('Unexpected error checking authentication:', error);
            // On error, redirect to login to be safe
            sessionStorage.setItem('pendingReview', 'true');
            window.location.href = 'landing.html';
        }
    }

    // Static method to trigger popup from external button
    static async triggerReviewPopup() {
        // Directly go to review page, bypassing popup for manual triggers
        try {
            const { data: { session }, error } = await window.supabaseClient.auth.getSession();
            
            if (error) {
                console.error('Error checking auth status:', error);
                sessionStorage.setItem('pendingReview', 'true');
                window.location.href = 'landing.html';
                return;
            }

            if (session && session.user) {
                console.log('User authenticated, redirecting to review page');
                window.location.href = 'apartment-review.html';
            } else {
                console.log('User not authenticated, redirecting to login');
                sessionStorage.setItem('pendingReview', 'true');
                window.location.href = 'landing.html';
            }
        } catch (error) {
            console.error('Unexpected error:', error);
            sessionStorage.setItem('pendingReview', 'true');
            window.location.href = 'landing.html';
        }
    }

    // Method to check if user came back from login to make a review
    static checkPendingReview() {
        if (sessionStorage.getItem('pendingReview') === 'true') {
            sessionStorage.removeItem('pendingReview');
            // Redirect to review page
            window.location.href = 'apartment-review.html';
        }
    }
}

// Initialize the review popup when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Check if user came back from login to make a review
    ReviewPopupManager.checkPendingReview();
    
    // Initialize the popup manager
    new ReviewPopupManager();
});
