import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler


class Logger:
    def __init__(self, log_path=None, default_log_path='logs/llm_gateway.log', log_level=logging.INFO):
        self.log_path = os.getenv('LOG_PATH', default_log_path) if log_path is None else log_path

        log_dir = Path(self.log_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger('GatewayLogger')
        self.logger.setLevel(log_level)

        if not self.logger.handlers:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

            file_handler = RotatingFileHandler(
                self.log_path,
                maxBytes=5 * 1024 * 1024,
                backupCount=5
            )

            file_handler.setFormatter(formatter)
            file_handler.setLevel(log_level)

            self.logger.addHandler(file_handler)

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


logger = Logger()
