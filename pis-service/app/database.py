from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

client = AsyncIOMotorClient(settings.mongodb_uri)
db = client[settings.database_name]

products_collection = db["products"]
variants_collection = db["variants"]
offers_collection = db["offers"]
reviews_collection = db["reviews"]