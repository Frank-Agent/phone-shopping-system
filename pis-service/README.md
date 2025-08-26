# Product Information Service (PIS)

A comprehensive backend service for aggregating and serving real electronics product data from Best Buy including specifications, prices, availability, and reviews. Features a web portal for browsing and comparing products.

## 🚀 Quick Start

```bash
# 1. Install dependencies
make install

# 2. Seed database with real Best Buy products
make seed

# 3. Run the API server
make run

# 4. In another terminal, run the portal (optional)
cd ../phone-shopping-portal
python server.py  # Runs on http://localhost:8080
```

## ✨ Features

### Core Functionality
- **Product Search**: Search across 10 categories with filters for budget, brand, ratings
- **Product Details**: View comprehensive specs, variants, and pricing
- **Price Tracking**: Real-time pricing from Best Buy API
- **Review Aggregation**: Credibility-scored review summaries
- **Product Comparison**: Side-by-side comparison of multiple products
- **Favorites System**: Save and manage favorite products
- **Categories**: Browse products by category (smartphones, laptops, tablets, etc.)

### Data
- **99 Real Products**: Actual Best Buy products across 10 categories
- **Real Pricing**: Live prices fetched from Best Buy API
- **99 Variants**: Different SKUs and configurations  
- **Real Ratings**: Actual customer ratings from Best Buy
- **99 Offers**: Direct Best Buy pricing per product

## 📦 What's Included

### API Endpoints (Port 8000)
- `GET /api/v1/categories/` - List all product categories
- `GET /api/v1/categories/{id}/top` - Get top products in a category
- `GET /api/v1/search` - Search products with filters
- `GET /api/v1/products/` - List products
- `GET /api/v1/products/{id}` - Get product details
- `GET /api/v1/products/{id}/variants` - Get product variants
- `GET /api/v1/offers/variant/{id}` - Get offers for a variant
- `GET /api/v1/reviews/product/{id}/summary` - Get review summary
- `GET /api/v1/compare/` - Product comparison endpoints
- `GET /api/v1/favorites/` - Favorites management

### Web Portal (Port 8080)
- **Categories View**: Browse products by category
- **Search Interface**: Filter by budget, brand, specs
- **Product Details**: Modal with full specifications
- **Comparison Tool**: Compare up to 4 products
- **Favorites**: Save products for later

## 🛠️ Setup Options

### Option 1: Quick Setup (Recommended)
Use the included database dump for instant setup:

```bash
make install   # Install Python dependencies
make restore   # Restore database from dump (instant)
make run       # Start API server
```

### Option 2: Fresh Data from Amazon
Fetch new data using web scraping and API:

```bash
make install   # Install dependencies
make seed      # Fetch fresh data from Amazon (slower, requires API key)
make run       # Start server
```

### Option 3: Manual Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Start MongoDB
brew services start mongodb-community

# Restore database
mongorestore --db=pis_service --archive=pis_service_dump.archive

# Run server
uvicorn app.main:app --reload --port 8000
```

## 🔧 Configuration

### Environment Variables (.env)
```env
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=pis_service
PORT=8000
ENV=development
AMAZON_API_KEY=your_key_here      # Optional: For live pricing
AMAZON_API_DOMAIN=amazon.com      # Optional: Amazon domain
```

### Amazon API Integration
To enable real-time pricing and better model aggregation from Amazon:
1. Get an API key from [Rainforest API](https://www.rainforestapi.com/)
2. Add to `.env` file: `AMAZON_API_KEY=your_key_here`
3. Run `make seed` to fetch fresh data with live prices and improved product results

## 📊 Database Schema

### Products Collection
- `product_id`: Unique identifier
- `name`: Product name
- `category`: Product category
- `brand`: Manufacturer
- `specs`: Technical specifications
- `price_range`: Min/max prices
- `rating`: Average rating
- `popularity_rank`: Rank within category

### Categories Supported
- Smartphones
- Laptops
- Tablets
- Smartwatches
- Headphones
- Cameras
- Gaming Consoles
- Smart Home Devices
- TVs
- Speakers

## 🧪 Testing

```bash
# Run all tests (21 test cases)
make test

# Run with server auto-start
make test-with-server

# Watch mode (auto-run on file changes)
make watch-test
```

## 📁 Project Structure

```
phone-shopping-system/
├── pis-service/                  # Backend API
│   ├── app/
│   │   ├── models/              # Pydantic models & schemas
│   │   │   ├── product.py      # Product model
│   │   │   ├── response.py     # Response models with field mapping
│   │   │   └── ...
│   │   ├── routes/              # API endpoints
│   │   │   ├── products.py     # Product endpoints
│   │   │   ├── search.py       # Search functionality
│   │   │   ├── categories.py   # Category browsing
│   │   │   ├── compare.py      # Comparison features
│   │   │   └── ...
│   │   ├── config.py           # Settings configuration
│   │   ├── database.py         # MongoDB connection
│   │   └── utils.py            # Utility functions
│   ├── pis_service_dump.archive # Database dump (100 products)
│   ├── seed_amazon_data.py     # Amazon data fetcher
│   ├── test_system.py          # Comprehensive test suite
│   ├── Makefile                # Build automation
│   └── requirements.txt        # Python dependencies
│
└── phone-shopping-portal/       # Frontend
    ├── index.html              # Main page
    ├── js/app.js              # Application logic
    ├── css/styles.css         # Styling
    └── server.py              # No-cache development server
```

## 🚦 API Response Format

All API responses use consistent field naming:
- `product_id` instead of `_id` or `id`
- `category_id` for category identifiers
- `variant_id` for variant identifiers
- Prices are integers (no cents)

Example product response:
```json
{
  "product_id": "68accf3e29bc02cb86c60b81",
  "name": "Motorola Moto G Play 2024",
  "category": "smartphones",
  "brand": "Motorola",
  "price_range": {
    "min": 110,
    "max": 132
  },
  "rating": 4.2,
  "specs": {
    "os": "Android",
    "camera_mp": 50,
    "ram_gb": 4
  }
}
```

## 🛠️ Makefile Commands

```bash
make help         # Show all available commands
make install      # Install dependencies
make restore      # Restore database from dump
make seed         # Fetch fresh data from Amazon
make run          # Start API server
make test         # Run test suite
make clean        # Clean cache files
make dev          # Development mode with auto-reload
```

## 🐛 Troubleshooting

### MongoDB Connection Issues
```bash
# Check if MongoDB is running
brew services list | grep mongodb

# Restart MongoDB
brew services restart mongodb-community
```

### Port Already in Use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 8080
lsof -ti:8080 | xargs kill -9
```

### Cache Issues
The portal includes no-cache headers, but if you see stale content:
1. Hard refresh browser: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows/Linux)
2. Clear browser cache
3. Check the version in `index.html`: `<script src="js/app.js?v=4"></script>`

## 📝 License

MIT

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

For issues and questions, please open an issue on GitHub.

---

Built with ❤️ using FastAPI, MongoDB, and real Amazon data