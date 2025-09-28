#!/usr/bin/env python3
"""
Google Places Photo Updater for StingerSpaces
Updates apartment listings with Google Places API photos and handles user-generated listings
"""

import os
import requests
import json
import base64
from io import BytesIO
from PIL import Image
import psycopg2
from psycopg2.extras import RealDictCursor
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
GOOGLE_PLACES_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY', 'AIzaSyBv7At7YSjsUBgGUAJMd6_o-MTH1AB9QTE')
SUPABASE_DB_URL = os.getenv('SUPABASE_DB_URL')

# Default placeholder image (base64 encoded simple apartment icon)
PLACEHOLDER_IMAGE_B64 = """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"""

def get_database_connection():
    """Connect to Supabase PostgreSQL database"""
    return psycopg2.connect(SUPABASE_DB_URL)

def search_google_places(apartment_name, address):
    """Search for apartment using Google Places API"""
    query = f"{apartment_name} {address}"
    
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        'query': query,
        'key': GOOGLE_PLACES_API_KEY,
        'type': 'lodging'
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == 'OK' and data['results']:
            return data['results'][0]  # Return first result
        
    except Exception as e:
        print(f"Error searching Google Places for {apartment_name}: {e}")
    
    return None

def get_place_photo(photo_reference):
    """Get photo from Google Places API"""
    if not photo_reference:
        return None
        
    url = "https://maps.googleapis.com/maps/api/place/photo"
    params = {
        'photoreference': photo_reference,
        'maxwidth': 400,
        'key': GOOGLE_PLACES_API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        # Convert to base64
        img = Image.open(BytesIO(response.content))
        img = img.resize((400, 300), Image.Resampling.LANCZOS)
        
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return img_base64
        
    except Exception as e:
        print(f"Error fetching photo: {e}")
        return None

def update_apartments_with_photos():
    """Update existing apartments with Google Places photos"""
    conn = get_database_connection()
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get apartments without photos or user-generated ones
            cur.execute("""
                SELECT name, formatted_address, user_generated, image_base64
                FROM apartments 
                WHERE image_base64 IS NULL OR user_generated = true
                ORDER BY name
            """)
            
            apartments = cur.fetchall()
            
            for apt in apartments:
                print(f"Processing {apt['name']}...")
                
                if apt['user_generated']:
                    # User-generated apartment - use placeholder
                    print(f"  Using placeholder image for user-generated apartment")
                    
                    cur.execute("""
                        UPDATE apartments 
                        SET image_base64 = %s 
                        WHERE name = %s
                    """, (PLACEHOLDER_IMAGE_B64, apt['name']))
                    
                else:
                    # Try to get from Google Places
                    place_data = search_google_places(apt['name'], apt['formatted_address'])
                    
                    if place_data and 'photos' in place_data:
                        photo_ref = place_data['photos'][0]['photo_reference']
                        print(f"  Found Google Places photo")
                        
                        photo_base64 = get_place_photo(photo_ref)
                        
                        if photo_base64:
                            cur.execute("""
                                UPDATE apartments 
                                SET image_base64 = %s, google_place_photo_reference = %s
                                WHERE name = %s
                            """, (photo_base64, photo_ref, apt['name']))
                            
                            print(f"  Updated with Google photo")
                        else:
                            print(f"  Failed to fetch photo, using placeholder")
                            cur.execute("""
                                UPDATE apartments 
                                SET image_base64 = %s 
                                WHERE name = %s
                            """, (PLACEHOLDER_IMAGE_B64, apt['name']))
                    else:
                        print(f"  No Google Places data found, using placeholder")
                        cur.execute("""
                            UPDATE apartments 
                            SET image_base64 = %s 
                            WHERE name = %s
                        """, (PLACEHOLDER_IMAGE_B64, apt['name']))
                
                conn.commit()
                
                # Rate limiting
                time.sleep(0.5)
                
    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()
    finally:
        conn.close()

def update_price_ranges_from_reviews():
    """Update apartment price ranges based on review data"""
    conn = get_database_connection()
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                UPDATE apartments 
                SET price_range = CASE 
                    WHEN avg_monthly_rent IS NOT NULL THEN 
                        '$' || FLOOR(avg_monthly_rent)::text || ' - $' || CEIL(avg_monthly_rent * 1.2)::text
                    ELSE price_range 
                END
                WHERE avg_monthly_rent IS NOT NULL
            """)
            
            updated_count = cur.rowcount
            conn.commit()
            
            print(f"Updated price ranges for {updated_count} apartments based on review data")
            
    except Exception as e:
        print(f"Error updating price ranges: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("Starting apartment photo and price update...")
    
    print("\n1. Updating apartments with photos...")
    update_apartments_with_photos()
    
    print("\n2. Updating price ranges from review data...")
    update_price_ranges_from_reviews()
    
    print("\nUpdate completed!")
