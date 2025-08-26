from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class PriceRange(BaseModel):
    min: int
    max: int
    
    @validator('min', 'max', pre=True)
    def round_price(cls, v):
        if v is None:
            return 0
        return int(round(float(v)))

class ProductResponse(BaseModel):
    product_id: str = Field(alias="_id")
    name: str
    description: Optional[str] = None
    category: str
    brand: str
    series: Optional[str] = None
    model_name: str
    image_url: Optional[str] = None
    asin: Optional[str] = None
    release_date: Optional[datetime] = None
    price_range: Optional[PriceRange] = None
    rating: Optional[float] = None
    popularity_rank: Optional[int] = None
    default_variant_id: Optional[str] = None
    specs: Dict[str, Any] = {}
    tags: List[str] = []
    images: Optional[List[Dict[str, Any]]] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @validator('product_id', 'default_variant_id', pre=True)
    def convert_object_id(cls, v):
        if v is None:
            return None
        return str(v)
    
    @validator('price_range', pre=True)
    def convert_price_range(cls, v):
        if not v:
            return None
        if isinstance(v, dict):
            return PriceRange(min=v.get('min', 0), max=v.get('max', 0))
        return v
    
    @validator('specs', pre=True)
    def extract_spec_values(cls, v):
        if not v:
            return {}
        
        result = {}
        for key, value in v.items():
            if isinstance(value, dict):
                # If it has a 'value' field, extract it
                if 'value' in value:
                    result[key] = value['value']
                # If it's a min/max range
                elif 'min' in value and 'max' in value:
                    result[key] = f"{value['min']}-{value['max']}"
                # Otherwise take the first meaningful value
                else:
                    for k, val in value.items():
                        if val and k not in ['confidence', 'sources', 'unit']:
                            result[key] = val
                            break
            else:
                result[key] = value
        return result
    
    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        by_alias = True  # This ensures we output _id instead of id

class VariantResponse(BaseModel):
    variant_id: str = Field(alias="_id")
    product_id: str
    sku: str
    color: Optional[str] = None
    storage: Optional[str] = None
    price: Optional[int] = None
    availability: Optional[str] = None
    
    @validator('variant_id', 'product_id', pre=True)
    def convert_object_id(cls, v):
        if v is None:
            return None
        return str(v)
    
    @validator('price', pre=True)
    def round_price(cls, v):
        if v is None:
            return None
        return int(round(float(v)))
    
    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        by_alias = True  # This ensures we output _id instead of id

class SearchResultItem(BaseModel):
    product_id: str
    category: Optional[str] = None
    brand: str
    model_name: str
    price_range: Optional[PriceRange] = None
    rating: Optional[float] = None
    popularity_rank: Optional[int] = None
    specs: Dict[str, Any] = {}
    score: float = 0
    in_budget: Optional[bool] = None
    
    @validator('price_range', pre=True)
    def convert_price_range(cls, v):
        if not v:
            return None
        if isinstance(v, dict):
            return PriceRange(min=v.get('min', 0), max=v.get('max', 0))
        return v
    
    @validator('score', pre=True)
    def round_score(cls, v):
        return round(float(v), 1)

class CategoryInfo(BaseModel):
    category_id: str
    name: str
    product_count: int
    avg_rating: Optional[float] = None
    price_range: Optional[PriceRange] = None
    top_brands: List[str] = []
    
    @validator('price_range', pre=True)
    def convert_price_range(cls, v):
        if not v:
            return None
        if isinstance(v, dict):
            return PriceRange(min=v.get('min', 0), max=v.get('max', 0))
        return v