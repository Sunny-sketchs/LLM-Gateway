import logging
import sys
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import text
from src.app.db.connection import engine

PRICE_PER_TOKEN_USD = Decimal("0.00000015")


class Logger:
    def __init__(self, log_level=logging.INFO):
        self.logger = logging.getLogger('GatewayLogger')
        self.logger.setLevel(log_level)

        if not self.logger.handlers:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            stream_handler = logging.StreamHandler(sys.stdout)
            stream_handler.setFormatter(formatter)
            stream_handler.setLevel(log_level)
            self.logger.addHandler(stream_handler)

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)

    def exception(self, message):
        self.logger.exception(message)

    def log_request(
            self,
            provider: str,
            status_code: int,
            user_id: str = "guest",
            query_redacted: str | None = None,
            response_text: str | None = None,
            tokens_used: int = 0,
            tokens_saved: int = 0,
            cache_hit: bool = False,
            pii_detected: bool = False,
            injection_flagged: bool = False,
    ):
        """
        Structured, per-request log. Call this via BackgroundTasks so it never
        blocks the response — a failure here should never break the actual request.
        """

        self.info(
            f"request user={user_id} provider={provider} status={status_code} "
            f"cache_hit={cache_hit} pii={pii_detected} injection={injection_flagged} "
            f"tokens={tokens_used}"
        )

        cost_usd = Decimal(tokens_used) * PRICE_PER_TOKEN_USD

        try:
            with engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO request_logs
                        (user_id, provider, query_redacted, response, tokens_used,
                         tokens_saved, cost_usd, cache_hit, pii_detected,
                         injection_flagged, status_code, created_at)
                        VALUES
                        (:user_id, :provider, :query_redacted, :response, :tokens_used,
                         :tokens_saved, :cost_usd, :cache_hit, :pii_detected,
                         :injection_flagged, :status_code, :created_at)
                    """),
                    {
                        "user_id": user_id,
                        "provider": provider,
                        "query_redacted": query_redacted,
                        "response": response_text,
                        "tokens_used": tokens_used,
                        "tokens_saved": tokens_saved,
                        "cost_usd": cost_usd,
                        "cache_hit": cache_hit,
                        "pii_detected": pii_detected,
                        "injection_flagged": injection_flagged,
                        "status_code": status_code,
                        "created_at": datetime.now(timezone.utc),
                    }
                )
                conn.commit()
        except Exception:
            self.error("Failed to write request log to Neon")


logger = Logger()