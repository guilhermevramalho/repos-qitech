from fastapi import FastAPI

from constants import SERVICE_NAME, check_variables
from errors import register_error_handlers
from errors.base_error import error_verification
from middlewares import (
    register_internal_token_middleware,
    register_request_logger_middleware,
    register_secure_headers_middleware,
)
from routers import health_check_router, sample_entity_router
from utils.logger import setup_logging


DESCRIPTION = """
API de exemplo do Bootcamp QI Tech.

Esta pagina e gerada sozinha, a partir do codigo. Cada rota abaixo pode
ser testada aqui mesmo, no botao **Try it out** — sem instalar nada.
"""


def create_app() -> FastAPI:
    """Monta a aplicacao, peca por peca.

    A ordem importa e e sempre a mesma:
      1. as rotas          — o que a API sabe responder
      2. os middlewares    — o que acontece com TODA requisicao
      3. os error handlers — como cada erro vira uma resposta
    """
    application = FastAPI(
        title=SERVICE_NAME,
        description=DESCRIPTION,
        version="1.0.0",
        docs_url="/docs",
        redoc_url=None,
    )

    # As rotas ficam na raiz: o que o router declara como "/sample_entity"
    # atende em http://localhost:3000/sample_entity, sem nada na frente.
    # Router novo que voce criar entra aqui embaixo, numa linha igual
    # a estas duas.
    application.include_router(health_check_router)
    application.include_router(sample_entity_router)

    # Middleware e uma camada por fora da aplicacao: toda requisicao
    # atravessa todas elas na ida, e todas de novo na volta.
    #
    # O ULTIMO registrado e o mais externo — por isso os cabecalhos de
    # seguranca ficam por fim: assim eles entram ate nas respostas de
    # erro que o middleware de token devolve antes de chegar na rota.
    register_internal_token_middleware(application)
    register_request_logger_middleware(application)
    register_secure_headers_middleware(application)

    register_error_handlers(application)

    return application


def main() -> FastAPI:
    # Nao deixa a API subir com configuracao faltando: e melhor falhar
    # agora, na hora de ligar, do que na cara do cliente mais tarde.
    check_variables()
    error_verification()
    setup_logging()

    return create_app()


app = main()
