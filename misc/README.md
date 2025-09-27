# Georgia Tech Student Housing Scraper

## Overview
A daily apartment scraper designed to extract Georgia Tech student housing data from apartments.com without triggering IP bans. Outputs clean JSON data ready for Firebase database import and OpenStreetMap API integration.

## Features
- **Rate Limited**: 3-second delays between requests to avoid IP bans
- **Accurate Pricing**: Extracts real prices from FAQ data, not misleading budget categories
- **Database Ready**: Structured JSON output with all necessary fields
- **OpenStreetMap Compatible**: Properly formatted addresses for geocoding
- **Anti-Detection**: Headless Chrome with realistic user agent and anti-bot measures
- **Image Scraping**: Automatically gets exterior images from Bing Images
- **Cloud Optimized**: Base64 encoded images for direct database storage

## Output Structure
Each apartment listing contains:
```json
{
  "name": "Apartment Name",
  "street_address": "123 Main St",
  "city": "Atlanta", 
  "state": "GA",
  "zip_code": "30318",
  "formatted_address": "123 Main St, Atlanta, GA 30318",
  "phone": "+1-123-456-7890",
  "url": "https://www.apartments.com/...",
  "price_range": "$1,200 - $1,800",
  "bed_range": "1-4 Beds",
  "image_base64": "iVBORw0KGgoAAAANSUhEUgAA...", 
  "scraped_at": "2025-09-26T20:53:16.784896"
}
```

## Files
- `daily_apartment_scraper.py` - Main scraper script
- `apartment_data.json` - Output file with all apartment data
- `setup_daily_scraper.sh` - Cron job setup for daily execution

## Usage

### Manual Run
```bash
python daily_apartment_scraper.py
```

### Daily Automated Run
```bash
chmod +x setup_daily_scraper.sh
./setup_daily_scraper.sh
```

## Database Integration
The JSON output is structured for direct import into Firebase or any other database system. Each record contains all necessary fields for apartment listings with proper data types and formatting.

## Address Format
Addresses are formatted specifically for OpenStreetMap API compatibility:
- Format: "Street Address, City, State Zipcode"
- Example: "1011 Northside Dr NW, Atlanta, GA 30318"

## Image Handling
- **Source**: Bing Images search for apartment exteriors
- **Format**: Base64 encoded for direct database storage
- **Size Limit**: 1MB maximum per image
- **Display**: `<img src="data:image/jpeg;base64,{image_base64}" />`

## Rate Limiting
- 3-second delay between requests (apartments + images)
- Designed for once-daily execution
- Respectful crawling to avoid IP bans

## Current Results
Successfully extracts 17 Georgia Tech student housing listings with accurate pricing, availability data, and exterior images.
