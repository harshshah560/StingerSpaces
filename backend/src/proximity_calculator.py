"""
Proximity Calculator for Apartment Locations
Calculates distances from apartments to key campus locations like CULC, CRC, Tech Square
"""

import json
import math
import requests
import time
from typing import Dict, List, Tuple, Optional
import logging

class ProximityCalculator:
    def __init__(self):
        """Initialize the proximity calculator with Georgia Tech key locations"""
        
        # Key Georgia Tech locations with their coordinates
        self.key_locations = {
            "CULC": {
                "name": "CULC",
                "address": "266 4th St NW, Atlanta, GA 30313",
                "coordinates": (33.7747, -84.3965),  # (latitude, longitude)
                "category": "Campus"
            },
            "CRC": {
                "name": "Recreation Center",
                "address": "750 Ferst Dr NW, Atlanta, GA 30318",
                "coordinates": (33.7758, -84.4041),
                "category": "Campus"
            },
            "Tech Square": {
                "name": "Technology Square",
                "address": "84 5th St NW, Atlanta, GA 30308", 
                "coordinates": (33.7777, -84.3888),
                "category": "Campus"
            },
            "Student Center": {
                "name": "Student Center",
                "address": "350 Ferst Dr NW, Atlanta, GA 30313",
                "coordinates": (33.7738, -84.3986),
                "category": "Campus"
            }
        }
        
        # MARTA stations for finding the closest one
        self.marta_stations = {
            "North Avenue": {
                "name": "North Avenue MARTA",
                "address": "713 West Peachtree St NW, Atlanta, GA 30308",
                "coordinates": (33.7717, -84.3872),
                "category": "Transportation"
            },
            "Midtown": {
                "name": "Midtown MARTA",
                "address": "41 10th St NE, Atlanta, GA 30309",
                "coordinates": (33.7809, -84.3863),
                "category": "Transportation"
            },
            "Arts Center": {
                "name": "Arts Center MARTA",
                "address": "1255 West Peachtree St NE, Atlanta, GA 30309",
                "coordinates": (33.7890, -84.3871),
                "category": "Transportation"
            },
            "Vine City": {
                "name": "Vine City MARTA",
                "address": "1085 Joseph E Lowery Blvd NW, Atlanta, GA 30314",
                "coordinates": (33.7560, -84.4148),
                "category": "Transportation"
            },
            "Ashby": {
                "name": "Ashby MARTA",
                "address": "65 Joseph E Lowery Blvd NW, Atlanta, GA 30314",
                "coordinates": (33.7567, -84.4277),
                "category": "Transportation"
            }
        }
        
        logging.basicConfig(level=logging.INFO)

    def haversine_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """
        Calculate the great circle distance between two points on Earth
        Returns distance in miles
        """
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of Earth in miles
        r = 3956
        
        return c * r

    def standardize_atlanta_address(self, address: str) -> str:
        """
        Standardize Atlanta addresses for better geocoding success
        """
        # Common Atlanta address fixes
        standardized = address
        
        # Add NE/NW/SE/SW for common Atlanta patterns
        patterns = [
            (r'\b(10th St)\b(?! [NS][EW])', r'\1 NE'),
            (r'\b(14th St)\b(?! [NS][EW])', r'\1 NW'),
            (r'\b(Peachtree St)\b(?! [NS][EW])', r'\1 NE'),
            (r'\b(Spring St)\b(?! [NS][EW])', r'\1 NW'),
            (r'\b(Courtland St)\b(?! [NS][EW])', r'\1 NE'),
            (r'\b(John Wesley Dobbs Ave)\b(?! [NS][EW])', r'\1 NE'),
            (r'\b(Piedmont Ave)\b(?! [NS][EW])', r'\1 NE'),
            (r'\b(West Peachtree St)\b(?! [NS][EW])', r'\1 NW'),
        ]
        
        import re
        for pattern, replacement in patterns:
            standardized = re.sub(pattern, replacement, standardized, flags=re.IGNORECASE)
        
        return standardized

    def get_address_variations(self, address: str) -> List[str]:
        """
        Generate address variations for better geocoding success
        """
        variations = []
        
        # Original address
        variations.append(address)
        
        # Standardized address
        standardized = self.standardize_atlanta_address(address)
        if standardized != address:
            variations.append(standardized)
        
        # Add directional variations for Atlanta
        if 'Atlanta' in address and not any(direction in address.upper() for direction in ['NE', 'NW', 'SE', 'SW']):
            base_addr = address.replace(', Atlanta, GA', '').replace(' Atlanta, GA', '')
            for direction in ['NE', 'NW', 'SE', 'SW']:
                variations.append(f"{base_addr} {direction}, Atlanta, GA")
        
        # Avenue/Street variations
        if ' Ave ' in address or address.endswith(' Ave'):
            variations.append(address.replace(' Ave ', ' Avenue ').replace(' Ave', ' Avenue'))
        if ' St ' in address or address.endswith(' St'):
            variations.append(address.replace(' St ', ' Street ').replace(' St', ' Street'))
        
        # Without zip code
        import re
        no_zip = re.sub(r',?\s*\d{5}(-\d{4})?$', '', address)
        if no_zip != address:
            variations.append(no_zip)
        
        # Remove duplicates while preserving order
        unique_variations = []
        for var in variations:
            if var not in unique_variations:
                unique_variations.append(var)
        
        return unique_variations

    def try_single_geocode(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Try geocoding a single address variation
        """
        try:
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                'q': address,
                'format': 'json',
                'limit': 1,
                'countrycodes': 'us'
            }
            
            headers = {
                'User-Agent': 'StingerSpaces/1.0 (contact@stingerspaces.com)'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                logging.info(f"Successfully geocoded '{address}' -> ({lat}, {lon})")
                return (lat, lon)
            
            return None
                
        except Exception as e:
            logging.warning(f"Geocoding failed for '{address}': {e}")
            return None

    def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Convert address to coordinates using Nominatim geocoding service with fallback variations
        Returns (latitude, longitude) or None if all geocoding attempts fail
        """
        logging.info(f"Attempting to geocode: {address}")
        
        # Get all address variations
        variations = self.get_address_variations(address)
        
        for i, variation in enumerate(variations):
            if i > 0:
                logging.info(f"Trying variation {i+1}/{len(variations)}: {variation}")
            
            coords = self.try_single_geocode(variation)
            if coords:
                if variation != address:
                    logging.info(f"Success with variation: '{variation}' instead of '{address}'")
                return coords
            
            # Rate limiting between attempts
            if i < len(variations) - 1:
                time.sleep(1)
        
        logging.error(f"All geocoding attempts failed for: {address}")
        return None

    def calculate_apartment_proximities(self, apartment_data: List[Dict]) -> List[Dict]:
        """
        Calculate proximities for all apartments to key locations
        """
        updated_apartments = []
        failed_apartments = []
        
        for i, apartment in enumerate(apartment_data):
            apartment_name = apartment.get('name', f'Apartment #{i+1}')
            logging.info(f"Processing apartment {i+1}/{len(apartment_data)}: {apartment_name}")
            
            # Get apartment coordinates
            apt_address = apartment.get('formatted_address', '')
            if not apt_address:
                logging.error(f"No formatted_address for apartment: {apartment_name}")
                apartment['proximities'] = {}
                failed_apartments.append(apartment_name)
                updated_apartments.append(apartment)
                continue
            
            apt_coords = self.geocode_address(apt_address)
            
            if not apt_coords:
                logging.error(f"Could not geocode apartment: {apartment_name} (address: {apt_address})")
                # Add empty proximity data but don't give up completely
                apartment['proximities'] = {}
                failed_apartments.append(apartment_name)
                updated_apartments.append(apartment)
                continue
            
            # Calculate distances to all key locations
            proximities = {}
            
            for location_key, location_info in self.key_locations.items():
                distance_miles = self.haversine_distance(apt_coords, location_info['coordinates'])
                
                # Calculate walking time (assume 3 mph walking speed)
                walking_time_minutes = (distance_miles / 3.0) * 60
                
                proximities[location_key] = {
                    'name': location_info['name'],
                    'category': location_info['category'],
                    'distance_miles': round(distance_miles, 2),
                    'walking_time_minutes': round(walking_time_minutes, 1),
                    'walking_time_text': self._format_walking_time(walking_time_minutes)
                }
            
            # Find closest MARTA station
            closest_marta = None
            closest_marta_distance = float('inf')
            
            for station_key, station_info in self.marta_stations.items():
                distance_miles = self.haversine_distance(apt_coords, station_info['coordinates'])
                if distance_miles < closest_marta_distance:
                    closest_marta_distance = distance_miles
                    closest_marta = station_info
            
            # Add closest MARTA station to proximities
            if closest_marta:
                walking_time_minutes = (closest_marta_distance / 3.0) * 60
                proximities['MARTA'] = {
                    'name': closest_marta['name'],
                    'category': closest_marta['category'],
                    'distance_miles': round(closest_marta_distance, 2),
                    'walking_time_minutes': round(walking_time_minutes, 1),
                    'walking_time_text': self._format_walking_time(walking_time_minutes)
                }
            
            # Add coordinates to apartment data for future use
            apartment['coordinates'] = apt_coords
            apartment['proximities'] = proximities
            
            updated_apartments.append(apartment)
            
            # Rate limiting to be nice to the geocoding service
            time.sleep(1)
        
        # Report failed apartments
        if failed_apartments:
            logging.warning(f"Failed to process {len(failed_apartments)} apartments: {', '.join(failed_apartments)}")
            print(f"\n⚠️  Warning: {len(failed_apartments)} apartments could not be fully processed:")
            for name in failed_apartments:
                print(f"   • {name}")
            print("   These apartments will have empty proximity data.")
        
        return updated_apartments

    def _format_walking_time(self, minutes: float) -> str:
        """Format walking time in a human-readable way"""
        if minutes < 1:
            return "< 1 min walk"
        elif minutes < 60:
            return f"{int(minutes)} min walk"
        else:
            hours = int(minutes // 60)
            remaining_minutes = int(minutes % 60)
            if remaining_minutes == 0:
                return f"{hours} hour walk"
            else:
                return f"{hours}h {remaining_minutes}m walk"

    def get_proximity_summary(self, apartment_data: List[Dict]) -> Dict:
        """Generate a summary of proximity data"""
        summary = {
            'total_apartments': len(apartment_data),
            'apartments_with_proximities': 0,
            'average_distances': {},
            'closest_to_each_location': {}
        }
        
        # Get all possible location keys from actual data
        all_location_keys = set()
        for apartment in apartment_data:
            if 'proximities' in apartment and apartment['proximities']:
                all_location_keys.update(apartment['proximities'].keys())
        
        # Calculate averages and find closest apartments
        location_distances = {loc: [] for loc in all_location_keys}
        
        for apartment in apartment_data:
            if 'proximities' in apartment and apartment['proximities']:
                summary['apartments_with_proximities'] += 1
                
                for location_key, proximity_info in apartment['proximities'].items():
                    distance = proximity_info['distance_miles']
                    location_distances[location_key].append({
                        'apartment': apartment['name'],
                        'distance': distance
                    })
        
        # Calculate averages and find closest
        for location_key, distances in location_distances.items():
            if distances:
                avg_distance = sum(d['distance'] for d in distances) / len(distances)
                summary['average_distances'][location_key] = round(avg_distance, 2)
                
                closest = min(distances, key=lambda x: x['distance'])
                summary['closest_to_each_location'][location_key] = closest
        
        return summary

    def update_apartment_data_file(self, input_file: str, output_file: str = None):
        """
        Update apartment data file with proximity information
        """
        if output_file is None:
            output_file = input_file
        
        try:
            # Load existing apartment data
            with open(input_file, 'r') as f:
                apartment_data = json.load(f)
            
            logging.info(f"Loaded {len(apartment_data)} apartments from {input_file}")
            
            # Calculate proximities
            updated_data = self.calculate_apartment_proximities(apartment_data)
            
            # Save updated data
            with open(output_file, 'w') as f:
                json.dump(updated_data, f, indent=2)
            
            logging.info(f"Updated apartment data saved to {output_file}")
            
            # Generate and display summary
            summary = self.get_proximity_summary(updated_data)
            self._print_summary(summary)
            
            return updated_data
            
        except Exception as e:
            logging.error(f"Error updating apartment data: {e}")
            return None

    def _print_summary(self, summary: Dict):
        """Print a formatted summary of proximity calculations"""
        print("\n" + "="*60)
        print("🏠 APARTMENT PROXIMITY SUMMARY")
        print("="*60)
        print(f"📊 Total apartments: {summary['total_apartments']}")
        print(f"✅ With proximity data: {summary['apartments_with_proximities']}")
        print()
        
        print("📏 Average distances to key locations:")
        for location, avg_dist in summary['average_distances'].items():
            # For key_locations, get the name, otherwise use the location key as-is
            if location in self.key_locations:
                location_name = self.key_locations[location]['name']
            else:
                location_name = location
            print(f"   {location_name}: {avg_dist} miles")
        print()
        
        print("🎯 Closest apartments to each location:")
        for location, closest_info in summary['closest_to_each_location'].items():
            # For key_locations, get the name, otherwise use the location key as-is
            if location in self.key_locations:
                location_name = self.key_locations[location]['name']
            else:
                location_name = location
            print(f"   {location_name}:")
            print(f"      {closest_info['apartment']} ({closest_info['distance']} miles)")
        print("="*60)


def main():
    """Test the proximity calculation system"""
    calculator = ProximityCalculator()
    
    # Update the apartment data file with proximity information
    input_file = "/Users/harshshah/Documents/hackgt/backend/data/apartment_data.json"
    
    print("🚀 Starting proximity calculation for Georgia Tech apartments...")
    updated_data = calculator.update_apartment_data_file(input_file)
    
    if updated_data:
        print("\n✅ Proximity calculation completed successfully!")
        
        # Show a sample apartment's proximity data
        sample_apt = updated_data[0]
        if 'proximities' in sample_apt:
            print(f"\n📍 Sample proximity data for {sample_apt['name']}:")
            for location, info in sample_apt['proximities'].items():
                print(f"   {info['name']}: {info['distance_miles']} miles ({info['walking_time_text']})")
    else:
        print("❌ Proximity calculation failed")


if __name__ == "__main__":
    main()
