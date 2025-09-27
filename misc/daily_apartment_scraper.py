#!/usr/bin/env python3
"""
Daily Georgia Tech Student Housing Scraper
Designed to run once per day to avoid IP bans
Outputs structured data for Firebase database updates and OpenStreetMap API compatibility
"""

import json
import re
import time
import base64
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Target URL for Georgia Tech student housing listings
APARTMENTS_URL = "https://www.apartments.com/off-campus-housing/ga/atlanta/georgia-institute-of-technology/student-housing-per-person/"

def get_chrome_driver():
    """
    Create and configure a Chrome WebDriver instance
    Uses headless mode and anti-detection settings to avoid being blocked
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run browser in background (no GUI)
    chrome_options.add_argument("--no-sandbox")  # Bypass OS security restrictions
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Hide automation flags
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])  # Remove automation switches
    chrome_options.add_experimental_option('useAutomationExtension', False)  # Disable automation extension
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")  # Set realistic user agent
    
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def format_address_for_openstreetmap(street, city, state, zipcode):
    """
    Format address components for OpenStreetMap API compatibility
    Returns a clean, standardized address string
    """
    # Remove any extra whitespace and combine components
    street = street.strip() if street else ""
    city = city.strip() if city else ""
    state = state.strip() if state else ""
    zipcode = zipcode.strip() if zipcode else ""
    
    # Create full address in standard format: "Street, City, State Zipcode"
    address_parts = []
    if street:
        address_parts.append(street)
    if city:
        address_parts.append(city)
    if state and zipcode:
        address_parts.append(f"{state} {zipcode}")
    elif state:
        address_parts.append(state)
    
    return ", ".join(address_parts)

def extract_apartment_basic_data(apartment_json):
    """
    Extract basic apartment information from JSON-LD structured data
    Returns a dictionary with apartment details or None if extraction fails
    """
    try:
        # Extract apartment name
        name = apartment_json.get('name', 'Unknown Apartment')
        
        # Extract apartment listing URL
        url = apartment_json.get('url', '')
        
        # Extract address components from nested Address object
        address_data = apartment_json.get('Address', {})
        if isinstance(address_data, dict):
            street = address_data.get('streetAddress', '')
            city = address_data.get('addressLocality', '')
            state = address_data.get('addressRegion', '')
            zipcode = address_data.get('postalCode', '')
            
            # Format address for OpenStreetMap API compatibility
            formatted_address = format_address_for_openstreetmap(street, city, state, zipcode)
        else:
            formatted_address = 'Address not available'
            street = city = state = zipcode = ''
        
        # Extract contact phone number
        phone = apartment_json.get('telephone', 'Phone not available')
        
        # Return structured data dictionary
        return {
            'name': name,
            'street_address': street,
            'city': city,
            'state': state,
            'zip_code': zipcode,
            'formatted_address': formatted_address,  # For OpenStreetMap API
            'phone': phone,
            'url': url,
            'price_range': None,  # Will be filled in detailed scraping
            'bed_range': None,    # Will be filled in detailed scraping
            'image_base64': None, # Will be filled with Google Images scraping
            'scraped_at': datetime.now().isoformat()  # Timestamp for database tracking
        }
        
    except Exception as e:
        print(f"Error extracting apartment data: {e}")
        return None

def scrape_main_apartment_listings():
    """
    Scrape the main Georgia Tech student housing page to get all apartment listings
    Returns a list of apartment dictionaries with basic information
    """
    print(f"Scraping main listing page: {APARTMENTS_URL}")
    
    # Create Chrome driver instance
    driver = get_chrome_driver()
    
    try:
        print("Loading main page...")
        driver.get(APARTMENTS_URL)
        time.sleep(3)  # Wait for page to load completely
        
        # Find all JSON-LD script tags that contain structured data
        script_tags = driver.find_elements(By.XPATH, "//script[@type='application/ld+json']")
        print(f"Found {len(script_tags)} JSON-LD script tags")
        
        apartments = []  # List to store apartment data
        
        # Process each JSON-LD script tag
        for script_index, script in enumerate(script_tags):
            try:
                # Extract JSON content from script tag
                json_content = script.get_attribute('innerHTML')
                data = json.loads(json_content)
                
                # Handle different JSON structures (list or single object)
                if isinstance(data, list):
                    # Process each item in the list
                    for item in data:
                        if isinstance(item, dict) and 'about' in item:
                            about_items = item.get('about', [])
                            # Look for apartment complex data in 'about' section
                            for about_item in about_items:
                                if about_item.get('@type') == 'ApartmentComplex':
                                    apartment = extract_apartment_basic_data(about_item)
                                    if apartment:
                                        apartments.append(apartment)
                elif isinstance(data, dict) and 'about' in data:
                    # Process single object with 'about' section
                    about_items = data.get('about', [])
                    for about_item in about_items:
                        if about_item.get('@type') == 'ApartmentComplex':
                            apartment = extract_apartment_basic_data(about_item)
                            if apartment:
                                apartments.append(apartment)
                                
            except json.JSONDecodeError as e:
                print(f"Invalid JSON in script {script_index + 1}: {e}")
                continue
            except Exception as e:
                print(f"Error processing script {script_index + 1}: {e}")
                continue
                
        # Remove duplicate apartments based on URL
        unique_apartments = []
        seen_urls = set()
        
        for apt in apartments:
            if apt['url'] not in seen_urls:
                unique_apartments.append(apt)
                seen_urls.add(apt['url'])
        
        print(f"Found {len(unique_apartments)} unique apartment listings")
        return unique_apartments
        
    except Exception as e:
        print(f"Error scraping main listings: {e}")
        return []
    finally:
        # Always close the browser to free resources
        driver.quit()

def scrape_google_image(apartment_name, city="Atlanta"):
    """
    Scrape the first exterior image from Google Images for the apartment
    Returns base64 encoded image data for cloud database storage
    """
    driver = get_chrome_driver()
    
    try:
        # Create search query for apartment exterior
        search_query = f"{apartment_name} {city} apartment building"
        # Use Bing Images instead - easier to scrape and more reliable
        bing_images_url = f"https://www.bing.com/images/search?q={search_query}"
        
        print(f"    Searching Bing Images for: {search_query}")
        driver.get(bing_images_url)
        time.sleep(3)  # Wait for images to load
        
        # Find the first Bing image result
        try:
            # Bing Images specific selectors
            bing_selectors = [
                'img.mimg',  # Main Bing image selector
                '.iusc img', # Image result container
                'img[src*="mm.bing.net"]',  # Bing hosted thumbnails
                '.imgpt img'  # Image point container
            ]
            
            image_url = None
            for selector in bing_selectors:
                try:
                    img_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if img_elements:
                        # Get the first image that's not a Bing UI element
                        for img in img_elements:
                            src = img.get_attribute('src')
                            if src and src.startswith('http'):
                                # Skip Bing UI elements
                                if not any(skip in src for skip in ['bing.com/th/id', 'bing.net/th']):
                                    continue
                                image_url = src
                                break
                        if image_url:
                            break
                except:
                    continue
            
            # Fallback: get any reasonable image from the page
            if not image_url:
                img_elements = driver.find_elements(By.CSS_SELECTOR, 'img')
                for img in img_elements:
                    src = img.get_attribute('src')
                    if (src and src.startswith('http') and 
                        ('bing.net/th' in src or 'bing.com/th' in src) and
                        len(src) > 50):
                        image_url = src
                        break
                            
        except Exception as e:
            print(f"    Error finding images: {e}")
            image_url = None
        
        if not image_url:
            print(f"    No suitable image found for {apartment_name}")
            return None
        
        # Download and convert image to base64
        try:
            print(f"    Downloading image: {image_url[:50]}...")
            response = requests.get(image_url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            })
            
            if response.status_code == 200:
                # Check image size to avoid huge files (limit to 1MB)
                if len(response.content) > 1024 * 1024:  # 1MB limit
                    print(f"    Image too large ({len(response.content)} bytes), skipping")
                    return None
                
                # Convert to base64 for database storage
                image_base64 = base64.b64encode(response.content).decode('utf-8')
                print(f"    Image converted to base64 ({len(image_base64)} chars, ~{len(response.content)/1024:.0f}KB)")
                return image_base64
            else:
                print(f"    Failed to download image: Status {response.status_code}")
                return None
                
        except Exception as e:
            print(f"    Error downloading image: {e}")
            return None
            
    except Exception as e:
        print(f"    Error scraping Google Images: {e}")
        return None
    finally:
        driver.quit()

def scrape_detailed_apartment_info(apartment_dict):
    """
    Scrape individual apartment page for detailed pricing and bedroom information
    Takes an apartment dictionary and adds detailed pricing/bedroom data
    """
    # Create new Chrome driver for this apartment
    driver = get_chrome_driver()
    
    try:
        print(f"  Scraping details for: {apartment_dict['name']}")
        
        # Load the individual apartment page
        driver.get(apartment_dict['url'])
        time.sleep(3)  # Wait for page to fully load
        
        # Wait for page body to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        price_text = None
        bed_info = None
        
        # METHOD 1: Extract from JSON-LD FAQ data (most accurate pricing source)
        try:
            script_tags = driver.find_elements(By.XPATH, "//script[@type='application/ld+json']")
            
            for script in script_tags:
                json_content = script.get_attribute('innerHTML')
                data = json.loads(json_content)
                
                # Look for FAQ structured data which contains accurate pricing
                if isinstance(data, dict) and data.get('@type') == 'FAQPage':
                    main_entity = data.get('mainEntity', [])
                    
                    # Search through FAQ questions and answers
                    for faq_item in main_entity:
                        if 'acceptedAnswer' in faq_item:
                            answer_text = faq_item['acceptedAnswer'].get('text', '')
                            
                            # Extract price range from FAQ text using regex
                            if not price_text:
                                price_match = re.search(r'\$[\d,]+(?:/mo\.?)?\s*(?:to|-)?\s*\$[\d,]+(?:/mo\.?)?', answer_text)
                                if price_match:
                                    # Clean up the price text (remove /mo suffixes, standardize format)
                                    price_text = price_match.group().replace('/mo.', '').replace('/mo', '').replace(' to ', ' - ')
                            
                            # Extract bedroom information from FAQ text
                            if not bed_info:
                                bed_match = re.search(r'(?:one to four|1-4|studio to \d+|\d+ to \d+)\s*bedroom', answer_text, re.IGNORECASE)
                                if bed_match:
                                    bed_range = bed_match.group()
                                    # Convert text descriptions to standard format
                                    if 'one to four' in bed_range.lower():
                                        bed_info = '1-4 Beds'
                                    else:
                                        bed_info = bed_range
                        
        except Exception as e:
            print(f"    JSON-LD extraction error: {e}")
        
        # METHOD 2: Extract from CSS selectors (backup method)
        if not price_text:
            # List of CSS selectors to try for price information (in priority order)
            price_selectors = [
                '.rentInfoDetail',  # Primary selector with accurate pricing
                '.rentInfoDetail .rentRangeContainer',
                '.pricingContainer .rentRange',
                '.rentRange',
                '.priceRange', 
                '.pricing .price',
                '[data-tab-content-id="all"] .rentRange',
                '.mortar-wrapper .rentRange',
                '.detailsWrapper .rentRange'
            ]
            
            # Try each selector until we find pricing data
            for selector in price_selectors:
                try:
                    price_element = driver.find_element(By.CSS_SELECTOR, selector)
                    price_text = price_element.text.strip()
                    # Validate that we found actual price data (contains $, not budget categories)
                    if price_text and '$' in price_text and 'Under' not in price_text and 'Budget' not in price_text:
                        break
                    else:
                        price_text = None  # Reset if not valid price data
                except:
                    continue
        
        # METHOD 3: Extract bedroom info from CSS selectors
        if not bed_info:
            # List of CSS selectors to try for bedroom information
            bed_selectors = [
                '.rentInfoDetail',  # Also contains bed info like "1 - 4 bd"
                '.bedRange',
                '.bed-range',
                '.bedroomBathroom .bedroom',
                '.detailsWrapper .bedRange',
                '.mortar-wrapper .bedRange'
            ]
            
            # Try each selector to find bedroom information
            for selector in bed_selectors:
                try:
                    bed_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for bed_element in bed_elements:
                        text = bed_element.text.strip()
                        # Look for bedroom patterns like "1 - 4 bd" or "Studio - 2 Beds"
                        if re.search(r'(?:\d+\s*-\s*\d+|studio)\s*(?:bd|bed)', text, re.IGNORECASE):
                            bed_info = text
                            break
                    if bed_info:
                        break
                except:
                    continue
        
        # METHOD 4: Parse page source as last resort
        if not price_text or not bed_info:
            try:
                page_source = driver.page_source
                
                # Search for price patterns in page source
                if not price_text:
                    price_patterns = [
                        r'\$[\d,]+\s*-\s*\$[\d,]+',  # Format: $1,200 - $1,800
                        r'\$[\d,]+(?:\s*per month)?'  # Format: $1,500 per month
                    ]
                    
                    for pattern in price_patterns:
                        matches = re.findall(pattern, page_source)
                        # Filter out budget category prices by checking surrounding context
                        valid_matches = []
                        for match in matches:
                            # Check context around the price to avoid budget categories
                            match_index = page_source.find(match)
                            surrounding_text = page_source[max(0, match_index-100):match_index+100]
                            if 'Under' not in surrounding_text and 'Budget' not in surrounding_text:
                                valid_matches.append(match)
                        
                        if valid_matches:
                            price_text = valid_matches[0]
                            break
                
                # Search for bedroom patterns in page source
                if not bed_info:
                    bed_patterns = [
                        r'(?:Studio|[\d]+)\s*-\s*[\d]+\s*Bed(?:room)?s?',
                        r'(?:Studio|[\d]+)\s*Bed(?:room)?s?'
                    ]
                    
                    for pattern in bed_patterns:
                        matches = re.findall(pattern, page_source, re.IGNORECASE)
                        if matches:
                            bed_info = matches[0]
                            break
                        
            except Exception as e:
                print(f"    Page source parsing error: {e}")
        
        # Update apartment dictionary with extracted information
        apartment_dict['price_range'] = price_text if price_text else 'Price not available'
        apartment_dict['bed_range'] = bed_info if bed_info else 'Bed info not available'
        
        print(f"    Price: {apartment_dict['price_range']}, Beds: {apartment_dict['bed_range']}")
        return apartment_dict
        
    except Exception as e:
        print(f"    Error scraping {apartment_dict['name']}: {e}")
        # Set error values if scraping fails
        apartment_dict['price_range'] = 'Error retrieving price'
        apartment_dict['bed_range'] = 'Error retrieving bed info'
        return apartment_dict
    finally:
        # Always close the browser to free resources
        driver.quit()

def save_data_to_file(apartments_data, filename="apartment_data.json"):
    """
    Save apartment data to a JSON file for database import
    Creates clean JSON format only
    """
    try:
        # Save as clean JSON file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(apartments_data, f, indent=2, ensure_ascii=False)
            
        print(f"Data saved to {filename}")
        
    except Exception as e:
        print(f"Error saving data to file: {e}")

def main():
    """
    Main function that orchestrates the entire scraping process
    Designed to run once daily to avoid IP bans
    """
    print("Starting Georgia Tech Student Housing Scraper")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    # Step 1: Scrape main listings page for basic apartment information
    apartments = scrape_main_apartment_listings()
    
    if not apartments:
        print("No apartments found! Exiting.")
        return
    
    print(f"\nFound {len(apartments)} apartments. Extracting detailed information...")
    print("=" * 80)
    
    # Step 2: Scrape detailed information for each apartment
    detailed_apartments = []
    for i, apt in enumerate(apartments, 1):
        print(f"\n[{i}/{len(apartments)}] Processing: {apt['name']}")
        
        # Step 2a: Scrape detailed info for this apartment
        detailed_apt = scrape_detailed_apartment_info(apt)
        
        # Step 2b: Scrape Google Images for apartment exterior
        print(f"    Getting exterior image from Google Images...")
        image_base64 = scrape_google_image(apt['name'], apt['city'])
        detailed_apt['image_base64'] = image_base64
        
        detailed_apartments.append(detailed_apt)
        
        # Add delay between requests to be respectful to both servers
        print(f"    Waiting 3 seconds before next request...")
        time.sleep(3)
    
    # Step 3: Save data to file for review and database import
    print(f"\nSaving data to file...")
    save_data_to_file(detailed_apartments)
    
    # Step 4: Display summary
    print(f"\nSCRAPING COMPLETED!")
    print(f"Total listings processed: {len(detailed_apartments)}")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Data saved to apartment_data.json")
    print("\nReady for Firebase database import!")

# Entry point - run the scraper when script is executed directly
if __name__ == "__main__":
    main()
