# Product Information Service (PIS) - MVP

A simplified backend service for aggregating and serving phone product data including specs, prices, availability, and reviews.

## Features

- Search phones by budget, OS, RAM, brand, and camera importance
- View detailed product specifications and variants
- Find best prices across multiple retailers (new and refurbished)
- Aggregate review summaries with credibility scoring
- Simple web interface for testing

## Project Status

✅ **Completed:**
- Python/FastAPI project structure created
- MongoDB models defined with Pydantic
- API endpoints built (search, products, offers, reviews)
- Web interface created with HTML/CSS/JS
- Sample data seeding script ready with 5 phones

## Setup Instructions

### 1. Prerequisites
- MongoDB installed via Homebrew
- Conda environment created: `pis-service` with Python 3.11

### 2. Start MongoDB
```bash
brew services start mongodb-community
```

### 3. Activate Environment
```bash
conda activate pis-service
```

### 4. Install Dependencies (if needed)
```bash
pip install -r requirements.txt
```

### 5. Seed Database
```bash
python seed_data.py
```

### 6. Run Server
```bash
uvicorn app.main:app --reload --port 8000
```

### 7. Access Web Interface
Open browser to: http://localhost:8000

## API Endpoints

- `GET /api/v1/search` - Search products with filters
- `GET /api/v1/products/{id}` - Get product details
- `GET /api/v1/offers/variant/{id}` - Get offers for a variant  
- `GET /api/v1/reviews/product/{id}/summary` - Get review summary

## Sample Data Included

5 Android phones with full specs, variants, offers, and reviews:
- Samsung Galaxy S23
- Google Pixel 8
- OnePlus 11
- Motorola Edge 40
- Nothing Phone (2)

## Use Case Demo Flow

1. **Search**: "I need an Android phone under $1000"
2. **Filter**: By RAM, storage, brand preferences
3. **Compare**: View spec ranges and scores
4. **Reviews**: Check credibility-scored review summaries
5. **Pricing**: Find best prices (new vs refurbished)
6. **Availability**: Check store pickup vs shipping options

## Project Structure

```
pis-service/
├── app/
│   ├── models/         # Pydantic models
│   ├── routes/         # API endpoints
│   ├── config.py       # Settings
│   └── database.py     # MongoDB connection
├── static/            # CSS/JS files
├── templates/         # HTML templates
├── seed_data.py       # Database seeding script
└── requirements.txt   # Python dependencies
```

## Environment Variables

```
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=pis_service
PORT=8000
ENV=development
```

## Troubleshooting

If MongoDB connection fails:
```bash
# Check if MongoDB is running
brew services list | grep mongodb

# Restart MongoDB
brew services restart mongodb-community
```

If conda environment issues:
```bash
# Recreate environment
conda env remove -n pis-service
conda create -n pis-service python=3.11 -y
conda activate pis-service
pip install -r requirements.txt
```