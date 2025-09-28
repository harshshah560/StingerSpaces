// Smart Apartment Matcher with Fuzzy Search and Dynamic Creation
class SmartApartmentMatcher {
    constructor() {
        this.apartmentData = [];
        this.similarityThreshold = 0.6; // 60% similarity to match
        this.highConfidenceThreshold = 0.8; // 80% similarity for high confidence
    }

    async init() {
        await this.loadApartmentData();
    }

    async loadApartmentData() {
        try {
            const response = await fetch('./apartment_data.json');
            this.apartmentData = await response.json();
            console.log(`Loaded ${this.apartmentData.length} apartments for matching`);
        } catch (error) {
            console.error('Error loading apartment data:', error);
            this.apartmentData = [];
        }
    }

    // Main function: find apartment or get suggestions
    async findOrCreateApartment(userInput) {
        const input = userInput.trim();
        
        if (!input) {
            return { success: false, error: 'Empty apartment name' };
        }

        // Step 1: Try exact match
        const exactMatch = this.findExactMatch(input);
        if (exactMatch) {
            return {
                success: true,
                apartment: exactMatch,
                confidence: 'high',
                action: 'matched_exact'
            };
        }

        // Step 2: Try fuzzy match
        const fuzzyMatch = this.findFuzzyMatch(input);
        if (fuzzyMatch) {
            return {
                success: true,
                apartment: fuzzyMatch.apartment,
                confidence: fuzzyMatch.confidence,
                action: 'matched_fuzzy',
                similarity: fuzzyMatch.similarity
            };
        }

        // Step 3: Get Google Places suggestions (don't auto-create)
        const googleSuggestions = await this.getGooglePlacesSuggestions(input);
        
        // Step 4: Also provide similar local suggestions based on partial matching
        const localSuggestions = this.getLocalSuggestions(input);
        
        return {
            success: false,
            action: 'needs_confirmation',
            userInput: input,
            googleSuggestions: googleSuggestions,
            localSuggestions: localSuggestions,
            message: 'No exact match found. Please select from suggestions or create manually.'
        };
    }

    // Find exact match (case-insensitive)
    findExactMatch(input) {
        return this.apartmentData.find(apt => 
            apt.name.toLowerCase() === input.toLowerCase()
        );
    }

    // Find fuzzy match using string similarity
    findFuzzyMatch(input) {
        const similarities = this.apartmentData.map(apt => ({
            apartment: apt,
            similarity: this.calculateSimilarity(input.toLowerCase(), apt.name.toLowerCase())
        }));

        // Sort by similarity (highest first)
        similarities.sort((a, b) => b.similarity - a.similarity);
        const bestMatch = similarities[0];

        if (bestMatch.similarity >= this.similarityThreshold) {
            return {
                apartment: bestMatch.apartment,
                similarity: bestMatch.similarity,
                confidence: bestMatch.similarity >= this.highConfidenceThreshold ? 'high' : 'medium'
            };
        }

        return null;
    }

    // Get Google Places suggestions (don't create automatically)
    async getGooglePlacesSuggestions(apartmentName) {
        try {
            console.log(`🔍 Attempting Google Places suggestions for "${apartmentName}"`);
            
            if (!window.google || !window.google.maps) {
                console.warn('Google Maps not available');
                return [];
            }

            // Try the new Places API first
            try {
                const { Place } = await google.maps.importLibrary("places");
                
                const request = {
                    textQuery: `${apartmentName} Atlanta GA apartment housing`,
                    fields: ['id', 'displayName', 'formattedAddress', 'location', 'nationalPhoneNumber', 'websiteURI', 'types'],
                    locationBias: {
                        lat: 33.7756, 
                        lng: -84.3963 // Georgia Tech coordinates
                    },
                    maxResultCount: 5
                };

                const { places } = await Place.searchByText(request);
                
                if (places && places.length > 0) {
                    const suggestions = places
                        .filter(place => this.isHousingRelated(place))
                        .map(place => this.formatGooglePlaceSuggestion(place))
                        .slice(0, 3);

                    console.log(`✅ Found ${suggestions.length} Google Places (New) suggestions`);
                    return suggestions;
                }
            } catch (newApiError) {
                console.warn('New Google Places API failed, trying fallback:', newApiError.message);
                
                // Fallback to old PlacesService API
                return await this.getGooglePlacesSuggestionsLegacy(apartmentName);
            }

            return [];

        } catch (error) {
            console.error('Error getting Google Places suggestions:', error);
            return [];
        }
    }

    // Fallback to legacy Google Places API
    async getGooglePlacesSuggestionsLegacy(apartmentName) {
        try {
            console.log(`🔄 Trying legacy Google Places API for "${apartmentName}"`);
            
            return new Promise((resolve) => {
                const service = new google.maps.places.PlacesService(
                    document.createElement('div')
                );

                const request = {
                    query: `${apartmentName} Atlanta GA apartment housing`,
                    fields: [
                        'place_id', 'name', 'formatted_address', 'geometry',
                        'formatted_phone_number', 'website', 'types'
                    ]
                };

                service.findPlaceFromQuery(request, (results, status) => {
                    if (status === google.maps.places.PlacesServiceStatus.OK && results && results.length > 0) {
                        const suggestions = results
                            .filter(place => this.isHousingRelatedLegacy(place))
                            .map(place => this.formatLegacyGooglePlaceSuggestion(place))
                            .slice(0, 3);

                        console.log(`✅ Found ${suggestions.length} Google Places (Legacy) suggestions`);
                        resolve(suggestions);
                    } else {
                        console.log(`Google Places (Legacy) API error: ${status}`);
                        resolve([]);
                    }
                });
            });
        } catch (error) {
            console.error('Legacy Google Places API also failed:', error);
            return [];
        }
    }

    // Check if a legacy Google Place is housing-related
    isHousingRelatedLegacy(place) {
        const housingTypes = [
            'lodging', 'real_estate_agency', 'premise', 'establishment',
            'point_of_interest'
        ];
        const hasHousingType = place.types?.some(type => housingTypes.includes(type));
        
        const housingKeywords = ['apartment', 'housing', 'residence', 'complex', 'loft', 'tower', 'village', 'place'];
        const nameContainsHousing = housingKeywords.some(keyword => 
            place.name?.toLowerCase().includes(keyword)
        );
        
        return hasHousingType || nameContainsHousing;
    }

    // Format legacy Google Place as a suggestion object
    formatLegacyGooglePlaceSuggestion(place) {
        const addressComponents = this.parseGoogleAddress(place.formatted_address);
        
        return {
            source: 'google_places_legacy',
            place_id: place.place_id,
            name: place.name,
            formatted_address: place.formatted_address,
            street_address: addressComponents.street,
            city: addressComponents.city,
            state: addressComponents.state,
            zip_code: addressComponents.zip,
            phone: place.formatted_phone_number,
            url: place.website,
            latitude: place.geometry?.location?.lat(),
            longitude: place.geometry?.location?.lng(),
            user_generated: true,
            google_place_id: place.place_id,
            google_verified: true
        };
    }

    // Check if a Google Place is housing-related
    isHousingRelated(place) {
        const housingTypes = [
            'lodging', 'real_estate_agency', 'premise', 'establishment',
            'point_of_interest'
        ];
        const hasHousingType = place.types?.some(type => housingTypes.includes(type));
        
        const housingKeywords = ['apartment', 'housing', 'residence', 'complex', 'loft', 'tower', 'village', 'place'];
        const nameContainsHousing = housingKeywords.some(keyword => 
            place.displayName?.toLowerCase().includes(keyword)
        );
        
        return hasHousingType || nameContainsHousing;
    }

    // Format Google Place as a suggestion object
    formatGooglePlaceSuggestion(place) {
        const addressComponents = this.parseNewGoogleAddress(place.formattedAddress);
        
        return {
            source: 'google_places',
            place_id: place.id,
            name: place.displayName,
            formatted_address: place.formattedAddress,
            street_address: addressComponents.street,
            city: addressComponents.city,
            state: addressComponents.state,
            zip_code: addressComponents.zip,
            phone: place.nationalPhoneNumber,
            url: place.websiteURI,
            latitude: place.location?.lat(),
            longitude: place.location?.lng(),
            user_generated: true,
            google_place_id: place.id,
            google_verified: true
        };
    }

        // Create apartment from user confirmation
    async createApartmentFromSuggestion(suggestion) {
        try {
            console.log('Creating apartment from user-confirmed suggestion:', suggestion.name);
            
            // First, check if apartment already exists to avoid duplicate key error
            const { data: existingApartment, error: checkError } = await window.supabaseClient
                .from('apartments')
                .select('*')
                .eq('name', suggestion.name)
                .single();

            if (existingApartment) {
                console.log('✅ Apartment already exists, using existing apartment:', existingApartment.name);
                // Add to local data if not already there
                if (!this.apartmentData.find(apt => apt.name === existingApartment.name)) {
                    this.apartmentData.push(existingApartment);
                }
                return existingApartment;
            }
            
            if (checkError && !checkError.message.includes('No rows')) {
                console.warn('Error checking for existing apartment:', checkError);
            }
            
            // Clean the suggestion object to only include valid database columns
            const cleanedSuggestion = {
                name: suggestion.name,
                street_address: suggestion.street_address,
                city: suggestion.city,
                state: suggestion.state,
                zip_code: suggestion.zip_code,
                formatted_address: suggestion.formatted_address,
                phone: suggestion.phone,
                url: suggestion.url,
                price_range: suggestion.price_range || null,
                bed_range: suggestion.bed_range || null,
                image_url: suggestion.image_url || null,
                user_generated: suggestion.user_generated || true,
                google_place_id: suggestion.google_place_id || null,
                google_verified: suggestion.google_verified || false
            };

            console.log('Cleaned suggestion for database:', cleanedSuggestion);
            
            const { data, error } = await window.supabaseClient
                .from('apartments')
                .insert(cleanedSuggestion)
                .select()
                .single();

            if (error) {
                console.error('Error creating apartment from suggestion:', error);
                
                // If specific columns are missing, try with minimal data
                if (error.message.includes('Could not find')) {
                    console.log('Retrying with minimal apartment data...');
                    const minimalApartment = {
                        name: suggestion.name,
                        street_address: suggestion.street_address,
                        city: suggestion.city || 'Atlanta',
                        state: suggestion.state || 'GA',
                        zip_code: suggestion.zip_code,
                        formatted_address: suggestion.formatted_address,
                        phone: suggestion.phone,
                        url: suggestion.url
                    };
                    
                    const { data: retryData, error: retryError } = await window.supabaseClient
                        .from('apartments')
                        .insert(minimalApartment)
                        .select()
                        .single();
                    
                    if (retryError) {
                        console.error('Retry also failed:', retryError);
                        throw new Error(`Failed to create apartment: ${retryError.message}`);
                    }
                    
                    console.log('✅ Created apartment with minimal data:', retryData.name);
                    this.apartmentData.push(retryData);
                    return retryData;
                }
                
                throw new Error(`Failed to create apartment: ${error.message}`);
            }

            console.log('✅ Created apartment from suggestion:', data.name);
            
            // Add to local data for future matches
            this.apartmentData.push(data);
            
            return data;
        } catch (error) {
            console.error('Error inserting apartment:', error);
            throw error; // Re-throw so the UI can handle it properly
        }
    }

    // Create new apartment entry with Google Maps validation
    async createNewApartment(name) {
        console.log(`🔍 Validating "${name}" with Google Maps...`);
        
        // Step 1: Validate with Google Maps
        const googleValidation = await this.validateWithGoogleMaps(name);
        
        let newApartment;
        if (googleValidation.success) {
            // Use Google Maps data if validation successful
            newApartment = {
                name: name,
                street_address: googleValidation.data.street_address,
                city: googleValidation.data.city || 'Atlanta',
                state: googleValidation.data.state || 'GA',
                zip_code: googleValidation.data.zip_code,
                formatted_address: googleValidation.data.formatted_address,
                phone: googleValidation.data.phone,
                url: googleValidation.data.website,
                price_range: null,
                bed_range: null,
                image_url: null,
                user_generated: true,
                google_place_id: googleValidation.data.place_id,
                google_verified: true
            };
            console.log('✅ Google Maps validation successful');
        } else {
            // Create basic entry if Google validation fails
            newApartment = {
                name: name,
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
            console.log('⚠️ Google Maps validation failed, creating basic entry');
        }

        // Step 2: Add to Supabase
        try {
            const { data, error } = await window.supabaseClient
                .from('apartments')
                .insert(newApartment)
                .select()
                .single();

            if (error) {
                console.error('Error creating new apartment:', error);
                return newApartment;
            }

            console.log('✅ Created new apartment:', data.name);
            
            // Add to local data for future matches
            this.apartmentData.push(newApartment);
            
            return data;
        } catch (error) {
            console.error('Error inserting new apartment:', error);
            return newApartment;
        }
    }

    // Validate apartment with Google Maps Places (New) API
    async validateWithGoogleMaps(apartmentName) {
        try {
            // Check if Google Maps is available
            if (!window.google || !window.google.maps) {
                console.warn('Google Maps not available, skipping validation');
                return { success: false, error: 'Google Maps not loaded' };
            }

            // Import the new Places library
            const { Place, SearchNearbyRankPreference } = await google.maps.importLibrary("places");
            
            // Create a text search request
            const request = {
                textQuery: `${apartmentName} Atlanta GA apartment housing`,
                fields: ['id', 'displayName', 'formattedAddress', 'location', 'nationalPhoneNumber', 'websiteURI', 'types'],
                locationBias: {
                    lat: 33.7756, 
                    lng: -84.3963 // Georgia Tech coordinates
                },
                maxResultCount: 5
            };

            // Use the new searchByText method
            const { places } = await Place.searchByText(request);
            
            if (places && places.length > 0) {
                const place = places[0];
                
                // Check if it's a reasonable result (contains housing-related types or keywords)
                const housingTypes = [
                    'lodging', 'real_estate_agency', 'premise', 'establishment',
                    'point_of_interest'
                ];
                const hasHousingType = place.types?.some(type => housingTypes.includes(type));
                const nameContainsHousing = place.displayName?.toLowerCase().includes('apartment') ||
                                          place.displayName?.toLowerCase().includes('housing') ||
                                          place.displayName?.toLowerCase().includes('residence') ||
                                          place.displayName?.toLowerCase().includes('complex') ||
                                          place.displayName?.toLowerCase().includes('loft');
                
                if (hasHousingType || nameContainsHousing) {
                    // Parse address components
                    const addressComponents = this.parseNewGoogleAddress(place.formattedAddress);
                    
                    return {
                        success: true,
                        data: {
                            place_id: place.id,
                            name: place.displayName || apartmentName,
                            formatted_address: place.formattedAddress,
                            street_address: addressComponents.street,
                            city: addressComponents.city,
                            state: addressComponents.state,
                            zip_code: addressComponents.zip,
                            phone: place.nationalPhoneNumber,
                            website: place.websiteURI,
                            latitude: place.location?.lat(),
                            longitude: place.location?.lng()
                        }
                    };
                } else {
                    return { success: false, error: 'Not a housing-related result' };
                }
            } else {
                return { success: false, error: 'No places found' };
            }
        } catch (error) {
            console.error('Google Maps validation error:', error);
            return { success: false, error: error.message };
        }
    }

    // Parse address components from formatted address string
    parseNewGoogleAddress(formattedAddress) {
        if (!formattedAddress) {
            return { street: null, city: null, state: null, zip: null };
        }
        
        return this.parseGoogleAddress(formattedAddress);
    }

    // Parse Google formatted address into components
    parseGoogleAddress(formattedAddress) {
        const parts = formattedAddress.split(', ');
        return {
            street: parts[0] || null,
            city: parts[1] || null,
            state: parts[2]?.split(' ')[0] || null,
            zip: parts[2]?.split(' ')[1] || null
        };
    }

    // Calculate string similarity using Jaro-Winkler algorithm (better for names)
    calculateSimilarity(str1, str2) {
        // Handle identical strings
        if (str1 === str2) return 1.0;
        
        // Handle empty strings
        if (str1.length === 0 || str2.length === 0) return 0.0;

        // Use Levenshtein distance for now (simpler implementation)
        const distance = this.levenshteinDistance(str1, str2);
        const maxLength = Math.max(str1.length, str2.length);
        
        return (maxLength - distance) / maxLength;
    }

    // Levenshtein distance calculation
    levenshteinDistance(str1, str2) {
        const matrix = [];
        
        // Initialize matrix
        for (let i = 0; i <= str2.length; i++) {
            matrix[i] = [i];
        }
        for (let j = 0; j <= str1.length; j++) {
            matrix[0][j] = j;
        }

        // Fill matrix
        for (let i = 1; i <= str2.length; i++) {
            for (let j = 1; j <= str1.length; j++) {
                if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
                    matrix[i][j] = matrix[i - 1][j - 1];
                } else {
                    matrix[i][j] = Math.min(
                        matrix[i - 1][j - 1] + 1, // substitution
                        matrix[i][j - 1] + 1,     // insertion
                        matrix[i - 1][j] + 1      // deletion
                    );
                }
            }
        }

        return matrix[str2.length][str1.length];
    }

    // Get suggestions for partial matches
    getSuggestions(input, limit = 5) {
        const similarities = this.apartmentData.map(apt => ({
            apartment: apt,
            similarity: this.calculateSimilarity(input.toLowerCase(), apt.name.toLowerCase())
        }));

        return similarities
            .sort((a, b) => b.similarity - a.similarity)
            .slice(0, limit)
            .map(item => item.apartment);
    }

    // Get local suggestions based on partial matching
    getLocalSuggestions(input) {
        if (!input || input.length < 2) return [];
        
        const inputLower = input.toLowerCase();
        const suggestions = [];
        
        // Find apartments that contain the input as a substring
        this.apartmentData.forEach(apt => {
            const nameLower = apt.name.toLowerCase();
            if (nameLower.includes(inputLower) && nameLower !== inputLower) {
                const similarity = this.calculateSimilarity(inputLower, nameLower);
                if (similarity > 0.3) { // Lower threshold for partial matches
                    suggestions.push({
                        ...apt,
                        similarity: similarity,
                        source: 'local_partial'
                    });
                }
            }
        });
        
        // Sort by similarity and take top 3
        return suggestions
            .sort((a, b) => b.similarity - a.similarity)
            .slice(0, 3);
    }
}

// Export for use
window.SmartApartmentMatcher = SmartApartmentMatcher;
