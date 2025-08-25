from fastapi import APIRouter, Query
from typing import Optional, List, Dict, Any
from bson import ObjectId
from app.database import db
from app.models.response import SearchResultItem

router = APIRouter()

@router.get("/")
async def search_products(
    category: Optional[str] = Query(None),
    budget_max: Optional[int] = Query(None),
    brand: Optional[str] = Query(None),
    min_rating: Optional[float] = Query(None),
    sort: str = Query("rating", regex="^(rating|price|popularity)$"),
    limit: int = Query(20, le=100)
):
    filter_query = {}
    
    if category:
        filter_query["category"] = category
    
    if brand:
        filter_query["brand"] = {"$regex": brand, "$options": "i"}
    
    if min_rating:
        filter_query["rating"] = {"$gte": min_rating}
    
    # Get products matching filters
    products = await db.products.find(filter_query).to_list(limit * 2)  # Get extra for budget filtering
    results = []
    
    for product in products:
        product_id = product["_id"]
        
        # Get price information from variants and offers
        price_range = {"min": float('inf'), "max": 0}
        in_budget = False
        
        variants = await db.variants.find({"product_id": product_id}).to_list(10)
        
        for variant in variants:
            offers = await db.offers.find({
                "variant_id": variant["_id"],
                "condition": "new"
            }).to_list(10)
            
            for offer in offers:
                price = offer["price_amount"]
                if price < price_range["min"]:
                    price_range["min"] = price
                if price > price_range["max"]:
                    price_range["max"] = price
                
                if budget_max and price <= budget_max:
                    in_budget = True
        
        # Skip if outside budget
        if budget_max and not in_budget and price_range["min"] != float('inf'):
            continue
        
        # Use price_range from product if no offers found
        if price_range["min"] == float('inf') and product.get("price_range"):
            price_range = product["price_range"]
            if budget_max:
                in_budget = price_range["min"] <= budget_max
        
        # Skip if still outside budget
        if budget_max and not in_budget:
            continue
        
        # Build generic spec summary
        spec_summary = {}
        if isinstance(product.get("specs"), dict):
            # Extract key specs dynamically
            for key, value in product["specs"].items():
                if isinstance(value, dict):
                    # Handle nested spec objects
                    if "value" in value:
                        spec_summary[key] = value["value"]
                    elif "min" in value and "max" in value:
                        spec_summary[key] = f"{value['min']}-{value['max']}"
                    else:
                        # Take first meaningful value
                        for k, v in value.items():
                            if v and k not in ["confidence", "sources"]:
                                spec_summary[key] = v
                                break
                elif value:
                    spec_summary[key] = value
        
        # Calculate score based on available metrics
        score = 0
        
        # Rating score
        if product.get("rating"):
            score += product["rating"] * 10
        
        # Price score (lower is better if within budget)
        if budget_max and price_range["min"] != float('inf'):
            price_score = (budget_max - price_range["min"]) / budget_max * 30
            score += max(0, price_score)
        
        # Popularity score
        if product.get("popularity_rank"):
            score += max(0, 100 - product["popularity_rank"])
        
        final_price_range = price_range if price_range["min"] != float('inf') else product.get("price_range", {"min": 0, "max": 0})
        results.append(SearchResultItem(
            product_id=str(product_id),
            category=product.get("category"),
            brand=product["brand"],
            model_name=product["model_name"],
            price_range=final_price_range,
            rating=product.get("rating"),
            popularity_rank=product.get("popularity_rank"),
            specs=spec_summary,
            score=score,
            in_budget=in_budget if budget_max else None
        ))
    
    # Sort based on selected criteria
    if sort == "price":
        results.sort(key=lambda x: x.price_range.min if x.price_range else 0)
    elif sort == "popularity":
        results.sort(key=lambda x: x.popularity_rank or 999)
    else:  # Default to rating/score
        results.sort(key=lambda x: x.score, reverse=True)
    
    return {
        "query": {
            "category": category,
            "budget_max": budget_max,
            "brand": brand,
            "min_rating": min_rating,
            "sort": sort
        },
        "total_results": len(results),
        "products": [r.dict() for r in results[:limit]]
    }