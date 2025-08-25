from fastapi import APIRouter, HTTPException, Cookie, Response
from typing import Optional, List
from bson import ObjectId
from app.database import db
from datetime import datetime, timedelta
from pydantic import BaseModel
import uuid
import hashlib

router = APIRouter()

class FavoriteRequest(BaseModel):
    product_id: str

class FavoriteItem(BaseModel):
    product_id: str
    added_at: datetime
    
def get_or_create_user_id(user_token: Optional[str]) -> str:
    """Get user ID from token or create a new one"""
    if user_token:
        return user_token
    # Generate a unique user token
    return str(uuid.uuid4())

def hash_user_token(token: str) -> str:
    """Hash the user token for database storage"""
    return hashlib.sha256(token.encode()).hexdigest()

@router.get("/")
async def get_favorites(
    response: Response,
    user_token: Optional[str] = Cookie(None, alias="user_id")
):
    """Get all favorites for a user"""
    # Get or create user token
    if not user_token:
        user_token = get_or_create_user_id(None)
        response.set_cookie(
            key="user_id",
            value=user_token,
            max_age=365 * 24 * 60 * 60,  # 1 year
            httponly=True,
            samesite="lax"
        )
    
    user_hash = hash_user_token(user_token)
    
    # Get user's favorites
    user_favorites = await db.favorites.find_one({"user_id": user_hash})
    
    if not user_favorites:
        return {
            "favorites": [],
            "count": 0
        }
    
    # Get product details for each favorite
    product_ids = [ObjectId(fav["product_id"]) for fav in user_favorites.get("items", [])]
    products = await db.products.find({"_id": {"$in": product_ids}}).to_list(None)
    
    # Convert ObjectIds to strings and add favorite metadata
    favorites_with_details = []
    for product in products:
        product["_id"] = str(product["_id"])
        if product.get("default_variant_id"):
            product["default_variant_id"] = str(product["default_variant_id"])
        
        # Find the favorite item metadata
        fav_item = next(
            (f for f in user_favorites["items"] if f["product_id"] == product["_id"]),
            None
        )
        
        favorites_with_details.append({
            "product": product,
            "added_at": fav_item["added_at"] if fav_item else None
        })
    
    # Sort by added_at date (newest first)
    favorites_with_details.sort(key=lambda x: x["added_at"] or datetime.min, reverse=True)
    
    return {
        "favorites": favorites_with_details,
        "count": len(favorites_with_details)
    }

@router.post("/add")
async def add_to_favorites(
    request: FavoriteRequest,
    response: Response,
    user_token: Optional[str] = Cookie(None, alias="user_id")
):
    """Add a product to favorites"""
    # Get or create user token
    if not user_token:
        user_token = get_or_create_user_id(None)
        response.set_cookie(
            key="user_id",
            value=user_token,
            max_age=365 * 24 * 60 * 60,  # 1 year
            httponly=True,
            samesite="lax"
        )
    
    user_hash = hash_user_token(user_token)
    product_id = request.product_id
    
    # Verify product exists
    product = await db.products.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get or create user favorites document
    user_favorites = await db.favorites.find_one({"user_id": user_hash})
    
    if not user_favorites:
        # Create new favorites document
        user_favorites = {
            "user_id": user_hash,
            "items": [],
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        await db.favorites.insert_one(user_favorites)
    
    # Check if already in favorites
    if any(item["product_id"] == product_id for item in user_favorites.get("items", [])):
        return {
            "message": "Product already in favorites",
            "product_id": product_id
        }
    
    # Add to favorites
    favorite_item = {
        "product_id": product_id,
        "added_at": datetime.now()
    }
    
    await db.favorites.update_one(
        {"user_id": user_hash},
        {
            "$push": {"items": favorite_item},
            "$set": {"updated_at": datetime.now()}
        }
    )
    
    return {
        "message": "Added to favorites",
        "product_id": product_id,
        "count": len(user_favorites.get("items", [])) + 1
    }

@router.delete("/remove/{product_id}")
async def remove_from_favorites(
    product_id: str,
    response: Response,
    user_token: Optional[str] = Cookie(None, alias="user_id")
):
    """Remove a product from favorites"""
    if not user_token:
        raise HTTPException(status_code=400, detail="No user session found")
    
    user_hash = hash_user_token(user_token)
    
    # Remove from favorites
    result = await db.favorites.update_one(
        {"user_id": user_hash},
        {
            "$pull": {"items": {"product_id": product_id}},
            "$set": {"updated_at": datetime.now()}
        }
    )
    
    if result.modified_count == 0:
        return {
            "message": "Product not in favorites",
            "product_id": product_id
        }
    
    # Get updated count
    user_favorites = await db.favorites.find_one({"user_id": user_hash})
    count = len(user_favorites.get("items", [])) if user_favorites else 0
    
    return {
        "message": "Removed from favorites",
        "product_id": product_id,
        "count": count
    }

@router.post("/toggle")
async def toggle_favorite(
    request: FavoriteRequest,
    response: Response,
    user_token: Optional[str] = Cookie(None, alias="user_id")
):
    """Toggle a product in favorites (add if not exists, remove if exists)"""
    # Get or create user token
    if not user_token:
        user_token = get_or_create_user_id(None)
        response.set_cookie(
            key="user_id",
            value=user_token,
            max_age=365 * 24 * 60 * 60,  # 1 year
            httponly=True,
            samesite="lax"
        )
    
    user_hash = hash_user_token(user_token)
    product_id = request.product_id
    
    # Get user favorites
    user_favorites = await db.favorites.find_one({"user_id": user_hash})
    
    # Check if product is already in favorites
    is_favorite = False
    if user_favorites and any(item["product_id"] == product_id for item in user_favorites.get("items", [])):
        is_favorite = True
    
    if is_favorite:
        # Remove from favorites
        await db.favorites.update_one(
            {"user_id": user_hash},
            {
                "$pull": {"items": {"product_id": product_id}},
                "$set": {"updated_at": datetime.now()}
            }
        )
        action = "removed"
    else:
        # Verify product exists
        product = await db.products.find_one({"_id": ObjectId(product_id)})
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Add to favorites
        if not user_favorites:
            # Create new favorites document
            user_favorites = {
                "user_id": user_hash,
                "items": [],
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            await db.favorites.insert_one(user_favorites)
        
        favorite_item = {
            "product_id": product_id,
            "added_at": datetime.now()
        }
        
        await db.favorites.update_one(
            {"user_id": user_hash},
            {
                "$push": {"items": favorite_item},
                "$set": {"updated_at": datetime.now()}
            }
        )
        action = "added"
    
    # Get updated count
    user_favorites = await db.favorites.find_one({"user_id": user_hash})
    count = len(user_favorites.get("items", [])) if user_favorites else 0
    
    return {
        "action": action,
        "product_id": product_id,
        "is_favorite": action == "added",
        "count": count
    }

@router.delete("/clear")
async def clear_favorites(
    user_token: Optional[str] = Cookie(None, alias="user_id")
):
    """Clear all favorites for a user"""
    if not user_token:
        raise HTTPException(status_code=400, detail="No user session found")
    
    user_hash = hash_user_token(user_token)
    
    # Clear favorites
    result = await db.favorites.update_one(
        {"user_id": user_hash},
        {
            "$set": {
                "items": [],
                "updated_at": datetime.now()
            }
        }
    )
    
    return {
        "message": "Favorites cleared",
        "count": 0
    }

@router.get("/check/{product_id}")
async def check_favorite(
    product_id: str,
    user_token: Optional[str] = Cookie(None, alias="user_id")
):
    """Check if a product is in favorites"""
    if not user_token:
        return {"is_favorite": False}
    
    user_hash = hash_user_token(user_token)
    
    # Get user favorites
    user_favorites = await db.favorites.find_one({"user_id": user_hash})
    
    if not user_favorites:
        return {"is_favorite": False}
    
    # Check if product is in favorites
    is_favorite = any(item["product_id"] == product_id for item in user_favorites.get("items", []))
    
    return {
        "product_id": product_id,
        "is_favorite": is_favorite
    }

@router.get("/count")
async def get_favorites_count(
    user_token: Optional[str] = Cookie(None, alias="user_id")
):
    """Get the count of favorites for a user"""
    if not user_token:
        return {"count": 0}
    
    user_hash = hash_user_token(user_token)
    
    # Get user favorites
    user_favorites = await db.favorites.find_one({"user_id": user_hash})
    
    if not user_favorites:
        return {"count": 0}
    
    return {"count": len(user_favorites.get("items", []))}