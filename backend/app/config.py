"""
Configuração da aplicação via variáveis de ambiente.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    APP_NAME: str = "Gestão de Apoio Arquivístico"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database (PostgreSQL)
    DATABASE_URL: str = "postgresql+asyncpg://gestor:gestor123@localhost:5432/gestao_arquivistica"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://:redis123@localhost:6379/0"

    # JWT Auth
    JWT_SECRET_KEY: str = "super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # MinIO / S3
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_EVIDENCIAS: str = "evidencias"
    S3_BUCKET_WORM: str = "worm-logs"

    # Celery
    CELERY_BROKER_URL: str = "redis://:redis123@localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://:redis123@localhost:6379/2"

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:4000",
        "http://localhost:3001",
        "http://localhost:3002",
    ]

    # Rate limit API
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_WINDOW: int = 120
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 50

    # Antivirus (ClamAV)
    CLAMAV_ENABLED: bool = True
    CLAMAV_HOST: str = "localhost"
    CLAMAV_PORT: int = 3310
    CLAMAV_TIMEOUT_SECONDS: int = 10
    CLAMAV_FAIL_OPEN: bool = False

    # Prometheus
    PROMETHEUS_ENABLED: bool = True

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()


settings = get_settings()
