# Application configuration
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DATABASE_URL: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str

    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    REDIS_HOST: str
    REDIS_PORT: int

    GROQ_API_KEY: str
    GROQ_BASE_URL: str 

    MAX_RETRIES: int = 3
    INITIAL_BACKOFF: float = 1.0

    STORAGE_ROOT: str = "uploads"
    STORAGE_PROVIDER: str = "local"

    MAX_DOCUMENT_SIZE : int = 10 * 1024 * 1024  # 10 MB in bytes

    ALLOWED_DOCUMENT_TYPES : list[str] = [
        "application/pdf",
    ]

    QDRANT_URL:str
    QDRANT_API_KEY:str
    QDRANT_COLLECTION_NAME:str

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()