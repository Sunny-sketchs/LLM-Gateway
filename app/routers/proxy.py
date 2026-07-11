from fastapi import APIRouter, HTTPException
from app.models.schemas import AskRequest, AskResponse
from app.llm_client import llm

router = APIRouter()

@router.post("/ask")
def ask_query(request: str):
    try:
        response = llm.invoke(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return response

