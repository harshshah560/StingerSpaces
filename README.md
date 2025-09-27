# StingerSpaces
**Atlanta Student Housing Search Platform**

A clean, fast apartment search platform designed for students in Atlanta, with a focus on Georgia Tech area housing. Browse apartments with detailed information, images, and interactive maps.

## ✨ Features

- **Interactive Map**: Browse apartments on a full-screen map with detailed markers
- **Detailed Listings**: Complete apartment information including prices, addresses, and contact details
- **Image Gallery**: Property photos for each apartment
- **Mobile Responsive**: Works seamlessly on desktop and mobile devices
- **Fast Loading**: Optimized for quick apartment browsing

## 🚀 Quick Start

1. **Start the server**:
   ```bash
   ./start_server.sh
   ```

2. **Open your browser** to `http://localhost:8000`

3. **Browse apartments** on the interactive map or click through to detailed pages

## 📂 Project Structure

```
StingerSpaces/
├── frontend/           # Web application
│   ├── index.html     # Main map page
│   ├── apartment-details.html
│   └── apartment_data.json
├── backend/           # Data processing
│   ├── src/          # Python scripts
│   ├── data/         # Raw apartment data
│   └── reddit_archive/  # Archived Reddit integration
└── start_server.sh   # Quick start script
```

## 🏗️ Architecture

- **Frontend**: Pure HTML/CSS/JavaScript with Leaflet.js for mapping
- **Backend**: Python scripts for data scraping and processing
- **Data**: JSON-based storage for fast loading

## 📊 Data Sources

- Apartments.com scraping for comprehensive listings
- Custom data processing for optimized display
- Geocoding for accurate map positioning

## 🔧 Development

### Adding New Apartments
1. Update `backend/data/apartment_data.json`
2. Run data processing scripts in `backend/src/`
3. Copy updated data to `frontend/apartment_data.json`

### Reddit Integration (Archived)
Previous Reddit-based comment analysis has been moved to `backend/reddit_archive/` and can be restored if needed in the future.

## 🎯 Target Users

- Georgia Tech students looking for off-campus housing
- Students at other Atlanta universities
- Anyone searching for apartments near downtown/midtown Atlanta

---

**Built for students, by students** 🐝 
