#!/usr/bin/env python3
"""
Test script to demonstrate Amazon price fetching functionality
"""

import asyncio
import os
import httpx
from typing import Optional

async def fetch_amazon_price(model_name: str) -> Optional[float]:
    """Fetch the latest price from Amazon for the given model name.
    
    This function uses the Rainforest API to get real Amazon prices.
    You need to set the AMAZON_API_KEY environment variable.
    """
    
    api_key = os.getenv("AMAZON_API_KEY")
    if not api_key:
        print(f"⚠️  AMAZON_API_KEY not set - using mock prices")
        return None
    
    params = {
        "api_key": api_key,
        "type": "search",
        "amazon_domain": os.getenv("AMAZON_API_DOMAIN", "amazon.com"),
        "search_term": model_name,
    }
    
    print(f"🔍 Searching Amazon for: {model_name}")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("https://api.rainforestapi.com/request", params=params)
            data = response.json()
            
            if response.status_code != 200:
                print(f"❌ API Error: {data.get('message', 'Unknown error')}")
                return None
                
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None
    
    results = data.get("search_results") or []
    if not results:
        print(f"❌ No results found for {model_name}")
        return None
    
    # Get the first result's price
    first_result = results[0]
    price_info = first_result.get("price") or {}
    amount = price_info.get("value")
    
    if amount is None:
        print(f"❌ No price found in results")
        return None
        
    try:
        price = float(amount)
        print(f"✅ Found price: ${price:.2f}")
        print(f"   Product: {first_result.get('title', 'N/A')}")
        print(f"   ASIN: {first_result.get('asin', 'N/A')}")
        return price
    except (TypeError, ValueError):
        print(f"❌ Invalid price format: {amount}")
        return None


async def test_pricing():
    """Test the Amazon pricing API with sample products"""
    
    print("=" * 60)
    print("Amazon Pricing API Test")
    print("=" * 60)
    
    # Check if API key is set
    if not os.getenv("AMAZON_API_KEY"):
        print("\n⚠️  WARNING: AMAZON_API_KEY environment variable not set!")
        print("To use real Amazon prices, you need to:")
        print("1. Sign up for a Rainforest API account at https://www.rainforestapi.com/")
        print("2. Get your API key from the dashboard")
        print("3. Set the environment variable:")
        print("   export AMAZON_API_KEY='your-api-key-here'")
        print("\n")
    
    # Test with some popular phone models
    test_models = [
        "Samsung Galaxy S23",
        "Google Pixel 8",
        "iPhone 15 Pro Max",
        "OnePlus 11",
    ]
    
    print("Testing with sample phone models:\n")
    
    for model in test_models:
        price = await fetch_amazon_price(model)
        if price:
            print(f"   → {model}: ${price:.2f}")
        else:
            print(f"   → {model}: No price available")
        print()
        
        # Add small delay to avoid rate limiting
        await asyncio.sleep(1)
    
    print("=" * 60)
    print("\nTo integrate this in your seed data:")
    print("1. Set AMAZON_API_KEY environment variable")
    print("2. Run the seed_data.py script")
    print("3. The script will automatically fetch real Amazon prices")
    print("4. If API fails, it falls back to default prices")


if __name__ == "__main__":
    asyncio.run(test_pricing())