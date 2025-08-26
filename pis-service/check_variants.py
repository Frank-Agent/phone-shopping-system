import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_variants():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.pis_service
    
    # Find a product with variants
    product = await db.products.find_one({"variant_options": {"$exists": True, "$ne": []}})
    
    if product:
        print(f"Product: {product.get('model_name', 'Unknown')}")
        print(f"\nVariants ({len(product.get('variant_options', []))} total):")
        for v in product.get("variant_options", [])[:5]:
            print(f"  - ASIN: {v.get('asin')}")
            print(f"    Title: {v.get('title')}")
            print(f"    Available: {v.get('is_available')}")
            print(f"    Price: ${v.get('price', 0)}")
            print()
    else:
        print("No products with variants found")
        
        # Check all products
        all_products = await db.products.find({}).to_list(10)
        print("\nSample products in DB:")
        for p in all_products[:3]:
            print(f"  - {p.get('model_name', p.get('name', 'Unknown'))}")
            print(f"    Has variant_options field: {'variant_options' in p}")
            if 'variant_options' in p:
                print(f"    Variant count: {len(p.get('variant_options', []))}")

asyncio.run(check_variants())