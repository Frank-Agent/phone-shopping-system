#!/usr/bin/env python3
"""
Debug script to see what data is available on Amazon product pages
"""

import asyncio
import httpx
from bs4 import BeautifulSoup
import json

async def debug_scrape(url: str):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers, follow_redirects=True)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print("=" * 80)
        print("AVAILABLE DATA ON AMAZON PRODUCT PAGE")
        print("=" * 80)
        
        # Product Title
        title = soup.find('span', {'id': 'productTitle'})
        if title:
            print(f"\n1. PRODUCT TITLE: {title.get_text(strip=True)[:100]}")
        
        # Brand/Byline
        brand = soup.find('a', {'id': 'bylineInfo'})
        if brand:
            print(f"\n2. BRAND/BYLINE: {brand.get_text(strip=True)}")
        
        # Technical Details Table
        print("\n3. TECHNICAL DETAILS TABLE:")
        tech_tables = soup.find_all(['table', 'div'], class_=['prodDetTable', 'a-keyvalue', 'pdTab'])
        for table in tech_tables[:2]:  # Limit to first 2 tables
            rows = table.find_all('tr')
            for row in rows[:10]:  # Show first 10 rows
                cells = row.find_all(['td', 'th', 'span'])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)[:50]
                    print(f"   - {label}: {value}")
        
        # Product Details Section
        print("\n4. PRODUCT DETAILS SECTION:")
        detail_list = soup.find('div', {'id': 'detailBullets_feature_div'})
        if detail_list:
            items = detail_list.find_all('span', class_='a-list-item')
            for item in items[:10]:
                text = item.get_text(strip=True)
                if ':' in text:
                    parts = text.split(':', 1)
                    print(f"   - {parts[0]}: {parts[1][:50] if len(parts) > 1 else 'N/A'}")
        
        # Feature Bullets
        print("\n5. FEATURE BULLETS:")
        feature_div = soup.find('div', {'id': 'feature-bullets'})
        if feature_div:
            bullets = feature_div.find_all('span', class_='a-list-item')
            for i, bullet in enumerate(bullets[:3], 1):
                text = bullet.get_text(strip=True)
                if text and not bullet.find_parent('div', class_='aplus-v2'):
                    print(f"   {i}. {text[:100]}...")
        
        # About This Item
        print("\n6. ABOUT THIS ITEM:")
        about_div = soup.find('div', {'id': 'feature-bullets'})
        if about_div:
            h2 = about_div.find('h2')
            if h2 and 'About this item' in h2.get_text():
                items = about_div.find_all('span', class_='a-list-item')
                for i, item in enumerate(items[:3], 1):
                    print(f"   {i}. {item.get_text(strip=True)[:100]}...")
        
        # Product Overview Table
        print("\n7. PRODUCT OVERVIEW TABLE:")
        overview = soup.find('table', {'id': 'productOverview_feature_div'})
        if not overview:
            overview = soup.find('div', {'id': 'productOverview_feature_div'})
        if overview:
            rows = overview.find_all('tr')
            for row in rows[:10]:
                cells = row.find_all(['td', 'span'])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    print(f"   - {label}: {value[:50]}")
        
        # Additional Info
        print("\n8. ADDITIONAL PRODUCT INFORMATION:")
        add_info = soup.find('div', {'id': 'prodDetails'})
        if add_info:
            tables = add_info.find_all('table')
            for table in tables[:1]:
                rows = table.find_all('tr')
                for row in rows[:5]:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)[:50]
                        print(f"   - {label}: {value}")
        
        print("\n" + "=" * 80)

# Test with a real Amazon URL
if __name__ == "__main__":
    # Using one of the products from our database
    test_url = "https://www.amazon.com/dp/B0FJMGXCX7"
    asyncio.run(debug_scrape(test_url))