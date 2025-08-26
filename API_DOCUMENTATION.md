# Phone Shopping System API Documentation

## Overview

This system consists of two main components:
1. **PIS Service (Product Information Service)** - Backend API for phone data and pricing
2. **Phone Shopping Portal** - Frontend web interface

## API Architecture

The PIS Service provides RESTful endpoints for:
- Product information retrieval
- Price comparison across retailers
- Product search functionality
- Review aggregation

## API Endpoints

### Base URL
```
http://localhost:8000/api/v1
```

### 1. Products API

#### Get All Products
```http
GET /products?category=phone&brand=Samsung&limit=10
```

**Query Parameters:**
- `category` (optional): Filter by category (e.g., "phone")
- `brand` (optional): Filter by brand name (case-insensitive)
- `limit` (optional): Maximum results (default: 10, max: 100)

**Example Response:**
```json
[
  {
    "_id": "68ac85fbf3894b7b00ff6611",
    "brand": "Apple",
    "model_name": "iPhone 15 Pro Max",
    "series": "iPhone 15",
    "release_date": "2023-09-22T00:00:00",
    "specs": {...},
    "default_variant_id": "68ac85fbf3894b7b00ff6612"
  }
]
```

#### Get Product Details
```http
GET /products/{product_id}
```

Returns detailed product information including all variants.

### 2. Pricing/Offers API

#### Get Variant Offers
```http
GET /offers/variant/{variant_id}?country=US&postal=94107
```

**Query Parameters:**
- `country` (optional): Country code (default: "US")
- `postal` (optional): Postal code for location-based pricing

**Example Response:**
```json
{
  "variant_id": "68ac85fbf3894b7b00ff6612",
  "country": "US",
  "offers": [
    {
      "_id": "68ac85fbf3894b7b00ff6619",
      "retailer": "Adorama",
      "condition": "new",
      "price_amount": 1243.16,
      "price_currency": "USD",
      "availability": "in_stock",
      "url": "https://adorama.com/product/..."
    }
  ],
  "best_new": {...},
  "best_refurbished": {...},
  "total_offers": 5
}
```

#### Batch Price Check
```http
POST /offers/batch
Content-Type: application/json

["variant_id_1", "variant_id_2", "variant_id_3"]
```

Efficiently check prices for multiple variants in a single request.

**Example Response:**
```json
{
  "region": "US",
  "results": [
    {
      "variant_id": "variant_id_1",
      "cheapest_offer": {
        "retailer": "Amazon",
        "price_amount": 699.99,
        "availability": "in_stock"
      }
    }
  ]
}
```

### 3. Search API
```http
GET /search?query=galaxy&min_price=500&max_price=1000
```

### 4. Reviews API
```http
GET /reviews/product/{product_id}
```

## Best Buy Price Integration

The system fetches real-time product data and prices from Best Buy using their official API.

### Setup Best Buy Integration

1. **Get Best Buy API Key**
   - Visit https://developer.bestbuy.com/
   - Create an account and get your API key (free)

2. **Configure Environment**
   ```bash
   # Add to pis-service/.env
   BESTBUY_API_KEY=your-api-key-here
   ```

3. **How It Works**
   - The seed script fetches real product data from Best Buy API
   - Includes products from 10 categories (smartphones, laptops, tablets, etc.)
   - Retrieves actual pricing, availability, and product specifications
   - Implements throttling to respect API rate limits

### Seed Database with Best Buy Products

```bash
# Seed with real Best Buy data
make seed

# This will fetch ~100 products across 10 categories
```

## Using the API with curl

### Get Products
```bash
# List all products
curl http://localhost:8000/api/v1/products

# Filter by brand
curl "http://localhost:8000/api/v1/products?brand=Samsung"

# Get specific product
curl http://localhost:8000/api/v1/products/{product_id}
```

### Get Prices
```bash
# Single variant pricing
curl http://localhost:8000/api/v1/offers/variant/{variant_id}

# Batch pricing
curl -X POST http://localhost:8000/api/v1/offers/batch \
  -H "Content-Type: application/json" \
  -d '["variant_id_1", "variant_id_2"]'
```

## Using the API with Python

```python
import httpx
import asyncio

async def get_phone_prices():
    async with httpx.AsyncClient() as client:
        # Get products
        products = await client.get(
            "http://localhost:8000/api/v1/products",
            params={"brand": "Samsung", "limit": 5}
        )
        
        # Get prices for first product's default variant
        product = products.json()[0]
        variant_id = product["default_variant_id"]
        
        prices = await client.get(
            f"http://localhost:8000/api/v1/offers/variant/{variant_id}"
        )
        
        return prices.json()

# Run the async function
result = asyncio.run(get_phone_prices())
print(f"Best price: ${result['best_new']['price_amount']}")
```

## Database Structure

The MongoDB database contains:

- **products**: Phone models with specifications
- **variants**: Specific SKUs (color/storage combinations)
- **offers**: Retailer pricing and availability
- **reviews**: Aggregated review scores

## Running the System

1. **Start MongoDB**
   ```bash
   mongod
   ```

2. **Start API Server**
   ```bash
   cd pis-service
   python3 app/main.py
   ```

3. **Seed Database** (if needed)
   ```bash
   cd pis-service
   python3 seed_data.py
   ```

4. **Access Frontend**
   ```bash
   cd phone-shopping-portal
   # Open index.html in browser
   ```

## API Response Status Codes

- `200 OK`: Successful request
- `400 Bad Request`: Invalid parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

## Rate Limiting

- Amazon API: Limited by Rainforest API plan
- Local API: No rate limiting for development

## Troubleshooting

### No Products Showing
1. Check MongoDB is running: `mongod`
2. Check database has data: `python3 seed_data.py`
3. Check API server: `curl http://localhost:8000/health`

### Amazon Prices Not Working
1. Verify API key is set: `echo $AMAZON_API_KEY`
2. Check API key is valid with Rainforest
3. Monitor API quota/limits

### API Connection Issues
1. Verify server is running on port 8000
2. Check CORS settings if accessing from browser
3. Check MongoDB connection string in .env