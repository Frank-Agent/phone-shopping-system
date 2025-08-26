#!/usr/bin/env python3
"""
Seed script that fetches real product data from Best Buy API.
Only uses real data - no synthetic generation, no fallbacks.
"""

import asyncio
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from bson import ObjectId
import logging
import httpx
import time
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BestBuyAPI:
    """Best Buy API client for fetching real product data"""
    
    def __init__(self):
        self.api_key = os.getenv("BESTBUY_API_KEY", "")
        if not self.api_key:
            raise ValueError("BESTBUY_API_KEY not found in environment variables")
        
        self.base_url = "https://api.bestbuy.com/v1"
        self.client = httpx.AsyncClient(timeout=30.0)
        self.last_request_time = 0
        self.min_delay = 2.0  # 2 seconds between requests to be safe
    
    async def _throttle(self):
        """Throttle API requests to avoid rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay:
            delay = self.min_delay - time_since_last
            logger.debug(f"Throttling: waiting {delay:.2f} seconds")
            await asyncio.sleep(delay)
        
        self.last_request_time = time.time()
    
    async def get_categories(self) -> Dict[str, str]:
        """Fetch available categories from Best Buy API"""
        await self._throttle()
        
        try:
            url = f"{self.base_url}/categories"
            params = {
                "apiKey": self.api_key,
                "format": "json",
                "show": "id,name"
            }
            
            response = await self.client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                categories = {}
                
                # Map specific category names to our internal names
                # Using exact matches for better accuracy
                category_mapping = {
                    "Cell Phones with Plans": "smartphones",
                    "All Cell Phones with Plans": "smartphones",
                    "Unlocked Cell Phones": "smartphones_unlocked",
                    "All Laptops": "laptops",
                    "Laptops": "laptops",
                    "iPad, Tablets & E-Readers": "tablets",
                    "All Tablets": "tablets",
                    "iPads": "tablets_ipad",
                    "Fitness & GPS Watches": "smartwatches",
                    "Apple Watch": "smartwatches_apple",
                    "All Headphones": "headphones",
                    "Headphones": "headphones",
                    "Digital Cameras": "cameras",
                    "Cameras & Camcorders": "cameras",
                    "Xbox One": "gaming_xbox",
                    "PlayStation 4": "gaming_ps4",
                    "PlayStation 5": "gaming_ps5",
                    "Nintendo Switch": "gaming_nintendo",
                    "Smart Home": "smart_home",
                    "Smart Home & Security": "smart_home",
                    "TVs": "tvs",
                    "All Flat-Screen TVs": "tvs_all",
                    "Bluetooth & Wireless Speakers": "speakers",
                    "Portable Bluetooth Speakers": "speakers"
                }
                
                for category in data.get("categories", []):
                    name = category.get("name", "")
                    cat_id = category.get("id", "")
                    
                    if name in category_mapping:
                        internal_name = category_mapping[name]
                        # Only add main categories, skip subcategories
                        base_category = internal_name.split('_')[0]
                        if base_category not in categories or not internal_name.endswith(('_unlocked', '_ipad', '_apple', '_all')):
                            categories[base_category] = cat_id
                            logger.info(f"Found category: {name} -> {cat_id}")
                
                return categories
            else:
                logger.error(f"Failed to fetch categories: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"Error fetching categories: {e}")
            return {}
    
    async def search_products_by_category(self, category_name: str, category_id: str, limit: int = 10) -> List[Dict]:
        """Search for products in a specific Best Buy category"""
        products = []
        
        # Throttle before making request
        await self._throttle()
        
        params = {
            "apiKey": self.api_key,
            "format": "json",
            "show": "sku,name,salePrice,regularPrice,image,thumbnailImage,largeImage,manufacturer,modelNumber,color,mobileUrl,onlineAvailability,customerReviewAverage,customerReviewCount,longDescription,features.feature,details.value,details.name",
            "pageSize": limit,
            "sort": "bestSellingRank"
        }
        
        # Query for products in the category using category ID
        search_query = f"(categoryPath.id={category_id})"
        
        try:
            url = f"{self.base_url}/products({search_query})"
            response = await self.client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                for product in data.get("products", []):
                    formatted_product = self._format_product(product, category_name)
                    products.append(formatted_product)
                    
                logger.info(f"Found {len(products)} products in {category_name} from Best Buy API")
            elif response.status_code == 403:
                # Rate limit hit
                logger.warning(f"Rate limit hit for {category_name}. Status: {response.status_code}")
                if "Over Quota" in response.text:
                    logger.warning("API quota exceeded. Try again later or reduce request frequency.")
            else:
                logger.error(f"Best Buy API error for {category_name}: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error fetching from Best Buy API for {category_name}: {e}")
            
        return products
    
    def _format_product(self, bb_product: Dict, category_name: str) -> Dict:
        """Format Best Buy product to our schema"""
        
        # Extract specs from details
        specs = {}
        if bb_product.get("details"):
            for detail in bb_product["details"]:
                name = detail.get("name", "").lower().replace(" ", "_")
                value = detail.get("value")
                if name and value:
                    specs[name] = value
        
        # Extract features
        features = []
        if bb_product.get("features"):
            for feature in bb_product["features"]:
                if feature.get("feature"):
                    features.append(feature["feature"])
        
        return {
            "sku": bb_product.get("sku"),
            "name": bb_product.get("name"),
            "brand": bb_product.get("manufacturer"),
            "model_name": self._extract_model_name(bb_product.get("name", "")),
            "model_number": bb_product.get("modelNumber"),
            "category": category_name,
            "description": bb_product.get("longDescription", ""),
            "price": bb_product.get("salePrice"),
            "regular_price": bb_product.get("regularPrice"),
            "image_url": bb_product.get("largeImage") or bb_product.get("image"),
            "thumbnail_url": bb_product.get("thumbnailImage"),
            "color": bb_product.get("color"),
            "url": bb_product.get("mobileUrl"),
            "in_stock": bb_product.get("onlineAvailability", False),
            "rating": bb_product.get("customerReviewAverage"),
            "review_count": bb_product.get("customerReviewCount", 0),
            "specs": specs,
            "features": features[:5],  # Limit to 5 key features
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
    
    def _extract_model_name(self, full_name: str) -> str:
        """Extract clean model name from product title"""
        import re
        
        # Best Buy format is usually: "Brand - Model with specs"
        # First, remove "Geek Squad Certified Refurbished" if present
        clean_name = re.sub(r'Geek Squad Certified Refurbished\s*', '', full_name)
        
        # Split by dash and take the part after brand
        parts = clean_name.split(' - ')
        if len(parts) >= 2:
            model_part = parts[1]
        else:
            model_part = clean_name
        
        # Extract known model patterns
        patterns = [
            (r'(iPhone\s+\d+(?:\s+Pro(?:\s+Max)?)?)', None),  # iPhone 15 Pro Max
            (r'(Galaxy\s+[SZA]\d+(?:\s+Ultra)?)', None),  # Galaxy S24 Ultra
            (r'(Galaxy\s+Note\d+)', None),  # Galaxy Note20
            (r'(Galaxy\s+Z\s+(?:Fold|Flip)\s*\d*)', None),  # Galaxy Z Fold 5
            (r'(Pixel\s+\d+(?:\s+Pro)?)', None),  # Pixel 8 Pro
            (r'(OnePlus\s+\d+(?:[RT])?)', None),  # OnePlus 12T
            (r'([QVG]\d+)', 'LG'),  # LG Q6, V60, G8
            (r'(Moto\s+[GEZ]\s*\d*(?:\s+\w+)?)', None),  # Moto G Power
        ]
        
        for pattern, brand_check in patterns:
            if brand_check is None or brand_check in full_name:
                match = re.search(pattern, model_part, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
        
        # Fallback: take first few words before specs
        model_part = re.sub(r'\s+with\s+.*', '', model_part)  # Remove "with..."
        model_part = re.sub(r'\s+\d+GB.*', '', model_part)  # Remove storage
        model_part = re.sub(r'\s+4G\s+LTE.*', '', model_part)  # Remove network
        model_part = re.sub(r'\s+Cell Phone.*', '', model_part)  # Remove "Cell Phone"
        model_part = re.sub(r'\s*\(.*?\)', '', model_part)  # Remove parentheses
        
        return model_part.strip() or "Unknown Model"
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


async def seed_database():
    """Main function to seed the database with Best Buy product data"""
    
    # MongoDB connection - use same database as the app
    mongo_url = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_url)
    db = client.pis_service  # Use the same database name as the app!
    
    # Initialize Best Buy API client
    try:
        bb_api = BestBuyAPI()
    except ValueError as e:
        logger.error(f"Failed to initialize Best Buy API: {e}")
        logger.info("Please set BESTBUY_API_KEY in your .env file")
        logger.info("You can get a free API key from: https://developer.bestbuy.com/")
        return
    
    # Define Best Buy categories with their IDs
    # These are verified working category IDs from Best Buy
    categories = {
        "smartphones": "pcmcat209400050001",  # Cell Phones with Plans
        "laptops": "abcat0502000",  # Laptops
        "tablets": "pcmcat209000050006",  # iPads & Tablets  
        "smartwatches": "pcmcat321000050004",  # Smart Watches
        "headphones": "abcat0204000",  # Headphones
        "cameras": "abcat0401000",  # Digital Cameras
        "gaming_consoles": "pcmcat1587395025973",  # PS5 Consoles (actual hardware)
        "smart_home": "pcmcat254000050002",  # Smart Home
        "tvs": "abcat0101000",  # TVs
        "speakers": "pcmcat241600050001"  # Bluetooth Speakers
    }
    
    logger.info(f"Fetching products from {len(categories)} categories")
    
    try:
        # Clear existing data
        logger.info("=" * 60)
        logger.info("CLEARING DATABASE...")
        await client.drop_database('pis_service')
        db = client.pis_service
        logger.info("Database cleared")
        logger.info("=" * 60)
        
        # Process and insert products
        all_products = []
        all_variants = []
        all_offers = []
        
        # Fetch products for each category
        for category_name, category_id in categories.items():
            logger.info(f"Fetching products for {category_name} (ID: {category_id})...")
            products = await bb_api.search_products_by_category(category_name, category_id, limit=10)
            
            if not products:
                logger.warning(f"No products found for {category_name}")
                continue
            
            # Process each product in this category
            for idx, product_data in enumerate(products):
                # Generate product ID
                product_id = ObjectId()
                
                # Log product details
                logger.info(f"  Product {idx+1}/{len(products)}: {product_data['model_name']}")
                logger.info(f"    Brand: {product_data['brand']}")
                if product_data['price']:
                    logger.info(f"    Price: ${product_data['price']:.2f}")
                logger.info(f"    In Stock: {product_data['in_stock']}")
                
                # Create product document
                product_doc = {
                    "_id": product_id,
                    "name": product_data["name"],
                    "brand": product_data["brand"],
                    "model_name": product_data["model_name"],
                    "model_number": product_data.get("model_number"),
                    "category": product_data["category"],
                    "description": product_data["description"],
                    "price_range": {
                        "min": product_data["price"] or 0,
                        "max": product_data["regular_price"] or product_data["price"] or 0,
                        "currency": "USD"
                    },
                    "rating": product_data["rating"],
                    "review_count": product_data["review_count"],
                    "image_url": product_data["image_url"],
                    "thumbnail_url": product_data["thumbnail_url"],
                    "specs": product_data["specs"],
                    "features": product_data["features"],
                    "tags": ["best-buy", "official", category_name],
                    "popularity_rank": idx + 1,
                    "created_at": product_data["created_at"],
                    "updated_at": product_data["updated_at"]
                }
                
                all_products.append(product_doc)
                
                # Create a single variant for the product
                variant = {
                    "_id": ObjectId(),
                    "product_id": product_id,
                    "sku": str(product_data["sku"]) if product_data.get("sku") else f"BB{product_id}",
                    "attributes": {
                        "color": product_data.get("color", "Default")
                    },
                    "created_at": datetime.now()
                }
                all_variants.append(variant)
                
                # Create offer from Best Buy
                if product_data.get("price"):
                    offer = {
                        "_id": ObjectId(),
                        "variant_id": variant["_id"],
                        "retailer": "Best Buy",
                        "price_amount": product_data["price"],
                        "price_currency": "USD",
                        "availability": "in_stock" if product_data["in_stock"] else "out_of_stock",
                        "condition": "new",
                        "shipping_cost": 0,
                        "url": product_data.get("url", ""),
                        "last_updated": datetime.now()
                    }
                    all_offers.append(offer)
        
        # Insert all data
        logger.info("=" * 60)
        logger.info("Inserting data into database...")
        
        if all_products:
            await db.products.insert_many(all_products)
            logger.info(f"Inserted {len(all_products)} products")
        
        if all_variants:
            await db.variants.insert_many(all_variants)
            logger.info(f"Inserted {len(all_variants)} variants")
        
        if all_offers:
            await db.offers.insert_many(all_offers)
            logger.info(f"Inserted {len(all_offers)} offers")
        
        # Create indexes
        await db.products.create_index("category")
        await db.products.create_index("brand")
        await db.products.create_index("rating")
        await db.variants.create_index("product_id")
        await db.offers.create_index("variant_id")
        logger.info("Created database indexes")
        
        # Final summary
        logger.info("=" * 60)
        logger.info("DATABASE SEEDING COMPLETED!")
        logger.info(f"Total products: {len(all_products)}")
        logger.info(f"Total variants: {len(all_variants)}")
        logger.info(f"Total offers: {len(all_offers)}")
        
        # Show top products
        logger.info("\nTop 5 Products:")
        for i, product in enumerate(all_products[:5], 1):
            logger.info(f"{i}. {product['brand']} {product['model_name']} - ${product['price_range']['min']:.2f}")
        
        logger.info("=" * 60)
        
    finally:
        await bb_api.close()
        client.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Best Buy Product Data Seeder")
    print("This script fetches REAL product data from Best Buy API")
    print("No synthetic data, no fallbacks - only real products!")
    print("=" * 60)
    
    asyncio.run(seed_database())