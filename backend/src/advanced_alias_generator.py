"""
Advanced Alias Generator for Apartment Names
This module generates comprehensive aliases for apartment names to catch all possible variations,
including short forms, abbreviations, and common misspellings.
"""

import re
import itertools
from typing import List, Set, Dict
import json
from dataclasses import dataclass
from fuzzywuzzy import fuzz
import phonetics


@dataclass
class ApartmentAlias:
    original_name: str
    aliases: Set[str]
    confidence_scores: Dict[str, float]


class AdvancedAliasGenerator:
    def __init__(self, location_config: Dict[str, List[str]] = None):
        """
        Initialize the alias generator with optional location-specific configurations
        
        Args:
            location_config: Optional dict mapping location terms to their abbreviations
                           e.g., {'midtown': ['mid', 'mdt'], 'university': ['uni', 'u']}
        """
        # Common housing-related words that don't add meaning for search
        self.common_words = {
            'apartment', 'apartments', 'apt', 'apts',
            'student', 'housing', 'residences', 'residence',
            'complex', 'community', 'towers', 'tower',
            'lofts', 'loft', 'place', 'plaza', 'point', 'pointe',
            'square', 'station', 'flats', 'the', 'at', 'on', 'of',
            'hall', 'halls', 'house', 'houses', 'village', 'commons',
            'center', 'centre', 'park', 'gardens', 'court', 'courts'
        }
        
        # Number word to digit conversion (universal)
        self.number_words = {
            'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
            'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10',
            'eleven': '11', 'twelve': '12', 'thirteen': '13', 'fourteen': '14',
            'fifteen': '15', 'sixteen': '16', 'seventeen': '17', 'eighteen': '18',
            'nineteen': '19', 'twenty': '20', 'thirty': '30', 'forty': '40',
            'fifty': '50', 'sixty': '60', 'seventy': '70', 'eighty': '80',
            'ninety': '90', 'hundred': '100'
        }
        
        # Ordinal word to number conversion (universal)
        self.ordinal_words = {
            'first': '1st', 'second': '2nd', 'third': '3rd', 'fourth': '4th',
            'fifth': '5th', 'sixth': '6th', 'seventh': '7th', 'eighth': '8th',
            'ninth': '9th', 'tenth': '10th', 'eleventh': '11th', 'twelfth': '12th',
            'thirteenth': '13th', 'fourteenth': '14th', 'fifteenth': '15th',
            'sixteenth': '16th', 'seventeenth': '17th', 'eighteenth': '18th',
            'nineteenth': '19th', 'twentieth': '20th'
        }
        
        # Generic abbreviation patterns (universal)
        self.abbreviation_patterns = {
            'apartment': ['apt'], 'apartments': ['apts'], 
            'building': ['bldg'], 'buildings': ['bldgs'],
            'tower': ['twr'], 'towers': ['twrs'],
            'place': ['pl'], 'plaza': ['plz'],
            'street': ['st'], 'avenue': ['ave'], 'boulevard': ['blvd'],
            'court': ['ct'], 'circle': ['cir'], 'drive': ['dr'],
            'residence': ['res'], 'residences': ['res'],
            'student': ['stud'], 'university': ['univ', 'u'],
            'college': ['coll'], 'campus': ['camp']
        }
        
        # Location-specific configuration (can be customized per university/city)
        self.location_config = location_config or {}

    def generate_all_aliases(self, apartment_name: str) -> ApartmentAlias:
        """Generate all possible aliases for an apartment name"""
        aliases = set()
        confidence_scores = {}
        
        # Add original name
        aliases.add(apartment_name.lower())
        confidence_scores[apartment_name.lower()] = 1.0
        
        # 1. Basic variations
        basic_aliases = self._generate_basic_aliases(apartment_name)
        aliases.update(basic_aliases)
        for alias in basic_aliases:
            confidence_scores[alias] = 0.9
        
        # 2. Abbreviation-based aliases
        abbrev_aliases = self._generate_abbreviation_aliases(apartment_name)
        aliases.update(abbrev_aliases)
        for alias in abbrev_aliases:
            confidence_scores[alias] = 0.8
        
        # 3. Short-form aliases (like SQ5 for Square on 5th)
        short_aliases = self._generate_short_form_aliases(apartment_name)
        aliases.update(short_aliases)
        for alias in short_aliases:
            confidence_scores[alias] = 0.7
        
        # 4. Phonetic aliases
        phonetic_aliases = self._generate_phonetic_aliases(apartment_name)
        aliases.update(phonetic_aliases)
        for alias in phonetic_aliases:
            confidence_scores[alias] = 0.6
        
        # 5. Number word conversions
        number_aliases = self._generate_number_aliases(apartment_name)
        aliases.update(number_aliases)
        for alias in number_aliases:
            confidence_scores[alias] = 0.85
        
        # 6. Location-based aliases
        location_aliases = self._generate_location_aliases(apartment_name)
        aliases.update(location_aliases)
        for alias in location_aliases:
            confidence_scores[alias] = 0.75
        
        return ApartmentAlias(apartment_name, aliases, confidence_scores)

    def _generate_basic_aliases(self, name: str) -> Set[str]:
        """Generate basic variations like removing 'the', plurals, etc."""
        aliases = set()
        clean_name = name.lower()
        
        # Remove common words
        words = clean_name.split()
        filtered_words = [w for w in words if w not in self.common_words]
        if filtered_words:
            aliases.add(' '.join(filtered_words))
        
        # Remove 'the' at the beginning
        if clean_name.startswith('the '):
            aliases.add(clean_name[4:])
        
        # Remove punctuation and special chars
        clean_no_punct = re.sub(r'[^\w\s]', '', clean_name)
        aliases.add(clean_no_punct)
        
        # Replace spaces with nothing
        aliases.add(clean_name.replace(' ', ''))
        
        return aliases

    def _generate_abbreviation_aliases(self, name: str) -> Set[str]:
        """Generate abbreviation-based aliases"""
        aliases = set()
        words = name.lower().split()
        
        # First letter of each word
        if len(words) > 1:
            abbrev = ''.join([w[0] for w in words if w not in self.common_words])
            if len(abbrev) >= 2:
                aliases.add(abbrev)
        
        # First letter + numbers
        letters = [w[0] for w in words if w not in self.common_words and not w.isdigit()]
        numbers = [w for w in words if w.isdigit() or any(c.isdigit() for c in w)]
        
        if letters and numbers:
            for num in numbers:
                aliases.add(''.join(letters) + num)
        
        return aliases

    def _generate_short_form_aliases(self, name: str) -> Set[str]:
        """Generate short-form aliases like SQ5 for Square on 5th"""
        aliases = set()
        words = name.lower().split()
        
        # Extract numbers/ordinals first
        numbers = []
        for word in words:
            if word.isdigit():
                numbers.append(word)
            elif any(c.isdigit() for c in word):
                # Extract number from word like "5th"
                num_match = re.search(r'\d+', word)
                if num_match:
                    numbers.append(num_match.group())
        
        # Convert ordinal words to numbers
        for word in words:
            if word in self.ordinal_words:
                ordinal_num = self.ordinal_words[word]
                num_match = re.search(r'\d+', ordinal_num)
                if num_match:
                    numbers.append(num_match.group())
        
        main_words = [w for w in words if w not in self.common_words and not any(c.isdigit() for c in w)]
        
        # Pattern 1: First 2-3 letters of main words + numbers
        if main_words and numbers:
            for main_word in main_words:
                for num in numbers:
                    # 2 letters + number
                    if len(main_word) >= 2:
                        aliases.add(main_word[:2].upper() + num)
                    # 3 letters + number  
                    if len(main_word) >= 3:
                        aliases.add(main_word[:3].upper() + num)
        
        # Pattern 2: Consonants only + numbers
        for word in main_words:
            consonants = ''.join([c for c in word if c not in 'aeiou'])
            if len(consonants) >= 2:
                for num in numbers:
                    aliases.add(consonants.upper() + num)
        
        # Pattern 3: Common abbreviation patterns
        abbreviation_patterns = {
            'square': ['sq', 'sqr'],
            'apartment': ['apt'],
            'building': ['bldg'],
            'tower': ['twr'],
            'place': ['pl'],
            'street': ['st'],
            'avenue': ['ave'],
            'court': ['ct'],
            'circle': ['cir'],
            'drive': ['dr'],
            'station': ['sta', 'stn']
        }
        
        for word in words:
            if word in abbreviation_patterns:
                for abbrev in abbreviation_patterns[word]:
                    new_name = name.lower().replace(word, abbrev)
                    aliases.add(new_name.replace(' ', ''))
                    if numbers:
                        for num in numbers:
                            aliases.add(abbrev.upper() + num)
        
        # Pattern 4: Multi-word abbreviations + numbers (generalized)
        if len(main_words) >= 1 and numbers:
            # Single word + number combinations
            for word in main_words:
                for num in numbers:
                    # First 2-3 letters + number
                    if len(word) >= 2:
                        aliases.add(word[:2].upper() + num)
                    if len(word) >= 3:
                        aliases.add(word[:3].upper() + num)
            
            # Multi-word: Take first letter of each main word + numbers
            if len(main_words) >= 2:
                first_letters = ''.join([w[0].upper() for w in main_words])
                for num in numbers:
                    aliases.add(first_letters + num)
        
        # Pattern 5: Word combinations with common abbreviations + numbers
        for word in main_words:
            if word in self.abbreviation_patterns:
                for abbrev in self.abbreviation_patterns[word]:
                    for num in numbers:
                        aliases.add(abbrev.upper() + num)
                        aliases.add(abbrev.lower() + num)
        
        return aliases

    def _generate_phonetic_aliases(self, name: str) -> Set[str]:
        """Generate phonetically similar aliases"""
        aliases = set()
        
        # Use Soundex for phonetic matching
        try:
            soundex = phonetics.soundex(name)
            aliases.add(soundex)
        except:
            pass
        
        # Common phonetic substitutions
        phonetic_subs = {
            'ph': 'f', 'f': 'ph', 'c': 'k', 'k': 'c',
            'z': 's', 's': 'z', 'i': 'y', 'y': 'i'
        }
        
        for original, replacement in phonetic_subs.items():
            if original in name.lower():
                alias = name.lower().replace(original, replacement)
                aliases.add(alias)
        
        return aliases

    def _generate_number_aliases(self, name: str) -> Set[str]:
        """Convert between number words and digits"""
        aliases = set()
        name_lower = name.lower()
        
        # Convert number words to digits
        for word, digit in self.number_words.items():
            if word in name_lower:
                alias = name_lower.replace(word, digit)
                aliases.add(alias)
        
        # Convert ordinal words to numbers
        for word, ordinal in self.ordinal_words.items():
            if word in name_lower:
                alias = name_lower.replace(word, ordinal)
                aliases.add(alias)
                # Also try without 'st', 'nd', 'rd', 'th'
                number = ordinal[:-2]
                alias2 = name_lower.replace(word, number)
                aliases.add(alias2)
        
        return aliases

    def _generate_location_aliases(self, name: str) -> Set[str]:
        """Generate location-based aliases using configurable location patterns"""
        aliases = set()
        
        # Use configured location abbreviations if provided
        if not self.location_config:
            return aliases
        
        name_lower = name.lower()
        for location_term, abbrevs in self.location_config.items():
            location_lower = location_term.lower()
            if location_lower in name_lower:
                for abbrev in abbrevs:
                    # Replace location term with abbreviation
                    alias = name_lower.replace(location_lower, abbrev.lower())
                    aliases.add(alias)
                    # Also try without spaces
                    alias_no_space = alias.replace(' ', '')
                    aliases.add(alias_no_space)
        
        return aliases

    def find_best_match(self, search_term: str, apartment_aliases: List[ApartmentAlias], 
                       threshold: int = 80) -> List[tuple]:
        """Find the best matching apartments for a search term"""
        matches = []
        search_term_lower = search_term.lower()
        
        for apt_alias in apartment_aliases:
            best_score = 0
            best_alias = None
            confidence = 0
            
            for alias in apt_alias.aliases:
                # Exact match gets highest score
                if search_term_lower == alias:
                    score = 100
                else:
                    # Fuzzy match
                    score = fuzz.ratio(search_term_lower, alias)
                
                if score > best_score:
                    best_score = score
                    best_alias = alias
                    confidence = apt_alias.confidence_scores.get(alias, 0.5)
            
            if best_score >= threshold:
                matches.append((apt_alias.original_name, best_score, best_alias, confidence))
        
        # Sort by score descending
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches


def create_generator_for_university(university_name: str = "generic") -> AdvancedAliasGenerator:
    """
    Factory function to create a configured alias generator for different universities
    
    Args:
        university_name: Name of the university/location to configure for
                        Options: 'gt', 'gatech', 'uga', 'emory', 'generic'
    """
    location_configs = {
        'gt': {
            'midtown': ['mid', 'mdt', 'midtwn'],
            'downtown': ['dwtn', 'dt', 'dtown'],
            'atlanta': ['atl', 'atla'],
            'west end': ['we', 'westend'],
            'atlantic station': ['as', 'atlsta'],
            'tech': ['gt', 'gatech'],
            'georgia tech': ['gt', 'gatech']
        },
        'gatech': {  # Same as 'gt'
            'midtown': ['mid', 'mdt', 'midtwn'],
            'downtown': ['dwtn', 'dt', 'dtown'],
            'atlanta': ['atl', 'atla'],
            'west end': ['we', 'westend'],
            'atlantic station': ['as', 'atlsta'],
            'tech': ['gt', 'gatech'],
            'georgia tech': ['gt', 'gatech']
        },
        'uga': {
            'athens': ['ath'],
            'downtown': ['dwtn', 'dt'],
            'campus': ['camp'],
            'university': ['uga', 'u'],
            'georgia': ['ga', 'uga']
        },
        'emory': {
            'atlanta': ['atl', 'atla'],
            'druid hills': ['dh'],
            'emory': ['em'],
            'university': ['univ', 'u']
        },
        'generic': {}  # No location-specific abbreviations
    }
    
    config = location_configs.get(university_name.lower(), {})
    return AdvancedAliasGenerator(location_config=config)


def main():
    """Test the alias generator with sample apartment names"""
    # Create a generator for Georgia Tech (can be changed for other universities)
    generator = create_generator_for_university('gt')
    
    # Load apartment data
    with open('/Users/harshshah/Documents/hackgt/backend/data/apartment_data.json', 'r') as f:
        apartments = json.load(f)
    
    # Generate aliases for all apartments
    all_aliases = []
    
    print("Generating comprehensive aliases for all apartments...\n")
    
    for apt in apartments:
        apt_name = apt['name']
        aliases = generator.generate_all_aliases(apt_name)
        all_aliases.append(aliases)
        
        print(f"🏢 {apt_name}")
        print("   Aliases:", list(aliases.aliases)[:10])  # Show first 10
        print(f"   Total aliases: {len(aliases.aliases)}")
        print()
    
    # Test common abbreviation patterns (generalized)
    test_terms = []
    
    # Generate test terms dynamically from the loaded apartments
    for apt in apartments[:5]:  # Test first 5 apartments
        apt_name = apt['name']
        words = apt_name.lower().split()
        
        # Generate some test patterns
        # Pattern 1: First letters + numbers
        main_words = [w for w in words if w not in generator.common_words and not w.isdigit()]
        numbers = [w for w in words if w.isdigit() or any(c.isdigit() for c in w)]
        
        if main_words and numbers:
            first_letters = ''.join([w[0] for w in main_words])
            for num in numbers:
                num_only = ''.join(filter(str.isdigit, num))
                if num_only:
                    test_terms.append(first_letters.upper() + num_only)
        
        # Pattern 2: First word only
        if main_words:
            test_terms.append(main_words[0].lower())
        
        # Pattern 3: Abbreviated forms
        for word in main_words:
            if len(word) >= 3:
                test_terms.append(word[:3].lower())
    
    # Remove duplicates and limit to reasonable number
    test_terms = list(set(test_terms))[:8]
    
    print("Testing alias matching:")
    print("=" * 50)
    
    for term in test_terms:
        print(f"\n🔍 Searching for: '{term}'")
        matches = generator.find_best_match(term, all_aliases, threshold=70)
        
        if matches:
            for match in matches[:3]:  # Top 3 matches
                name, score, matched_alias, confidence = match
                print(f"   ✅ {name} (score: {score}, alias: '{matched_alias}', confidence: {confidence:.2f})")
        else:
            print("   ❌ No matches found")
    
    # Save aliases to file
    alias_data = {}
    for aliases in all_aliases:
        alias_data[aliases.original_name] = {
            'aliases': list(aliases.aliases),
            'confidence_scores': aliases.confidence_scores
        }
    
    with open('/Users/harshshah/Documents/hackgt/backend/output/apartment_aliases.json', 'w') as f:
        json.dump(alias_data, f, indent=2)
    
    print(f"\n✅ Saved aliases for {len(alias_data)} apartments to apartment_aliases.json")


if __name__ == "__main__":
    main()
