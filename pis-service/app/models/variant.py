from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from bson import ObjectId

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

class Variant(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    product_id: PyObjectId
    sku: Optional[str] = None
    mpn: Optional[str] = None
    gtin_ean_upc: Optional[str] = None
    color: str
    storage_gb: int
    ram_gb: Optional[int] = None
    other_differentiators: Optional[Dict[str, Any]] = None
    dimensions_mm: Optional[Dict[str, float]] = None
    weight_g: Optional[int] = None
    os_version: Optional[str] = None
    connectivity: Optional[Dict[str, Any]] = None
    battery_mah: Optional[int] = None
    charging_w: Optional[int] = None
    wireless_charging: Optional[bool] = False
    display: Optional[Dict[str, Any]] = None
    camera: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}