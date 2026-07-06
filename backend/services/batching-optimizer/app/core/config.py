from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "batching-optimizer"
    APP_ENV: str = "development"

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    LOG_LEVEL: str = "INFO"

    # PostgreSQL connection settings – optional for test environments.
    POSTGRES_HOST: str | None = None
    POSTGRES_PORT: int | None = None
    POSTGRES_DB: str | None = None
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None

    # Redis settings – default to localhost for local development.
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    SOLVER_TIMEOUT: int = 10
    MAX_RIDER_CAPACITY: int = 3
    BATCH_WINDOW_SECONDS: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        """Construct the database URL.

        Uses PostgreSQL if all settings are provided, otherwise falls back to SQLite.
        """
        if all([
            self.POSTGRES_HOST,
            self.POSTGRES_PORT,
            self.POSTGRES_DB,
            self.POSTGRES_USER,
            self.POSTGRES_PASSWORD,
        ]):
            return (
                f"postgresql+psycopg2://"
                f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/"
                f"{self.POSTGRES_DB}"
            )
        return "sqlite:///./test.db"

    @property
    def redis_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

@lru_cache
def get_settings() -> Settings:
    return Settings()
