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

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()