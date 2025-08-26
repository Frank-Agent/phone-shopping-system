#!/usr/bin/env python3
"""
Test script to verify Amazon API integration
"""

import asyncio
import os
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_rainforest_api():
    """Test Rainforest API with a sample ASIN"""
    
    api_key = os.getenv('AMAZON_API_KEY')
    if not api_key:
        print("\n⚠️  AMAZON_API_KEY not set!")
        print("To use the Rainforest API for accurate pricing:")
        print("1. Sign up at https://www.rainforestapi.com/")
        print("2. Get your API key")
        print("3. Export it: export AMAZON_API_KEY='your-key-here'")
        return
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    # Test with a popular product ASIN
    test_asin = "B0B1YQM4Z9"  # Example: iPhone or popular product
    
    async with httpx.AsyncClient() as client:
        api_url = "https://api.rainforestapi.com/request"
        params = {
            "api_key": api_key,
            "type": "product",
            "amazon_domain": "amazon.com",
            "asin": test_asin
        }
        
        print(f"\n🔍 Fetching product details for ASIN: {test_asin}")
        
        try:
            response = await client.get(api_url, params=params, timeout=30.0)
            
            if response.status_code == 200:
                data = response.json()
                product = data.get('product', {})
                
                if product:
                    print("\n✅ Successfully fetched product data!")
                    print(f"📦 Title: {product.get('title', 'N/A')[:80]}")
                    print(f"💰 Price: ${product.get('buybox_winner', {}).get('price', {}).get('value', 'N/A')}")
                    print(f"⭐ Rating: {product.get('rating', 'N/A')}/5")
                    print(f"🏷️  Brand: {product.get('brand', 'N/A')}")
                    print(f"📸 Image: {'Yes' if product.get('main_image') else 'No'}")
                    print(f"📝 Features: {len(product.get('feature_bullets', []))} bullet points")
                    print(f"🔄 Variants: {len(product.get('variants', []))} found")
                    
                    # Show price structure
                    print("\n💵 Price Structure:")
                    if product.get('buybox_winner'):
                        bb = product['buybox_winner']
                        print(f"  Buybox Price: ${bb.get('price', {}).get('value', 'N/A')}")
                        print(f"  Availability: {bb.get('availability', {}).get('raw', 'N/A')}")
                    
                    return True
                else:
                    print("❌ No product data in response")
            else:
                print(f"❌ API returned status: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return False

async def test_search_api():
    """Test search API"""
    api_key = os.getenv('AMAZON_API_KEY')
    if not api_key:
        return
    
    print("\n\n📱 Testing Search API...")
    
    async with httpx.AsyncClient() as client:
        api_url = "https://api.rainforestapi.com/request"
        params = {
            "api_key": api_key,
            "type": "search",
            "amazon_domain": "amazon.com",
            "search_term": "iPhone 15 Pro",
            "sort_by": "featured"
        }
        
        try:
            response = await client.get(api_url, params=params, timeout=30.0)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('search_results', [])
                
                print(f"✅ Found {len(results)} search results")
                
                for i, result in enumerate(results[:3]):
                    print(f"\n[{i+1}] {result.get('title', 'N/A')[:60]}")
                    print(f"    ASIN: {result.get('asin', 'N/A')}")
                    print(f"    Price: ${result.get('price', {}).get('value', 'N/A')}")
                    print(f"    Rating: {result.get('rating', 'N/A')}")
                    
        except Exception as e:
            print(f"❌ Search Error: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("Amazon Rainforest API Integration Test")
    print("=" * 60)
    
    asyncio.run(test_rainforest_api())
    asyncio.run(test_search_api())
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)