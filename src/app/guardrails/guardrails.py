from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from fastapi import HTTPException, BackgroundTasks
from src.app.config import settings
from src.app.utils.log_util import logger
from src.app.models.schemas import AskRequest

# 1. NLP engine
configuration = {
    "nlp_engine_name": settings.guard_nlp_engine_name,
    "models": settings.guard_models,
}
provider = NlpEngineProvider(nlp_configuration=configuration)
nlp_engine = provider.create_engine()

# 2. Registry — load Presidio's built-in recognizers FIRST, or you lose
#    EMAIL_ADDRESS, CREDIT_CARD, US_SSN, IBAN_CODE, etc. entirely.
registry = RecognizerRegistry()
registry.load_predefined_recognizers()

# 3. Custom recognizers, added on top of the defaults
indian_phone_pattern = Pattern(
    name="indian_phone_pattern",
    regex=r"(\+91[\-\s]?[6-9]\d{9}|0[6-9]\d{9}|[6-9]\d{9})",
    score=0.9,
)
indian_phone_recognizer = PatternRecognizer(
    supported_entity="INDIAN_PHONE_NUMBER",
    patterns=[indian_phone_pattern],
)
registry.add_recognizer(indian_phone_recognizer)

pan_pattern = Pattern(
    name="pan_pattern",
    regex=r"[A-Z]{5}[0-9]{4}[A-Z]{1}",
    score=0.9,
)
pan_recognizer = PatternRecognizer(
    supported_entity="INDIA_PAN",
    patterns=[pan_pattern],
)
registry.add_recognizer(pan_recognizer)

# 4. Analyzer built with the full registry (defaults + custom)
analyzer = AnalyzerEngine(
    nlp_engine=nlp_engine,
    registry=registry,
    supported_languages=["en"],
)

anonymizer = AnonymizerEngine()

# Added INDIAN_PHONE_NUMBER and INDIA_PAN alongside the existing high-confidence set.
# PHONE_NUMBER (Presidio's default, US-biased) is kept too — some numbers may still
# match it directly; the Indian-specific recognizer is additive, not a replacement.
HIGH_CONFIDENCE_ENTITIES = {
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "CREDIT_CARD",
    "US_SSN",
    "IBAN_CODE",
    "INDIAN_PHONE_NUMBER",
    "INDIA_PAN",
}


class PII:
    """
    Guardrails PII.
    """

    def pii_detect(self, request: AskRequest, background_tasks: BackgroundTasks):
        """
        PII Detection and Redact
        """
        try:
            query = request.query
            results = analyzer.analyze(query, language="en")

            filter_by_score = [
                r for r in results
                if r.score > settings.guard_pii_threshold and r.entity_type in HIGH_CONFIDENCE_ENTITIES
            ]

            if len(filter_by_score) == 0:
                logger.info("NO PII Detected")
                background_tasks.add_task(
                    logger.log_request,
                    provider=request.provider,
                    user_id=request.user_id,
                    status_code=200,
                    pii_detected=False,
                    query_redacted=query,
                )
                return False

            logger.info(f"PII detected: {[r.entity_type for r in filter_by_score]}")
            anonymizer_result = anonymizer.anonymize(
                text=query,
                analyzer_results=filter_by_score,
            )

            background_tasks.add_task(
                logger.log_request,
                provider=request.provider,
                user_id=request.user_id,
                status_code=200,
                pii_detected=True,
            )
            return anonymizer_result.text
        except HTTPException:
            raise  # let intentional HTTP errors (403, 422, 400, etc.) pass through untouched
        except Exception as e:
            logger.info("PII Guardrail failed")
            background_tasks.add_task(
                logger.log_request,
                provider=request.provider,
                user_id=request.user_id,
                status_code=500,
            )
            raise HTTPException(status_code=500, detail=f'gaurdrail -> {e}')


pii = PII()

