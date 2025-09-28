# StingerSpaces Financial Information Feature

## Overview
Added comprehensive financial information tracking to reviews to make StingerSpaces stand out by showing real cost data from residents.

## Database Changes (ADD_FINANCIAL_COLUMNS.sql)

### New Columns in `apartment_reviews`:
- `monthly_rent` (DECIMAL): Monthly rent per person in USD
- `hidden_fees` (DECIMAL): Hidden fees per month (admin fees, etc.)
- `utilities_cost` (DECIMAL): Monthly utilities cost 
- `parking_cost` (DECIMAL): Monthly parking cost (0 if free)

### New Columns in `apartments`:
- `avg_monthly_rent` (DECIMAL): Calculated average from reviews
- `avg_hidden_fees` (DECIMAL): Calculated average from reviews
- `avg_utilities_cost` (DECIMAL): Calculated average from reviews
- `avg_parking_cost` (DECIMAL): Calculated average from reviews
- `google_place_photo_reference` (TEXT): Google Places photo reference

### Automatic Triggers:
- `update_apartment_averages()` function automatically calculates averages when reviews are added/updated/deleted

## Frontend Changes

### apartment-details.html:
- **Financial Summary Section**: Shows average costs with prominent "Total Monthly" calculation
- **Individual Review Financial Info**: Each review shows rent, fees, utilities, and parking in a compact grid
- **Improved Styling**: Financial information has distinct styling with Georgia Tech colors

### apartment-review.html:
- **Financial Information Form**: 4 input fields for monthly costs
- **User-Friendly Layout**: Grid layout with helpful placeholders and descriptions

### apartment-review.js:
- **Data Collection**: Captures financial information from form inputs
- **Validation**: Handles empty/null values appropriately
- **Submission**: Includes financial data in review submission to Supabase

## Scripts

### update_apartment_photos.py:
- **Google Places Integration**: Fetches photos for existing apartments
- **Placeholder Images**: Uses apartment icon for user-generated listings
- **Price Updates**: Updates price ranges based on review averages
- **Rate Limiting**: Respects Google API limits

## Key Features

### Cost Transparency:
- Real rent costs from actual residents
- Hidden fees disclosure
- Utilities and parking cost breakdown
- Total monthly cost calculation

### Visual Impact:
- Prominent financial summary with total cost highlight
- Clean, professional styling matching GT branding
- Mobile-responsive design

### User Experience:
- Optional financial information (not required)
- Clear labels and helpful placeholder text
- Automatic averaging across all reviews

## Installation Steps

1. **Run SQL Migration**:
   ```sql
   -- Copy and paste ADD_FINANCIAL_COLUMNS.sql into Supabase SQL Editor
   ```

2. **Install Python Dependencies**:
   ```bash
   pip install -r requirements_photos.txt
   ```

3. **Set Environment Variables**:
   ```bash
   export GOOGLE_PLACES_API_KEY="your_api_key"
   export SUPABASE_DB_URL="your_supabase_db_url"
   ```

4. **Update Photos** (Optional):
   ```bash
   python scripts/update_apartment_photos.py
   ```

## Competitive Advantage

This feature makes StingerSpaces unique by providing:
- **Real cost data** from actual residents
- **Comprehensive financial picture** beyond just rent
- **Transparency** about hidden fees and true costs
- **Data-driven insights** for student housing decisions

The financial information becomes the standout feature that sets StingerSpaces apart from other housing platforms that only show basic rent ranges.
