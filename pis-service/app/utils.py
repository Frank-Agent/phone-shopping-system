from typing import Dict, Any, Optional

def round_price_range(price_range: Optional[Dict[str, float]]) -> Optional[Dict[str, float]]:
    """Round price range values to 2 decimal places"""
    if not price_range:
        return price_range
    return {
        "min": round(price_range.get("min", 0), 2),
        "max": round(price_range.get("max", 0), 2)
    }

def round_product_prices(product: Dict[str, Any]) -> Dict[str, Any]:
    """Round all price-related fields in a product"""
    if "price_range" in product:
        product["price_range"] = round_price_range(product["price_range"])
    if "price" in product:
        product["price"] = round(product["price"], 2)
    return product