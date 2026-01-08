from pydantic_settings import BaseSettings
from pydantic import SecretStr, RedisDsn, PostgresDsn, field_validator

class Settings(BaseSettings):
    BOT_TOKEN: SecretStr
    ADMIN_IDS: list[int]
    
    # Database
    DATABASE_URL: str | None = None
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None
    POSTGRES_DB: str | None = None
    POSTGRES_HOST: str | None = None
    POSTGRES_PORT: int | None = None
    
    USE_SQLITE: bool = False
    SQLITE_DB_PATH: str = "bot.db"

    # Redis
    REDIS_URL: str | None = None
    REDIS_HOST: str | None = None
    REDIS_PORT: int | None = None
    REDIS_DB: int | None = None
    USE_REDIS: bool = True

    LOG_LEVEL: str = "INFO"

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v: str | int | list) -> list[int]:
        if isinstance(v, int):
            return [v]
        if isinstance(v, str):
            # Handle "123,456" or "[123, 456]"
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                import json
                return json.loads(v)
            return [int(x) for x in v.split(",") if x.strip()]
        return v

    @property
    def database_url(self) -> str:
        if self.USE_SQLITE:
            return f"sqlite+aiosqlite:///{self.SQLITE_DB_PATH}"
        
        if self.DATABASE_URL:
            # Fix for Railway/Heroku postgres URLs
            url = self.DATABASE_URL
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url
            
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def redis_url(self) -> str | None:
        if not self.USE_REDIS:
            return None
            
        if self.REDIS_URL:
            return self.REDIS_URL
            
        if self.REDIS_HOST:
            return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
            
        return None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
