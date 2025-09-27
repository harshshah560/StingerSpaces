#!/usr/bin/env python3
"""
Check Google Images page source to find the right patterns
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import re

def analyze_page_source():
    """Analyze Google Images page source to find image URL patterns"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        query = "Square on 5th Atlanta"
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}&tbm=isch"
        
        driver.get(search_url)
        time.sleep(3)
        
        page_source = driver.page_source
        
        print(f"🔍 Analyzing page source for image URL patterns...")
        print(f"📏 Page source length: {len(page_source)} characters")
        
        # Look for various URL patterns
        patterns_to_test = [
            (r'"ou":"([^"]+)"', "Original URL pattern"),
            (r'"ow":(\d+),"oh":(\d+)', "Dimensions pattern"),
            (r'https://[^"]*\.jpg[^"]*', "Direct .jpg URLs"),
            (r'https://[^"]*\.jpeg[^"]*', "Direct .jpeg URLs"),
            (r'https://[^"]*\.png[^"]*', "Direct .png URLs"),
            (r'https://[^"]*\.webp[^"]*', "Direct .webp URLs"),
            (r'https://encrypted-tbn0\.gstatic\.com/images[^"]*', "Gstatic thumbnails"),
        ]
        
        for pattern, description in patterns_to_test:
            matches = re.findall(pattern, page_source)
            print(f"\n{description}:")
            print(f"   Found {len(matches)} matches")
            if matches:
                for i, match in enumerate(matches[:3]):  # Show first 3
                    if isinstance(match, tuple):
                        print(f"   [{i+1}] {match}")
                    else:
                        print(f"   [{i+1}] {match[:80]}...")
        
        # Also check for JSON data structures
        if '"data"' in page_source:
            print(f"\n✅ Found JSON data structures in page source")
        
        # Look for specific Google Images metadata
        if 'AF_initDataCallback' in page_source:
            print(f"✅ Found AF_initDataCallback (Google's data structure)")
            
        # Try to find any URLs that look like high-quality images
        all_urls = re.findall(r'https://[^\s"<>]+', page_source)
        image_urls = [url for url in all_urls if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp'])]
        
        print(f"\n📸 Found {len(image_urls)} potential image URLs")
        for i, url in enumerate(image_urls[:5]):
            print(f"   [{i+1}] {url[:80]}...")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    analyze_page_source()
