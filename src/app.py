from fastapi import FastAPI

from constants import check_variables
from errors import register_error_handlers
from errors.base_error import error_verification
from middlewares import (
    register_internal_token_middleware,
    register_request_logger_middleware,
    register_secure_headers_middleware,
)
from routers import health_check_router, sample_entity_router
from sqs import create_queue
from utils.logger import setup_logging


def create_app() -> FastAPI:
    """Monta a aplicação, peça por peça.

    Os três blocos abaixo seguem a ordem em que a requisição encontra
    cada um — de fora pra dentro:
      1. os middlewares    — o que acontece com TODA requisição
      2. as rotas          — o que a API sabe responder
      3. os error handlers — como cada erro vira uma resposta

    Essa ordem serve pra leitura, não é exigência: o FastAPI monta a
    pilha de middlewares na primeira requisição que chega, então
    registrar rota antes ou depois de middleware dá no mesmo. Só a
    ordem DENTRO do bloco de middlewares tem consequência, e ela está
    explicada logo abaixo.
    """
    # Os três None desligam a documentação automática: o FastAPI sabe
    # gerar sozinho umas páginas descrevendo a API, e aqui elas não
    # existem. Pra ver o que cada rota responde, mande uma requisição —
    # tem exemplo pronto de cada uma no README.
    application = FastAPI(
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    # Middleware é uma camada por fora da aplicação: toda requisição
    # atravessa todas elas na ida, e todas de novo na volta.
    #
    # O ÚLTIMO registrado é o mais externo — por isso os cabeçalhos de
    # segurança ficam por fim: assim eles entram até nas respostas de
    # erro que o middleware de token devolve antes de chegar na rota.
    # Ou seja: destas três linhas, a de BAIXO é a primeira que a
    # requisição encontra. Trocar a ordem delas muda o comportamento.
    register_internal_token_middleware(application)
    register_request_logger_middleware(application)
    register_secure_headers_middleware(application)

    # As rotas ficam na raiz: o que o router declara como "/sample_entity"
    # atende em http://localhost:3000/sample_entity, sem nada na frente.
    # Router novo que você criar entra aqui embaixo, numa linha igual
    # a estas duas.
    application.include_router(health_check_router)
    application.include_router(sample_entity_router)

    register_error_handlers(application)

    return application


def main() -> FastAPI:
    # Não deixa a API subir com configuração faltando: é melhor falhar
    # agora, na hora de ligar, do que na cara do cliente mais tarde.
    check_variables()
    error_verification()
    setup_logging()

    # Garante que a fila existe antes da primeira requisição chegar. O
    # consumer faz a mesma chamada quando sobe: criar fila que já existe
    # não dá erro, e assim nenhum dos dois depende do outro ter subido
    # primeiro — nem de você rodar comando nenhum na mão.
    create_queue()

    return create_app()


app = main()
