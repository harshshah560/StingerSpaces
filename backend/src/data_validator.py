"""
Data Validation Script for StingerSpaces
Validates apartment data integrity and reports issues
"""

import json
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import sys
import os

@dataclass
class ValidationResult:
    """Structure to hold validation results"""
    apartment_name: str
    issues: List[str]
    warnings: List[str]
    is_valid: bool

class ApartmentDataValidator:
    """Validates apartment data for completeness and accuracy"""
    
    def __init__(self):
        self.required_fields = [
            'name', 'street_address', 'city', 'state', 'zip_code',
            'formatted_address', 'phone', 'url', 'price_range', 'bed_range'
        ]
        
        self.required_proximity_locations = [
            'CULC', 'CRC', 'Tech Square', 'Student Center', 'MARTA'
        ]
        
        self.required_proximity_fields = [
            'name', 'category', 'distance_miles', 'walking_time_minutes', 'walking_time_text'
        ]

    def validate_basic_fields(self, apartment: Dict) -> Tuple[List[str], List[str]]:
        """Validate basic apartment fields"""
        issues = []
        warnings = []
        
        # Check required fields
        for field in self.required_fields:
            if field not in apartment:
                issues.append(f"Missing required field: {field}")
            elif not apartment[field] or str(apartment[field]).strip() == "":
                issues.append(f"Empty required field: {field}")
        
        # Validate phone format
        if 'phone' in apartment:
            phone = apartment['phone']
            if not phone.startswith('+1-') and not phone.startswith('('):
                warnings.append(f"Phone format may be non-standard: {phone}")
        
        # Validate price range format
        if 'price_range' in apartment:
            price = apartment['price_range']
            if not ('$' in price and ('-' in price or 'to' in price.lower())):
                warnings.append(f"Price range format may be non-standard: {price}")
                
        return issues, warnings

    def validate_coordinates(self, apartment: Dict) -> Tuple[List[str], List[str]]:
        """Validate apartment coordinates"""
        issues = []
        warnings = []
        
        if 'coordinates' not in apartment:
            issues.append("Missing coordinates")
            return issues, warnings
        
        coords = apartment['coordinates']
        
        if not isinstance(coords, list) or len(coords) != 2:
            issues.append("Coordinates should be a list of [latitude, longitude]")
            return issues, warnings
        
        lat, lon = coords
        
        # Validate coordinate ranges for Atlanta area
        if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            issues.append("Coordinates must be numeric")
        else:
            # Atlanta is roughly between 33.6-33.9 latitude, -84.6 to -84.2 longitude
            if not (33.4 <= lat <= 34.0):
                warnings.append(f"Latitude {lat} seems outside Atlanta area (expected ~33.6-33.9)")
            if not (-84.8 <= lon <= -84.0):
                warnings.append(f"Longitude {lon} seems outside Atlanta area (expected ~-84.6 to -84.2)")
                
        return issues, warnings

    def validate_proximities(self, apartment: Dict) -> Tuple[List[str], List[str]]:
        """Validate proximity data"""
        issues = []
        warnings = []
        
        if 'proximities' not in apartment:
            issues.append("Missing proximities")
            return issues, warnings
        
        proximities = apartment['proximities']
        
        if not isinstance(proximities, dict):
            issues.append("Proximities should be a dictionary")
            return issues, warnings
        
        if not proximities:
            issues.append("Proximities dictionary is empty")
            return issues, warnings
        
        # Check for required locations
        missing_locations = []
        for required_loc in self.required_proximity_locations:
            if required_loc not in proximities:
                missing_locations.append(required_loc)
        
        if missing_locations:
            issues.append(f"Missing proximity data for: {', '.join(missing_locations)}")
        
        # Validate each proximity entry
        for location, data in proximities.items():
            if not isinstance(data, dict):
                issues.append(f"Proximity data for {location} should be a dictionary")
                continue
            
            # Check required fields
            for field in self.required_proximity_fields:
                if field not in data:
                    issues.append(f"Missing field '{field}' in {location} proximity data")
                elif not data[field] and data[field] != 0:
                    issues.append(f"Empty field '{field}' in {location} proximity data")
            
            # Validate numeric fields
            if 'distance_miles' in data:
                distance = data['distance_miles']
                if not isinstance(distance, (int, float)) or distance < 0:
                    issues.append(f"Invalid distance for {location}: {distance}")
                elif distance > 20:
                    warnings.append(f"Distance to {location} seems very large: {distance} miles")
            
            if 'walking_time_minutes' in data:
                time_mins = data['walking_time_minutes']
                if not isinstance(time_mins, (int, float)) or time_mins < 0:
                    issues.append(f"Invalid walking time for {location}: {time_mins}")
                    
        return issues, warnings

    def validate_apartment(self, apartment: Dict) -> ValidationResult:
        """Validate a single apartment"""
        apartment_name = apartment.get('name', 'Unknown')
        all_issues = []
        all_warnings = []
        
        # Validate basic fields
        issues, warnings = self.validate_basic_fields(apartment)
        all_issues.extend(issues)
        all_warnings.extend(warnings)
        
        # Validate coordinates
        issues, warnings = self.validate_coordinates(apartment)
        all_issues.extend(issues)
        all_warnings.extend(warnings)
        
        # Validate proximities
        issues, warnings = self.validate_proximities(apartment)
        all_issues.extend(issues)
        all_warnings.extend(warnings)
        
        is_valid = len(all_issues) == 0
        
        return ValidationResult(
            apartment_name=apartment_name,
            issues=all_issues,
            warnings=all_warnings,
            is_valid=is_valid
        )

    def validate_data_file(self, file_path: str) -> Dict:
        """Validate entire apartment data file"""
        try:
            with open(file_path, 'r') as f:
                apartments = json.load(f)
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to load data file: {e}",
                'results': []
            }
        
        if not isinstance(apartments, list):
            return {
                'success': False,
                'error': "Data file should contain a list of apartments",
                'results': []
            }
        
        results = []
        valid_count = 0
        
        for apartment in apartments:
            result = self.validate_apartment(apartment)
            results.append(result)
            if result.is_valid:
                valid_count += 1
        
        return {
            'success': True,
            'total_apartments': len(apartments),
            'valid_apartments': valid_count,
            'invalid_apartments': len(apartments) - valid_count,
            'results': results
        }

    def print_validation_report(self, validation_data: Dict):
        """Print a formatted validation report"""
        if not validation_data['success']:
            print(f"❌ Validation failed: {validation_data['error']}")
            return
        
        total = validation_data['total_apartments']
        valid = validation_data['valid_apartments']
        invalid = validation_data['invalid_apartments']
        
        print("="*60)
        print("🏠 APARTMENT DATA VALIDATION REPORT")
        print("="*60)
        print(f"📊 Total apartments: {total}")
        print(f"✅ Valid apartments: {valid}")
        print(f"❌ Invalid apartments: {invalid}")
        print(f"📈 Success rate: {(valid/total*100):.1f}%")
        print()
        
        if invalid > 0:
            print("🚨 ISSUES FOUND:")
            print("-" * 40)
            
            for result in validation_data['results']:
                if not result.is_valid:
                    print(f"\n❌ {result.apartment_name}:")
                    for issue in result.issues:
                        print(f"   • {issue}")
        
        # Show warnings
        warning_count = sum(len(r.warnings) for r in validation_data['results'])
        if warning_count > 0:
            print(f"\n⚠️  WARNINGS ({warning_count} total):")
            print("-" * 40)
            
            for result in validation_data['results']:
                if result.warnings:
                    print(f"\n⚠️  {result.apartment_name}:")
                    for warning in result.warnings:
                        print(f"   • {warning}")
        
        print("\n" + "="*60)
        
        if invalid == 0 and warning_count == 0:
            print("🎉 All apartments passed validation with no issues!")
        elif invalid == 0:
            print("✅ All apartments are valid (some warnings to review)")
        else:
            print(f"🔧 {invalid} apartments need attention")

def main():
    """Main function to run validation"""
    if len(sys.argv) != 2:
        print("Usage: python data_validator.py <apartment_data.json>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found")
        sys.exit(1)
    
    validator = ApartmentDataValidator()
    validation_data = validator.validate_data_file(file_path)
    validator.print_validation_report(validation_data)
    
    # Exit with error code if validation failed
    if not validation_data['success'] or validation_data['invalid_apartments'] > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
