# StingerSpaces

**Georgia Tech Off-Campus Housing Finder** - A comprehensive platform helping GT students find the perfect apartment near campus.

## What is StingerSpaces?

StingerSpaces is a web application designed specifically for Georgia Tech students looking for off-campus housing. We combine real apartment listing data with authentic student reviews to help you make informed housing decisions.

### 🎯 Key Features

- **Interactive Campus Map**: Visual apartment search with proximity to key GT locations (CULC, CRC, Tech Square, Student Center, MARTA stations)
- **Real Listing Data**: Up-to-date apartment information sourced from Apartments.com (in compliance with their terms of service)
- **Student Reviews**: Authentic reviews from GT students covering safety, management, amenities, and costs
- **Financial Transparency**: Real cost breakdowns from residents including rent, fees, utilities, and parking
- **User Authentication**: Secure login system for adding and managing reviews

## 📊 Data Sources

### Apartment Listings
- **Primary Source**: Apartments.com - We scrape publicly available listing data in accordance with their terms of service
- **Data Includes**: Property names, addresses, contact info, price ranges, bedroom configurations
- **Updates**: Regular automated scraping keeps listings current

### Student Reviews & Insights
- **Community Reviews**: Student-submitted reviews through our secure platform
- **Financial Data**: Real costs reported by current and former residents
- **Rating Categories**: Safety, proximity to groceries, maintenance quality, management responsiveness, amenities
- **Privacy**: All personal information is anonymized

## 🛠 Technology Stack

### Frontend
- **Pure HTML/CSS/JavaScript** - No frameworks used
- **Leaflet.js** - Interactive maps and campus proximity visualization
- **Supabase Integration** - Real-time data and user authentication
- **Responsive Design** - Works on desktop and mobile devices

### Backend
- **Python** - Data processing and web scraping
- **Supabase** - Database, authentication, and real-time updates
- **Automated Jobs** - Daily data synchronization and updates
- **RESTful APIs** - Clean data exchange between frontend and backend

### Database (Supabase)
- **Apartments Table** - Listing data with coordinates and metadata
- **Reviews Table** - Student reviews with ratings and financial data
- **User Management** - Secure authentication and profile management

## 🚀 Getting Started

### For Users
1. Visit the StingerSpaces web application
2. Browse apartments on the interactive map
3. Click on any apartment for detailed information and reviews
4. Create an account to add your own reviews and help fellow students


## 📁 Project Structure

```
StingerSpaces/
├── frontend/                    # Web application frontend
│   ├── index.html              # Main apartment map interface
│   ├── apartment-details.html  # Detailed apartment information
│   ├── apartment-review.html   # Review submission form
│   ├── user-setup.html         # User profile management
│   ├── landing.html            # Welcome page
│   ├── auth/                   # Authentication UI components
│   └── js/                     # JavaScript modules
├── backend/                     # Data processing and automation
│   ├── src/                    # Python scripts for data management
│   └── scripts/                # Automation and deployment scripts
├── SQL files                   # Database setup and schema
└── Documentation              # Setup guides and API documentation
```

## 🔧 Key Components

### Interactive Map (`frontend/index.html`)
- Real-time apartment listings from Supabase
- Campus proximity visualization
- Advanced filtering and search
- Mobile-responsive design

### Apartment Details (`frontend/apartment-details.html`)
- Comprehensive property information
- Student review aggregation
- Financial cost analysis
- Campus proximity with visual map

### Review System (`frontend/apartment-review.html`)
- Authenticated review submission
- Multi-category rating system
- Financial data collection
- Anti-spam and validation measures

### Data Management (`backend/src/`)
- Automated apartment data scraping
- Supabase synchronization
- Data validation and cleaning
- Review processing and moderation


## 📄 Legal & Compliance

- **Data Scraping**: All web scraping is performed in compliance with apartments.com's terms of service
- **Privacy**: User data is handled according to privacy best practices
- **Academic Use**: This project was developed for educational purposes at Georgia Tech
- **Open Source**: Licensed under MIT - see LICENSE file for details

## 🎓 About

StingerSpaces was created for GT students to make off-campus housing search transparent, informative, and community-driven.

**Built with 💛 for the Georgia Tech community**

---

*Last updated: September 2025*
