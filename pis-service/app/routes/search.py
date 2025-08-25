from fastapi import APIRouter, Query
from typing import Optional
from bson import ObjectId
from app.database import db

router = APIRouter()

@router.get("/")
async def search_products(
    category: str = Query("phone"),
    budget_max: Optional[int] = Query(None),
    os: Optional[str] = Query(None),
    min_ram: Optional[int] = Query(None),
    min_storage: Optional[int] = Query(None),
    brand: Optional[str] = Query(None),
    camera_importance: str = Query("medium", regex="^(low|medium|high)$"),
    sort: str = Query("value")
):
    filter_query = {"category": category}
    
    if os:
        filter_query["specs.os.value"] = {"$regex": os, "$options": "i"}
    
    if brand:
        filter_query["brand"] = {"$regex": brand, "$options": "i"}
    
    if min_ram:
        filter_query["specs.ram_gb.value"] = {"$gte": min_ram}
    
    products = await db.products.find(filter_query).to_list(100)
    results = []
    
    for product in products:
        product_id = product["_id"]
        variants = await db.variants.find({"product_id": product_id}).to_list(100)
        
        price_range = {"min": float('inf'), "max": 0}
        in_budget = False
        
        for variant in variants:
            offers = await db.offers.find({
                "variant_id": variant["_id"],
                "condition": "new"
            }).to_list(100)
            
            for offer in offers:
                price = offer["price_amount"]
                if price < price_range["min"]:
                    price_range["min"] = price
                if price > price_range["max"]:
                    price_range["max"] = price
                
                if budget_max and price <= budget_max:
                    in_budget = True
        
        if budget_max and not in_budget:
            continue
        
        if min_storage and product["specs"].get("storage_gb", {}).get("min", 0) < min_storage:
            continue
        
        spec_ranges = {
            "price": price_range if price_range["min"] != float('inf') else {"min": 0, "max": 0},
            "ram": f"{product['specs'].get('ram_gb', {}).get('value', 'N/A')} GB",
            "storage": f"{product['specs'].get('storage_gb', {}).get('min', 'N/A')}-{product['specs'].get('storage_gb', {}).get('max', 'N/A')} GB",
            "battery": f"{product['specs'].get('battery', {}).get('capacity_mah', 'N/A')} mAh",
            "display": f"{product['specs'].get('display', {}).get('size_in', 'N/A')}\" {product['specs'].get('display', {}).get('refresh_hz', 'N/A')}Hz",
            "charging": f"{product['specs'].get('battery', {}).get('wired_charging_w', 'N/A')}W"
        }
        
        score = 0
        if budget_max and price_range["min"] != float('inf'):
            score += (budget_max - price_range["min"]) / budget_max * 30
        
        ram_value = product["specs"].get("ram_gb", {}).get("value", 0)
        score += ram_value * 5
        
        battery_mah = product["specs"].get("battery", {}).get("capacity_mah", 0)
        score += battery_mah / 100
        
        refresh_hz = product["specs"].get("display", {}).get("refresh_hz", 0)
        score += refresh_hz / 10
        
        if camera_importance == "low":
            score += 10
        elif camera_importance == "high":
            cameras = product["specs"].get("cameras", {}).get("rear", [])
            if cameras:
                main_camera = next((c for c in cameras if c.get("role") == "main"), None)
                if main_camera:
                    score += main_camera.get("mp", 0) / 5
        
        results.append({
            "product_id": str(product_id),
            "brand": product["brand"],
            "model_name": product["model_name"],
            "specs": product["specs"],
            "spec_ranges": spec_ranges,
            "score": score,
            "explanation": "Within budget" if in_budget else "Best value"
        })
    
    results.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "query": {
            "category": category,
            "budget_max": budget_max,
            "os": os,
            "min_ram": min_ram,
            "min_storage": min_storage,
            "brand": brand,
            "camera_importance": camera_importance
        },
        "total_results": len(results),
        "products": results[:10]
    }