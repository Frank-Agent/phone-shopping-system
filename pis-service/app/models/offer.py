from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from enum import Enum

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, schema, handler):
        schema.update(type="string")
        return schema

class Retailer(str, Enum):
    amazon = "amazon"
    bestbuy = "bestbuy"
    samsung = "samsung"
    apple = "apple"
    walmart = "walmart"
    target = "target"

class Condition(str, Enum):
    new = "new"
    refurbished = "refurbished"
    open_box = "open-box"

class Availability(str, Enum):
    in_stock = "in-stock"
    out_of_stock = "out-of-stock"
    limited = "limited"
    preorder = "preorder"

class Fulfillment(str, Enum):
    ship = "ship"
    pickup = "pickup"

class Offer(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    variant_id: PyObjectId
    retailer: Retailer
    retailer_sku: Optional[str] = None
    condition: Condition = Condition.new
    price_amount: float
    price_currency: str = "USD"
    list_price_amount: Optional[float] = None
    discount_pct: Optional[float] = None
    promo_text: Optional[str] = None
    availability: Availability = Availability.in_stock
    fulfillment: List[Fulfillment] = []
    store_id: Optional[str] = None
    store_name: Optional[str] = None
    store_address: Optional[str] = None
    ship_eta_days: Optional[int] = None
    last_seen_at: datetime = Field(default_factory=datetime.utcnow)
    url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}