from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    app_name : str = "llm-gateway"
    app_version: str = "1.0.0"
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(
        env_file=os.getenv(".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

settings = Settings()