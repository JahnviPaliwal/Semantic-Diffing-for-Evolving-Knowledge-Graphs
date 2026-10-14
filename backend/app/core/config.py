"""
Application configuration using Pydantic Settings v2.
Reads from environment variables and provides production defaults.
"""
import os
from typing import List, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "Semantic Knowledge Graph Diff API"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api"

    # Database
    DATABASE_URL: str = Field(
        default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./data/app.db")
    )

    # Security & JWT
    SECRET_KEY: str = Field(
        default_factory=lambda: os.getenv("SECRET_KEY", "change-this-in-production-secret-jwt-key-2026")
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:80",
        "http://localhost",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:80",
        "http://127.0.0.1",
    ]

    # Rate Limiting
    RATE_LIMIT_DEFAULT: str = "120/minute"

    # LLM & ML settings
    GROQ_API_KEY: str = Field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    GROQ_MODEL: str = Field(default_factory=lambda: os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b"))
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    DISABLE_HEAVY_EMBEDDINGS: bool = Field(
        default_factory=lambda: os.getenv("DISABLE_HEAVY_EMBEDDINGS", "").lower() in ("1", "true", "yes")
    )

    # File Uploads & Storage Abstraction
    UPLOAD_MAX_BYTES: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = [".txt", ".pdf", ".docx"]
    UPLOAD_DIR: str = Field(default_factory=lambda: os.getenv("UPLOAD_DIR", "./data/uploads"))
    STORAGE_BACKEND: str = Field(default_factory=lambda: os.getenv("STORAGE_BACKEND", "local"))

    # Graph Database
    DEFAULT_GRAPH_STORE: str = Field(default_factory=lambda: os.getenv("DEFAULT_GRAPH_STORE", "networkx"))
    NEO4J_URI: str = Field(default_factory=lambda: os.getenv("NEO4J_URI", "bolt://localhost:7687"))
    NEO4J_USER: str = Field(default_factory=lambda: os.getenv("NEO4J_USER", "neo4j"))
    NEO4J_PASSWORD: str = Field(default_factory=lambda: os.getenv("NEO4J_PASSWORD", "password123"))

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]


settings = Settings()
