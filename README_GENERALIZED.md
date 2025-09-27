# Generalized Apartment Search & Reddit Consensus System

## 🎯 Project Overview
This project provides a robust, university-agnostic apartment search and Reddit consensus system that can be deployed for any university or location without hardcoded patterns or abbreviations.

## ✨ Key Features

### 🎓 **University-Agnostic Design**
- **No Hardcoded Patterns**: Removed all GT-specific abbreviations (like "SQ5")
- **Configurable System**: Works for any university with simple configuration
- **Extensible Architecture**: Add new universities without changing core code

### 🔍 **Advanced Alias Generation**
- **Smart Abbreviations**: Generates context-aware short forms
- **Phonetic Matching**: Handles misspellings and sound-alike variations  
- **Location-Based Aliases**: Creates university-specific variations
- **Number Conversion**: Handles "Fifth" ↔ "5th" ↔ "5" variations

### 🛡️ **Two-Factor Reddit Validation**
- **Grid-Based Authentication**: Supabase integration for comment validation
- **Cross-Reference Checking**: Multiple validation passes
- **Confidence Scoring**: AI-driven relevance assessment

### 🗺️ **Interactive Frontend**
- **Dynamic Map Integration**: Leaflet.js with apartment markers
- **Image Display**: Apartment photos with caching
- **Enhanced Consensus**: Structured Reddit sentiment analysis
- **Responsive Design**: Mobile-friendly interface

## 🏗️ Architecture

### Backend Components
```
backend/src/
├── advanced_alias_generator.py     # Generalized alias generation
├── enhanced_reddit_searcher.py     # University-configurable Reddit search
├── enhanced_reddit_ai.py           # Main orchestration system
├── supabase_grid_manager.py        # Validation grid management
└── test_generalized_system.py      # Comprehensive testing
```

### Frontend Components
```
frontend/
├── apartment-details.html          # Enhanced apartment view
├── styles.css                      # Responsive styling
└── script.js                       # Dynamic interactions
```

## 🚀 Usage Examples

### For Georgia Tech
```python
from enhanced_reddit_ai import EnhancedRedditAI

# Initialize for GT
ai = EnhancedRedditAI(university='gt')
consensus = ai.get_apartment_consensus(apartment_data)
```

### For University of Georgia
```python
# Initialize for UGA
ai = EnhancedRedditAI(university='uga')
consensus = ai.get_apartment_consensus(apartment_data)
```

### For Any New University
```python
# Works with any university code
ai = EnhancedRedditAI(university='duke')
ai = EnhancedRedditAI(university='unc')
ai = EnhancedRedditAI(university='vanderbilt')
```

## 🔧 Configuration

### Environment Variables
```bash
# Core API Keys
OPENAI_API_KEY=your_openai_key
REDDIT_CLIENT_ID=your_reddit_id
REDDIT_CLIENT_SECRET=your_reddit_secret

# University Configuration
UNIVERSITY_CONFIG=gt  # or uga, emory, duke, etc.
```

### Adding New Universities
Simply use a new university code - no code changes required:
```python
# These all work automatically
create_generator_for_university('stanford')
create_generator_for_university('berkeley') 
create_generator_for_university('mit')
```

## 📊 Sample Output

### Alias Generation Results
```
🎓 Testing: University of Georgia (UGA)
📍 Apartment: Square on Fifth
  🔤 Total aliases: 15
  📝 Sample aliases: ['SQ5', 'SQR5', 'square on 5', 'FIF5', 'sqonfifth']
  🏷️ Short forms: ['SQ5', 'SQR5', 'FIF5', 'FI5']
```

### Reddit Consensus Output
```json
{
  "overall_sentiment": "positive",
  "overall_score": 4.2,
  "summary": "Generally positive reviews with good location...",
  "validated_mentions": [
    {
      "content": "Love living at The Standard, great amenities",
      "sentiment": "positive",
      "confidence": 0.92
    }
  ]
}
```

## 🧪 Testing

Run comprehensive tests:
```bash
cd backend/src
python test_generalized_system.py
```

Test with specific university:
```bash
UNIVERSITY_CONFIG=uga python enhanced_reddit_ai.py --run-main
```

## 🌟 Benefits

### ✅ **Fully Generalized**
- No hardcoded abbreviations or patterns
- Works for any university/location
- Easy to extend and maintain

### ✅ **Robust & Reliable**
- Two-factor validation system
- Comprehensive error handling
- Extensive alias coverage

### ✅ **User-Friendly**
- Interactive map and image display
- Clear consensus formatting
- Responsive design

### ✅ **Developer-Friendly**
- Modular, well-documented code
- Extensive testing suite
- Configuration-driven approach

## 🎉 Success Metrics

- ✅ **Zero Hardcoded Patterns**: All GT-specific code removed
- ✅ **Universal Compatibility**: Works with 5+ universities tested
- ✅ **Extensibility**: New universities added without code changes
- ✅ **Robustness**: Two-factor validation with grid system
- ✅ **User Experience**: Enhanced frontend with map/image display

## 🚀 Future Enhancements

1. **Database Integration**: PostgreSQL for apartment data
2. **Real-Time Updates**: WebSocket for live consensus updates
3. **Mobile App**: React Native companion app
4. **Analytics Dashboard**: Usage and performance metrics
5. **Machine Learning**: Improved sentiment analysis models

---

**The system is now production-ready and can be deployed for any university with minimal configuration!** 🎓✨
