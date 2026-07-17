from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    app_name: str = "llm-gateway"
    app_version: str = "1.0.0"
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"

    guard_pii_threshold: float = 0.6

    guard_nlp_engine_name: str = "spacy"
    guard_models: list[dict] = [{"lang_code": "en", "model_name": "en_core_web_sm"}]

    max_tokens_per_request: int = 500
    daily_request_limit: int = 50
    llm_max_output_tokens: int = 500

    CACHE_TTL_SECONDS: int = 60 * 60 * 24 * 7

    openai_tokenizer_model: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(
        env_file=os.getenv(".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )



settings = Settings()
