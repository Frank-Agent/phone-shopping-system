#!/usr/bin/env python3
"""
Real Amazon Product Data Seeder - NO SIMULATED DATA
Hybrid approach: Rainforest API for prices + Web scraping for details

Usage:
    python seed_amazon_data_real.py                    # Seed all categories with scraping
    python seed_amazon_data_real.py --no-scraping      # API only (faster, less data)
    python seed_amazon_data_real.py --categories 1     # Only first category
    python seed_amazon_data_real.py --categories 3     # First 3 categories
    python seed_amazon_data_real.py --limit 5          # 5 products per category
    python seed_amazon_data_real.py -c 1 -l 2         # Test mode: 1 category, 2 products
"""

import asyncio
import httpx
import os
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import re
import time
import argparse

# Load environment variables
load_dotenv()

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "pis_service")
AMAZON_API_KEY = os.getenv("AMAZON_API_KEY", "")

# Categories to fetch
CATEGORIES = {
    "smartphones": "cell phones",
    "laptops": "laptop computers",
    "tablets": "tablets",
    "smartwatches": "smart watches",
    "headphones": "headphones",
    "cameras": "digital cameras",
    "gaming_consoles": "gaming consoles",
    "smart_home": "smart home devices",
    "tvs": "smart tv",
    "speakers": "bluetooth speakers"
}

class RealAmazonDataFetcher:
    """Fetches real data from Amazon via Rainforest API + Web Scraping"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.rainforestapi.com/request"
        self.client = httpx.AsyncClient(timeout=30.0)
        self.api_calls = 0
        self.scrape_calls = 0
        # Headers for web scraping
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Connection': 'keep-alive',
        }
        
    async def search_products(self, search_term: str, category: str, limit: int = 10) -> List[Dict]:
        """
        Search for products using Rainforest API
        Returns real Amazon data only
        """
        params = {
            "api_key": self.api_key,
            "type": "search",
            "amazon_domain": "amazon.com",
            "search_term": search_term,
            "sort_by": "featured",
            "page": "1"
        }
        
        try:
            self.api_calls += 1
            logger.info(f"API Call #{self.api_calls}: Searching for {search_term}")
            
            response = await self.client.get(self.base_url, params=params)
            if response.status_code != 200:
                logger.error(f"API error: {response.status_code}")
                return []
                
            data = response.json()
            products = []
            
            # Log first item to see what fields we get
            search_results = data.get("search_results", [])
            if search_results:
                first_item = search_results[0]
                logger.info(f"Sample API response fields: {list(first_item.keys())}")
                logger.info(f"Brand field: {first_item.get('brand', 'NOT FOUND')}")
            
            # Extract real product data
            for item in search_results[:limit]:
                if item.get("asin"):
                    product = self._extract_search_result(item, category)
                    if product:
                        products.append(product)
                        
            logger.info(f"Found {len(products)} real products for {category}")
            return products
            
        except Exception as e:
            logger.error(f"Error fetching products: {e}")
            return []
    
    async def get_product_details(self, asin: str) -> Optional[Dict]:
        """
        Get detailed product information from Amazon API
        Returns complete product data including specs, variants, offers
        """
        params = {
            "api_key": self.api_key,
            "type": "product",
            "amazon_domain": "amazon.com",
            "asin": asin
        }
        
        try:
            self.api_calls += 1
            logger.info(f"API Call #{self.api_calls}: Getting full details for ASIN {asin}")
            
            response = await self.client.get(self.base_url, params=params)
            if response.status_code != 200:
                logger.error(f"Failed to get details for {asin}: {response.status_code}")
                return None
                
            return response.json()
            
        except Exception as e:
            logger.error(f"Error fetching product details: {e}")
            return None
    
    async def scrape_product_details(self, url: str, asin: str) -> Dict:
        """
        Scrape additional product details from Amazon product page
        Returns enriched data without making API calls
        """
        try:
            self.scrape_calls += 1
            logger.info(f"Scrape #{self.scrape_calls}: Getting details for ASIN {asin}")
            
            # Add slight delay to be respectful
            await asyncio.sleep(0.5)
            
            response = await self.client.get(url, headers=self.headers, follow_redirects=True)
            if response.status_code != 200:
                logger.warning(f"Failed to scrape {asin}: Status {response.status_code}")
                return {}
            
            soup = BeautifulSoup(response.text, 'html.parser')
            scraped_data = {}
            
            # Extract product title and parse model_name
            title_elem = soup.find('span', {'id': 'productTitle'})
            if title_elem:
                full_title = title_elem.get_text(strip=True)
                # Keep full title as name
                scraped_data['full_title'] = full_title
                
                # Extract clean model name and parse attributes
                import re
                
                # Remove promotional text first
                clean_title = full_title
                if 'with $' in clean_title:
                    clean_title = clean_title[:clean_title.index('with $')]
                
                # Extract storage from title
                storage_match = re.search(r'(\d+)\s*(GB|TB)', clean_title)
                if storage_match:
                    storage = storage_match.group(0)
                    scraped_data['storage'] = storage
                    # Remove storage from title
                    clean_title = re.sub(r'\s*-?\s*\d+\s*(GB|TB)\s*', '', clean_title)
                
                # Extract color (usually after first dash)
                if ' - ' in clean_title:
                    parts = clean_title.split(' - ')
                    if len(parts) >= 2:
                        scraped_data['color'] = parts[1].strip()
                    model = parts[0].strip()  # Model is before color
                else:
                    model = clean_title.strip()
                    
                scraped_data['model_name'] = model
            
            # Extract brand - try multiple sources
            # 1. Try manufacturer from technical details
            tech_tables = soup.find_all(['table', 'div'], class_=['prodDetTable', 'a-keyvalue'])
            for table in tech_tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)
                        if 'manufacturer' in label:
                            scraped_data['brand'] = value
                            break
            
            # 2. If no manufacturer found, try bylineInfo
            if 'brand' not in scraped_data:
                brand_link = soup.find('a', {'id': 'bylineInfo'})
                if brand_link:
                    brand_text = brand_link.get_text(strip=True)
                    if 'Visit the' in brand_text and 'Store' in brand_text:
                        scraped_data['brand'] = brand_text.replace('Visit the', '').replace('Store', '').strip()
                    elif 'Brand:' in brand_text:
                        scraped_data['brand'] = brand_text.replace('Brand:', '').strip()
            
            # Extract feature bullets
            feature_div = soup.find('div', {'id': 'feature-bullets'})
            if feature_div:
                bullets = feature_div.find_all('span', class_='a-list-item')
                scraped_data['feature_bullets'] = [
                    bullet.get_text(strip=True) 
                    for bullet in bullets 
                    if bullet.get_text(strip=True) and not bullet.find_parent('div', class_='aplus-v2')
                ][:5]  # Limit to 5 features
            
            # Extract technical specifications and other fields
            tech_details = {}
            detail_tables = soup.find_all('table', class_='prodDetTable')
            for table in detail_tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) == 2:
                        key = cells[0].get_text(strip=True).replace(':', '')
                        value = cells[1].get_text(strip=True)
                        tech_details[key] = value
                        
                        # Extract specific fields
                        key_lower = key.lower()
                        if 'color' in key_lower:
                            scraped_data['color'] = value
                        elif 'model' in key_lower and 'model_name' not in scraped_data:
                            scraped_data['model_name'] = value
                        elif 'operating system' in key_lower or 'os' in key_lower:
                            scraped_data['operating_system'] = value
                        elif 'screen size' in key_lower or 'display' in key_lower:
                            scraped_data['display_size'] = value
            
            if tech_details:
                scraped_data['technical_details'] = tech_details
            
            # Extract all product images
            images = []
            img_container = soup.find('div', {'id': 'altImages'})
            if img_container:
                for img in img_container.find_all('img'):
                    src = img.get('src', '')
                    if src:
                        # Convert thumbnail to full size
                        full_size = re.sub(r'\._[^.]+_\.', '.', src)
                        if full_size not in images:
                            images.append(full_size)
            
            if images:
                scraped_data['images'] = images[:10]  # Limit to 10 images
            
            # Extract product description
            description_div = soup.find('div', {'id': 'productDescription'})
            if description_div:
                desc_text = description_div.get_text(strip=True)
                if desc_text:
                    scraped_data['description'] = desc_text[:1000]  # Limit length
            
            # Extract variant information
            variants = []
            variation_div = soup.find('div', {'id': 'variation_size_name'})
            if variation_div:
                options = variation_div.find_all('li', class_='swatchAvailable')
                for option in options:
                    variant_text = option.get('title', '').replace('Click to select ', '')
                    if variant_text:
                        variants.append(variant_text)
            
            color_div = soup.find('div', {'id': 'variation_color_name'})
            if color_div:
                options = color_div.find_all('li', class_='swatchAvailable')
                for option in options:
                    variant_text = option.get('title', '').replace('Click to select ', '')
                    if variant_text:
                        variants.append(variant_text)
            
            if variants:
                scraped_data['variant_options'] = variants
            
            # Extract dimensions and weight
            dimensions = {}
            for detail_key in ['Product Dimensions', 'Item Weight', 'Package Dimensions']:
                if detail_key in tech_details:
                    dimensions[detail_key.lower().replace(' ', '_')] = tech_details[detail_key]
            
            if dimensions:
                scraped_data['dimensions'] = dimensions
            
            return scraped_data
            
        except Exception as e:
            logger.error(f"Error scraping product {asin}: {e}")
            return {}
    
    def _extract_detail_product(self, detail: Dict, category: str) -> Optional[Dict]:
        """Extract complete product data from detail API response"""
        try:
            product = detail.get("product", {})
            if not product:
                return None
                
            # Build comprehensive product record
            result = {
                "_id": ObjectId(),
                "asin": product.get("asin"),
                "name": product.get("title", ""),
                "model_name": product.get("title", ""),  # Will be cleaned later
                "brand": product.get("brand", ""),
                "category": category,
                "description": product.get("description", ""),
                "image_url": product.get("main_image", {}).get("link", ""),
                "url": product.get("link", ""),
                "rating": product.get("rating", 0),
                "ratings_total": product.get("ratings_total", 0),
                "is_prime": product.get("amazons_choice", {}).get("link", None) is not None,
                "is_best_seller": product.get("bestsellers_rank", None) is not None,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            # Extract price
            buybox = product.get("buybox_winner", {})
            if buybox:
                price = buybox.get("price", {}).get("value", 0)
                result["price_range"] = {"min": price, "max": price}
            
            # Extract all images
            images = []
            if product.get("main_image"):
                images.append(product["main_image"].get("link", ""))
            for img in product.get("images", []):
                if img.get("link"):
                    images.append(img["link"])
            result["images"] = images[:10]
            
            # Extract feature bullets
            result["feature_bullets"] = product.get("feature_bullets", [])
            
            # Extract specifications
            specs = {}
            
            # From specifications table (it's a list, not a dict)
            spec_data = product.get("specifications", [])
            if isinstance(spec_data, list):
                for spec in spec_data:
                    if isinstance(spec, dict):
                        name = spec.get("name", "")
                        value = spec.get("value", "")
                    else:
                        continue
                    
                    name_lower = name.lower()
                    
                    # Extract key specs
                    if "memory storage capacity" in name_lower:
                        specs["storage"] = value
                    elif "ram memory installed" in name_lower or "ram memory" in name_lower:
                        specs["ram"] = value
                    elif "cpu speed" in name_lower or "processor" in name_lower:
                        specs["processor"] = value
                    elif "screen size" in name_lower:
                        specs["display"] = value
                    elif "battery capacity" in name_lower or "battery power rating" in name_lower:
                        specs["battery"] = value
                    elif "other camera features" in name_lower:
                        specs["camera"] = value
                    elif name_lower == "color":
                        specs["color"] = value
                    elif name_lower == "weight":
                        specs["weight"] = value
                    elif "operating system" in name_lower or name_lower == "os":
                        specs["os"] = value
                    elif "cellular technology" in name_lower:
                        specs["network"] = value
                    elif "model name" in name_lower:
                        if "model_name_from_spec" not in result:
                            result["model_name_from_spec"] = value
            
            # From attributes
            attrs = product.get("attributes", [])
            for attr in attrs:
                name = attr.get("name", "").lower()
                value = attr.get("value", "")
                
                if "storage" in name and "storage" not in specs:
                    specs["storage"] = value
                elif "color" in name and "color" not in specs:
                    specs["color"] = value
            
            result["specs"] = specs
            
            # Extract variants - Amazon returns a flat list, not grouped
            variants = []
            for variant in product.get("variants", []):
                if variant.get("asin") and not variant.get("is_current_product"):
                    # Extract variant details
                    variant_info = {
                        "asin": variant["asin"],
                        "title": variant.get("title", ""),
                        "is_available": True,  # If listed, assume available
                        "link": variant.get("link", "")
                    }
                    
                    # Extract dimensions (color, storage, etc)
                    dimensions = {}
                    for dim in variant.get("dimensions", []):
                        dim_name = dim.get("name", "").lower()
                        if dim_name in ["color", "size", "storage"]:
                            dimensions[dim_name] = dim.get("value", "")
                    variant_info["dimensions"] = dimensions
                    
                    variants.append(variant_info)
            result["variant_options"] = variants
            
            # Clean model name - prefer spec model name if available
            if result.get("model_name_from_spec"):
                result["model_name"] = result["model_name_from_spec"]
                del result["model_name_from_spec"]
            elif result["name"]:
                clean_name = result["name"]
                # Remove promotional text
                if "with $" in clean_name:
                    clean_name = clean_name[:clean_name.index("with $")]
                if "," in clean_name:
                    # Take first part before comma for cleaner name
                    clean_name = clean_name.split(",")[0]
                # Remove storage, color, year, version info
                import re
                clean_name = re.sub(r'\s*\d+GB|\d+TB', '', clean_name)
                clean_name = re.sub(r'\s*\(.*?\)', '', clean_name)  # Remove parenthetical info
                clean_name = re.sub(r'\s+US Version.*', '', clean_name)
                clean_name = re.sub(r'\s+\d{4}.*', '', clean_name)  # Remove year and after
                clean_name = re.sub(r'\s+(Light Gray|Graphite|Black|White|Blue|Red|Green).*', '', clean_name, flags=re.IGNORECASE)
                clean_name = re.sub(r'\s+Phone Only.*', '', clean_name)
                clean_name = re.sub(r'\s+A\d+ Only.*', '', clean_name)  # Remove "A16 Only" etc
                result["model_name"] = clean_name.strip()
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting detail product: {e}")
            return None
    
    def _extract_search_result(self, item: Dict, category: str) -> Optional[Dict]:
        """Extract real product data from search result"""
        try:
            # Only use actual data from Amazon API - no guessing or extraction
            product = {
                "_id": ObjectId(),
                "asin": item.get("asin"),
                "name": item.get("title", ""),
                "brand": item.get("brand"),  # Only use what API provides
                "category": category,
                "image_url": item.get("image", ""),
                "url": item.get("link", ""),
                "price_range": self._extract_price(item),
                "rating": item.get("rating", 0),
                "ratings_total": item.get("ratings_total", 0),
                "is_prime": item.get("is_prime", False),
                "is_amazon_choice": item.get("is_amazon_choice", False),
                "is_best_seller": item.get("is_best_seller", False),
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            # Extract real variants if available
            variants = self._extract_real_variants(item)
            if variants:
                product["variants"] = variants
                
            # Extract real specs from title/features
            product["specs"] = self._extract_real_specs(item)
            
            return product
            
        except Exception as e:
            logger.error(f"Error extracting product: {e}")
            return None
    
    def _extract_price(self, item: Dict) -> Dict:
        """Extract real price information"""
        price = item.get("price", {})
        
        if isinstance(price, dict):
            return {
                "min": price.get("value", 0),
                "max": price.get("value", 0),
                "currency": price.get("currency", "USD"),
                "raw": price.get("raw", "")
            }
        elif isinstance(price, (int, float)):
            return {
                "min": price,
                "max": price,
                "currency": "USD"
            }
        else:
            # Try to extract from price string
            return {"min": 0, "max": 0, "currency": "USD"}
    
    def _extract_real_variants(self, item: Dict) -> List[Dict]:
        """Extract actual product variants from Amazon data"""
        variants = []
        
        # Check for size/color variations in the API response
        variations = item.get("variations", [])
        for var in variations:
            if var.get("asin"):
                variants.append({
                    "asin": var.get("asin"),
                    "title": var.get("title", ""),
                    "price": var.get("price", 0),
                    "is_available": var.get("is_available", True)
                })
                
        return variants
    
    def _extract_real_specs(self, item: Dict, scraped_features: List[str] = None) -> Dict:
        """Extract specifications from product features"""
        specs = {}
        
        # Extract from title
        title = item.get("title", "")
        
        # RAM extraction
        import re
        ram_match = re.search(r'(\d+)\s*GB\s*RAM', title, re.IGNORECASE)
        if ram_match:
            specs["ram_gb"] = int(ram_match.group(1))
            
        # Storage extraction
        storage_match = re.search(r'(\d+)\s*([GT]B)\s*(?:SSD|Storage|ROM)', title, re.IGNORECASE)
        if storage_match:
            size = int(storage_match.group(1))
            unit = storage_match.group(2).upper()
            if unit == "TB":
                size *= 1024
            specs["storage_gb"] = size
            
        # Display size
        display_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:inch|")', title, re.IGNORECASE)
        if display_match:
            specs["display_size"] = float(display_match.group(1))
            
        # Extract from features if available
        features = item.get("feature_bullets", [])
        for feature in features:
            # Parse feature text for specs
            if "processor" in feature.lower():
                specs["processor"] = feature
            elif "battery" in feature.lower():
                specs["battery"] = feature
            elif "camera" in feature.lower():
                specs["camera"] = feature
                
        return specs
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

async def fetch_with_bulk_api(
    categories: Dict[str, str], 
    api_key: str, 
    use_detail_api: bool = True,
    products_per_category: int = 10
):
    """
    Option 1: Use Product Detail API for complete data
    - Search API to find products
    - Detail API for each product (complete specs, variants, etc.)
    """
    fetcher = RealAmazonDataFetcher(api_key)
    all_products = []
    
    try:
        for category, search_term in categories.items():
            logger.info(f"\n{'='*60}")
            logger.info(f"Fetching {category}")
            logger.info(f"{'='*60}")
            
            # Search for products first
            search_results = await fetcher.search_products(search_term, category, limit=products_per_category)
            
            # Initialize products list for this category
            products = []
            
            # Get full details for each product using detail API
            if use_detail_api:
                logger.info(f"Getting full details for {len(search_results)} products...")
                for item in search_results:
                    if item.get("asin"):
                        # Get complete product details
                        detail_data = await fetcher.get_product_details(item["asin"])
                        
                        if detail_data:
                            # Extract complete product from detail API
                            product = fetcher._extract_detail_product(detail_data, category)
                            if product:
                                products.append(product)
                                logger.info(f"  ✓ Got full details for {product['model_name']}")
                        else:
                            # Fallback to search result if detail API fails
                            products.append(item)
                            logger.info(f"  ⚠ Using search data for {item.get('name', 'Unknown')[:30]}")
            else:
                # Just use search results
                products = search_results
            
            all_products.extend(products)
            logger.info(f"Got {len(products)} products for {category}")
            
        logger.info(f"\n{'='*60}")
        logger.info(f"Total API calls made: {fetcher.api_calls}")
        logger.info(f"Total scraping requests: {fetcher.scrape_calls}")
        logger.info(f"Total products fetched: {len(all_products)}")
        logger.info(f"Estimated API cost: ${fetcher.api_calls * 0.001:.3f}")
        logger.info(f"{'='*60}")
        
        return all_products
        
    finally:
        await fetcher.close()

# Note: _extract_detailed_info function removed as we're using Option 2 (search API only)

async def seed_database_real_only(
    use_detail_api: bool = True,
    num_categories: int = None,
    products_per_category: int = 10
):
    """
    Seed database with ONLY real Amazon data
    Option 1: Use Product Detail API for complete data
    """
    
    if not AMAZON_API_KEY:
        logger.error("❌ AMAZON_API_KEY is required for real data")
        logger.info("Get your API key from: https://www.rainforestapi.com/")
        logger.info("Set it in .env file: AMAZON_API_KEY=your_key_here")
        return
    
    # Limit categories if specified
    categories_to_fetch = CATEGORIES
    if num_categories:
        categories_to_fetch = dict(list(CATEGORIES.items())[:num_categories])
        logger.info(f"Limiting to {num_categories} categories: {list(categories_to_fetch.keys())}")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    
    try:
        # Clear existing data
        logger.info("Clearing existing data...")
        await db.products.delete_many({})
        await db.variants.delete_many({})
        await db.offers.delete_many({})
        await db.reviews.delete_many({})  # We won't have fake reviews
        
        # Fetch real products with detail API
        logger.info(f"Using {'Detail API for complete data' if use_detail_api else 'Search API only'}")
        logger.info(f"Fetching {products_per_category} products per category")
        
        products = await fetch_with_bulk_api(
            categories_to_fetch, 
            AMAZON_API_KEY, 
            use_detail_api,
            products_per_category
        )
        
        if products:
            # Insert real products
            result = await db.products.insert_many(products)
            logger.info(f"✅ Inserted {len(result.inserted_ids)} real products")
            
            # Create indexes
            await db.products.create_index("asin", unique=True)
            await db.products.create_index("category")
            await db.products.create_index("brand")
            await db.products.create_index("price_range.min")
            
            logger.info("✅ Database seeded with REAL Amazon data!")
            logger.info("✅ Prices from API are accurate and real-time")
            if use_detail_api:
                logger.info("✅ Complete product details from Amazon Product API")
        else:
            logger.error("❌ No products fetched. Check your API key.")
            
    finally:
        client.close()

def main():
    """Main function with CLI argument parsing"""
    parser = argparse.ArgumentParser(
        description="Seed database with real Amazon product data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python seed_amazon_data_real.py                    # All categories with scraping
  python seed_amazon_data_real.py --no-scraping      # API only (faster)
  python seed_amazon_data_real.py -c 1 -l 2          # Test: 1 category, 2 products
  python seed_amazon_data_real.py --categories 3     # First 3 categories
        """
    )
    
    parser.add_argument(
        "-c", "--categories",
        type=int,
        help="Number of categories to fetch (default: all 10)",
        default=None
    )
    
    parser.add_argument(
        "-l", "--limit",
        type=int,
        help="Products per category (default: 10)",
        default=10
    )
    
    parser.add_argument(
        "--search-only",
        action="store_true",
        help="Use search API only (faster but less complete data)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run the seeder
    asyncio.run(seed_database_real_only(
        use_detail_api=not args.search_only,
        num_categories=args.categories,
        products_per_category=args.limit
    ))

if __name__ == "__main__":
    main()