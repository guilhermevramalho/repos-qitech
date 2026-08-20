import logging
import sys

from constants import APP_ENV, SERVICE_NAME


LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"


def setup_logging() -> None:
    """Liga o log da aplicação. Chamada uma vez, quando a API sobe."""
    level = logging.INFO
    if APP_ENV.upper() in ("LOCAL", "TEST"):
        level = logging.DEBUG

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]

    # Estas bibliotecas falam MUITO em modo debug: o boto3 escreve a
    # assinatura criptográfica de cada chamada à fila, e são dezenas de
    # linhas por mensagem. Nada disso é sobre o seu código, e no meio
    # dessa parede você não acharia a sua própria linha de log.
    for biblioteca_falante in ["urllib3", "boto3", "botocore", "s3transfer"]:
        logging.getLogger(biblioteca_falante).setLevel(logging.CRITICAL)


def get_logger(class_name: str) -> logging.Logger:
    """Devolve o log com o nome de quem está escrevendo.

    Assim, olhando a linha do log, você sabe de qual arquivo ela veio.
    """
    return logging.getLogger(f"{SERVICE_NAME}.{class_name}")
