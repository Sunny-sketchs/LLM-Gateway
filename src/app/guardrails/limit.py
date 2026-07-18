from datetime import datetime, timezone
from src.app.config import settings
from fastapi import HTTPException
from src.app.redis_setup.redis_client import redis_client
from src.app.utils.log_util import logger

class LIMIT:

    def check_prompt_limit(self, query: str, provider: str = "openai"):
        try:
            logger.info(f'limit-> provider = {provider}')

            if provider == "openai":

                import tiktoken

                encoding = tiktoken.encoding_for_model(settings.openai_tokenizer_model)
                token_count = len(encoding.encode(query))
                logger.info(f'limit-> total count = {token_count}')

                if token_count > settings.max_tokens_per_request:
                    logger.info(f"limit-> total count > max token per request({settings.max_tokens_per_request})")
                    raise HTTPException(status_code=400, detail=f'Token limit exceeded, token count-> {token_count} max token-> {settings.max_tokens_per_request}')

                return token_count
        except Exception as e:
            logger.info(f"limit-> Exception-> {e}")
            raise HTTPException(status_code=500, detail=e)


    def check_daily_limit(self, user_id: str):
        try:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            logger.info(f"limit-> today = {today}")

            key = f"usage:{user_id}:{today}"
            logger.info(f'limit-> redis key : {key}')

            count = redis_client.incr(key)
            logger.info(f'limit-> count = {count}')
            if count == 1:
                redis_client.expire(key, 86400)

            if count > settings.daily_request_limit:
                logger.info(f'limit-> count exceeds daily rate limit')
                raise HTTPException(status_code=429, detail=f"Exhausted request limit")

            return count
        except Exception as e:
            logger.info(f'limit-> {e}')
            raise HTTPException(status_code=500, detail=e)


limit = LIMIT()