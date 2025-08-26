from fastapi import APIRouter, HTTPException
from bson import ObjectId
from app.database import db
from typing import Dict, Any

router = APIRouter()

@router.get("/product/{product_id}/summary")
async def get_review_summary(product_id: str) -> Dict[str, Any]:
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product ID")
    
    product = await db.products.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    reviews = await db.reviews.find({
        "product_id": ObjectId(product_id)
    }).sort("credibility_score", -1).to_list(100)
    
    if not reviews:
        return {
            "product_id": product_id,
            "model_name": product.get("model_name", product.get("name", "Unknown")),
            "coverage_level": "none",
            "message": "No reviews available for this product",
            "reviews": []
        }
    
    pro_reviews = [r for r in reviews if r.get("source_type") == "pro-review"]
    user_reviews = [r for r in reviews if r.get("source_type") == "user-review" or r.get("source_type") is None]
    
    coverage_level = "low"
    if len(reviews) >= 10:
        coverage_level = "high"
    elif len(reviews) >= 5:
        coverage_level = "medium"
    
    avg_rating = sum(r.get("rating", 0) for r in reviews) / len(reviews) if reviews else 0
    avg_credibility = sum(r.get("credibility_score", 7) for r in reviews) / len(reviews) if reviews else 0
    
    all_pros = []
    all_cons = []
    for review in reviews:
        all_pros.extend(review.get("pros", []))
        all_cons.extend(review.get("cons", []))
    
    pro_consensus = list(set(all_pros))[:5]
    con_consensus = list(set(all_cons))[:3]
    
    summary_message = ""
    if coverage_level == "low":
        summary_message = f"Limited reviews available ({len(pro_reviews)} professional, {len(user_reviews)} user reviews). The available reviews suggest "
    elif coverage_level == "medium":
        summary_message = f"Based on {len(pro_reviews)} professional reviews and {len(user_reviews)} user reviews, "
    else:
        summary_message = f"Well-reviewed product with {len(pro_reviews)} professional sources. Consensus shows "
    
    summary_message += f"an average rating of {avg_rating:.1f}/10. "
    
    if pro_consensus:
        summary_message += f"Main strengths: {', '.join(pro_consensus[:3])}. "
    if con_consensus:
        summary_message += f"Common concerns: {', '.join(con_consensus[:2])}."
    
    review_list = []
    for review in reviews[:5]:
        review_list.append({
            "source": review.get("source", review.get("reviewer_name", "User")),
            "type": review.get("source_type", "user-review"),
            "rating": review.get("rating", 0),
            "credibility": review.get("credibility_score", 7),
            "summary": review.get("summary", review.get("comment", "")),
            "url": review.get("url", "")
        })
    
    return {
        "product_id": product_id,
        "model_name": product.get("model_name", product.get("name", "Unknown")),
        "coverage_level": coverage_level,
        "average_rating": round(avg_rating, 1),
        "average_credibility": round(avg_credibility, 2),
        "pro_consensus": pro_consensus,
        "con_consensus": con_consensus,
        "summary": summary_message,
        "credibility_breakdown": {
            "pro_reviews": len(pro_reviews),
            "user_reviews": len(user_reviews),
            "avg_credibility": round(avg_credibility, 2)
        },
        "reviews": review_list
    }