import asyncio
from datetime import datetime, timedelta
import random
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from app.models import Product, ProductSpecs, Display, Battery, Camera, Connectivity
from app.models import Variant, Offer, Review

client = AsyncIOMotorClient(settings.mongodb_uri)
db = client[settings.database_name]

sample_phones = [
    {
        "brand": "Samsung",
        "series": "Galaxy S",
        "model_name": "Galaxy S23",
        "release_date": datetime(2023, 2, 1),
        "specs": {
            "os": {"value": "Android 13", "confidence": 0.95, "sources": ["samsung.com"]},
            "soc": {"value": "Snapdragon 8 Gen 2", "confidence": 0.95},
            "ram_gb": {"value": 8, "unit": "GB", "confidence": 0.95},
            "storage_gb": {"min": 128, "max": 512},
            "display": {
                "size_in": 6.1,
                "tech": "Dynamic AMOLED 2X",
                "refresh_hz": 120,
                "brightness_nits_peak": 1750
            },
            "battery": {
                "capacity_mah": 3900,
                "wired_charging_w": 25,
                "wireless_charging_w": 15
            },
            "cameras": {
                "rear": [
                    {"mp": 50, "role": "main", "ois": True},
                    {"mp": 12, "role": "ultrawide", "ois": False},
                    {"mp": 10, "role": "telephoto", "ois": True}
                ],
                "front": {"mp": 12}
            },
            "ip_rating": "IP68",
            "dimensions_mm": {"width": 70.9, "height": 146.3, "depth": 7.6},
            "weight_g": 168,
            "connectivity": {
                "sim": "Dual SIM (Nano + eSIM)",
                "bands_5g": ["n1", "n3", "n5", "n7", "n8", "n28", "n66", "n77", "n78"],
                "wifi": "Wi-Fi 6E",
                "bluetooth": "5.3"
            }
        },
        "variants": [
            {"color": "Phantom Black", "storage_gb": 128, "price": 799},
            {"color": "Phantom Black", "storage_gb": 256, "price": 859},
            {"color": "Cream", "storage_gb": 128, "price": 799},
            {"color": "Green", "storage_gb": 256, "price": 859}
        ]
    },
    {
        "brand": "Google",
        "series": "Pixel",
        "model_name": "Pixel 8",
        "release_date": datetime(2023, 10, 4),
        "specs": {
            "os": {"value": "Android 14", "confidence": 0.95, "sources": ["google.com"]},
            "soc": {"value": "Google Tensor G3", "confidence": 0.95},
            "ram_gb": {"value": 8, "unit": "GB", "confidence": 0.95},
            "storage_gb": {"min": 128, "max": 256},
            "display": {
                "size_in": 6.2,
                "tech": "OLED",
                "refresh_hz": 120,
                "brightness_nits_peak": 2000
            },
            "battery": {
                "capacity_mah": 4575,
                "wired_charging_w": 30,
                "wireless_charging_w": 18
            },
            "cameras": {
                "rear": [
                    {"mp": 50, "role": "main", "ois": True},
                    {"mp": 12, "role": "ultrawide", "ois": False}
                ],
                "front": {"mp": 10.5}
            },
            "ip_rating": "IP68",
            "dimensions_mm": {"width": 70.8, "height": 150.5, "depth": 8.9},
            "weight_g": 187,
            "connectivity": {
                "sim": "Dual SIM (Nano + eSIM)",
                "bands_5g": ["n1", "n2", "n3", "n5", "n7", "n8", "n12", "n20", "n25", "n28", "n30"],
                "wifi": "Wi-Fi 7",
                "bluetooth": "5.3"
            }
        },
        "variants": [
            {"color": "Obsidian", "storage_gb": 128, "price": 699},
            {"color": "Obsidian", "storage_gb": 256, "price": 759},
            {"color": "Hazel", "storage_gb": 128, "price": 699},
            {"color": "Rose", "storage_gb": 128, "price": 699}
        ]
    },
    {
        "brand": "OnePlus",
        "series": "11",
        "model_name": "OnePlus 11",
        "release_date": datetime(2023, 2, 7),
        "specs": {
            "os": {"value": "Android 13", "confidence": 0.95, "sources": ["oneplus.com"]},
            "soc": {"value": "Snapdragon 8 Gen 2", "confidence": 0.95},
            "ram_gb": {"value": 12, "unit": "GB", "confidence": 0.95},
            "storage_gb": {"min": 128, "max": 256},
            "display": {
                "size_in": 6.7,
                "tech": "LTPO3 Fluid AMOLED",
                "refresh_hz": 120,
                "brightness_nits_peak": 1300
            },
            "battery": {
                "capacity_mah": 5000,
                "wired_charging_w": 100,
                "wireless_charging_w": 0
            },
            "cameras": {
                "rear": [
                    {"mp": 50, "role": "main", "ois": True},
                    {"mp": 48, "role": "ultrawide", "ois": False},
                    {"mp": 32, "role": "telephoto", "ois": False}
                ],
                "front": {"mp": 16}
            },
            "ip_rating": "IP64",
            "dimensions_mm": {"width": 74.1, "height": 163.1, "depth": 8.5},
            "weight_g": 205,
            "connectivity": {
                "sim": "Dual SIM",
                "bands_5g": ["n1", "n3", "n5", "n7", "n8", "n20", "n28", "n38", "n40", "n41", "n66"],
                "wifi": "Wi-Fi 7",
                "bluetooth": "5.3"
            }
        },
        "variants": [
            {"color": "Titan Black", "storage_gb": 128, "price": 699},
            {"color": "Titan Black", "storage_gb": 256, "price": 799},
            {"color": "Eternal Green", "storage_gb": 256, "price": 799}
        ]
    },
    {
        "brand": "Motorola",
        "series": "Edge",
        "model_name": "Edge 40",
        "release_date": datetime(2023, 5, 4),
        "specs": {
            "os": {"value": "Android 13", "confidence": 0.95, "sources": ["motorola.com"]},
            "soc": {"value": "MediaTek Dimensity 8020", "confidence": 0.95},
            "ram_gb": {"value": 8, "unit": "GB", "confidence": 0.95},
            "storage_gb": {"min": 256, "max": 256},
            "display": {
                "size_in": 6.55,
                "tech": "P-OLED",
                "refresh_hz": 144,
                "brightness_nits_peak": 1200
            },
            "battery": {
                "capacity_mah": 4400,
                "wired_charging_w": 68,
                "wireless_charging_w": 15
            },
            "cameras": {
                "rear": [
                    {"mp": 50, "role": "main", "ois": True},
                    {"mp": 13, "role": "ultrawide", "ois": False}
                ],
                "front": {"mp": 32}
            },
            "ip_rating": "IP68",
            "dimensions_mm": {"width": 71.99, "height": 158.43, "depth": 7.58},
            "weight_g": 167,
            "connectivity": {
                "sim": "Dual SIM (Nano + eSIM)",
                "bands_5g": ["n1", "n3", "n5", "n7", "n8", "n20", "n28", "n38", "n40", "n41", "n66", "n77", "n78"],
                "wifi": "Wi-Fi 6E",
                "bluetooth": "5.2"
            }
        },
        "variants": [
            {"color": "Eclipse Black", "storage_gb": 256, "price": 599},
            {"color": "Lunar Blue", "storage_gb": 256, "price": 599},
            {"color": "Viva Magenta", "storage_gb": 256, "price": 599}
        ]
    },
    {
        "brand": "Nothing",
        "series": "Phone",
        "model_name": "Phone (2)",
        "release_date": datetime(2023, 7, 11),
        "specs": {
            "os": {"value": "Android 13", "confidence": 0.95, "sources": ["nothing.tech"]},
            "soc": {"value": "Snapdragon 8+ Gen 1", "confidence": 0.95},
            "ram_gb": {"value": 12, "unit": "GB", "confidence": 0.95},
            "storage_gb": {"min": 128, "max": 512},
            "display": {
                "size_in": 6.7,
                "tech": "LTPO OLED",
                "refresh_hz": 120,
                "brightness_nits_peak": 1600
            },
            "battery": {
                "capacity_mah": 4700,
                "wired_charging_w": 45,
                "wireless_charging_w": 15
            },
            "cameras": {
                "rear": [
                    {"mp": 50, "role": "main", "ois": True},
                    {"mp": 50, "role": "ultrawide", "ois": False}
                ],
                "front": {"mp": 32}
            },
            "ip_rating": "IP54",
            "dimensions_mm": {"width": 76.4, "height": 162.1, "depth": 8.6},
            "weight_g": 201,
            "connectivity": {
                "sim": "Dual SIM",
                "bands_5g": ["n1", "n3", "n5", "n7", "n8", "n20", "n28", "n38", "n40", "n41", "n77", "n78"],
                "wifi": "Wi-Fi 6",
                "bluetooth": "5.3"
            }
        },
        "variants": [
            {"color": "Dark Grey", "storage_gb": 128, "price": 599},
            {"color": "Dark Grey", "storage_gb": 256, "price": 699},
            {"color": "White", "storage_gb": 256, "price": 699},
            {"color": "White", "storage_gb": 512, "price": 799}
        ]
    }
]

async def seed_database():
    print("Connecting to MongoDB...")
    
    await db.products.delete_many({})
    await db.variants.delete_many({})
    await db.offers.delete_many({})
    await db.reviews.delete_many({})
    print("Cleared existing data")
    
    for phone_data in sample_phones:
        variants_data = phone_data.pop("variants")
        
        product_doc = phone_data.copy()
        product_doc["_id"] = ObjectId()
        product_doc["category"] = "phone"
        product_doc["created_at"] = datetime.utcnow()
        product_doc["updated_at"] = datetime.utcnow()
        
        await db.products.insert_one(product_doc)
        print(f"Created product: {product_doc['model_name']}")
        
        for variant_data in variants_data:
            variant_doc = {
                "_id": ObjectId(),
                "product_id": product_doc["_id"],
                "color": variant_data["color"],
                "storage_gb": variant_data["storage_gb"],
                "ram_gb": product_doc["specs"]["ram_gb"]["value"],
                "sku": f"{product_doc['brand']}-{product_doc['model_name']}-{variant_data['color']}-{variant_data['storage_gb']}".replace(" ", "-").upper(),
                "mpn": f"{product_doc['brand'][:3].upper()}{int(datetime.now().timestamp())}{random.randint(100, 999)}",
                "os_version": product_doc["specs"]["os"]["value"],
                "battery_mah": product_doc["specs"]["battery"]["capacity_mah"],
                "charging_w": product_doc["specs"]["battery"]["wired_charging_w"],
                "wireless_charging": product_doc["specs"]["battery"]["wireless_charging_w"] > 0,
                "display": {
                    "size_in": product_doc["specs"]["display"]["size_in"],
                    "tech": product_doc["specs"]["display"]["tech"],
                    "refresh_hz": product_doc["specs"]["display"]["refresh_hz"],
                    "brightness_nits": product_doc["specs"]["display"]["brightness_nits_peak"]
                },
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await db.variants.insert_one(variant_doc)
            
            if "default_variant_id" not in product_doc:
                await db.products.update_one(
                    {"_id": product_doc["_id"]},
                    {"$set": {"default_variant_id": variant_doc["_id"]}}
                )
            
            retailers = ["amazon", "bestbuy", "samsung", "walmart"]
            base_price = variant_data["price"]
            
            for retailer in retailers:
                price_variation = random.uniform(-0.05, 0.05)
                retailer_price = round(base_price * (1 + price_variation))
                has_discount = random.random() > 0.7
                is_refurbished = random.random() > 0.85
                
                offer_doc = {
                    "_id": ObjectId(),
                    "variant_id": variant_doc["_id"],
                    "retailer": retailer,
                    "retailer_sku": f"{retailer}-{variant_doc['sku']}",
                    "condition": "refurbished" if is_refurbished else "new",
                    "price_amount": retailer_price * 0.85 if is_refurbished else retailer_price,
                    "price_currency": "USD",
                    "list_price_amount": base_price,
                    "discount_pct": random.randint(5, 15) if has_discount else 0,
                    "promo_text": "Limited Time Offer" if has_discount else None,
                    "availability": "in-stock" if random.random() > 0.2 else "limited",
                    "fulfillment": ["ship", "pickup"],
                    "store_name": "Best Buy Main St" if retailer == "bestbuy" else None,
                    "store_address": "123 Main St, San Francisco, CA 94107" if retailer == "bestbuy" else None,
                    "ship_eta_days": random.randint(1, 5),
                    "url": f"https://www.{retailer}.com/products/{variant_doc['sku']}",
                    "last_seen_at": datetime.utcnow(),
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                await db.offers.insert_one(offer_doc)
        
        review_sources = [
            {"name": "TechRadar", "type": "pro-review", "credibility": 0.9},
            {"name": "GSMArena", "type": "pro-review", "credibility": 0.85},
            {"name": "User Reviews", "type": "user-review", "credibility": 0.6},
            {"name": "Android Authority", "type": "pro-review", "credibility": 0.88}
        ]
        
        num_reviews = random.randint(1, 3)
        for _ in range(num_reviews):
            source = random.choice(review_sources)
            rating = random.uniform(6.5, 9.5)
            
            review_doc = {
                "_id": ObjectId(),
                "product_id": product_doc["_id"],
                "source": source["name"],
                "source_type": source["type"],
                "rating": round(rating, 1),
                "title": f"{product_doc['model_name']} Review",
                "summary": f"The {product_doc['model_name']} offers solid performance with its {product_doc['specs']['soc']['value']} processor and {product_doc['specs']['display']['tech']} display.",
                "pros": [
                    "Great display quality",
                    "Fast performance",
                    "Good battery life"
                ],
                "cons": [
                    "Camera could be better in low light",
                    "No headphone jack"
                ],
                "url": f"https://www.{source['name'].lower().replace(' ', '')}.com/reviews/{product_doc['model_name'].replace(' ', '-').lower()}",
                "credibility_score": source["credibility"],
                "published_at": datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                "last_checked_at": datetime.utcnow(),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await db.reviews.insert_one(review_doc)
    
    print(f"Database seeded successfully!")
    print(f"Created {len(sample_phones)} products with variants, offers, and reviews")

if __name__ == "__main__":
    asyncio.run(seed_database())