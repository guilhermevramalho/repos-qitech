import logging
import sys

from constants import APP_ENV, SERVICE_NAME


LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"


def setup_logging() -> None:
    """Liga o log da aplicacao. Chamada uma vez, quando a API sobe."""
    level = logging.INFO
    if APP_ENV.upper() in ("LOCAL", "TEST"):
        level = logging.DEBUG

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]

    logging.getLogger("urllib3").setLevel(logging.CRITICAL)


def get_logger(class_name: str) -> logging.Logger:
    """Devolve o log com o nome de quem esta escrevendo.

    Assim, olhando a linha do log, voce sabe de qual arquivo ela veio.
    """
    return logging.getLogger(f"{SERVICE_NAME}.{class_name}")
