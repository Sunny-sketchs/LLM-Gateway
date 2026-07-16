from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from fastapi.exceptions import HTTPException
from app.config import settings
import logging

logger = logging.getLogger(__name__)

configuration = {
    "nlp_engine_name": settings.guard_nlp_engine_name,
    "models": settings.guard_models,
}

provider = NlpEngineProvider(nlp_configuration=configuration)
nlp_engine = provider.create_engine()

analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])

anonymizer = AnonymizerEngine()

HIGH_CONFIDENCE_ENTITIES = {"EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "US_SSN", "IBAN_CODE"}

class PII:
    """
    Guardrails PII.
    """

    def pii_detect(self, query: str):

        try:
            print(query)
            results = analyzer.analyze(query, language="en")
            print(results)
            filter_by_score = [
                r for r in results
                if r.score > settings.guard_pii_threshold and r.entity_type in HIGH_CONFIDENCE_ENTITIES
            ]
            print(filter_by_score)
            anonymizer_result = anonymizer.anonymize(
                text=query,
                analyzer_results=filter_by_score
            )
            print(anonymizer_result.text)

            return anonymizer_result.text
        except Exception as e:
            logger.exception("PII Guardrail failed")
            raise HTTPException(status_code=500, detail=f'gaurdrail -> {e}')


pii = PII()
