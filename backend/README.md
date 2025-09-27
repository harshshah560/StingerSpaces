# StingerSpaces Backend

This directory contains all the backend code for the StingerSpaces apartment search platform.

## Directory Structure

```
backend/
├── src/                    # Main source code
│   ├── reddit_ai.py       # Reddit analysis and AI summarization
│   ├── alias_utils.py     # Apartment name alias generation utilities
│   ├── apt_alias.py       # Apartment alias processing
│   ├── daily_apartment_scraper.py  # Web scraping for apartment data
│   ├── upload_apartments.py        # Supabase database uploader
│   ├── reddit_scanner.py           # Reddit scanning utilities
│   ├── comment_scanner.py          # Comment processing
│   └── analyze_google_source.py    # Google source analysis
├── data/                   # Data files
│   └── apartment_data.json # Scraped apartment listings
├── scripts/                # Automation scripts
│   └── run_daily_job.sh   # Daily scraping and upload job
├── logs/                   # Log files
├── output/                 # Generated output files
│   ├── apartments_with_consensus.json  # Final results with Reddit analysis
│   └── comments.txt       # Extracted comments
└── README.md              # This file
```

## Key Components

### reddit_ai.py
The main Reddit analysis script that:
- Automatically generates smart aliases for apartment names
- Searches Reddit using multiple query strategies
- Filters comments from the last 5 years
- Uses AI to filter relevant apartment discussions
- Generates comprehensive summaries of resident experiences

### daily_apartment_scraper.py
Web scraper that collects apartment listing data from various sources.

### upload_apartments.py
Uploads processed apartment data to Supabase database.

## Usage

### Running Reddit Analysis
```bash
cd backend/src
python reddit_ai.py
```

### Running Daily Jobs
```bash
cd backend/scripts
./run_daily_job.sh
```

## Environment Variables
Make sure the `.env` file in the project root contains:
- `REDDIT_CLIENT_ID`
- `REDDIT_CLIENT_SECRET` 
- `REDDIT_USER_AGENT`
- `OPENAI_API_KEY`
- Supabase credentials

## Output
- Processed apartment data: `backend/data/apartment_data.json`
- Reddit analysis results: `backend/output/apartments_with_consensus.json`
- Logs: `backend/logs/`
