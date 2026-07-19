from fastapi import APIRouter, HTTPException, BackgroundTasks
from src.app.llm.llm_client import llm
from src.app.models.schemas import AskRequest, CacheEntry
from src.app.guardrails.limit import limit
from src.app.utils.cache_tools import hashes_query
from src.app.redis_setup.cache import get_cache, store_cache
from src.app.utils.log_util import logger
from src.app.guardrails.injections import detect_injection

router = APIRouter()


@router.post("/ask")
def ask_query(request: AskRequest, background_tasks: BackgroundTasks):
    try:
        # check if the prompt is longer then specified
        prompt_token = limit.check_prompt_limit(request, background_tasks)
        logger.info(f'Proxy-> promt_token = {prompt_token}')

        # check daily request count
        daily_request_count = limit.check_daily_limit(request, background_tasks)
        logger.info(f'Proxy-> daily_request_count = {daily_request_count}')

        # Normalized + hash the query
        hash_query = hashes_query(request, background_tasks)
        logger.info(f'Proxy-> hash_query = {hash_query}')

        # check if the query exists in the cache
        result = get_cache(hash_query)
        logger.info(f'Proxy-> Query exist-> {result}')

        # if query exists return the answer
        if result:

            logger.log_request(
                provider=request.provider,
                user_id=request.user_id,
                status_code=200,
                cache_hit=True,
                tokens_saved=result.response.tokens_used
            )
            return result

        # check for prompt injections
        injection_result = detect_injection(request)
        if injection_result["injection"]["flagged"]:
            logger.info(f'Injection found as {injection_result["injection"]["matched_patterns"]}')
            print("ABOUT TO ADD TASK")
            logger.log_request(
                provider=request.provider,
                user_id=request.user_id,
                status_code=403,
                injection_flagged=True,
            )
            print(f"Number of tasks queued: {len(background_tasks.tasks)}")
            print("TASK ADDED")
            raise HTTPException(status_code=403, detail="Request logged as potential prompt injection attempt.")

        # call the llm, returns AskResponse
        response = llm.openai_invoke(request, background_tasks)

        cached_at = None

        if not response.pii_detected:
            # returns Cache_Entry
            cache_obj = store_cache(hashed_query=hash_query, response_obj=response)
            cached_at = cache_obj.cached_at

        final_response = CacheEntry(
            response=response,
            cached_at=cached_at
        )

        return final_response

    except HTTPException:
        raise  # let intentional HTTP errors (403, 422, 400, etc.) pass through untouched
    except Exception as e:
        logger.log_request(
            provider=request.provider,
            user_id=request.user_id,
            status_code=500,
        )
        raise HTTPException(status_code=500, detail=f'proxy - >{str(e)}')