"""Configuration settings for EPA Envirofacts MCP Server."""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # EPA API Configuration
    epa_api_base_url: str = "https://data.epa.gov/efservice/"
    request_timeout: int = 300
    retry_attempts: int = 3
    max_results_per_query: int = 1000
    
    # Geocoding Configuration
    geocoding_service: str = "nominatim"
    geocoding_user_agent: str = "epa-envirofacts-mcp/1.0"
    geocoding_api_key: Optional[str] = None
    
    # Logging Configuration
    log_level: str = "INFO"
    
    # Optional: Redis for caching (not implemented in Phase 1)
    redis_url: Optional[str] = None
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False
    )


# Global settings instance
settings = Settings()
