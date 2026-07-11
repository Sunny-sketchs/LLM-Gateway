from openai import OpenAI
from config import settings
from fastapi import HTTPException
from models.schemas import AskRequest, AskResponse
import os

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


class llm:
    """
    this is how the endpoint will talk to openai
    """
    def invoke(self, request: str):
        try:
            response = client.chat.completions.create(
                model=settings.llm_model,
                messages=[{"role": "user", "content": request}]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        return response