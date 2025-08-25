from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from bson import ObjectId
from app.database import db

router = APIRouter()

@router.get("/")
async def get_products(
    category: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    limit: int = Query(10, le=100)
):
    filter_query = {}
    if category:
        filter_query["category"] = category
    if brand:
        filter_query["brand"] = {"$regex": brand, "$options": "i"}
    
    products = await db.products.find(filter_query).limit(limit).to_list(limit)
    
    for product in products:
        product["_id"] = str(product["_id"])
        if product.get("default_variant_id"):
            product["default_variant_id"] = str(product["default_variant_id"])
    
    return products

@router.get("/{product_id}")
async def get_product(product_id: str):
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product ID")
    
    product = await db.products.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product["_id"] = str(product["_id"])
    if product.get("default_variant_id"):
        product["default_variant_id"] = str(product["default_variant_id"])
    
    variants = await db.variants.find({"product_id": ObjectId(product_id)}).to_list(100)
    for variant in variants:
        variant["_id"] = str(variant["_id"])
        variant["product_id"] = str(variant["product_id"])
    
    return {
        "product": product,
        "variants": variants,
        "total_variants": len(variants)
    }

@router.get("/{product_id}/specs/{spec_path}/provenance")
async def get_spec_provenance(product_id: str, spec_path: str):
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product ID")
    
    product = await db.products.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    spec_keys = spec_path.split(".")
    spec = product.get("specs", {})
    
    for key in spec_keys:
        spec = spec.get(key)
        if spec is None:
            raise HTTPException(status_code=404, detail="Spec not found")
    
    return {
        "field": spec_path,
        "value": spec.get("value", spec) if isinstance(spec, dict) else spec,
        "confidence": spec.get("confidence", 0.9) if isinstance(spec, dict) else 0.9,
        "sources": spec.get("sources", ["manufacturer"]) if isinstance(spec, dict) else ["manufacturer"],
        "last_updated": product.get("updated_at")
    }