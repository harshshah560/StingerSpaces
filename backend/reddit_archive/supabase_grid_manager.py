"""
Supabase Integration for Two-Factor Authentication Grid
This module manages a grid where both rows and columns are apartments,
providing cross-validation for Reddit comments about apartments.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import hashlib

# For Supabase - will install if needed
try:
    from supabase import create_client, Client
except ImportError:
    print("Supabase not installed. Run: pip install supabase")
    Client = None


@dataclass
class CommentValidation:
    comment_id: str
    source_apartment: str  # The apartment being searched for
    mentioned_apartment: str  # The apartment mentioned in comment
    comment_text: str
    confidence_score: float
    validation_status: str  # 'pending', 'verified', 'invalid'
    created_at: datetime
    reddit_post_id: str
    reddit_comment_id: str


class SupabaseGridManager:
    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        """Initialize Supabase client for the apartment validation grid"""
        
        # Use environment variables or provided credentials
        self.supabase_url = supabase_url or os.getenv('SUPABASE_URL')
        self.supabase_key = supabase_key or os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            logging.warning("Supabase credentials not provided. Using local file storage.")
            self.client = None
            self.use_local_storage = True
            self.local_storage_path = '/Users/harshshah/Documents/hackgt/backend/output/validation_grid.json'
        else:
            self.client = create_client(self.supabase_url, self.supabase_key)
            self.use_local_storage = False
        
        self.apartments = []
        self.load_apartments()

    def load_apartments(self):
        """Load apartment names from the data file"""
        try:
            with open('/Users/harshshah/Documents/hackgt/backend/data/apartment_data.json', 'r') as f:
                data = json.load(f)
                self.apartments = [apt['name'] for apt in data]
                logging.info(f"Loaded {len(self.apartments)} apartments")
        except Exception as e:
            logging.error(f"Error loading apartments: {e}")
            self.apartments = []

    def create_tables(self):
        """Create the necessary tables in Supabase (or initialize local storage)"""
        if self.use_local_storage:
            self._initialize_local_storage()
        else:
            self._create_supabase_tables()

    def _initialize_local_storage(self):
        """Initialize local JSON storage for the validation grid"""
        grid_structure = {
            'apartments': self.apartments,
            'validation_grid': {},
            'comments': {},
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'total_apartments': len(self.apartments)
            }
        }
        
        # Initialize grid - each apartment can reference every other apartment
        for source_apt in self.apartments:
            grid_structure['validation_grid'][source_apt] = {}
            for target_apt in self.apartments:
                grid_structure['validation_grid'][source_apt][target_apt] = {
                    'comment_count': 0,
                    'verified_comments': 0,
                    'confidence_sum': 0.0,
                    'average_confidence': 0.0,
                    'last_updated': None
                }
        
        # Save to file
        os.makedirs(os.path.dirname(self.local_storage_path), exist_ok=True)
        with open(self.local_storage_path, 'w') as f:
            json.dump(grid_structure, f, indent=2)
        
        logging.info(f"Initialized local validation grid at {self.local_storage_path}")

    def _create_supabase_tables(self):
        """Create tables in Supabase (requires SQL execution)"""
        # This would typically be done through Supabase dashboard or SQL
        # Here we'll show the SQL structure that should be created
        
        sql_commands = """
        -- Apartments table
        CREATE TABLE apartments (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            aliases JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        );
        
        -- Comments validation table
        CREATE TABLE comment_validations (
            id SERIAL PRIMARY KEY,
            comment_id TEXT UNIQUE NOT NULL,
            source_apartment TEXT NOT NULL,
            mentioned_apartment TEXT NOT NULL,
            comment_text TEXT NOT NULL,
            confidence_score FLOAT NOT NULL,
            validation_status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT NOW(),
            reddit_post_id TEXT,
            reddit_comment_id TEXT,
            FOREIGN KEY (source_apartment) REFERENCES apartments(name),
            FOREIGN KEY (mentioned_apartment) REFERENCES apartments(name)
        );
        
        -- Validation grid summary table
        CREATE TABLE validation_grid (
            id SERIAL PRIMARY KEY,
            source_apartment TEXT NOT NULL,
            mentioned_apartment TEXT NOT NULL,
            comment_count INTEGER DEFAULT 0,
            verified_comments INTEGER DEFAULT 0,
            confidence_sum FLOAT DEFAULT 0.0,
            average_confidence FLOAT DEFAULT 0.0,
            last_updated TIMESTAMP DEFAULT NOW(),
            UNIQUE(source_apartment, mentioned_apartment),
            FOREIGN KEY (source_apartment) REFERENCES apartments(name),
            FOREIGN KEY (mentioned_apartment) REFERENCES apartments(name)
        );
        """
        
        logging.info("SQL commands for Supabase tables:")
        logging.info(sql_commands)
        return sql_commands

    def add_comment_validation(self, validation: CommentValidation) -> bool:
        """Add a comment validation to the grid"""
        if self.use_local_storage:
            return self._add_validation_local(validation)
        else:
            return self._add_validation_supabase(validation)

    def _add_validation_local(self, validation: CommentValidation) -> bool:
        """Add validation to local storage"""
        try:
            # Load current grid
            with open(self.local_storage_path, 'r') as f:
                grid_data = json.load(f)
            
            # Generate unique comment ID if not provided
            if not validation.comment_id:
                validation.comment_id = hashlib.md5(
                    f"{validation.source_apartment}{validation.mentioned_apartment}{validation.comment_text[:100]}"
                    .encode()
                ).hexdigest()
            
            # Add to comments section
            grid_data['comments'][validation.comment_id] = {
                'source_apartment': validation.source_apartment,
                'mentioned_apartment': validation.mentioned_apartment,
                'comment_text': validation.comment_text,
                'confidence_score': validation.confidence_score,
                'validation_status': validation.validation_status,
                'created_at': validation.created_at.isoformat(),
                'reddit_post_id': validation.reddit_post_id,
                'reddit_comment_id': validation.reddit_comment_id
            }
            
            # Update grid statistics
            source = validation.source_apartment
            mentioned = validation.mentioned_apartment
            
            if source in grid_data['validation_grid'] and mentioned in grid_data['validation_grid'][source]:
                cell = grid_data['validation_grid'][source][mentioned]
                cell['comment_count'] += 1
                cell['confidence_sum'] += validation.confidence_score
                cell['average_confidence'] = cell['confidence_sum'] / cell['comment_count']
                if validation.validation_status == 'verified':
                    cell['verified_comments'] += 1
                cell['last_updated'] = datetime.now().isoformat()
            
            # Update metadata
            grid_data['metadata']['last_updated'] = datetime.now().isoformat()
            
            # Save back to file
            with open(self.local_storage_path, 'w') as f:
                json.dump(grid_data, f, indent=2)
            
            logging.info(f"Added validation: {source} -> {mentioned} (confidence: {validation.confidence_score:.2f})")
            return True
            
        except Exception as e:
            logging.error(f"Error adding validation to local storage: {e}")
            return False

    def _add_validation_supabase(self, validation: CommentValidation) -> bool:
        """Add validation to Supabase"""
        try:
            # Insert into comment_validations table
            result = self.client.table('comment_validations').insert({
                'comment_id': validation.comment_id,
                'source_apartment': validation.source_apartment,
                'mentioned_apartment': validation.mentioned_apartment,
                'comment_text': validation.comment_text,
                'confidence_score': validation.confidence_score,
                'validation_status': validation.validation_status,
                'reddit_post_id': validation.reddit_post_id,
                'reddit_comment_id': validation.reddit_comment_id
            }).execute()
            
            # Update validation grid summary
            self._update_grid_cell_supabase(validation.source_apartment, validation.mentioned_apartment)
            
            logging.info(f"Added validation to Supabase: {validation.source_apartment} -> {validation.mentioned_apartment}")
            return True
            
        except Exception as e:
            logging.error(f"Error adding validation to Supabase: {e}")
            return False

    def get_validation_summary(self, source_apartment: str, mentioned_apartment: str) -> Dict:
        """Get validation summary for a specific apartment pair"""
        if self.use_local_storage:
            return self._get_summary_local(source_apartment, mentioned_apartment)
        else:
            return self._get_summary_supabase(source_apartment, mentioned_apartment)

    def _get_summary_local(self, source_apartment: str, mentioned_apartment: str) -> Dict:
        """Get summary from local storage"""
        try:
            with open(self.local_storage_path, 'r') as f:
                grid_data = json.load(f)
            
            if (source_apartment in grid_data['validation_grid'] and 
                mentioned_apartment in grid_data['validation_grid'][source_apartment]):
                return grid_data['validation_grid'][source_apartment][mentioned_apartment]
            else:
                return {'comment_count': 0, 'verified_comments': 0, 'average_confidence': 0.0}
                
        except Exception as e:
            logging.error(f"Error getting summary from local storage: {e}")
            return {'comment_count': 0, 'verified_comments': 0, 'average_confidence': 0.0}

    def get_all_validations_for_apartment(self, apartment_name: str) -> List[Dict]:
        """Get all validations where this apartment is the source"""
        if self.use_local_storage:
            return self._get_apartment_validations_local(apartment_name)
        else:
            return self._get_apartment_validations_supabase(apartment_name)

    def _get_apartment_validations_local(self, apartment_name: str) -> List[Dict]:
        """Get apartment validations from local storage"""
        try:
            with open(self.local_storage_path, 'r') as f:
                grid_data = json.load(f)
            
            validations = []
            for comment_id, comment_data in grid_data['comments'].items():
                if comment_data['source_apartment'] == apartment_name:
                    validations.append(comment_data)
            
            return validations
            
        except Exception as e:
            logging.error(f"Error getting apartment validations: {e}")
            return []

    def validate_comment_relevance(self, comment_text: str, source_apartment: str, 
                                 mentioned_apartment: str) -> float:
        """
        Validate if a comment about source_apartment actually mentions mentioned_apartment
        Returns confidence score 0.0 - 1.0
        """
        comment_lower = comment_text.lower()
        mentioned_lower = mentioned_apartment.lower()
        
        # Load aliases for better matching
        try:
            with open('/Users/harshshah/Documents/hackgt/backend/output/apartment_aliases.json', 'r') as f:
                alias_data = json.load(f)
            
            mentioned_aliases = alias_data.get(mentioned_apartment, {}).get('aliases', [])
        except:
            mentioned_aliases = [mentioned_lower]
        
        # Check for exact mentions
        for alias in mentioned_aliases:
            if alias.lower() in comment_lower:
                return 0.9  # High confidence for exact match
        
        # Check for partial matches (word boundaries)
        words_in_comment = set(comment_lower.split())
        mentioned_words = set(mentioned_lower.split())
        
        overlap = len(words_in_comment.intersection(mentioned_words))
        if overlap > 0:
            return min(0.7, overlap / len(mentioned_words))
        
        return 0.0  # No relevant mention found

    def print_grid_summary(self):
        """Print a summary of the validation grid"""
        if self.use_local_storage:
            try:
                with open(self.local_storage_path, 'r') as f:
                    grid_data = json.load(f)
                
                print("🏢 Apartment Validation Grid Summary")
                print("=" * 50)
                
                total_comments = len(grid_data['comments'])
                print(f"Total Comments: {total_comments}")
                print(f"Total Apartments: {len(self.apartments)}")
                print()
                
                # Show top validated pairs
                pairs = []
                for source in grid_data['validation_grid']:
                    for mentioned in grid_data['validation_grid'][source]:
                        cell = grid_data['validation_grid'][source][mentioned]
                        if cell['comment_count'] > 0:
                            pairs.append((source, mentioned, cell))
                
                pairs.sort(key=lambda x: x[2]['comment_count'], reverse=True)
                
                print("Top Apartment Pairs with Comments:")
                for i, (source, mentioned, cell) in enumerate(pairs[:10]):
                    print(f"{i+1:2d}. {source} -> {mentioned}")
                    print(f"    Comments: {cell['comment_count']}, Verified: {cell['verified_comments']}")
                    print(f"    Avg Confidence: {cell['average_confidence']:.2f}")
                    print()
                    
            except Exception as e:
                logging.error(f"Error printing grid summary: {e}")


def main():
    """Test the Supabase grid manager"""
    logging.basicConfig(level=logging.INFO)
    
    # Initialize grid manager (will use local storage without Supabase credentials)
    grid_manager = SupabaseGridManager()
    
    # Create tables/initialize storage
    grid_manager.create_tables()
    
    # Test adding some validations
    test_validations = [
        CommentValidation(
            comment_id="",
            source_apartment="Catalyst Midtown",
            mentioned_apartment="Square On 5th",
            comment_text="I lived at Catalyst but my friend was at SQ5 and said it was much better",
            confidence_score=0.85,
            validation_status="verified",
            created_at=datetime.now(),
            reddit_post_id="test_post_1",
            reddit_comment_id="test_comment_1"
        ),
        CommentValidation(
            comment_id="",
            source_apartment="Square On 5th",
            mentioned_apartment="The Connector",
            comment_text="Square on 5th is okay but Connector has better amenities",
            confidence_score=0.90,
            validation_status="verified",
            created_at=datetime.now(),
            reddit_post_id="test_post_2",
            reddit_comment_id="test_comment_2"
        ),
        CommentValidation(
            comment_id="",
            source_apartment="The Connector",
            mentioned_apartment="100 Midtown",
            comment_text="Connector is nice but 100 Midtown is closer to campus",
            confidence_score=0.80,
            validation_status="pending",
            created_at=datetime.now(),
            reddit_post_id="test_post_3",
            reddit_comment_id="test_comment_3"
        )
    ]
    
    print("Adding test validations...")
    for validation in test_validations:
        success = grid_manager.add_comment_validation(validation)
        if success:
            print(f"✅ Added: {validation.source_apartment} -> {validation.mentioned_apartment}")
        else:
            print(f"❌ Failed: {validation.source_apartment} -> {validation.mentioned_apartment}")
    
    print()
    grid_manager.print_grid_summary()
    
    # Test validation relevance
    print("\nTesting comment relevance validation:")
    test_cases = [
        ("I love SQ5!", "Square On 5th", "Square On 5th"),
        ("Catalyst is better than Square on 5th", "Catalyst Midtown", "Square On 5th"),
        ("Random comment about pizza", "Catalyst Midtown", "Square On 5th"),
        ("The connector has great amenities", "The Connector", "The Connector"),
    ]
    
    for comment, source, mentioned in test_cases:
        score = grid_manager.validate_comment_relevance(comment, source, mentioned)
        print(f"'{comment}' -> {source}/{mentioned}: {score:.2f}")


if __name__ == "__main__":
    main()
