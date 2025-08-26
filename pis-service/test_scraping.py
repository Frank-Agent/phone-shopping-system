#!/usr/bin/env python3
"""
Test Amazon scraping to debug price extraction
"""

import asyncio
import httpx
from bs4 import BeautifulSoup
import re

async def test_scraping():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        # Search for smartphones
        url = "https://www.amazon.com/s"
        params = {
            'k': 'iPhone 15 Pro unlocked',
            'i': 'electronics',
            's': 'relevancerank'
        }
        
        print("Fetching Amazon search results...")
        response = await client.get(url, params=params)
        
        if response.status_code != 200:
            print(f"Error: Status {response.status_code}")
            return
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find product cards
        cards = soup.find_all('div', {'data-component-type': 's-search-result'})
        print(f"Found {len(cards)} product cards\n")
        
        for i, card in enumerate(cards[:3]):
            print(f"=== Product {i+1} ===")
            
            # ASIN
            asin = card.get('data-asin', 'No ASIN')
            print(f"ASIN: {asin}")
            
            # Title - try multiple selectors
            title = None
            title_selectors = [
                ('h2', {'class': 's-size-mini'}),
                ('h2', {'class': 'a-size-mini'}),
                ('h2', {'class': 'a-size-base-plus'}),
                ('h2', {}),  # Any h2
                ('span', {'class': 'a-size-medium'}),
                ('span', {'class': 'a-size-base-plus'}),
            ]
            
            for tag, attrs in title_selectors:
                elem = card.find(tag, attrs)
                if elem:
                    title = elem.get_text(strip=True)
                    print(f"Title ({tag} {attrs}): {title[:60]}...")
                    break
            
            if not title:
                print("Title: NOT FOUND")
            
            # Price - try multiple methods
            print("\nPrice Detection:")
            
            # Method 1: a-price-whole
            price_whole = card.find('span', class_='a-price-whole')
            if price_whole:
                print(f"  a-price-whole: {price_whole.get_text(strip=True)}")
            
            # Method 2: a-price with a-offscreen
            price_offscreen = card.find('span', class_='a-offscreen')
            if price_offscreen:
                print(f"  a-offscreen: {price_offscreen.get_text(strip=True)}")
            
            # Method 3: a-price span
            price_span = card.find('span', class_='a-price')
            if price_span:
                # Get the data-a-size attribute which sometimes has price
                price_data = price_span.get('data-a-size')
                print(f"  a-price data: {price_data}")
                
                # Get all text within
                all_text = price_span.get_text(strip=True)
                print(f"  a-price text: {all_text}")
                
                # Look for a-price-range
                price_range = price_span.find('span', class_='a-price-range')
                if price_range:
                    print(f"  a-price-range: {price_range.get_text(strip=True)}")
            
            # Method 4: Direct search for price pattern
            card_text = card.get_text()
            price_matches = re.findall(r'\$[\d,]+\.?\d*', card_text)
            if price_matches:
                print(f"  Regex matches: {price_matches[:3]}")
            
            # Rating
            rating = card.find('span', class_='a-icon-alt')
            if rating:
                print(f"\nRating: {rating.get_text(strip=True)}")
            
            print("\n" + "-" * 40 + "\n")

if __name__ == "__main__":
    asyncio.run(test_scraping())