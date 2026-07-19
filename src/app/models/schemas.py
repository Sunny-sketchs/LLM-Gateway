from pydantic import BaseModel, field_validator
from datetime import datetime


class AskRequest(BaseModel):
    query: str
    user_id: str = "anonymous"
    provider: str = "openai"

    @field_validator("query")
    @classmethod
    def query_non_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("query cannot be empty")
        # if len(v) > 2000:
        #     raise ValueError("query too long max(2000 characters)")
        return v


class AskResponse(BaseModel):
    response: str | None = None
    tokens_used: int = 0
    provider: str | None = None
    cache_hit : bool = False
    pii_detected: bool = False


class CacheEntry(BaseModel):
    response: AskResponse
    cached_at: datetime | None = None

