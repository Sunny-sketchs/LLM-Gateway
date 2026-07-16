from fastapi import APIRouter, HTTPException
from app.llm.llm_client import llm
from app.models.schemas import AskRequest, AskResponse
from app.guardrails.limit import limit

router = APIRouter()


@router.post("/ask")
def ask_query(request: AskRequest):
    try:
        prompt_token = limit.check_prompt_limit(request.query)
        daily_request_count = limit.check_daily_limit(request.user_id)
        response = llm.openai_invoke(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'proxy - >{str(e)}')
    return response
