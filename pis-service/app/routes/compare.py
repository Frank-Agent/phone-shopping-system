from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional, Dict, Any
from bson import ObjectId
from app.database import db
from datetime import datetime
from pydantic import BaseModel
import uuid
from app.models.response import ProductResponse

class AddProductRequest(BaseModel):
    product_id: str

router = APIRouter()

# In-memory storage for comparison sessions (in production, use Redis or database)
comparison_sessions = {}

@router.post("/session")
async def create_comparison_session():
    """Create a new comparison session"""
    session_id = str(uuid.uuid4())
    comparison_sessions[session_id] = {
        "product_ids": [],
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    return {"session_id": session_id}

@router.get("/session/{session_id}")
async def get_comparison_session(session_id: str):
    """Get products in a comparison session"""
    if session_id not in comparison_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = comparison_sessions[session_id]
    product_ids = [ObjectId(pid) for pid in session["product_ids"]]
    
    if not product_ids:
        return {
            "session_id": session_id,
            "products": [],
            "comparison": {}
        }
    
    # Fetch all products
    products_raw = await db.products.find({"_id": {"$in": product_ids}}).to_list(None)
    
    # Convert to ProductResponse models
    products = [ProductResponse(**product) for product in products_raw]
    
    # Build comparison matrix
    comparison = await build_comparison_matrix([p.dict() for p in products])
    
    return {
        "session_id": session_id,
        "products": [p.dict() for p in products],
        "comparison": comparison
    }

@router.post("/session/{session_id}/add")
async def add_to_comparison(session_id: str, request: AddProductRequest):
    """Add a product to comparison session"""
    if session_id not in comparison_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    product_id = request.product_id
    
    session = comparison_sessions[session_id]
    
    # Limit to 4 products
    if len(session["product_ids"]) >= 4:
        return {"error": "Maximum 4 products can be compared", "session_id": session_id}
    
    # Check if product exists
    product = await db.products.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Add if not already in comparison
    if product_id not in session["product_ids"]:
        session["product_ids"].append(product_id)
        session["updated_at"] = datetime.now()
    
    return {
        "session_id": session_id,
        "product_ids": session["product_ids"],
        "count": len(session["product_ids"])
    }

@router.delete("/session/{session_id}/remove/{product_id}")
async def remove_from_comparison(session_id: str, product_id: str):
    """Remove a product from comparison session"""
    if session_id not in comparison_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = comparison_sessions[session_id]
    
    if product_id in session["product_ids"]:
        session["product_ids"].remove(product_id)
        session["updated_at"] = datetime.now()
    
    return {
        "session_id": session_id,
        "product_ids": session["product_ids"],
        "count": len(session["product_ids"])
    }

@router.delete("/session/{session_id}")
async def clear_comparison(session_id: str):
    """Clear all products from comparison session"""
    if session_id not in comparison_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    comparison_sessions[session_id]["product_ids"] = []
    comparison_sessions[session_id]["updated_at"] = datetime.now()
    
    return {"session_id": session_id, "cleared": True}

@router.get("/compare")
async def compare_products(product_ids: str = Query(..., description="Comma-separated product IDs")):
    """Direct comparison of products without session"""
    ids = product_ids.split(",")
    
    if len(ids) > 4:
        raise HTTPException(status_code=400, detail="Maximum 4 products can be compared")
    
    object_ids = [ObjectId(pid.strip()) for pid in ids]
    products_raw = await db.products.find({"_id": {"$in": object_ids}}).to_list(None)
    
    if not products_raw:
        return {"products": [], "comparison": {}}
    
    # Convert to ProductResponse models
    products = [ProductResponse(**product) for product in products_raw]
    
    # Build comparison matrix
    comparison = await build_comparison_matrix([p.dict() for p in products])
    
    return {
        "products": [p.dict() for p in products],
        "comparison": comparison
    }

async def build_comparison_matrix(products: List[Dict]) -> Dict[str, Any]:
    """Build a comparison matrix for products"""
    if not products:
        return {}
    
    comparison = {
        "basic_info": {},
        "pricing": {},
        "specs": {},
        "ratings": {},
        "availability": {}
    }
    
    # Extract common spec keys
    all_spec_keys = set()
    for product in products:
        if isinstance(product.get("specs"), dict):
            all_spec_keys.update(product["specs"].keys())
    
    for product in products:
        # Use product_id since we're using Pydantic models
        product_id = str(product.get("product_id", ""))
        
        # Basic info
        comparison["basic_info"][product_id] = {
            "brand": product.get("brand"),
            "model": product.get("model_name"),
            "category": product.get("category")
        }
        
        # Pricing
        price_range = product.get("price_range", {})
        comparison["pricing"][product_id] = {
            "min": price_range.get("min", 0),
            "max": price_range.get("max", 0),
            "currency": "USD"
        }
        
        # Get best offer
        if product.get("default_variant_id"):
            best_offer = await db.offers.find_one(
                {"variant_id": ObjectId(product["default_variant_id"]), "condition": "new"},
                sort=[("price_amount", 1)]
            )
            if best_offer:
                comparison["pricing"][product_id]["best_price"] = best_offer["price_amount"]
                comparison["pricing"][product_id]["retailer"] = best_offer.get("retailer")
        
        # Specs - normalize for comparison
        comparison["specs"][product_id] = {}
        for key in all_spec_keys:
            spec_value = product.get("specs", {}).get(key)
            if spec_value:
                # Extract value from different formats
                if isinstance(spec_value, dict):
                    if "value" in spec_value:
                        comparison["specs"][product_id][key] = spec_value["value"]
                    elif "min" in spec_value and "max" in spec_value:
                        comparison["specs"][product_id][key] = f"{spec_value['min']}-{spec_value['max']}"
                    else:
                        # Get first meaningful value
                        for k, v in spec_value.items():
                            if v and k not in ["confidence", "sources"]:
                                comparison["specs"][product_id][key] = v
                                break
                else:
                    comparison["specs"][product_id][key] = spec_value
            else:
                comparison["specs"][product_id][key] = "—"
        
        # Ratings
        comparison["ratings"][product_id] = {
            "average": product.get("rating", 0),
            "popularity_rank": product.get("popularity_rank")
        }
        
        # Get review count
        review_count = await db.reviews.count_documents({"product_id": ObjectId(product_id)})
        comparison["ratings"][product_id]["review_count"] = review_count
        
        # Availability
        variant_count = await db.variants.count_documents({"product_id": ObjectId(product_id)})
        offer_count = 0
        if variant_count > 0:
            variants = await db.variants.find({"product_id": ObjectId(product_id)}).to_list(None)
            for variant in variants:
                offer_count += await db.offers.count_documents({"variant_id": variant["_id"]})
        
        comparison["availability"][product_id] = {
            "variants": variant_count,
            "offers": offer_count,
            "in_stock": offer_count > 0
        }
    
    # Add spec labels for display
    comparison["spec_labels"] = {
        "display": "Display",
        "storage": "Storage",
        "ram": "RAM",
        "chip": "Processor",
        "battery": "Battery",
        "camera": "Camera",
        "os": "Operating System",
        "connectivity": "Connectivity",
        "weight": "Weight",
        "dimensions": "Dimensions"
    }
    
    return comparison

# Cleanup old sessions periodically (in production, use a background task)
async def cleanup_old_sessions():
    """Remove sessions older than 24 hours"""
    cutoff = datetime.now().timestamp() - 86400  # 24 hours
    to_remove = []
    for session_id, session in comparison_sessions.items():
        if session["created_at"].timestamp() < cutoff:
            to_remove.append(session_id)
    for session_id in to_remove:
        del comparison_sessions[session_id]