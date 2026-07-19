from src.app.redis_setup.redis_client import redis_client
from src.app.models.schemas import AskResponse, CacheEntry
from datetime import datetime, timezone
from src.app.config import settings
from src.app.utils.log_util import logger
from fastapi import HTTPException


def get_cache(hashed_query: str):
    """
    Get the cached query if stored.
    """
    try:
        key = f"cache:{hashed_query}"
        raw = redis_client.get(key)
        if not raw:
            logger.info(f'cache-> Query not in cached')
            return False

        result = CacheEntry.model_validate_json(raw)
        result.response.cache_hit = True
        logger.info(f'cache-> Query in cached')
        return result
    except HTTPException:
        raise  # let intentional HTTP errors (403, 422, 400, etc.) pass through untouched
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)


def store_cache(hashed_query: str, response_obj: AskResponse):
    """
    Stores the hashed query with cache response.
    """
    try:
        entry = CacheEntry(response=response_obj, cached_at=datetime.now(timezone.utc))
        redis_client.set(f"cache:{hashed_query}", entry.model_dump_json(), ex=settings.CACHE_TTL_SECONDS)
        logger.info(f'Cache created')
        return entry
    except HTTPException:
        raise  # let intentional HTTP errors (403, 422, 400, etc.) pass through untouched
    except Exception as e:
        logger.info(f'Could not store cache-> {e}')
        raise HTTPException(status_code=500, detail=e)
