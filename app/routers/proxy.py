from fastapi import APIRouter, HTTPException
from app.llm.llm_client import llm
from app.models.schemas import AskRequest,AskResponse

router = APIRouter()


@router.post("/ask")
def ask_query(request: AskRequest):
    try:
        response = llm.openai_invoke(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'proxy - >{str(e)}')
    return response
