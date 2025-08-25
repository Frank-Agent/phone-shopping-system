#!/usr/bin/env python3
"""
Comprehensive system test for PIS (Product Information Service)
Tests all API endpoints and functionality
"""

import asyncio
import httpx
import json
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
import time

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Test results tracking
test_results = {
    "passed": 0,
    "failed": 0,
    "errors": []
}

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_test(name: str, status: str, details: str = ""):
    """Print formatted test result"""
    if status == "PASS":
        print(f"{Colors.GREEN}✓{Colors.RESET} {name}")
        test_results["passed"] += 1
    elif status == "FAIL":
        print(f"{Colors.RED}✗{Colors.RESET} {name}")
        if details:
            print(f"  {Colors.YELLOW}→ {details}{Colors.RESET}")
        test_results["failed"] += 1
        test_results["errors"].append(f"{name}: {details}")
    else:
        print(f"{Colors.BLUE}→{Colors.RESET} {name}")

async def test_health_check(client: httpx.AsyncClient) -> bool:
    """Test health endpoint"""
    try:
        response = await client.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ok":
                print_test("Health Check", "PASS")
                return True
        print_test("Health Check", "FAIL", f"Status: {response.status_code}")
        return False
    except Exception as e:
        print_test("Health Check", "FAIL", str(e))
        return False

async def test_categories(client: httpx.AsyncClient) -> Optional[List[str]]:
    """Test categories endpoint"""
    try:
        response = await client.get(f"{API_BASE}/categories/")
        if response.status_code == 200:
            data = response.json()
            categories = data.get("categories", [])
            if len(categories) > 0:
                print_test(f"Categories API ({len(categories)} categories)", "PASS")
                return [cat["category_id"] for cat in categories]
            else:
                print_test("Categories API", "FAIL", "No categories found")
                return None
        print_test("Categories API", "FAIL", f"Status: {response.status_code}")
        return None
    except Exception as e:
        print_test("Categories API", "FAIL", str(e))
        return None

async def test_category_products(client: httpx.AsyncClient, category: str) -> Optional[List[str]]:
    """Test getting products for a category"""
    try:
        response = await client.get(f"{API_BASE}/categories/{category}/top")
        if response.status_code == 200:
            data = response.json()
            products = data.get("products", [])
            if len(products) > 0:
                print_test(f"Category Products ({category})", "PASS")
                return [str(p["product_id"]) for p in products]
            else:
                print_test(f"Category Products ({category})", "FAIL", "No products found")
                return None
        print_test(f"Category Products ({category})", "FAIL", f"Status: {response.status_code}")
        return None
    except Exception as e:
        print_test(f"Category Products ({category})", "FAIL", str(e))
        return None

async def test_product_details(client: httpx.AsyncClient, product_id: str) -> bool:
    """Test product details endpoint"""
    try:
        response = await client.get(f"{API_BASE}/products/{product_id}")
        if response.status_code == 200:
            data = response.json()
            # Check if we got product data (nested structure)
            if data and ("product" in data or "product_id" in data or "name" in data):
                print_test(f"Product Details", "PASS")
                return True
        print_test(f"Product Details", "FAIL", f"Status: {response.status_code}")
        return False
    except Exception as e:
        print_test(f"Product Details", "FAIL", str(e))
        return False

async def test_search(client: httpx.AsyncClient, category: str) -> bool:
    """Test search functionality"""
    try:
        response = await client.get(f"{API_BASE}/search/", params={
            "category": category,
            "limit": 5
        })
        if response.status_code == 200:
            data = response.json()
            if "products" in data:
                print_test(f"Search API ({category})", "PASS")
                return True
        print_test(f"Search API ({category})", "FAIL", f"Status: {response.status_code}")
        return False
    except Exception as e:
        print_test(f"Search API ({category})", "FAIL", str(e))
        return False

async def test_reviews(client: httpx.AsyncClient, product_id: str) -> bool:
    """Test reviews endpoints"""
    try:
        # Test review summary
        response = await client.get(f"{API_BASE}/reviews/product/{product_id}/summary")
        if response.status_code == 200:
            data = response.json()
            if data.get("product_id") == product_id:
                print_test("Reviews Summary", "PASS")
                
                # Test reviews list (may not exist for all products)
                response = await client.get(f"{API_BASE}/reviews/product/{product_id}")
                if response.status_code in [200, 404]:  # 404 is ok if no reviews
                    print_test("Reviews List", "PASS")
                    return True
                else:
                    print_test("Reviews List", "FAIL", f"Status: {response.status_code}")
                    return False
        print_test("Reviews Summary", "FAIL", f"Status: {response.status_code}")
        return False
    except Exception as e:
        print_test("Reviews API", "FAIL", str(e))
        return False

async def test_offers(client: httpx.AsyncClient, product_id: str) -> bool:
    """Test offers endpoint"""
    try:
        response = await client.get(f"{API_BASE}/offers/product/{product_id}")
        if response.status_code in [200, 404]:  # 404 is ok if no offers
            if response.status_code == 200:
                data = response.json()
                if "offers" in data or "message" in data:
                    print_test("Offers API", "PASS")
                    return True
            else:
                print_test("Offers API", "PASS")  # No offers is valid
                return True
        print_test("Offers API", "FAIL", f"Status: {response.status_code}")
        return False
    except Exception as e:
        print_test("Offers API", "FAIL", str(e))
        return False

async def test_comparison(client: httpx.AsyncClient, product_ids: List[str]) -> bool:
    """Test comparison functionality"""
    try:
        # Create comparison session
        response = await client.post(f"{API_BASE}/compare/session")
        if response.status_code != 200:
            print_test("Compare Session Create", "FAIL", f"Status: {response.status_code}")
            return False
        
        session_data = response.json()
        session_id = session_data.get("session_id")
        if not session_id:
            print_test("Compare Session Create", "FAIL", "No session ID")
            return False
        
        print_test("Compare Session Create", "PASS")
        
        # Add products to comparison
        success = True
        for pid in product_ids[:3]:  # Test with 3 products
            response = await client.post(
                f"{API_BASE}/compare/session/{session_id}/add",
                json={"product_id": pid}
            )
            if response.status_code != 200:
                print_test(f"Add to Comparison", "FAIL", f"Product {pid}")
                success = False
                break
        
        if success:
            print_test("Add to Comparison", "PASS")
            
            # Get comparison
            response = await client.get(f"{API_BASE}/compare/session/{session_id}")
            if response.status_code == 200:
                data = response.json()
                if "comparison" in data:
                    print_test("Get Comparison", "PASS")
                    
                    # Clear comparison
                    response = await client.delete(f"{API_BASE}/compare/session/{session_id}")
                    if response.status_code == 200:
                        print_test("Clear Comparison", "PASS")
                        return True
                    else:
                        print_test("Clear Comparison", "FAIL", f"Status: {response.status_code}")
                else:
                    print_test("Get Comparison", "FAIL", "No comparison data")
            else:
                print_test("Get Comparison", "FAIL", f"Status: {response.status_code}")
        
        return False
    except Exception as e:
        print_test("Comparison API", "FAIL", str(e))
        return False

async def test_favorites(client: httpx.AsyncClient, product_id: str) -> bool:
    """Test favorites functionality with cookies"""
    try:
        # Get initial favorites (should create cookie)
        response = await client.get(f"{API_BASE}/favorites/")
        if response.status_code != 200:
            print_test("Get Favorites", "FAIL", f"Status: {response.status_code}")
            return False
        
        initial_data = response.json()
        initial_count = initial_data.get("count", 0)
        print_test("Get Favorites", "PASS")
        
        # Add to favorites
        response = await client.post(
            f"{API_BASE}/favorites/add",
            json={"product_id": product_id}
        )
        if response.status_code != 200:
            print_test("Add to Favorites", "FAIL", f"Status: {response.status_code}")
            return False
        
        add_data = response.json()
        if add_data.get("count", 0) > initial_count:
            print_test("Add to Favorites", "PASS")
        else:
            print_test("Add to Favorites", "FAIL", "Count did not increase")
            return False
        
        # Check if product is in favorites
        response = await client.get(f"{API_BASE}/favorites/check/{product_id}")
        if response.status_code == 200:
            check_data = response.json()
            if check_data.get("is_favorite"):
                print_test("Check Favorite", "PASS")
            else:
                print_test("Check Favorite", "FAIL", "Product not marked as favorite")
                return False
        else:
            print_test("Check Favorite", "FAIL", f"Status: {response.status_code}")
            return False
        
        # Toggle favorite (should remove)
        response = await client.post(
            f"{API_BASE}/favorites/toggle",
            json={"product_id": product_id}
        )
        if response.status_code == 200:
            toggle_data = response.json()
            if toggle_data.get("action") == "removed":
                print_test("Toggle Favorite", "PASS")
            else:
                print_test("Toggle Favorite", "FAIL", "Expected removal")
                return False
        else:
            print_test("Toggle Favorite", "FAIL", f"Status: {response.status_code}")
            return False
        
        # Get count
        response = await client.get(f"{API_BASE}/favorites/count")
        if response.status_code == 200:
            count_data = response.json()
            print_test(f"Favorites Count ({count_data.get('count', 0)} items)", "PASS")
        else:
            print_test("Favorites Count", "FAIL", f"Status: {response.status_code}")
            return False
        
        # Clear favorites
        response = await client.delete(f"{API_BASE}/favorites/clear")
        if response.status_code == 200:
            print_test("Clear Favorites", "PASS")
            return True
        else:
            print_test("Clear Favorites", "FAIL", f"Status: {response.status_code}")
            return False
        
    except Exception as e:
        print_test("Favorites API", "FAIL", str(e))
        return False

async def test_cors(client: httpx.AsyncClient) -> bool:
    """Test CORS headers"""
    try:
        # Test CORS with a regular GET request (CORS headers should be present)
        response = await client.get(f"{API_BASE}/categories/")
        if response.status_code == 200:
            headers = response.headers
            # Check for CORS headers (case-insensitive)
            cors_header = None
            for key in headers:
                if key.lower() == "access-control-allow-origin":
                    cors_header = headers[key]
                    break
            
            if cors_header:
                print_test(f"CORS Headers (Origin: {cors_header})", "PASS")
                return True
            else:
                print_test("CORS Headers", "WARN", "No CORS headers found")
                return True  # Not a failure, just a warning
        else:
            print_test("CORS Headers", "FAIL", f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_test("CORS Headers", "FAIL", str(e))
        return False

async def run_all_tests():
    """Run all system tests"""
    print(f"\n{Colors.BOLD}=== PIS System Test Suite ==={Colors.RESET}")
    print(f"Starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Create HTTP client with cookie support
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Basic connectivity
        print(f"{Colors.BLUE}Testing Basic Connectivity...{Colors.RESET}")
        if not await test_health_check(client):
            print(f"\n{Colors.RED}Server is not responding. Is it running?{Colors.RESET}")
            return False
        
        # Test CORS
        await test_cors(client)
        
        # Categories and Products
        print(f"\n{Colors.BLUE}Testing Categories & Products...{Colors.RESET}")
        categories = await test_categories(client)
        if not categories:
            print(f"{Colors.RED}Cannot proceed without categories{Colors.RESET}")
            return False
        
        # Test first 3 categories
        all_product_ids = []
        for category in categories[:3]:
            product_ids = await test_category_products(client, category)
            if product_ids:
                all_product_ids.extend(product_ids[:2])
        
        if not all_product_ids:
            print(f"{Colors.RED}No products found to test{Colors.RESET}")
            return False
        
        # Test with first product
        test_product_id = all_product_ids[0]
        
        # Product Details
        print(f"\n{Colors.BLUE}Testing Product Operations...{Colors.RESET}")
        await test_product_details(client, test_product_id)
        
        # Search
        print(f"\n{Colors.BLUE}Testing Search...{Colors.RESET}")
        for category in categories[:2]:
            await test_search(client, category)
        
        # Reviews and Offers
        print(f"\n{Colors.BLUE}Testing Reviews & Offers...{Colors.RESET}")
        await test_reviews(client, test_product_id)
        await test_offers(client, test_product_id)
        
        # Comparison
        print(f"\n{Colors.BLUE}Testing Comparison...{Colors.RESET}")
        if len(all_product_ids) >= 3:
            await test_comparison(client, all_product_ids[:3])
        else:
            print_test("Comparison", "SKIP", "Not enough products")
        
        # Favorites
        print(f"\n{Colors.BLUE}Testing Favorites...{Colors.RESET}")
        await test_favorites(client, test_product_id)
    
    return True

async def check_server_running() -> bool:
    """Check if the server is running"""
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{BASE_URL}/health")
            return response.status_code == 200
    except:
        return False

def print_summary():
    """Print test summary"""
    total = test_results["passed"] + test_results["failed"]
    
    print(f"\n{Colors.BOLD}=== Test Summary ==={Colors.RESET}")
    print(f"Total Tests: {total}")
    print(f"{Colors.GREEN}Passed: {test_results['passed']}{Colors.RESET}")
    print(f"{Colors.RED}Failed: {test_results['failed']}{Colors.RESET}")
    
    if test_results["failed"] > 0:
        print(f"\n{Colors.RED}Failed Tests:{Colors.RESET}")
        for error in test_results["errors"]:
            print(f"  • {error}")
    
    if test_results["failed"] == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ All tests passed!{Colors.RESET}")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ Some tests failed{Colors.RESET}")
        return 1

async def main():
    """Main test runner"""
    # Check if server is running
    if not await check_server_running():
        print(f"{Colors.RED}Error: Server is not running at {BASE_URL}{Colors.RESET}")
        print(f"Please start the server with: uvicorn app.main:app --reload --port 8000")
        return 1
    
    # Run tests
    try:
        await run_all_tests()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.RESET}")
        return 1
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.RESET}")
        return 1
    
    # Print summary and return exit code
    return print_summary()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)