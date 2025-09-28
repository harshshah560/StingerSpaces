// Main app authentication integration
class MainAppAuth {
    constructor() {
        console.log('MainAppAuth initializing...');
        this.init();
    }

    async init() {
        // Check authentication status
        await this.checkAuthStatus();
        
        // Add login/logout buttons to header
        this.addAuthButtons();
    }

    async checkAuthStatus() {
        // Wait for both authManager and supabaseClient to be available
        if (!window.authManager || !window.supabaseClient) {
            console.log('Auth services not yet available, waiting...');
            setTimeout(() => this.checkAuthStatus(), 100);
            return;
        }

        // Wait a bit more to ensure AuthManager has finished initializing
        await new Promise(resolve => setTimeout(resolve, 200));

        // Get the current session from Supabase directly to ensure accuracy
        try {
            const { data: { session } } = await window.supabaseClient.auth.getSession();
            
            if (session && session.user) {
                console.log('User is authenticated:', session.user.email);
                window.authManager.currentUser = session.user; // Update the auth manager
                this.showAuthenticatedState(session.user);
            } else {
                console.log('User is not authenticated - staying on page');
                window.authManager.currentUser = null;
                this.showUnauthenticatedState();
                // Don't redirect - let users view the map without authentication
            }
        } catch (error) {
            console.error('Error checking auth status:', error);
            this.showUnauthenticatedState();
            // Don't redirect on error - let users view the map
        }
    }

    addAuthButtons() {
        const header = document.querySelector('header .header-left');
        if (!header) return;

        const authContainer = document.createElement('div');
        authContainer.id = 'auth-container';
        authContainer.style.cssText = `
            position: absolute;
            top: 15px;
            right: 20px;
            display: flex;
            align-items: center;
            gap: 12px;
        `;

        header.parentElement.appendChild(authContainer);
        
        // Add CSS animations for the profile dropdown
        this.addProfileStyles();
        
        this.updateAuthButtons();
    }

    updateAuthButtons(user = null) {
        const authContainer = document.getElementById('auth-container');
        if (!authContainer) return;

        // Use passed user or get from authManager
        const currentUser = user || window.authManager?.getCurrentUser();
        
        if (currentUser) {
            // Get user initials
            const fullName = currentUser.user_metadata?.full_name || currentUser.email;
            const initials = this.getInitials(fullName);
            
            authContainer.innerHTML = `
                <button id="review-button" class="review-button" style="
                    background: var(--gt-gold);
                    color: var(--gt-navy);
                    border: none;
                    padding: 8px 12px;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                " title="Write a review">
                    <span style="font-size: 16px;">⭐</span>
                    Review
                </button>
                
                <div class="profile-container" style="position: relative;">
                    <div id="profile-avatar" class="profile-avatar" style="
                        width: 40px;
                        height: 40px;
                        border-radius: 50%;
                        background: linear-gradient(135deg, var(--gt-gold) 0%, #C4B876 100%);
                        color: var(--gt-navy);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-weight: 700;
                        font-size: 14px;
                        cursor: pointer;
                        border: 3px solid white;
                        box-shadow: 0 2px 6px rgba(0,0,0,0.15);
                        transition: all 0.3s ease;
                        user-select: none;
                        position: relative;
                    " title="${fullName}">
                        ${initials}
                        <div style="
                            position: absolute;
                            bottom: 2px;
                            right: 2px;
                            width: 12px;
                            height: 12px;
                            background: #10B981;
                            border: 2px solid white;
                            border-radius: 50%;
                            box-shadow: 0 1px 3px rgba(0,0,0,0.2);
                        "></div>
                    </div>
                    
                    <div id="profile-dropdown" class="profile-dropdown" style="
                        position: absolute;
                        top: 50px;
                        right: 0;
                        background: white;
                        border: 1px solid #e0e0e0;
                        border-radius: 12px;
                        box-shadow: 0 8px 24px rgba(0,0,0,0.12), 0 2px 8px rgba(0,0,0,0.08);
                        min-width: 220px;
                        z-index: 1000;
                        display: none;
                        overflow: hidden;
                        animation: fadeIn 0.2s ease-out;
                    ">
                        <div style="
                            padding: 16px;
                            border-bottom: 1px solid #eee;
                            background: #f9f9f9;
                        ">
                            <div style="
                                font-weight: 600;
                                color: var(--gt-navy);
                                font-size: 14px;
                                margin-bottom: 4px;
                            ">
                                ${currentUser.user_metadata?.full_name || 'User'}
                            </div>
                            <div style="
                                color: #666;
                                font-size: 12px;
                            ">
                                ${currentUser.email}
                            </div>
                        </div>
                        
                        <div class="dropdown-item" id="logout-option" style="
                            padding: 12px 16px;
                            cursor: pointer;
                            color: var(--gt-navy);
                            font-size: 14px;
                            transition: background-color 0.2s ease;
                            display: flex;
                            align-items: center;
                            gap: 8px;
                        ">
                            <span style="font-size: 16px;">🚪</span>
                            Sign Out
                        </div>
                    </div>
                </div>
            `;

            // Add event listeners
            this.setupProfileListeners();
            this.setupReviewButton();
        } else {
            authContainer.innerHTML = `
                <a href="landing.html" style="
                    background: var(--gt-gold);
                    color: var(--gt-navy);
                    text-decoration: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-size: 14px;
                    font-weight: 500;
                    transition: all 0.3s ease;
                ">Login / Sign Up</a>
            `;
        }
    }

    getInitials(name) {
        if (!name) return '?';
        
        // If it's an email, use the part before @
        if (name.includes('@')) {
            name = name.split('@')[0];
        }
        
        // Split by spaces and get first letter of each word
        const words = name.trim().split(/\s+/);
        if (words.length === 1) {
            // Single word - take first two characters
            return words[0].substring(0, 2).toUpperCase();
        } else {
            // Multiple words - take first letter of first two words
            return (words[0].charAt(0) + words[1].charAt(0)).toUpperCase();
        }
    }

    setupReviewButton() {
        const reviewButton = document.getElementById('review-button');
        if (!reviewButton) return;

        // Add hover effects
        reviewButton.addEventListener('mouseenter', () => {
            reviewButton.style.background = '#C4B876';
            reviewButton.style.transform = 'translateY(-1px)';
            reviewButton.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)';
        });

        reviewButton.addEventListener('mouseleave', () => {
            reviewButton.style.background = 'var(--gt-gold)';
            reviewButton.style.transform = 'translateY(0)';
            reviewButton.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
        });

        // Handle click - trigger review popup
        reviewButton.addEventListener('click', async () => {
            if (window.ReviewPopupManager && window.ReviewPopupManager.triggerReviewPopup) {
                await window.ReviewPopupManager.triggerReviewPopup();
            } else {
                // Fallback if ReviewPopupManager not available
                window.location.href = 'apartment-review.html';
            }
        });
    }

    setupProfileListeners() {
        const profileAvatar = document.getElementById('profile-avatar');
        const profileDropdown = document.getElementById('profile-dropdown');
        const logoutOption = document.getElementById('logout-option');
        
        if (!profileAvatar || !profileDropdown || !logoutOption) return;

        // Toggle dropdown on avatar click
        profileAvatar.addEventListener('click', (e) => {
            e.stopPropagation();
            const isVisible = profileDropdown.style.display === 'block';
            
            if (isVisible) {
                this.hideDropdown(profileAvatar, profileDropdown);
            } else {
                this.showDropdown(profileAvatar, profileDropdown);
            }
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!profileAvatar.contains(e.target) && !profileDropdown.contains(e.target)) {
                this.hideDropdown(profileAvatar, profileDropdown);
            }
        });

        // Handle logout
        logoutOption.addEventListener('click', async () => {
            this.hideDropdown(profileAvatar, profileDropdown);
            await window.authManager.signOut();
            window.location.href = 'landing.html';
        });

        // Add hover effect to logout option
        logoutOption.addEventListener('mouseenter', () => {
            logoutOption.style.backgroundColor = '#f5f5f5';
        });

        logoutOption.addEventListener('mouseleave', () => {
            logoutOption.style.backgroundColor = 'transparent';
        });
    }

    showAuthenticatedState(user) {
        // Add any authenticated user UI updates here
        console.log('Showing authenticated state for:', user.email);
        
        // Update auth buttons to show user info
        this.updateAuthButtons(user);
        
        // You can add more authenticated state updates here
        // For example: show user profile info, enable user-specific features, etc.
    }

    showUnauthenticatedState() {
        // Add any unauthenticated user UI updates here
        console.log('Showing unauthenticated state');
        
        // Update auth buttons to show login option
        this.updateAuthButtons();
    }

    addProfileStyles() {
        // Check if styles already added
        if (document.getElementById('profile-styles')) return;
        
        const styleSheet = document.createElement('style');
        styleSheet.id = 'profile-styles';
        styleSheet.textContent = `
            @keyframes fadeIn {
                from {
                    opacity: 0;
                    transform: translateY(-10px) scale(0.95);
                }
                to {
                    opacity: 1;
                    transform: translateY(0) scale(1);
                }
            }
            
            @keyframes fadeOut {
                from {
                    opacity: 1;
                    transform: translateY(0) scale(1);
                }
                to {
                    opacity: 0;
                    transform: translateY(-10px) scale(0.95);
                }
            }
            
            .profile-dropdown.hiding {
                animation: fadeOut 0.2s ease-in forwards;
            }
            
            .profile-avatar:hover {
                transform: scale(1.05) !important;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
            }
            
            .profile-avatar.active {
                transform: scale(1.05) !important;
                box-shadow: 0 4px 12px rgba(0,0,0,0.25) !important;
                background: linear-gradient(135deg, #C4B876 0%, var(--gt-gold) 100%) !important;
            }
        `;
        document.head.appendChild(styleSheet);
    }

    showDropdown(profileAvatar, profileDropdown) {
        profileDropdown.classList.remove('hiding');
        profileDropdown.style.display = 'block';
        profileAvatar.classList.add('active');
    }

    hideDropdown(profileAvatar, profileDropdown) {
        profileAvatar.classList.remove('active');
        profileDropdown.classList.add('hiding');
        
        // Hide after animation completes
        setTimeout(() => {
            profileDropdown.style.display = 'none';
            profileDropdown.classList.remove('hiding');
        }, 200);
    }
}

// Initialize when auth manager is ready
document.addEventListener('DOMContentLoaded', () => {
    // Wait for auth manager to initialize
    const checkAuthManager = setInterval(() => {
        if (window.authManager) {
            clearInterval(checkAuthManager);
            new MainAppAuth();
        }
    }, 100);
});
