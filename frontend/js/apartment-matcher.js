// Google Places API Integration for Apartment Matching
class ApartmentMatcher {
    constructor(apiKey) {
        this.apiKey = apiKey;
        this.service = null;
        this.map = null;
        this.gtLocation = { lat: 33.7756, lng: -84.3963 }; // Georgia Tech coordinates
        this.searchRadius = 10000; // 10km radius
    }

    // Initialize Google Maps and Places service
    async init() {
        return new Promise((resolve, reject) => {
            if (window.google) {
                this.initializeServices();
                resolve();
            } else {
                // Load Google Maps API
                const script = document.createElement('script');
                script.src = `https://maps.googleapis.com/maps/api/js?key=${this.apiKey}&libraries=places&callback=initMap`;
                script.async = true;
                script.defer = true;
                
                window.initMap = () => {
                    this.initializeServices();
                    resolve();
                };
                
                script.onerror = () => reject(new Error('Failed to load Google Maps API'));
                document.head.appendChild(script);
            }
        });
    }

    initializeServices() {
        // Create a hidden map element for the service
        const mapDiv = document.createElement('div');
        mapDiv.style.display = 'none';
        document.body.appendChild(mapDiv);
        
        this.map = new google.maps.Map(mapDiv, {
            center: this.gtLocation,
            zoom: 13
        });
        
        this.service = new google.maps.places.PlacesService(this.map);
    }

    // Search for apartments and student housing near Georgia Tech
    async searchNearbyApartments() {
        return new Promise((resolve, reject) => {
            const request = {
                location: this.gtLocation,
                radius: this.searchRadius,
                keyword: 'student housing apartments',
                type: 'lodging'
            };

            this.service.nearbySearch(request, (results, status) => {
                if (status === google.maps.places.PlacesServiceStatus.OK) {
                    // Filter and process results
                    const apartments = this.processApartmentResults(results);
                    resolve(apartments);
                } else {
                    reject(new Error(`Places search failed: ${status}`));
                }
            });
        });
    }

    // Process and clean apartment results
    processApartmentResults(results) {
        return results.map(place => ({
            place_id: place.place_id,
            name: place.name,
            address: place.vicinity || place.formatted_address,
            location: {
                lat: place.geometry.location.lat(),
                lng: place.geometry.location.lng()
            },
            rating: place.rating || 0,
            price_level: place.price_level || 0,
            types: place.types,
            photos: place.photos ? place.photos.map(photo => ({
                url: photo.getUrl({ maxWidth: 400, maxHeight: 400 })
            })) : [],
            // Calculate distance from Georgia Tech
            distance_from_gt: this.calculateDistance(
                this.gtLocation,
                {
                    lat: place.geometry.location.lat(),
                    lng: place.geometry.location.lng()
                }
            )
        }));
    }

    // Search for a specific apartment by name
    async searchSpecificApartment(apartmentName) {
        return new Promise((resolve, reject) => {
            const request = {
                query: `${apartmentName} student housing apartment near Georgia Tech Atlanta`,
                location: this.gtLocation,
                radius: this.searchRadius
            };

            this.service.textSearch(request, (results, status) => {
                if (status === google.maps.places.PlacesServiceStatus.OK && results.length > 0) {
                    const apartment = this.processApartmentResults(results)[0];
                    resolve(apartment);
                } else {
                    resolve(null); // No match found
                }
            });
        });
    }

    // Get detailed information about a place
    async getPlaceDetails(placeId) {
        return new Promise((resolve, reject) => {
            const request = {
                placeId: placeId,
                fields: [
                    'name', 'formatted_address', 'geometry', 'rating',
                    'price_level', 'photos', 'website', 'formatted_phone_number',
                    'opening_hours', 'reviews'
                ]
            };

            this.service.getDetails(request, (place, status) => {
                if (status === google.maps.places.PlacesServiceStatus.OK) {
                    resolve({
                        place_id: place.place_id,
                        name: place.name,
                        address: place.formatted_address,
                        location: {
                            lat: place.geometry.location.lat(),
                            lng: place.geometry.location.lng()
                        },
                        rating: place.rating || 0,
                        price_level: place.price_level || 0,
                        website: place.website,
                        phone: place.formatted_phone_number,
                        hours: place.opening_hours,
                        reviews: place.reviews || [],
                        photos: place.photos ? place.photos.map(photo => ({
                            url: photo.getUrl({ maxWidth: 800, maxHeight: 600 })
                        })) : [],
                        distance_from_gt: this.calculateDistance(
                            this.gtLocation,
                            {
                                lat: place.geometry.location.lat(),
                                lng: place.geometry.location.lng()
                            }
                        )
                    });
                } else {
                    reject(new Error(`Place details failed: ${status}`));
                }
            });
        });
    }

    // Calculate distance between two coordinates (in meters)
    calculateDistance(pos1, pos2) {
        const R = 6371e3; // Earth's radius in meters
        const φ1 = pos1.lat * Math.PI/180;
        const φ2 = pos2.lat * Math.PI/180;
        const Δφ = (pos2.lat-pos1.lat) * Math.PI/180;
        const Δλ = (pos2.lng-pos1.lng) * Math.PI/180;

        const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
                Math.cos(φ1) * Math.cos(φ2) *
                Math.sin(Δλ/2) * Math.sin(Δλ/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

        return Math.round(R * c); // Distance in meters
    }

    // Match user input to existing apartments
    async matchUserApartment(userInput) {
        try {
            // First try exact search
            let match = await this.searchSpecificApartment(userInput);
            
            if (match) {
                return {
                    success: true,
                    apartment: match,
                    confidence: 'high'
                };
            }

            // If no exact match, search nearby apartments and find best match
            const nearbyApartments = await this.searchNearbyApartments();
            const fuzzyMatch = this.findFuzzyMatch(userInput, nearbyApartments);
            
            if (fuzzyMatch) {
                return {
                    success: true,
                    apartment: fuzzyMatch.apartment,
                    confidence: fuzzyMatch.confidence
                };
            }

            return {
                success: false,
                message: 'No matching apartment found',
                suggestions: nearbyApartments.slice(0, 5) // Top 5 suggestions
            };

        } catch (error) {
            console.error('Apartment matching error:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    // Find fuzzy matches using string similarity
    findFuzzyMatch(userInput, apartments) {
        const similarities = apartments.map(apt => ({
            apartment: apt,
            similarity: this.calculateStringSimilarity(
                userInput.toLowerCase(),
                apt.name.toLowerCase()
            )
        }));

        // Sort by similarity
        similarities.sort((a, b) => b.similarity - a.similarity);

        const bestMatch = similarities[0];
        
        if (bestMatch.similarity > 0.6) {
            return {
                apartment: bestMatch.apartment,
                confidence: bestMatch.similarity > 0.8 ? 'high' : 'medium'
            };
        }

        return null;
    }

    // Calculate string similarity using Levenshtein distance
    calculateStringSimilarity(str1, str2) {
        const longer = str1.length > str2.length ? str1 : str2;
        const shorter = str1.length > str2.length ? str2 : str1;
        
        if (longer.length === 0) return 1.0;
        
        const distance = this.levenshteinDistance(longer, shorter);
        return (longer.length - distance) / longer.length;
    }

    levenshteinDistance(str1, str2) {
        const matrix = [];
        
        for (let i = 0; i <= str2.length; i++) {
            matrix[i] = [i];
        }
        
        for (let j = 0; j <= str1.length; j++) {
            matrix[0][j] = j;
        }
        
        for (let i = 1; i <= str2.length; i++) {
            for (let j = 1; j <= str1.length; j++) {
                if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
                    matrix[i][j] = matrix[i - 1][j - 1];
                } else {
                    matrix[i][j] = Math.min(
                        matrix[i - 1][j - 1] + 1,
                        matrix[i][j - 1] + 1,
                        matrix[i - 1][j] + 1
                    );
                }
            }
        }
        
        return matrix[str2.length][str1.length];
    }
}

// Export for use in other modules
window.ApartmentMatcher = ApartmentMatcher;
