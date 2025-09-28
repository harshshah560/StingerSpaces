// Apartment Review System
class ApartmentReview {
    constructor() {
        this.selectedApartment = null;
        this.ratings = {};
        this.apartmentMatcher = null;
        
        this.init();
    }

    init() {
        this.checkAuthentication();
        this.setupEventListeners();
        this.initializeApartmentMatcher();
    }

    async checkAuthentication() {
        // Wait for auth manager and supabase to be available
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
                console.error('Error checking auth status:', error);
                sessionStorage.setItem('pendingReview', 'true');
                window.location.href = 'landing.html';
                return;
            }

            if (!session || !session.user) {
                console.log('User not authenticated, redirecting to login');
                sessionStorage.setItem('pendingReview', 'true');
                window.location.href = 'landing.html';
                return;
            }
            
            console.log('User authenticated for review:', session.user.email);
            // Update auth manager with current user
            window.authManager.currentUser = session.user;
        } catch (error) {
            console.error('Unexpected error checking authentication:', error);
            sessionStorage.setItem('pendingReview', 'true');
            window.location.href = 'landing.html';
        }
    }

    setupEventListeners() {
        // Apartment search
        document.getElementById('search-apartment-btn').addEventListener('click', () => this.searchApartment());
        document.getElementById('apartment-search-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.searchApartment();
        });

        // Navigation buttons
        document.getElementById('apartment-confirm').addEventListener('click', () => this.showRatingSection());
        document.getElementById('submit-review').addEventListener('click', () => this.submitReview());
        document.getElementById('back-to-map').addEventListener('click', () => {
            window.location.href = 'index.html';
        });

        // Written review character count
        const writtenReviewTextarea = document.getElementById('written-review');
        const charCountElement = document.getElementById('review-char-count');
        
        if (writtenReviewTextarea && charCountElement) {
            writtenReviewTextarea.addEventListener('input', () => {
                const currentLength = writtenReviewTextarea.value.length;
                charCountElement.textContent = currentLength;
                
                // Change color when approaching limit
                if (currentLength > 900) {
                    charCountElement.style.color = '#d32f2f';
                } else if (currentLength > 750) {
                    charCountElement.style.color = '#f57c00';
                } else {
                    charCountElement.style.color = '#666';
                }
            });
        }

        // Rating stars
        document.querySelectorAll('.rating-star').forEach(star => {
            star.addEventListener('click', (e) => this.setRating(e));
            star.addEventListener('mouseover', (e) => this.hoverRating(e));
            star.addEventListener('mouseleave', (e) => this.unhoverRating(e));
        });
    }

    async initializeApartmentMatcher() {
        if (!this.apartmentMatcher) {
            this.apartmentMatcher = new SmartApartmentMatcher();
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
            const result = await this.apartmentMatcher.findOrCreateApartment(query);
            
            if (result.success) {
                // Show the matched apartment with action info
                this.displaySmartSearchResult(result);
            } else if (result.action === 'needs_confirmation') {
                // Show suggestions and manual option
                this.displaySuggestionResults(result, query);
            } else {
                this.showSearchError(result.error || 'No results found');
            }
        } catch (error) {
            console.error('Search error:', error);
            this.showSearchError('An unexpected error occurred');
        } finally {
            searchBtn.textContent = 'Search';
            searchBtn.disabled = false;
        }
    }

    displaySmartSearchResult(result) {
        const resultsContainer = document.getElementById('search-results');
        resultsContainer.innerHTML = '';

        const apt = result.apartment;
        const resultItem = document.createElement('div');
        resultItem.className = 'search-result-item smart-result';
        
        // Generate appropriate messages based on action
        let actionMessage = '';
        let actionClass = '';
        
        switch (result.action) {
            case 'matched_exact':
                actionMessage = '✅ Exact match found';
                actionClass = 'exact-match';
                break;
            case 'matched_fuzzy':
                actionMessage = `🎯 Similar match found (${Math.round(result.similarity * 100)}% similarity)`;
                actionClass = 'fuzzy-match';
                break;
            case 'matched_similar':
                actionMessage = `🏠 Related apartment selected (${Math.round(result.similarity * 100)}% similarity)`;
                actionClass = 'fuzzy-match';
                break;
            case 'created_new':
                if (apt.google_verified) {
                    actionMessage = '✨ New apartment created (Google verified)';
                    actionClass = 'new-apartment-verified';
                } else {
                    actionMessage = '⚠️ New apartment created (unverified)';
                    actionClass = 'new-apartment-unverified';
                }
                break;
        }
        
        const address = apt.formatted_address || apt.address || 'Address not available';
        
        resultItem.innerHTML = `
            <div class="action-indicator ${actionClass}">${actionMessage}</div>
            <div class="result-name">${apt.name}</div>
            <div class="result-address">${address}</div>
            ${apt.price_range ? `<div class="result-price">${apt.price_range}</div>` : ''}
            ${apt.bed_range ? `<div class="result-beds">${apt.bed_range}</div>` : ''}
        `;

        resultItem.addEventListener('click', () => this.selectApartment(apt, resultItem));
        resultsContainer.appendChild(resultItem);
        
        // Auto-select if it's a high confidence match
        if (result.confidence === 'high') {
            setTimeout(() => {
                this.selectApartment(apt, resultItem);
            }, 500);
        }
    }

    displaySuggestionResults(result, originalQuery) {
        const resultsContainer = document.getElementById('search-results');
        resultsContainer.innerHTML = '';

        // Add header message
        const headerDiv = document.createElement('div');
        headerDiv.className = 'suggestions-header';
        headerDiv.innerHTML = `
            <div class="no-match-message">No exact match found for "<strong>${originalQuery}</strong>"</div>
            <div class="suggestions-subtitle">Select from suggestions or create manually:</div>
        `;
        resultsContainer.appendChild(headerDiv);

        // Add local partial match suggestions
        if (result.localSuggestions && result.localSuggestions.length > 0) {
            result.localSuggestions.forEach(suggestion => {
                const suggestionItem = document.createElement('div');
                suggestionItem.className = 'search-result-item suggestion-item local-suggestion';
                
                suggestionItem.innerHTML = `
                    <div class="action-indicator local-match">🏠 Similar apartment found</div>
                    <div class="result-name">${suggestion.name}</div>
                    <div class="result-address">${suggestion.formatted_address || 'Address not available'}</div>
                    <div class="suggestion-note">Click to select this existing apartment</div>
                `;

                suggestionItem.addEventListener('click', () => this.selectExistingApartment(suggestion, suggestionItem));
                resultsContainer.appendChild(suggestionItem);
            });
        }

        // Add Google Places suggestions
        if (result.googleSuggestions && result.googleSuggestions.length > 0) {
            result.googleSuggestions.forEach(suggestion => {
                const suggestionItem = document.createElement('div');
                suggestionItem.className = 'search-result-item suggestion-item';
                
                const apiSource = suggestion.source === 'google_places_legacy' ? 'Google Places (Legacy)' : 'Google Places';
                
                suggestionItem.innerHTML = `
                    <div class="action-indicator google-suggestion">🌐 ${apiSource} suggestion</div>
                    <div class="result-name">${suggestion.name}</div>
                    <div class="result-address">${suggestion.formatted_address}</div>
                    ${suggestion.phone ? `<div class="result-phone">📞 ${suggestion.phone}</div>` : ''}
                    <div class="suggestion-note">Click to add this apartment to our database</div>
                `;

                suggestionItem.addEventListener('click', () => this.confirmGoogleSuggestion(suggestion, suggestionItem));
                resultsContainer.appendChild(suggestionItem);
            });
        }

        // Add manual creation option
        const manualItem = document.createElement('div');
        manualItem.className = 'search-result-item manual-creation-item';
        manualItem.innerHTML = `
            <div class="action-indicator manual-creation">✏️ Create manually</div>
            <div class="result-name">${originalQuery}</div>
            <div class="result-address">Address not available</div>
            <div class="suggestion-note">Click to create this apartment manually</div>
        `;

        manualItem.addEventListener('click', () => this.createManualApartment(originalQuery, manualItem));
        resultsContainer.appendChild(manualItem);
    }

    selectExistingApartment(apartment, element) {
        // Clear other results
        const resultsContainer = document.getElementById('search-results');
        resultsContainer.innerHTML = '';
        
        // Display as selected apartment
        this.displaySmartSearchResult({
            success: true,
            apartment: apartment,
            confidence: 'medium',
            action: 'matched_similar',
            similarity: apartment.similarity
        });
    }

    async confirmGoogleSuggestion(suggestion, element) {
        // Visual feedback
        element.style.opacity = '0.7';
        element.innerHTML = '<div class="loading-results">✨ Adding apartment...</div>';

        try {
            // Create apartment from Google suggestion
            const apartment = await this.apartmentMatcher.createApartmentFromSuggestion(suggestion);
            
            // Clear other results and show success
            const resultsContainer = document.getElementById('search-results');
            resultsContainer.innerHTML = '';
            
            // Display as selected apartment
            this.displayConfirmedApartment(apartment, 'google_confirmed');
            
        } catch (error) {
            console.error('Error confirming Google suggestion:', error);
            
            // Show detailed error message
            let errorMessage = 'Failed to add apartment. ';
            if (error.message.includes('Could not find')) {
                errorMessage += 'Database schema needs to be updated. Please run the missing columns SQL script.';
            } else {
                errorMessage += error.message;
            }
            
            element.innerHTML = `<div class="search-error">${errorMessage}</div>`;
            element.style.opacity = '1';
        }
    }

    async createManualApartment(apartmentName, element) {
        // Visual feedback
        element.style.opacity = '0.7';
        element.innerHTML = '<div class="loading-results">✨ Creating apartment...</div>';

        try {
            // Create basic apartment entry
            const manualApartment = {
                name: apartmentName,
                street_address: null,
                city: 'Atlanta',
                state: 'GA',
                zip_code: null,
                formatted_address: null,
                phone: null,
                url: null,
                price_range: null,
                bed_range: null,
                image_url: null,
                user_generated: true,
                google_place_id: null,
                google_verified: false
            };

            const apartment = await this.apartmentMatcher.createApartmentFromSuggestion(manualApartment);
            
            // Clear other results and show success
            const resultsContainer = document.getElementById('search-results');
            resultsContainer.innerHTML = '';
            
            // Display as selected apartment
            this.displayConfirmedApartment(apartment, 'manual_confirmed');
            
        } catch (error) {
            console.error('Error creating manual apartment:', error);
            
            // Show detailed error message
            let errorMessage = 'Failed to create apartment. ';
            if (error.message.includes('Could not find')) {
                errorMessage += 'Database schema needs to be updated. Please run the missing columns SQL script.';
            } else {
                errorMessage += error.message;
            }
            
            element.innerHTML = `<div class="search-error">${errorMessage}</div>`;
            element.style.opacity = '1';
        }
    }

    displayConfirmedApartment(apartment, action) {
        const resultsContainer = document.getElementById('search-results');
        resultsContainer.innerHTML = '';

        const resultItem = document.createElement('div');
        resultItem.className = 'search-result-item confirmed-apartment';
        
        let actionMessage = '';
        let actionClass = '';
        
        switch (action) {
            case 'google_confirmed':
                actionMessage = '✅ Apartment added (Google verified)';
                actionClass = 'confirmed-google';
                break;
            case 'manual_confirmed':
                actionMessage = '✅ Apartment added (manual entry)';
                actionClass = 'confirmed-manual';
                break;
        }
        
        const address = apartment.formatted_address || apartment.address || 'Address not specified';
        
        resultItem.innerHTML = `
            <div class="action-indicator ${actionClass}">${actionMessage}</div>
            <div class="result-name">${apartment.name}</div>
            <div class="result-address">${address}</div>
            ${apartment.phone ? `<div class="result-phone">📞 ${apartment.phone}</div>` : ''}
            ${apartment.user_generated ? `<div class="user-contributed">👤 User-contributed apartment</div>` : ''}
        `;

        resultItem.addEventListener('click', () => this.selectApartment(apartment, resultItem));
        resultsContainer.appendChild(resultItem);
        
        // Auto-select the confirmed apartment
        setTimeout(() => {
            this.selectApartment(apartment, resultItem);
        }, 800);
    }

    displaySearchResults(apartments) {
        const resultsContainer = document.getElementById('search-results');
        resultsContainer.innerHTML = '';

        apartments.forEach(apt => {
            const resultItem = document.createElement('div');
            resultItem.className = 'search-result-item';
            
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

        const address = apartment.formatted_address || apartment.address || 'Address not specified';
        
        // Show selected apartment info
        const selectedContainer = document.getElementById('selected-apartment');
        selectedContainer.innerHTML = `
            <h4>✅ Selected: ${apartment.name}</h4>
            <p>📍 ${address}</p>
            ${apartment.price_range ? `<p>� ${apartment.price_range}</p>` : ''}
            ${apartment.bed_range ? `<p>🏠 ${apartment.bed_range}</p>` : ''}
            ${apartment.user_generated ? `<p>✨ User-contributed apartment</p>` : ''}
        `;
        selectedContainer.classList.add('show');

        // Show continue button
        document.getElementById('apartment-confirm').style.display = 'block';
    }

    showNoResults() {
        const resultsContainer = document.getElementById('search-results');
        resultsContainer.innerHTML = '<div class="no-results">No apartments found. Try a different search term.</div>';
    }

    showSearchError(message = 'Search error. Please try again.') {
        const resultsContainer = document.getElementById('search-results');
        resultsContainer.innerHTML = `<div class="search-error">${message}</div>`;
    }

    showRatingSection() {
        document.getElementById('apartment-search-section').style.display = 'none';
        document.getElementById('rating-section').classList.add('active');
        
        // Update the apartment name in the rating section
        document.getElementById('selected-apartment-name').textContent = this.selectedApartment.name;
    }

    setRating(e) {
        const star = e.target;
        const rating = parseInt(star.dataset.rating);
        const ratingContainer = star.parentElement;
        const ratingItem = ratingContainer.closest('.rating-item');
        const category = ratingItem.dataset.category;
        const stars = ratingContainer.querySelectorAll('.rating-star');

        // Store the rating
        this.ratings[category] = rating;

        // Clear all active states
        stars.forEach(s => s.classList.remove('active'));

        // Set active states up to clicked star
        for (let i = 0; i < rating; i++) {
            stars[i].classList.add('active');
        }

        // Check if all categories are rated
        this.checkReviewCompletion();
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

    checkReviewCompletion() {
        const requiredCategories = ['safety', 'proximity_grocery', 'maintenance', 'management', 'amenities'];
        const completedCategories = Object.keys(this.ratings);
        
        const isComplete = requiredCategories.every(category => 
            completedCategories.includes(category) && this.ratings[category] > 0
        );

        const submitBtn = document.getElementById('submit-review');
        submitBtn.disabled = !isComplete;
        
        if (isComplete) {
            submitBtn.textContent = 'Submit Review';
        } else {
            submitBtn.textContent = `Submit Review (${completedCategories.length}/${requiredCategories.length} categories rated)`;
        }
    }

    async submitReview() {
        if (!this.selectedApartment || Object.keys(this.ratings).length === 0) {
            alert('Please complete all ratings before submitting.');
            return;
        }

        const currentUser = window.authManager.getCurrentUser();
        if (!currentUser) {
            alert('You must be logged in to submit a review.');
            return;
        }

        const submitBtn = document.getElementById('submit-review');
        submitBtn.textContent = 'Submitting...';
        submitBtn.disabled = true;

        try {
            // Get written review if provided
            const writtenReviewElement = document.getElementById('written-review');
            const writtenReview = writtenReviewElement ? writtenReviewElement.value.trim() : '';

            // Get financial information
            const monthlyRent = document.getElementById('monthly-rent')?.value ? parseFloat(document.getElementById('monthly-rent').value) : null;
            const hiddenFees = document.getElementById('hidden-fees')?.value ? parseFloat(document.getElementById('hidden-fees').value) : null;
            const utilitiesCost = document.getElementById('utilities-cost')?.value ? parseFloat(document.getElementById('utilities-cost').value) : null;
            const parkingCost = document.getElementById('parking-cost')?.value !== '' ? parseFloat(document.getElementById('parking-cost').value || 0) : null;

            // Calculate overall rating as average of category ratings
            const categoryRatings = [
                this.ratings.safety,
                this.ratings.proximity_grocery,
                this.ratings.maintenance,
                this.ratings.management,
                this.ratings.amenities
            ].filter(rating => rating && rating > 0);
            
            const overallRating = categoryRatings.length > 0 
                ? categoryRatings.reduce((sum, rating) => sum + rating, 0) / categoryRatings.length 
                : null;

            // Prepare review data for Supabase using the correct column names
            const reviewData = {
                user_id: currentUser.id,
                apartment_name: this.selectedApartment.name,
                safety_rating: this.ratings.safety || null,
                proximity_grocery_rating: this.ratings.proximity_grocery || null,
                maintenance_rating: this.ratings.maintenance || null,
                management_rating: this.ratings.management || null,
                amenities_rating: this.ratings.amenities || null,
                overall_rating: overallRating,
                written_review: writtenReview || null
            };

            // Add financial data only if the fields exist (to handle migration timing)
            if (document.getElementById('monthly-rent')) {
                reviewData.monthly_rent = monthlyRent;
            }
            if (document.getElementById('hidden-fees')) {
                reviewData.hidden_fees = hiddenFees;
            }
            if (document.getElementById('utilities-cost')) {
                reviewData.utilities_cost = utilitiesCost;
            }
            if (document.getElementById('parking-cost')) {
                reviewData.parking_cost = parkingCost;
            }

            console.log('Submitting review to Supabase:', reviewData);

            // Submit to Supabase
            let { data, error } = await window.supabaseClient
                .from('apartment_reviews')
                .upsert(reviewData, {
                    onConflict: 'user_id,apartment_name'
                });

            // If financial columns don't exist, retry without them
            if (error && error.message.includes('Could not find') && (error.message.includes('hidden_fees') || error.message.includes('monthly_rent') || error.message.includes('utilities_cost') || error.message.includes('parking_cost'))) {
                console.log('Financial columns not found, retrying without financial data...');
                
                const basicReviewData = {
                    user_id: currentUser.id,
                    apartment_name: this.selectedApartment.name,
                    safety_rating: this.ratings.safety || null,
                    proximity_grocery_rating: this.ratings.proximity_grocery || null,
                    maintenance_rating: this.ratings.maintenance || null,
                    management_rating: this.ratings.management || null,
                    amenities_rating: this.ratings.amenities || null,
                    written_review: writtenReview || null
                };

                const retryResult = await window.supabaseClient
                    .from('apartment_reviews')
                    .upsert(basicReviewData, {
                        onConflict: 'user_id,apartment_name'
                    });

                data = retryResult.data;
                error = retryResult.error;
                
                if (!error) {
                    console.log('Review submitted successfully without financial data');
                }
            }

            if (error) {
                throw error;
            }

            console.log('Review submitted successfully:', data);

            // Update user preferences to mark they've submitted their first review
            await this.updateUserPreferences();

            // Show success
            this.showSuccessSection();

        } catch (error) {
            console.error('Error submitting review:', error);
            
            let errorMessage = 'Error submitting review. Please try again.';
            if (error.message) {
                if (error.message.includes('Could not find') && error.message.includes('hidden_fees')) {
                    errorMessage = 'Database schema needs to be updated. Please run the ADD_FINANCIAL_COLUMNS.sql script in Supabase first.';
                } else if (error.message.includes('Could not find')) {
                    errorMessage = 'Database schema needs to be updated. Please check for missing columns.';
                } else {
                    errorMessage = `Error: ${error.message}`;
                }
            }
            
            alert(errorMessage);
        } finally {
            submitBtn.textContent = 'Submit Review';
            submitBtn.disabled = false;
        }
    }

    async updateUserPreferences() {
        try {
            const currentUser = window.authManager.getCurrentUser();
            if (!currentUser) return;

            await window.supabaseClient
                .from('user_preferences')
                .upsert({
                    user_id: currentUser.id,
                    has_submitted_first_review: true,
                    show_review_popup: false,
                    updated_at: new Date().toISOString()
                }, {
                    onConflict: 'user_id'
                });

            console.log('User preferences updated after review submission');
        } catch (error) {
            console.error('Error updating user preferences:', error);
            // Don't fail the review submission if preferences update fails
        }
    }

    showSuccessSection() {
        document.getElementById('rating-section').classList.remove('active');
        document.getElementById('success-section').classList.add('active');
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ApartmentReview();
});
