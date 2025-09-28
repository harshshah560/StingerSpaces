"""
Enhanced Reddit Search and Validation System
This module implements a sophisticated multi-pass Reddit search strategy
with two-factor authentication for apartment comments.
"""

import praw
import json
import logging
import re
import time
from typing import Dict, List, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
import os
from fuzzywuzzy import fuzz

from advanced_alias_generator import AdvancedAliasGenerator, ApartmentAlias, create_generator_for_university
from supabase_grid_manager import SupabaseGridManager, CommentValidation


@dataclass
class RedditSearchResult:
    post_id: str
    comment_id: str
    comment_text: str
    subreddit: str
    created_utc: float
    score: int
    source_apartment: str
    mentioned_apartments: List[str]
    confidence_scores: Dict[str, float]
    search_term_used: str


class EnhancedRedditSearcher:
    def __init__(self, reddit_credentials: Dict[str, str], university: str = 'generic'):
        """
        Initialize Reddit searcher with enhanced validation
        
        Args:
            reddit_credentials: Reddit API credentials
            university: University configuration for location-specific aliases
                       ('gt', 'uga', 'emory', 'generic', etc.)
        """
        
        # Initialize Reddit API
        self.reddit = praw.Reddit(
            client_id=reddit_credentials['client_id'],
            client_secret=reddit_credentials['client_secret'],
            user_agent=reddit_credentials['user_agent']
        )
        
        # Initialize supporting systems with university-specific configuration
        self.alias_generator = create_generator_for_university(university)
        self.grid_manager = SupabaseGridManager()
        
        # Load apartment data and generate aliases
        self.apartments = []
        self.apartment_aliases = {}
        self.load_apartment_data()
        
        # Search configuration
        self.target_subreddits = ['gatech', 'Atlanta', 'GeorgiaTech', 'college']
        self.max_posts_per_search = 100
        self.max_comments_per_post = 50
        self.min_comment_length = 20
        
        # Context keywords that help validate apartment discussions
        self.housing_context_keywords = {
            'housing', 'apartment', 'living', 'rent', 'lease', 'roommate',
            'move', 'dorm', 'residence', 'amenities', 'price', 'cost',
            'utilities', 'parking', 'location', 'campus', 'walk', 'shuttle',
            'noise', 'quiet', 'party', 'management', 'maintenance', 'gym',
            'pool', 'laundry', 'kitchen', 'bedroom', 'bathroom', 'balcony'
        }

    def load_apartment_data(self):
        """Load apartment data and generate comprehensive aliases"""
        try:
            with open('/Users/harshshah/Documents/hackgt/backend/data/apartment_data.json', 'r') as f:
                apartment_data = json.load(f)
            
            self.apartments = [apt['name'] for apt in apartment_data]
            
            # Generate aliases for each apartment
            logging.info("Generating comprehensive aliases for all apartments...")
            for apt_name in self.apartments:
                aliases = self.alias_generator.generate_all_aliases(apt_name)
                self.apartment_aliases[apt_name] = aliases
            
            logging.info(f"Loaded {len(self.apartments)} apartments with aliases")
            
        except Exception as e:
            logging.error(f"Error loading apartment data: {e}")
            self.apartments = []
            self.apartment_aliases = {}

    def generate_search_terms(self, apartment_name: str) -> List[Tuple[str, float]]:
        """Generate prioritized search terms for an apartment"""
        search_terms = []
        
        if apartment_name not in self.apartment_aliases:
            return [(apartment_name.lower(), 1.0)]
        
        aliases = self.apartment_aliases[apartment_name]
        
        # Priority 1: Original name and high-confidence aliases
        search_terms.append((apartment_name.lower(), 1.0))
        
        for alias in aliases.aliases:
            confidence = aliases.confidence_scores.get(alias, 0.5)
            if confidence >= 0.8:
                search_terms.append((alias, confidence))
        
        # Priority 2: Medium confidence aliases (common abbreviations)
        for alias in aliases.aliases:
            confidence = aliases.confidence_scores.get(alias, 0.5)
            if 0.6 <= confidence < 0.8:
                search_terms.append((alias, confidence))
        
        # Sort by confidence, remove duplicates
        search_terms = list(set(search_terms))
        search_terms.sort(key=lambda x: x[1], reverse=True)
        
        return search_terms[:10]  # Top 10 search terms

    def search_reddit_for_apartment(self, apartment_name: str, days_back: int = 365) -> List[RedditSearchResult]:
        """
        Multi-pass search for apartment mentions with validation
        """
        all_results = []
        search_terms = self.generate_search_terms(apartment_name)
        
        logging.info(f"Searching for '{apartment_name}' using {len(search_terms)} search terms")
        
        # Calculate time threshold
        time_threshold = time.time() - (days_back * 24 * 60 * 60)
        
        for search_term, confidence in search_terms:
            logging.info(f"  Searching with term: '{search_term}' (confidence: {confidence:.2f})")
            
            try:
                # Search across multiple subreddits
                for subreddit_name in self.target_subreddits:
                    results = self._search_subreddit(
                        subreddit_name, search_term, apartment_name, 
                        time_threshold, confidence
                    )
                    all_results.extend(results)
                    
                    # Rate limiting
                    time.sleep(1)
                    
            except Exception as e:
                logging.error(f"Error searching for '{search_term}': {e}")
                continue
        
        # Remove duplicates and validate results
        unique_results = self._deduplicate_results(all_results)
        validated_results = self._validate_results(unique_results, apartment_name)
        
        logging.info(f"Found {len(validated_results)} validated results for '{apartment_name}'")
        return validated_results

    def _search_subreddit(self, subreddit_name: str, search_term: str, 
                         source_apartment: str, time_threshold: float, 
                         term_confidence: float) -> List[RedditSearchResult]:
        """Search a specific subreddit for the search term"""
        results = []
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Search posts
            for post in subreddit.search(search_term, limit=self.max_posts_per_search):
                if post.created_utc < time_threshold:
                    continue
                
                # Check post title and text
                post_text = f"{post.title} {getattr(post, 'selftext', '')}"
                if self._has_housing_context(post_text):
                    # Analyze post content
                    mentioned_apts = self._find_mentioned_apartments(post_text)
                    if mentioned_apts:
                        result = RedditSearchResult(
                            post_id=post.id,
                            comment_id="",  # This is a post, not a comment
                            comment_text=post_text,
                            subreddit=subreddit_name,
                            created_utc=post.created_utc,
                            score=post.score,
                            source_apartment=source_apartment,
                            mentioned_apartments=list(mentioned_apts.keys()),
                            confidence_scores=mentioned_apts,
                            search_term_used=search_term
                        )
                        results.append(result)
                
                # Check comments on this post
                try:
                    post.comments.replace_more(limit=0)
                    comment_count = 0
                    
                    for comment in post.comments.list():
                        if comment_count >= self.max_comments_per_post:
                            break
                        
                        if (hasattr(comment, 'body') and 
                            len(comment.body) >= self.min_comment_length and
                            comment.created_utc >= time_threshold):
                            
                            if self._has_housing_context(comment.body):
                                mentioned_apts = self._find_mentioned_apartments(comment.body)
                                if mentioned_apts:
                                    result = RedditSearchResult(
                                        post_id=post.id,
                                        comment_id=comment.id,
                                        comment_text=comment.body,
                                        subreddit=subreddit_name,
                                        created_utc=comment.created_utc,
                                        score=getattr(comment, 'score', 0),
                                        source_apartment=source_apartment,
                                        mentioned_apartments=list(mentioned_apts.keys()),
                                        confidence_scores=mentioned_apts,
                                        search_term_used=search_term
                                    )
                                    results.append(result)
                            
                            comment_count += 1
                            
                except Exception as e:
                    logging.warning(f"Error processing comments for post {post.id}: {e}")
                    continue
                    
        except Exception as e:
            logging.error(f"Error searching subreddit {subreddit_name}: {e}")
        
        return results

    def _has_housing_context(self, text: str) -> bool:
        """Check if text has housing-related context"""
        text_lower = text.lower()
        
        # Must contain at least 2 housing context keywords
        context_count = sum(1 for keyword in self.housing_context_keywords 
                          if keyword in text_lower)
        
        return context_count >= 2

    def _find_mentioned_apartments(self, text: str) -> Dict[str, float]:
        """Find all apartments mentioned in text with confidence scores"""
        mentioned = {}
        text_lower = text.lower()
        
        for apt_name in self.apartments:
            if apt_name not in self.apartment_aliases:
                continue
                
            aliases = self.apartment_aliases[apt_name]
            best_score = 0.0
            
            # Check each alias
            for alias in aliases.aliases:
                confidence = aliases.confidence_scores.get(alias, 0.5)
                
                # Exact match
                if alias in text_lower:
                    score = confidence
                else:
                    # Fuzzy match for longer aliases
                    if len(alias) > 4:
                        words_in_text = text_lower.split()
                        for word in words_in_text:
                            fuzzy_score = fuzz.ratio(alias, word)
                            if fuzzy_score >= 85:  # High similarity threshold
                                score = confidence * (fuzzy_score / 100.0)
                                break
                        else:
                            score = 0.0
                    else:
                        score = 0.0
                
                best_score = max(best_score, score)
            
            if best_score >= 0.6:  # Minimum confidence threshold
                mentioned[apt_name] = best_score
        
        return mentioned

    def _deduplicate_results(self, results: List[RedditSearchResult]) -> List[RedditSearchResult]:
        """Remove duplicate results based on comment/post ID"""
        seen = set()
        unique_results = []
        
        for result in results:
            key = f"{result.post_id}_{result.comment_id}"
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        return unique_results

    def _validate_results(self, results: List[RedditSearchResult], 
                         source_apartment: str) -> List[RedditSearchResult]:
        """Validate results using two-factor authentication"""
        validated_results = []
        
        for result in results:
            # Check if the comment actually mentions other apartments (cross-reference)
            other_apartments = [apt for apt in result.mentioned_apartments 
                             if apt != source_apartment]
            
            if other_apartments:
                # This is a cross-reference! Add to validation grid
                for mentioned_apt in other_apartments:
                    confidence = result.confidence_scores.get(mentioned_apt, 0.5)
                    
                    validation = CommentValidation(
                        comment_id="",
                        source_apartment=source_apartment,
                        mentioned_apartment=mentioned_apt,
                        comment_text=result.comment_text,
                        confidence_score=confidence,
                        validation_status="pending",
                        created_at=datetime.fromtimestamp(result.created_utc),
                        reddit_post_id=result.post_id,
                        reddit_comment_id=result.comment_id
                    )
                    
                    # Add to validation grid
                    self.grid_manager.add_comment_validation(validation)
                
                validated_results.append(result)
            
            # Also include comments that mention the source apartment itself
            elif source_apartment in result.mentioned_apartments:
                validated_results.append(result)
        
        return validated_results

    def search_all_apartments(self, days_back: int = 365) -> Dict[str, List[RedditSearchResult]]:
        """Search for all apartments and build validation grid"""
        all_results = {}
        
        logging.info(f"Starting comprehensive search for {len(self.apartments)} apartments")
        
        for i, apartment in enumerate(self.apartments):
            logging.info(f"Searching apartment {i+1}/{len(self.apartments)}: {apartment}")
            
            try:
                results = self.search_reddit_for_apartment(apartment, days_back)
                all_results[apartment] = results
                
                # Rate limiting between apartments
                time.sleep(2)
                
            except Exception as e:
                logging.error(f"Error searching for {apartment}: {e}")
                all_results[apartment] = []
        
        return all_results

    def generate_summary_report(self, search_results: Dict[str, List[RedditSearchResult]]) -> str:
        """Generate a comprehensive summary report"""
        report = []
        report.append("🏢 Enhanced Reddit Search Report")
        report.append("=" * 50)
        report.append("")
        
        total_results = sum(len(results) for results in search_results.values())
        apartments_with_results = sum(1 for results in search_results.values() if results)
        
        report.append(f"Total Results Found: {total_results}")
        report.append(f"Apartments with Results: {apartments_with_results}/{len(self.apartments)}")
        report.append("")
        
        # Top apartments by mention count
        apt_counts = [(apt, len(results)) for apt, results in search_results.items()]
        apt_counts.sort(key=lambda x: x[1], reverse=True)
        
        report.append("📊 Top Apartments by Mentions:")
        for i, (apt, count) in enumerate(apt_counts[:10]):
            if count > 0:
                report.append(f"{i+1:2d}. {apt}: {count} mentions")
        
        report.append("")
        
        # Two-factor authentication summary
        report.append("🔐 Two-Factor Authentication Grid:")
        cross_references = 0
        for results in search_results.values():
            for result in results:
                if len(result.mentioned_apartments) > 1:
                    cross_references += 1
        
        report.append(f"Cross-references found: {cross_references}")
        report.append("")
        
        # Sample high-confidence results
        high_conf_results = []
        for apt, results in search_results.items():
            for result in results:
                max_conf = max(result.confidence_scores.values()) if result.confidence_scores else 0
                if max_conf >= 0.8:
                    high_conf_results.append((apt, result, max_conf))
        
        high_conf_results.sort(key=lambda x: x[2], reverse=True)
        
        report.append("🎯 High-Confidence Results (sample):")
        for i, (apt, result, conf) in enumerate(high_conf_results[:5]):
            report.append(f"{i+1}. {apt} (confidence: {conf:.2f})")
            preview = result.comment_text[:100].replace('\n', ' ')
            report.append(f"   \"{preview}...\"")
            report.append("")
        
        return "\n".join(report)


def main():
    """Test the enhanced Reddit search system"""
    logging.basicConfig(level=logging.INFO)
    
    # Reddit credentials (read from environment or config file)
    reddit_creds = {
        'client_id': os.getenv('REDDIT_CLIENT_ID', 'your_client_id'),
        'client_secret': os.getenv('REDDIT_CLIENT_SECRET', 'your_client_secret'), 
        'user_agent': 'StingerSpaces/1.0 by YourUsername'
    }
    
    # Initialize searcher
    searcher = EnhancedRedditSearcher(reddit_creds)
    
    # Test search for one apartment
    test_apartment = "Square On 5th"
    print(f"Testing search for: {test_apartment}")
    
    results = searcher.search_reddit_for_apartment(test_apartment, days_back=30)
    
    print(f"\nFound {len(results)} results for {test_apartment}")
    
    for i, result in enumerate(results[:3]):  # Show first 3 results
        print(f"\n{i+1}. Score: {result.score}, Subreddit: r/{result.subreddit}")
        print(f"   Search term used: '{result.search_term_used}'")
        print(f"   Mentioned apartments: {result.mentioned_apartments}")
        print(f"   Confidence scores: {result.confidence_scores}")
        preview = result.comment_text[:150].replace('\n', ' ')
        print(f"   Text: \"{preview}...\"")
    
    # Print validation grid summary
    print("\n" + "="*50)
    searcher.grid_manager.print_grid_summary()


if __name__ == "__main__":
    main()
