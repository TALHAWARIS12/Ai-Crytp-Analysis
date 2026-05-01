from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/crypto_trading_db")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # API Keys
    grok_api_key: str = os.getenv("GROK_API_KEY", "")
    grok_model: str = os.getenv("GROK_MODEL", "grok-beta")
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_proxy: str = os.getenv("TELEGRAM_PROXY", "")
    binance_api_key: str = os.getenv("BINANCE_API_KEY", "")
    binance_api_secret: str = os.getenv("BINANCE_API_SECRET", "")
    binance_api_proxy: str = os.getenv("BINANCE_API_PROXY", "")  # For geo-restricted locations
    
    # Server
    backend_host: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    backend_port: int = int(os.getenv("BACKEND_PORT", 8000))
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    backend_url: str = os.getenv("BACKEND_URL", "http://localhost:8000")
    
    # Security
    jwt_secret: str = os.getenv("JWT_SECRET", "your-secret-key")
    algorithm: str = "HS256"
    
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Features
    rate_limit_enabled: bool = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", 60))
    cache_enabled: bool = os.getenv("CACHE_ENABLED", "True").lower() == "true"
    cache_ttl: int = int(os.getenv("CACHE_TTL", 300))
    
    class Config:
        env_file = ".env"

settings = Settings()
