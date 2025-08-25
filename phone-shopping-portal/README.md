# Phone Shopping Portal

A modern, responsive web portal for searching and comparing mobile phones using the PIS (Product Information Service) API.

## Features

### 🔍 Smart Search
- Filter by budget, operating system, brand, RAM, storage
- Adjustable camera importance for photography enthusiasts
- Real-time search results with scoring algorithm
- Visual product cards with key specifications

### 📊 Compare Phones
- Side-by-side comparison of up to 4 phones
- Compare prices, specifications, and scores
- Easy add/remove from comparison table
- Comprehensive feature comparison

### ❤️ Favorites
- Save your favorite phones for later
- Persistent storage using localStorage
- Quick access to saved phones
- Badge counter shows favorite count

### 📱 Product Details
- Detailed specifications view
- Professional review summaries
- Pros and cons consensus
- Average ratings and credibility scores

## Setup Instructions

### Prerequisites
- PIS Service running on http://localhost:8000
- Python 3.x for serving static files (or any HTTP server)

### Running the Portal

1. **Ensure PIS Service is running:**
   ```bash
   cd pis-service
   uvicorn app.main:app --reload --port 8000
   ```

2. **Start the portal server:**
   ```bash
   cd phone-shopping-portal
   python -m http.server 8080
   ```

3. **Access the portal:**
   Open your browser to http://localhost:8080

## Technologies Used

- **Frontend:** Vanilla JavaScript, HTML5, CSS3
- **Design:** Modern gradient UI with card-based layout
- **API Integration:** Fetch API for async requests
- **State Management:** Local state with localStorage for persistence
- **Responsive Design:** Mobile-first approach with CSS Grid/Flexbox

## Portal Structure

```
phone-shopping-portal/
├── index.html          # Main HTML file
├── css/
│   └── styles.css      # All styling
├── js/
│   └── app.js          # Application logic
├── images/             # Image assets (if needed)
└── README.md           # This file
```

## API Endpoints Used

- `GET /api/v1/search` - Search phones with filters
- `GET /api/v1/products/{id}` - Get product details
- `GET /api/v1/reviews/product/{id}/summary` - Get review summaries

## Features Walkthrough

### Search View
1. Enter your budget and preferences
2. Click "Search Phones" to find matching devices
3. Results show with scores based on your criteria
4. Each card displays key specs and price range

### Compare View
1. Click "Compare" on any phone card
2. Switch to Compare tab to see side-by-side comparison
3. Add up to 4 phones for comparison
4. Remove phones with the × button

### Favorites View
1. Click the heart icon to save favorites
2. Access saved phones in the Favorites tab
3. Favorites persist across browser sessions
4. Badge shows current favorite count

### Product Details Modal
1. Click "View Details" on any phone
2. Modal shows comprehensive specifications
3. Review summary with pros/cons
4. Professional review ratings

## Browser Compatibility

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Future Enhancements

- Price tracking over time
- Offer alerts
- User reviews integration
- Advanced filtering options
- Export comparison to PDF
- Dark mode toggle