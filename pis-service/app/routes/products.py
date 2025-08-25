from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from bson import ObjectId
from app.database import db
from app.models.response import ProductResponse, VariantResponse

router = APIRouter()

@router.get("/", response_model=List[ProductResponse])
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
    return [ProductResponse(**product) for product in products]

@router.get("/{product_id}")
async def get_product(product_id: str):
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product ID")
    
    product = await db.products.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    variants = await db.variants.find({"product_id": ObjectId(product_id)}).to_list(100)
    
    return {
        "product": ProductResponse(**product),
        "variants": [VariantResponse(**variant) for variant in variants],
        "total_variants": len(variants)
    }

@router.get("/{product_id}/variants", response_model=Dict[str, Any])
async def get_product_variants(product_id: str):
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product ID")
    
    variants = await db.variants.find({"product_id": ObjectId(product_id)}).to_list(100)
    
    return {
        "product_id": product_id,
        "variants": [VariantResponse(**variant) for variant in variants],
        "total": len(variants)
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