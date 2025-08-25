from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from bson import ObjectId
from app.database import db

router = APIRouter()

@router.get("/variant/{variant_id}")
async def get_variant_offers(
    variant_id: str,
    country: str = Query("US"),
    postal: Optional[str] = Query(None)
):
    if not ObjectId.is_valid(variant_id):
        raise HTTPException(status_code=400, detail="Invalid variant ID")
    
    offers = await db.offers.find({
        "variant_id": ObjectId(variant_id)
    }).sort("price_amount", 1).to_list(100)
    
    for offer in offers:
        offer["_id"] = str(offer["_id"])
        offer["variant_id"] = str(offer["variant_id"])
        if "price_amount" in offer:
            offer["price_amount"] = round(offer["price_amount"], 2)
    
    best_new = next((o for o in offers if o["condition"] == "new"), None)
    best_refurb = next((o for o in offers if o["condition"] == "refurbished"), None)
    
    return {
        "variant_id": variant_id,
        "country": country,
        "postal": postal,
        "offers": offers,
        "best_new": best_new,
        "best_refurbished": best_refurb,
        "total_offers": len(offers)
    }

@router.post("/batch")
async def batch_price_check(variant_ids: List[str], region: str = "US"):
    results = []
    
    for variant_id in variant_ids:
        if not ObjectId.is_valid(variant_id):
            results.append({
                "variant_id": variant_id,
                "error": "Invalid variant ID"
            })
            continue
        
        offers = await db.offers.find({
            "variant_id": ObjectId(variant_id),
            "condition": "new"
        }).sort("price_amount", 1).limit(1).to_list(1)
        
        if offers:
            offer = offers[0]
            offer["_id"] = str(offer["_id"])
            offer["variant_id"] = str(offer["variant_id"])
            results.append({
                "variant_id": variant_id,
                "cheapest_offer": offer
            })
        else:
            results.append({
                "variant_id": variant_id,
                "cheapest_offer": None
            })
    
    return {
        "region": region,
        "results": results
    }