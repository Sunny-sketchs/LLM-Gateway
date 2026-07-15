from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    app_name: str = "llm-gateway"
    app_version: str = "1.0.0"
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"

    # guard_nlp_engine_name = "spacy"
    # guard_models = [{"lang_code": "en", "model_name": "en_core_web_sm"}]


settings = Settings()
