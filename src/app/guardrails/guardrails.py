from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from fastapi.exceptions import HTTPException
from src.app.config import settings
from src.app.utils.log_util import logger


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
        """
        PII Detection and Redact
        """
        try:
            # analyzing the query
            results = analyzer.analyze(query, language="en")

            filter_by_score = [
                r for r in results
                if r.score > settings.guard_pii_threshold and r.entity_type in HIGH_CONFIDENCE_ENTITIES
            ]

            if len(filter_by_score) == 0:
                logger.info("NO PII Detected")
                return False

            logger.info("PII detected")
            anonymizer_result = anonymizer.anonymize(
                text=query,
                analyzer_results=filter_by_score
            )

            return anonymizer_result.text
        except Exception as e:
            logger.info("PII Guardrail failed")
            raise HTTPException(status_code=500, detail=f'gaurdrail -> {e}')


pii = PII()
