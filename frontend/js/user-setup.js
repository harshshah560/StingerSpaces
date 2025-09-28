// User Setup JavaScript
class UserSetup {
    constructor() {
        this.selectedOptions = [];
        this.seekerRanking = [];
        this.reviewerRatings = {};
        this.selectedApartment = null;
        this.currentStep = 'selection';
        this.apartmentMatcher = null; // Will be initialized when needed
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeDragAndDrop();
        this.checkAuthenticationStatus();
    }

    checkAuthenticationStatus() {
        // Wait for auth manager to be available
        const checkAuth = () => {
            if (window.authManager) {
                const user = window.authManager.getCurrentUser();
                if (user) {
                    console.log('User authenticated in setup:', user.email);
                } else {
                    console.log('Warning: User not authenticated in setup page');
                    // Optionally redirect to login if not authenticated
                    // window.location.href = 'landing.html';
                }
            } else {
                setTimeout(checkAuth, 100);
            }
        };
        checkAuth();
    }

    setupEventListeners() {
        // Option selection
        document.querySelectorAll('.setup-option').forEach(option => {
            option.addEventListener('click', (e) => this.toggleOption(e));
        });

        // Continue buttons
        document.getElementById('setup-continue').addEventListener('click', () => this.startSetup());
        document.getElementById('seeker-continue').addEventListener('click', () => this.completeSeekerSetup());
        document.getElementById('apartment-confirm').addEventListener('click', () => this.showRatingSetup());
        document.getElementById('reviewer-continue').addEventListener('click', () => this.completeReviewerSetup());
        document.getElementById('finish-setup').addEventListener('click', () => this.finishSetup());
        
        // Apartment search
        document.getElementById('search-apartment-btn').addEventListener('click', () => this.searchApartment());
        document.getElementById('apartment-search-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.searchApartment();
        });

        // Rating stars
        document.querySelectorAll('.rating-star').forEach(star => {
            star.addEventListener('click', (e) => this.setRating(e));
            star.addEventListener('mouseover', (e) => this.hoverRating(e));
            star.addEventListener('mouseleave', (e) => this.unhoverRating(e));
        });
    }

    toggleOption(e) {
        const option = e.currentTarget;
        const optionType = option.dataset.option;
        
        if (option.classList.contains('selected')) {
            option.classList.remove('selected');
            this.selectedOptions = this.selectedOptions.filter(opt => opt !== optionType);
        } else {
            option.classList.add('selected');
            this.selectedOptions.push(optionType);
        }

        // Enable/disable continue button
        const continueBtn = document.getElementById('setup-continue');
        continueBtn.disabled = this.selectedOptions.length === 0;
    }

    startSetup() {
        document.getElementById('option-selection').style.display = 'none';
        
        if (this.selectedOptions.includes('seeker')) {
            this.showSeekerSetup();
        } else if (this.selectedOptions.includes('reviewer')) {
            this.showReviewerSetup();
        }
    }

    showSeekerSetup() {
        document.getElementById('seeker-setup').classList.add('active');
        this.currentStep = 'seeker';
    }

    showReviewerSetup() {
        document.getElementById('reviewer-setup').classList.add('active');
        this.currentStep = 'reviewer';
        this.initializeApartmentMatcher();
    }

    async initializeApartmentMatcher() {
        if (!this.apartmentMatcher) {
            // Initialize with real Google Places API
            this.apartmentMatcher = new ApartmentMatcher('AIzaSyBv7At7YSjsUBgGUAJMd6_o-MTH1AB9QTE');
            await this.apartmentMatcher.init();
        }
    }



    async searchApartment() {
        const query = document.getElementById('apartment-search-input').value.trim();
        if (!query) return;

        const searchBtn = document.getElementById('search-apartment-btn');
        searchBtn.textContent = 'Searching...';
        searchBtn.disabled = true;

        // Show loading state
        const resultsContainer = document.getElementById('search-results');
        resultsContainer.innerHTML = '<div class="loading-results">🔍 Searching for apartments...</div>';

        try {
            // Use real Google Places API
            const result = await this.apartmentMatcher.matchUserApartment(query);
            
            if (result.success) {
                // If we found a direct match, show it
                this.displaySearchResults([result.apartment]);
            } else if (result.suggestions && result.suggestions.length > 0) {
                // Show suggestions if no direct match found
                this.displaySearchResults(result.suggestions);
            } else {
                this.showNoResults();
            }
        } catch (error) {
            console.error('Search error:', error);
            this.showSearchError();
        } finally {
            searchBtn.textContent = 'Search';
            searchBtn.disabled = false;
        }
    }

    displaySearchResults(apartments) {
        const resultsContainer = document.getElementById('search-results');
        resultsContainer.innerHTML = '';

        apartments.forEach(apt => {
            const resultItem = document.createElement('div');
            resultItem.className = 'search-result-item';
            
            // Format distance - handle both meters and potential undefined values
            const distance = apt.distance_from_gt ? 
                (apt.distance_from_gt > 1000 ? 
                    `${(apt.distance_from_gt / 1000).toFixed(1)}km` : 
                    `${Math.round(apt.distance_from_gt)}m`) 
                : 'Distance unknown';
            
            resultItem.innerHTML = `
                <div class="result-name">${apt.name}</div>
                <div class="result-address">${apt.address}</div>
                <div class="result-distance">${distance} from Georgia Tech</div>
                ${apt.rating ? `<div class="result-rating">⭐ ${apt.rating}/5</div>` : ''}
            `;

            resultItem.addEventListener('click', () => this.selectApartment(apt, resultItem));
            resultsContainer.appendChild(resultItem);
        });
    }

    selectApartment(apartment, element) {
        // Remove previous selections
        document.querySelectorAll('.search-result-item').forEach(item => {
            item.classList.remove('selected');
        });

        // Select current item
        element.classList.add('selected');
        this.selectedApartment = apartment;

        // Format distance consistently
        const distance = apartment.distance_from_gt ? 
            (apartment.distance_from_gt > 1000 ? 
                `${(apartment.distance_from_gt / 1000).toFixed(1)}km` : 
                `${Math.round(apartment.distance_from_gt)}m`) 
            : 'Distance unknown';

        // Show selected apartment info
        const selectedContainer = document.getElementById('selected-apartment');
        selectedContainer.innerHTML = `
            <h4>✅ Selected: ${apartment.name}</h4>
            <p>📍 ${apartment.address}</p>
            <p>📏 ${distance} from Georgia Tech</p>
            ${apartment.rating ? `<p>⭐ Google Rating: ${apartment.rating}/5</p>` : ''}
        `;
        selectedContainer.classList.add('show');

        // Show continue button
        document.getElementById('apartment-confirm').style.display = 'block';
    }

    showNoResults() {
        const resultsContainer = document.getElementById('search-results');
        resultsContainer.innerHTML = '<div class="no-results">No apartments found. Try a different search term.</div>';
    }

    showSearchError() {
        const resultsContainer = document.getElementById('search-results');
        resultsContainer.innerHTML = '<div class="search-error">Search error. Please try again.</div>';
    }

    showRatingSetup() {
        document.getElementById('reviewer-setup').classList.remove('active');
        document.getElementById('rating-setup').classList.add('active');
        
        // Update the apartment name in the rating section
        document.getElementById('selected-apartment-name').textContent = this.selectedApartment.name;
    }

    completeSeekerSetup() {
        // Get the current ranking order
        const rankingItems = document.querySelectorAll('#ranking-list .ranking-item');
        this.seekerRanking = Array.from(rankingItems).map(item => ({
            priority: item.dataset.priority,
            rank: Array.from(rankingItems).indexOf(item) + 1
        }));

        console.log('Seeker Rankings:', this.seekerRanking);

        document.getElementById('seeker-setup').classList.remove('active');

        if (this.selectedOptions.includes('reviewer')) {
            this.showReviewerSetup();
        } else {
            this.showComplete();
        }
    }

    completeReviewerSetup() {
        // Get all ratings
        document.querySelectorAll('#rating-setup .rating-item').forEach(item => {
            const category = item.dataset.category;
            const activeStars = item.querySelectorAll('.rating-star.active');
            this.reviewerRatings[category] = activeStars.length;
        });

        console.log('Reviewer Ratings:', this.reviewerRatings);

        document.getElementById('reviewer-setup').classList.remove('active');
        
        if (this.selectedOptions.includes('seeker') && this.currentStep !== 'seeker-complete') {
            this.showSeekerSetup();
            this.currentStep = 'seeker-complete';
        } else {
            this.showComplete();
        }
    }

    showComplete() {
        document.getElementById('complete-setup').classList.add('active');
        
        // Log final results
        console.log('Setup Complete!');
        console.log('Selected Options:', this.selectedOptions);
        console.log('Seeker Rankings:', this.seekerRanking);
        console.log('Reviewer Ratings:', this.reviewerRatings);
        
        // Here we would typically save to Supabase
        this.saveUserPreferences();
    }

    saveUserPreferences() {
        const userPreferences = {
            user_type: this.selectedOptions,
            seeker_preferences: this.seekerRanking,
            reviewer_ratings: this.reviewerRatings,
            selected_apartment: this.selectedApartment,
            setup_completed: true,
            created_at: new Date().toISOString()
        };

        // For now, just save to localStorage (we'll add Supabase later)
        localStorage.setItem('userPreferences', JSON.stringify(userPreferences));
        
        console.log('User preferences saved:', userPreferences);
    }

    finishSetup() {
        // Ensure user stays authenticated and redirect to main apartment map
        console.log('Setup complete, redirecting to main app...');
        
        // Make sure we preserve authentication state
        if (window.authManager && window.authManager.getCurrentUser()) {
            console.log('User authenticated, proceeding to main app');
        } else {
            console.log('Warning: User not authenticated in setup');
        }
        
        // Redirect to main apartment map
        window.location.href = 'index.html';
    }

    // Rating functionality
    setRating(e) {
        const star = e.target;
        const rating = parseInt(star.dataset.rating);
        const ratingContainer = star.parentElement;
        const stars = ratingContainer.querySelectorAll('.rating-star');

        // Clear all active states
        stars.forEach(s => s.classList.remove('active'));

        // Set active states up to clicked star
        for (let i = 0; i < rating; i++) {
            stars[i].classList.add('active');
        }
    }

    hoverRating(e) {
        const star = e.target;
        const rating = parseInt(star.dataset.rating);
        const ratingContainer = star.parentElement;
        const stars = ratingContainer.querySelectorAll('.rating-star');

        // Temporarily highlight stars up to hovered star
        stars.forEach((s, index) => {
            if (index < rating) {
                s.style.color = '#ffc107';
            } else {
                s.style.color = s.classList.contains('active') ? '#ffc107' : '#ddd';
            }
        });
    }

    unhoverRating(e) {
        const star = e.target;
        const ratingContainer = star.parentElement;
        const stars = ratingContainer.querySelectorAll('.rating-star');

        // Reset to normal state
        stars.forEach(s => {
            s.style.color = s.classList.contains('active') ? '#ffc107' : '#ddd';
        });
    }

    // Drag and drop functionality
    initializeDragAndDrop() {
        const rankingList = document.getElementById('ranking-list');
        let draggedElement = null;

        // Add drag event listeners to ranking items
        document.querySelectorAll('.ranking-item').forEach(item => {
            item.draggable = true;

            item.addEventListener('dragstart', (e) => {
                draggedElement = item;
                item.classList.add('dragging');
                e.dataTransfer.effectAllowed = 'move';
            });

            item.addEventListener('dragend', (e) => {
                item.classList.remove('dragging');
                draggedElement = null;
            });

            item.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';
            });

            item.addEventListener('drop', (e) => {
                e.preventDefault();
                if (draggedElement && draggedElement !== item) {
                    const draggedIndex = Array.from(rankingList.children).indexOf(draggedElement);
                    const targetIndex = Array.from(rankingList.children).indexOf(item);

                    if (draggedIndex < targetIndex) {
                        rankingList.insertBefore(draggedElement, item.nextSibling);
                    } else {
                        rankingList.insertBefore(draggedElement, item);
                    }
                }
            });
        });
    }
}

// Initialize setup when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new UserSetup();
});
