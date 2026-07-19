import re
import hashlib
from fastapi import HTTPException, BackgroundTasks
from src.app.utils.log_util import logger
from src.app.models.schemas import AskRequest


def normalize(query: str):
    """
       Normalize an SQL query string for consistent hashing.
       Steps:
       1. Strip leading/trailing whitespace.
       2. Collapse multiple spaces/tabs/newlines into a single space.
       3. Convert to lowercase (case-insensitive matching).
       4. Remove trailing semicolons.
    """
    try:
        query = query.strip()
        query = re.sub(r";+\s*$", "", query)
        query = re.sub(r"\s+", " ", query)
        query = query.lower()

        logger.info(f'Query Normalized')
        return query
    except HTTPException:
        raise  # let intentional HTTP errors (403, 422, 400, etc.) pass through untouched
    except Exception as e:
        logger.info(f'Query normalization error-> {e}')
        raise HTTPException(status_code=500, detail=e)


def hashes_query(request: AskRequest, background_Tasks: BackgroundTasks):
    """
        Generate an SHA-256 hash key for a normalized SQL query.
    """
    try:
        query = request.query
        normalized = normalize(query)
        hashed = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        logger.info(f'query hashed successfully')
        return hashed
    except HTTPException:
        raise  # let intentional HTTP errors (403, 422, 400, etc.) pass through untouched
    except Exception as e:
        logger.info(f'Hashing error -> {e}')
        background_Tasks.add_task(
            logger.log_request,
            provider=request.provider,
            user_id=request.user_id,
            status_code=500,
        )
        raise HTTPException(status_code=500, detail=e)


