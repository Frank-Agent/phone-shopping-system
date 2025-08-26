from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    mongodb_uri: str = "mongodb://localhost:27017"
    database_name: str = "pis_service"
    port: int = 8000
    env: str = "development"
    bestbuy_api_key: Optional[str] = ""
    
    class Config:
        env_file = ".env"

settings = Settings()