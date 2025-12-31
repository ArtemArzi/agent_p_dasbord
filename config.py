"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    # Supabase
    supabase_url: str
    supabase_service_key: str
    
    # App
    app_secret: str
    app_port: int = 8080
    app_host: str = "0.0.0.0"
    
    # Optional
    debug: bool = False


settings = Settings()

