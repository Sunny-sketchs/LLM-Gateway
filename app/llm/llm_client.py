from openai import OpenAI
from app.config import settings
from fastapi import HTTPException
from app.models.schemas import AskRequest, AskResponse,CacheEntry
from dotenv import load_dotenv
from app.llm.llm_prompt import prompts_llm
from app.guardrails.guardrails import pii
from app.utils.log_util import logger

load_dotenv()

client = OpenAI()


class LLM:
    """
    this is how the endpoint will talk to openai
    """
    def openai_invoke(self, request: AskRequest):
        """
        Befor invoke we need to check cache for quick answer,
        then check for PII detection,
        and llm wise prompt.
        """
        try:
            # PII Detection block
            flag_pii = True
            query = pii.pii_detect(request.query)
            if not query:
                logger.info("No PII detected")
                flag_pii = False
                query = request.query

            logger.info("PII detected")

            # Prompt layer
            messages = prompts_llm.build_prompt(query=query)

            # llm response to AskResponse
            response = client.responses.parse(
                model=settings.llm_model,
                input=messages,
                text_format=AskResponse,
                max_output_tokens=settings.llm_max_output_tokens
            )
            result = AskResponse(
                response=response.output_parsed.response,
                tokens_used=response.usage.total_tokens,
                provider=request.provider,
                pii_detected=flag_pii
            )

            return result
        except ValueError as e:
            logger.exception("LLM openai-invoke failed by ValueError")
            raise ValueError("Value Error")
        except Exception as e:
            logger.exception("LLM openai-invoke failed")
            raise HTTPException(status_code=500, detail=f'llm ->{e}')


llm = LLM()