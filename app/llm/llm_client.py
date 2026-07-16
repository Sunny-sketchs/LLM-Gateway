from openai import OpenAI
from app.config import settings
from fastapi import HTTPException
from app.models.schemas import AskRequest, AskResponse
from dotenv import load_dotenv
from app.llm.llm_prompt import prompts_llm
from app.guardrails.guardrails import pii
import logging
logger = logging.getLogger(__name__)

load_dotenv()

client = OpenAI()


class LLM:
    """
    this is how the endpoint will talk to openai
    """
    def openai_invoke(self, request: AskRequest):
        try:
            # print(request.query)
            query = pii.pii_detect(request.query)
            messages = prompts_llm.build_prompt(query=query)
            response = client.responses.parse(
                model=settings.llm_model,
                input=messages,
                text_format=AskResponse,
                max_output_tokens= settings.llm_max_output_tokens
            )
            result = AskResponse(
                response=response.output_parsed.response,
                tokens_used=response.usage.total_tokens,
                provider=request.provider
            )
            return result
        except ValueError as e:
            logger.exception("LLM openai-invoke failed by ValueError")
            raise ValueError("Value Error")
        except Exception as e:
            logger.exception("LLM openai-invoke failed")
            raise HTTPException(status_code=500, detail=f'llm ->{e}')


llm = LLM()
# l = AskRequest(query="Hello, my name is Sunny Bhatkar and email- advs@gmial.com. Tell me about email in one line.")
# s=llm.openai_invoke(l)
# print(s)