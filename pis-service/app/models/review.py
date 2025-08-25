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

class SourceType(str, Enum):
    pro_review = "pro-review"
    user_review = "user-review"

class Review(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    product_id: PyObjectId
    source: str
    source_type: SourceType
    rating: float = Field(ge=0, le=10)
    title: Optional[str] = None
    summary: Optional[str] = None
    pros: List[str] = []
    cons: List[str] = []
    url: Optional[str] = None
    credibility_score: float = Field(default=0.5, ge=0, le=1)
    published_at: Optional[datetime] = None
    last_checked_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}