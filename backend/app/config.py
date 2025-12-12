"""
CyberNexus Configuration Module

Handles all application configuration using Pydantic Settings.
"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "CyberNexus"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Security
    SECRET_KEY: str = Field(default="your-super-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Data Storage
    DATA_DIR: Path = Path("data")
    GRAPH_DIR: Path = Path("data/graph")
    INDEX_DIR: Path = Path("data/indices")
    EVENTS_DIR: Path = Path("data/events")
    CACHE_DIR: Path = Path("data/cache")
    BLOBS_DIR: Path = Path("data/blobs")
    
    # Collectors
    # Tor proxy host - defaults to "localhost" for local dev
    # For Railway deployment, set TOR_PROXY_HOST=tor-service via environment variable
    # Railway automatically resolves service names via internal DNS
    TOR_PROXY_HOST: str = Field(default="localhost", env="TOR_PROXY_HOST")
    TOR_PROXY_PORT: int = Field(default=9050, env="TOR_PROXY_PORT")
    TOR_PROXY_TYPE: str = Field(default="socks5h", env="TOR_PROXY_TYPE")
    TOR_TIMEOUT: int = 30
    TOR_REQUIRED: bool = Field(default=False, env="TOR_REQUIRED")
    TOR_HEALTH_CHECK_TIMEOUT: int = Field(default=60, env="TOR_HEALTH_CHECK_TIMEOUT")  # Increased to 60s for slow Tor connections
    REQUEST_TIMEOUT: int = 30
    MAX_CONCURRENT_REQUESTS: int = 10
    
    # Dark Web Intelligence - Keyword-Focused Crawler
    CRAWLER_DB_PATH: str = "crawlers"
    CRAWLER_DB_NAME: str = "url_database.db"
    CRAWLER_SCORE_CATEGORIE: int = 20
    CRAWLER_SCORE_KEYWORDS: int = 40
    CRAWLER_COUNT_CATEGORIES: int = 5
    CRAWLER_DAYS_TIME: int = 10
    DARKWEB_BATCH_SIZE: int = Field(default=5, env="DARKWEB_BATCH_SIZE")  # Number of URLs to process per batch
    
    # Dark Web Parallel Processing
    DARKWEB_MAX_WORKERS: int = Field(default=5, env="DARKWEB_MAX_WORKERS")  # Thread pool size for parallel crawling
    DARKWEB_DISCOVERY_TIMEOUT: int = Field(default=300, env="DARKWEB_DISCOVERY_TIMEOUT")  # 5 min timeout per discovery engine
    DARKWEB_CRAWL_TIMEOUT: int = Field(default=600, env="DARKWEB_CRAWL_TIMEOUT")  # 10 min timeout per crawl batch
    
    # Dark Web Intelligence - Site Analyzer (if using separate DB)
    ANALYZER_DB_HOST: Optional[str] = None
    ANALYZER_DB_NAME: Optional[str] = None
    ANALYZER_DB_USER: Optional[str] = None
    ANALYZER_DB_PASS: Optional[str] = None
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30
    
    # API Timeouts
    API_REQUEST_TIMEOUT: int = Field(default=300, env="API_REQUEST_TIMEOUT")  # 5 minutes for long-running jobs
    DARKWEB_JOB_TIMEOUT: int = Field(default=1800, env="DARKWEB_JOB_TIMEOUT")  # 30 minutes max for darkweb jobs
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    LOG_DETAILED_TIMING: bool = Field(default=True, env="LOG_DETAILED_TIMING")  # Enable verbose timing logs
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


def init_directories():
    """Create required data directories."""
    dirs = [
        settings.DATA_DIR,
        settings.GRAPH_DIR,
        settings.INDEX_DIR,
        settings.EVENTS_DIR,
        settings.CACHE_DIR,
        settings.BLOBS_DIR,
    ]
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)


