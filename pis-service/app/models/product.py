from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
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

class SpecValue(BaseModel):
    value: Any
    confidence: float = 0.9
    sources: List[str] = []

class Camera(BaseModel):
    mp: float
    role: str
    ois: bool = False

class Display(BaseModel):
    size_in: float
    tech: str
    refresh_hz: int
    brightness_nits_peak: int

class Battery(BaseModel):
    capacity_mah: int
    wired_charging_w: int
    wireless_charging_w: int = 0

class Connectivity(BaseModel):
    sim: str
    bands_5g: List[str] = []
    wifi: str
    bluetooth: str

class Dimensions(BaseModel):
    width: float
    height: float
    depth: float

class ProductSpecs(BaseModel):
    os: Optional[SpecValue] = None
    soc: Optional[SpecValue] = None
    ram_gb: Optional[SpecValue] = None
    storage_gb: Optional[Dict[str, int]] = None
    display: Optional[Display] = None
    battery: Optional[Battery] = None
    cameras: Optional[Dict[str, Any]] = None
    ip_rating: Optional[str] = None
    dimensions_mm: Optional[Dimensions] = None
    weight_g: Optional[int] = None
    connectivity: Optional[Connectivity] = None

class Product(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    category: str = "phone"
    brand: str
    series: Optional[str] = None
    model_name: str
    release_date: Optional[datetime] = None
    default_variant_id: Optional[PyObjectId] = None
    specs: ProductSpecs
    images: List[Dict[str, Any]] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        protected_namespaces = ()