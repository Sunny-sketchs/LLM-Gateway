from fastapi import APIRouter, HTTPException
from app.llm.llm_client import llm
from app.models.schemas import AskRequest, AskResponse, CacheEntry
from app.guardrails.limit import limit
from app.cache_tools import hashes_query
from app.redis_setup.cache import get_cache, store_cache
from app.utils.log_util import logger

router = APIRouter()


@router.post("/ask")
def ask_query(request: AskRequest):
    try:
        # check if the prompt is longer then specified
        prompt_token = limit.check_prompt_limit(request.query)
        logger.info(f'Proxy-> promt_token = {prompt_token}')

        # check daily request count
        daily_request_count = limit.check_daily_limit(request.user_id)
        logger.info(f'Proxy-> daily_request_count = {daily_request_count}')

        # Normalized + hash the query
        hash_query = hashes_query(request.query)
        logger.info(f'Proxy-> hash_query = {hash_query}')

        # check if the query exists in the cache
        result = get_cache(hash_query)
        logger.info(f'Proxy-> Query exist-> {result}')

        # if query exists return the answer
        if result:
            return result

        # call the llm, returns AskResponse
        response = llm.openai_invoke(request)

        cached_at = None

        if not response.pii_detected:
            # returns Cache_Entry
            cache_obj = store_cache(hashed_query=hash_query, response_obj=response)
            cached_at = cache_obj.cached_at

        final_response = CacheEntry(
            response=response,
            cached_at=cached_at
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f'proxy - >{str(e)}')
    return final_response
