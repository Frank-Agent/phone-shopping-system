from fastapi import APIRouter
from app.database import db
from typing import List, Dict, Any
from app.models.response import CategoryInfo, ProductResponse

router = APIRouter()

@router.get("/")
async def get_categories():
    """Get all available product categories dynamically from database"""
    
    # Get distinct categories from products collection
    pipeline = [
        {
            "$group": {
                "_id": "$category",
                "count": {"$sum": 1},
                "avg_rating": {"$avg": "$rating"},
                "min_price": {"$min": "$price_range.min"},
                "max_price": {"$max": "$price_range.max"},
                "brands": {"$addToSet": "$brand"}
            }
        },
        {
            "$project": {
                "category": "$_id",
                "product_count": "$count",
                "avg_rating": {"$round": ["$avg_rating", 1]},
                "price_range": {
                    "min": "$min_price",
                    "max": "$max_price"
                },
                "top_brands": {"$slice": ["$brands", 5]},
                "_id": 0
            }
        },
        {"$sort": {"product_count": -1}}
    ]
    
    categories = await db.products.aggregate(pipeline).to_list(None)
    
    # Format categories with display names
    formatted_categories = []
    for cat in categories:
        # Convert category ID to display name
        display_name = cat["category"].replace("_", " ").title()
        if cat["category"] == "tvs":
            display_name = "Smart TVs"
        elif cat["category"] == "gaming_consoles":
            display_name = "Gaming Consoles"
        elif cat["category"] == "smart_home":
            display_name = "Smart Home Devices"
            
        formatted_categories.append(CategoryInfo(
            category_id=cat["category"],
            name=display_name,
            product_count=cat["product_count"],
            avg_rating=cat["avg_rating"],
            price_range=cat["price_range"],
            top_brands=cat["top_brands"]
        ))
    
    return {
        "categories": [cat.dict() for cat in formatted_categories],
        "total": len(formatted_categories)
    }

@router.get("/{category_id}/top")
async def get_top_products(category_id: str, limit: int = 10):
    """Get top products in a category by popularity rank"""
    
    # Check if category exists
    category_exists = await db.products.find_one({"category": category_id})
    if not category_exists:
        return {"error": "Category not found", "available_categories": await get_category_list()}
    
    # Get top products sorted by popularity rank or rating
    products = await db.products.find(
        {"category": category_id}
    ).sort([("popularity_rank", 1), ("rating", -1)]).limit(limit).to_list(limit)
    
    # Convert to ProductResponse models
    product_responses = [ProductResponse(**product) for product in products]
    
    # Get category info
    display_name = category_id.replace("_", " ").title()
    if category_id == "tvs":
        display_name = "Smart TVs"
    elif category_id == "gaming_consoles":
        display_name = "Gaming Consoles"
    elif category_id == "smart_home":
        display_name = "Smart Home Devices"
    
    return {
        "category": {
            "id": category_id,
            "name": display_name
        },
        "products": [p.dict() for p in product_responses],
        "count": len(product_responses)
    }

@router.get("/{category_id}/brands")
async def get_category_brands(category_id: str):
    """Get all brands available in a specific category"""
    
    brands = await db.products.distinct("brand", {"category": category_id})
    
    if not brands:
        return {"error": "Category not found or no brands available"}
    
    # Get count for each brand
    brand_counts = []
    for brand in brands:
        count = await db.products.count_documents({"category": category_id, "brand": brand})
        brand_counts.append({
            "brand": brand,
            "product_count": count
        })
    
    # Sort by product count
    brand_counts.sort(key=lambda x: x["product_count"], reverse=True)
    
    return {
        "category": category_id,
        "brands": brand_counts,
        "total": len(brand_counts)
    }

async def get_category_list():
    """Helper function to get list of available categories"""
    categories = await db.products.distinct("category")
    return categories