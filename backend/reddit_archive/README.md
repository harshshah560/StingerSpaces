# Reddit Integration Archive

This folder contains the Reddit-based comment analysis and consensus system that was developed but later archived due to insufficient Reddit post volume for reliable apartment reviews.

## 📁 Archived Components

### Core Reddit Analysis System
- **`enhanced_reddit_ai.py`** - Main orchestration system for Reddit comment analysis
- **`enhanced_reddit_searcher.py`** - Multi-pass Reddit search with alias matching
- **`reddit_scanner.py`** - Basic Reddit scanning utilities
- **`comment_scanner.py`** - Comment processing and validation

### Database & Validation
- **`supabase_grid_manager.py`** - Two-factor authentication grid for comment validation
- **`validation_grid.json`** - Local storage for comment validation data
- **`apartments_with_consensus.json`** - Generated Reddit consensus data

### Setup & Documentation
- **`SUPABASE_SETUP_GUIDE.md`** - Complete guide for setting up Supabase backend

## 🔧 Key Features (Archived)

### Advanced Alias System
- Generated comprehensive aliases for apartment names
- Handled abbreviations, misspellings, and short forms
- University-configurable for different locations

### Two-Factor Validation
- Cross-reference validation between apartment mentions
- Confidence scoring for comment relevance
- Supabase integration for scalable storage

### Multi-Pass Search Strategy
- Searched multiple subreddits (r/gatech, r/Atlanta, etc.)
- Context-aware filtering for housing-related discussions
- Rate-limited API calls with error handling

## 🚫 Why Archived?

The Reddit integration was removed from the main application because:
1. **Low post volume** - Insufficient Reddit discussions about specific apartments
2. **Data quality** - Reddit comments were too sparse for reliable consensus
3. **Complexity vs. value** - The sophisticated system wasn't justified by results

## 🔄 Future Integration

If Reddit activity increases or you want to reintegrate this system:

1. **Restore files** to `backend/src/`
2. **Install dependencies**: `pip install praw supabase fuzzywuzzy python-levenshtein`
3. **Configure Reddit API** credentials in `.env`
4. **Set up Supabase** following the included guide
5. **Update imports** in main application files

## 📊 System Requirements (If Restored)

### Python Dependencies
```bash
pip install praw supabase fuzzywuzzy python-levenshtein phonetics
```

### Environment Variables
```env
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT="YourApp/1.0 by YourUsername"
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_key
```

### Database Setup
The system used both local JSON storage and optional Supabase PostgreSQL backend for scalability.

---

**Note**: This code represents a fully functional, production-ready Reddit analysis system that could be valuable for other apartment/housing analysis projects or if Reddit activity for this use case increases in the future.
