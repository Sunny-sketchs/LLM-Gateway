from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from fastapi.exceptions import HTTPException
from app.config import settings
import spacy
import logging

logger = logging.getLogger(__name__)

spacy.load('en_core_web_sm')

configuration = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
}

provider = NlpEngineProvider(nlp_configuration=configuration)
nlp_engine = provider.create_engine()

analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])

anonymizer = AnonymizerEngine()


class PII:
    """
    Guardrails PII.
    """

    def pii_detect(self, query: str):

        try:
            print(query)
            ans = analyzer.analyze(query, language="en")
            print(ans)
            filter_by_score = [r for r in ans if r.score > 0.5]
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
