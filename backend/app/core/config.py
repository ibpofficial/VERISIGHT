import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "VERISIGHT"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "verisight-super-secret-key-change-in-production-sih2026-mha"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours for operational shift
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    # Default to sqlite for smooth local execution; overrides with postgresql in docker/production
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./verisight.db"
    )
    
    # Storage & Uploads
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./data/uploads")
    PROCESSED_DIR: str = os.getenv("PROCESSED_DIR", "./data/processed")
    REPORTS_DIR: str = os.getenv("REPORTS_DIR", "./data/reports")
    MAX_UPLOAD_SIZE_BYTES: int = 15 * 1024 * 1024  # 15 MB
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # Feature Flags
    ENABLE_FACE_VERIFICATION: bool = True
    SYNTHETIC_DATA_MODE: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="allow"
    )


settings = Settings()
