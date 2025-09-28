#!/bin/bash

# StingerSpaces Data Health Check Script
# Runs comprehensive validation and reports on data quality

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${BLUE}🏠 StingerSpaces Data Health Check${NC}"
echo "=================================="
echo

# Check if apartment data file exists
APARTMENT_DATA="$PROJECT_ROOT/data/apartment_data.json"
if [ ! -f "$APARTMENT_DATA" ]; then
    echo -e "${RED}❌ Error: Apartment data file not found at $APARTMENT_DATA${NC}"
    exit 1
fi

echo -e "${BLUE}📊 Running data validation...${NC}"
echo

# Run data validation
cd "$SCRIPT_DIR"
if python3 data_validator.py "$APARTMENT_DATA"; then
    echo -e "${GREEN}✅ Data validation passed${NC}"
    VALIDATION_SUCCESS=true
else
    echo -e "${RED}❌ Data validation failed${NC}"
    VALIDATION_SUCCESS=false
fi

echo
echo -e "${BLUE}📈 Generating statistics...${NC}"

# Generate apartment statistics
python3 -c "
import json
import sys

try:
    with open('$APARTMENT_DATA', 'r') as f:
        apartments = json.load(f)
    
    total = len(apartments)
    with_coords = sum(1 for apt in apartments if 'coordinates' in apt and apt['coordinates'])
    with_proximities = sum(1 for apt in apartments if 'proximities' in apt and apt['proximities'])
    
    print(f'📊 Total apartments: {total}')
    print(f'🗺️  With coordinates: {with_coords}/{total} ({with_coords/total*100:.1f}%)')
    print(f'📍 With proximities: {with_proximities}/{total} ({with_proximities/total*100:.1f}%)')
    
    if with_coords < total:
        missing_coords = [apt['name'] for apt in apartments if 'coordinates' not in apt or not apt['coordinates']]
        print(f'❌ Missing coordinates: {missing_coords}')
    
    if with_proximities < total:
        missing_prox = [apt['name'] for apt in apartments if 'proximities' not in apt or not apt['proximities']]
        print(f'❌ Missing proximities: {missing_prox}')
        
except Exception as e:
    print(f'Error generating statistics: {e}')
    sys.exit(1)
"

echo
echo -e "${BLUE}🔍 Checking frontend sync...${NC}"

# Check if frontend data is in sync
FRONTEND_DATA="$PROJECT_ROOT/../frontend/apartment_data.json"
if [ -f "$FRONTEND_DATA" ]; then
    if cmp -s "$APARTMENT_DATA" "$FRONTEND_DATA"; then
        echo -e "${GREEN}✅ Frontend data is in sync${NC}"
    else
        echo -e "${YELLOW}⚠️  Frontend data is out of sync${NC}"
        echo "   Run: cp $APARTMENT_DATA $FRONTEND_DATA"
    fi
else
    echo -e "${YELLOW}⚠️  Frontend data file not found${NC}"
    echo "   Run: cp $APARTMENT_DATA $FRONTEND_DATA"
fi

echo
echo -e "${BLUE}🧪 Testing geocoding service...${NC}"

# Test geocoding service
python3 -c "
import requests
import time

def test_geocoding():
    url = 'https://nominatim.openstreetmap.org/search'
    params = {
        'q': '100 10th St NE, Atlanta, GA',
        'format': 'json',
        'limit': 1
    }
    headers = {
        'User-Agent': 'StingerSpaces/1.0 (test)'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data:
            print('✅ Geocoding service is responsive')
            return True
        else:
            print('⚠️  Geocoding service returned no results for test address')
            return False
    except Exception as e:
        print(f'❌ Geocoding service error: {e}')
        return False

test_geocoding()
"

echo
echo -e "${BLUE}📝 Health Check Summary${NC}"
echo "======================"

if [ "$VALIDATION_SUCCESS" = true ]; then
    echo -e "${GREEN}✅ Overall Status: HEALTHY${NC}"
    echo "   All data validation checks passed"
else
    echo -e "${RED}❌ Overall Status: NEEDS ATTENTION${NC}"
    echo "   Some validation checks failed - see details above"
fi

echo
echo -e "${BLUE}🛠️  Maintenance Commands:${NC}"
echo "   Recalculate proximities: python3 proximity_calculator.py"
echo "   Sync to frontend: cp $APARTMENT_DATA $FRONTEND_DATA"
echo "   Run validation: python3 data_validator.py $APARTMENT_DATA"
echo

if [ "$VALIDATION_SUCCESS" = false ]; then
    exit 1
fi
