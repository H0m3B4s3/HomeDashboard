import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application settings
    app_name: str = "HomeBase Calendar"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Database settings
    database_url: str = "sqlite+aiosqlite:///./database.db"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Calendar sync settings
    sync_interval_minutes: int = 15
    max_sync_retries: int = 3
    
    # CalDAV (iCloud) credentials for upward sync
    caldav_url: str = "https://caldav.icloud.com"
    icloud_username: Optional[str] = None  # Apple ID (typically email)
    icloud_password: Optional[str] = None  # App-specific password
    icloud_calendar_url: str = "webcal://p43-caldav.icloud.com/published/2/Mzk5NDQ4NDUzOTk0NDg0NYieABKiuSspjU8oqXOZnTvGWNwhKf6cpBl8WkUQZDQhqNWjzFxzS5-0BzlIZ9P1IXQtpDvRv0Xgs5PLYMQbjLc"
    
    # Weather API settings (Phase 2)
    weather_api_key: Optional[str] = None
    weather_zip_code: Optional[str] = None
    
    # Security settings
    secret_key: str = "your-secret-key-change-this-in-production"
    access_token_expire_minutes: int = 30
    
    # File paths
    base_dir: Path = Path(__file__).parent
    static_dir: Path = base_dir.parent / "frontend" / "static"
    templates_dir: Path = base_dir.parent / "frontend" / "templates"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Create settings instance
settings = Settings()

# Ensure directories exist
settings.static_dir.mkdir(parents=True, exist_ok=True)
settings.templates_dir.mkdir(parents=True, exist_ok=True) 