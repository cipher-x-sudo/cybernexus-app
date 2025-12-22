from pathlib import Path
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
import json


class Settings(BaseSettings):
    
    APP_NAME: str = "CyberNexus"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    SECRET_KEY: str = Field(default="your-super-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    DATA_DIR: Path = Path("data")
    GRAPH_DIR: Path = Path("data/graph")
    INDEX_DIR: Path = Path("data/indices")
    EVENTS_DIR: Path = Path("data/events")
    CACHE_DIR: Path = Path("data/cache")
    BLOBS_DIR: Path = Path("data/blobs")
    
    TOR_PROXY_HOST: str = Field(default="localhost", env="TOR_PROXY_HOST")
    TOR_PROXY_PORT: int = Field(default=9050, env="TOR_PROXY_PORT")
    TOR_PROXY_TYPE: str = Field(default="socks5h", env="TOR_PROXY_TYPE")
    TOR_TIMEOUT: int = 30
    TOR_REQUIRED: bool = Field(default=False, env="TOR_REQUIRED")
    TOR_HEALTH_CHECK_TIMEOUT: int = Field(default=60, env="TOR_HEALTH_CHECK_TIMEOUT")
    REQUEST_TIMEOUT: int = 30
    MAX_CONCURRENT_REQUESTS: int = 10
    
    CRAWLER_DB_PATH: str = "crawlers"
    CRAWLER_DB_NAME: str = "url_database.db"
    CRAWLER_SCORE_CATEGORIE: int = 20
    CRAWLER_SCORE_KEYWORDS: int = 40
    CRAWLER_COUNT_CATEGORIES: int = 5
    CRAWLER_DAYS_TIME: int = 10
    DARKWEB_BATCH_SIZE: int = Field(default=5, env="DARKWEB_BATCH_SIZE")
    
    ONIONSEARCH_ENGINES: List[str] = Field(
        default=["ahmia", "tor66"],
        env="ONIONSEARCH_ENGINES",
        description="List of OnionSearch engines to use (comma-separated string or JSON list)"
    )
    
    @field_validator('ONIONSEARCH_ENGINES', mode='before')
    @classmethod
    def parse_engines(cls, v):
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                pass
            return [e.strip() for e in v.split(',') if e.strip()]
        return v
    ONIONSEARCH_TIMEOUT: Optional[int] = Field(
        default=300,
        env="ONIONSEARCH_TIMEOUT",
        description="Request timeout in seconds for OnionSearch engines (minimum 300s, None = no timeout)"
    )
    
    @field_validator('ONIONSEARCH_TIMEOUT')
    @classmethod
    def validate_timeout(cls, v):
        if v is not None and v < 300:
            raise ValueError(f"ONIONSEARCH_TIMEOUT must be at least 300 seconds, got {v}")
        return v
    ONIONSEARCH_MAX_PAGES: int = Field(
        default=5,
        env="ONIONSEARCH_MAX_PAGES",
        description="Maximum number of pages to fetch per engine"
    )
    
    DARKWEB_MAX_WORKERS: int = Field(default=5, env="DARKWEB_MAX_WORKERS")
    DARKWEB_DISCOVERY_TIMEOUT: int = Field(default=300, env="DARKWEB_DISCOVERY_TIMEOUT")
    DARKWEB_CRAWL_TIMEOUT: int = Field(default=600, env="DARKWEB_CRAWL_TIMEOUT")
    DARKWEB_DEFAULT_CRAWL_LIMIT: int = Field(default=5, env="DARKWEB_DEFAULT_CRAWL_LIMIT")
    DARKWEB_MAX_ADDITIONAL_CRAWL: int = Field(default=10, env="DARKWEB_MAX_ADDITIONAL_CRAWL")
    
    ANALYZER_DB_HOST: Optional[str] = None
    ANALYZER_DB_NAME: Optional[str] = None
    ANALYZER_DB_USER: Optional[str] = None
    ANALYZER_DB_PASS: Optional[str] = None
    
    WS_HEARTBEAT_INTERVAL: int = 30
    
    API_REQUEST_TIMEOUT: int = Field(default=300, env="API_REQUEST_TIMEOUT")
    DARKWEB_JOB_TIMEOUT: int = Field(default=1800, env="DARKWEB_JOB_TIMEOUT")
    
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    LOG_DETAILED_TIMING: bool = Field(default=True, env="LOG_DETAILED_TIMING")
    
    CORS_ORIGINS: str = Field(
        default="*",
        env="CORS_ORIGINS",
        description="Comma-separated list of allowed origins, or '*' for all origins"
    )
    CORS_DEBUG: bool = Field(
        default=False,
        env="CORS_DEBUG",
        description="Enable detailed CORS logging for debugging"
    )
    
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/cybernexus",
        env="DATABASE_URL",
        description="PostgreSQL database connection URL. Railway provides this automatically."
    )
    DATABASE_POOL_SIZE: int = Field(
        default=5,
        env="DATABASE_POOL_SIZE",
        description="Database connection pool size"
    )
    DATABASE_MAX_OVERFLOW: int = Field(
        default=10,
        env="DATABASE_MAX_OVERFLOW",
        description="Maximum overflow connections in pool"
    )
    DATABASE_POOL_TIMEOUT: int = Field(
        default=30,
        env="DATABASE_POOL_TIMEOUT",
        description="Database pool timeout in seconds"
    )
    
    NETWORK_LOG_TTL_DAYS: int = Field(
        default=7,
        env="NETWORK_LOG_TTL_DAYS",
        description="Network log retention period in days"
    )
    NETWORK_RATE_LIMIT_IP: int = Field(
        default=100,
        env="NETWORK_RATE_LIMIT_IP",
        description="Requests per minute per IP"
    )
    NETWORK_RATE_LIMIT_ENDPOINT: int = Field(
        default=60,
        env="NETWORK_RATE_LIMIT_ENDPOINT",
        description="Requests per minute per endpoint per IP"
    )
    NETWORK_ENABLE_LOGGING: bool = Field(
        default=True,
        env="NETWORK_ENABLE_LOGGING",
        description="Enable/disable network logging"
    )
    NETWORK_ENABLE_BLOCKING: bool = Field(
        default=True,
        env="NETWORK_ENABLE_BLOCKING",
        description="Enable/disable network blocking"
    )
    NETWORK_ENABLE_TUNNEL_DETECTION: bool = Field(
        default=True,
        env="NETWORK_ENABLE_TUNNEL_DETECTION",
        description="Enable/disable real-time tunnel detection"
    )
    NETWORK_TUNNEL_CONFIDENCE_THRESHOLD: str = Field(
        default="medium",
        env="NETWORK_TUNNEL_CONFIDENCE_THRESHOLD",
        description="Minimum confidence to alert (low/medium/high/confirmed)"
    )
    NETWORK_MAX_BODY_SIZE: int = Field(
        default=1048576,
        env="NETWORK_MAX_BODY_SIZE",
        description="Maximum body size to log in bytes (1MB default)"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()


def init_directories():
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


