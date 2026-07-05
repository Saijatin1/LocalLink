from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    model_provider: str = "groq"
    model_name: str = "llama-3.3-70b-specdec"  # specdec is fine-tuned for tool calling on Groq
    groq_api_key: str = ""
    gemini_api_key: str = ""
    openai_api_key: str = ""

    ambiguity_threshold: int = 2

    catalog_service_url: str = "http://localhost:8001"
    order_service_url: str = "http://localhost:8002"


settings = Settings()
