from datetime import datetime, timezone
from app.config import settings
from fastapi import HTTPException
from app.redis.redis_client import redis_client

class LIMIT:

    def check_prompt_limit(query: str, provider: str = "openai"):
        try:
            if provider == "openai":
                import tiktoken
                encoding = tiktoken.encoding_for_model(settings.openai_tokenizer_model)
                token_count = encoding.encode(query)
                if token_count > settings.max_tokens_per_request:
                    raise HTTPException(status_code=400, detail=f'Token limit exceeded, token count-> {token_count} max token-> {settings.max_tokens_per_request}')
                return token_count
        except Exception as e:
            raise HTTPException(status_code=500, detail=e)


    def check_daily_limit(user_id: str):
        try:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            key = f"usage:{user_id}:{today}"

            count = redis_client.incr(key)
            if count == 1:
                redis_client.expire(key, 86400)

            if count > settings.daily_request_limit:
                raise HTTPException(status_code=429, detail=f"Exhausted request limit")

            return count
        except Exception as e:
            raise HTTPException(status_code=500, detail=e)


limit = LIMIT()