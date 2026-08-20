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
    """Monta a aplicacao, peca por peca.

    Os tres blocos abaixo seguem a ordem em que a requisicao encontra
    cada um — de fora pra dentro:
      1. os middlewares    — o que acontece com TODA requisicao
      2. as rotas          — o que a API sabe responder
      3. os error handlers — como cada erro vira uma resposta

    Essa ordem serve pra leitura, nao e exigencia: o FastAPI monta a
    pilha de middlewares na primeira requisicao que chega, entao
    registrar rota antes ou depois de middleware da no mesmo. So a
    ordem DENTRO do bloco de middlewares tem consequencia, e ela esta
    explicada logo abaixo.
    """
    # Os tres None desligam a documentacao automatica: o FastAPI sabe
    # gerar sozinho umas paginas descrevendo a API, e aqui elas nao
    # existem. Pra ver o que cada rota responde, mande uma requisicao —
    # tem exemplo pronto de cada uma no README.
    application = FastAPI(
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    # Middleware e uma camada por fora da aplicacao: toda requisicao
    # atravessa todas elas na ida, e todas de novo na volta.
    #
    # O ULTIMO registrado e o mais externo — por isso os cabecalhos de
    # seguranca ficam por fim: assim eles entram ate nas respostas de
    # erro que o middleware de token devolve antes de chegar na rota.
    # Ou seja: destas tres linhas, a de BAIXO e a primeira que a
    # requisicao encontra. Trocar a ordem delas muda o comportamento.
    register_internal_token_middleware(application)
    register_request_logger_middleware(application)
    register_secure_headers_middleware(application)

    # As rotas ficam na raiz: o que o router declara como "/sample_entity"
    # atende em http://localhost:3000/sample_entity, sem nada na frente.
    # Router novo que voce criar entra aqui embaixo, numa linha igual
    # a estas duas.
    application.include_router(health_check_router)
    application.include_router(sample_entity_router)

    register_error_handlers(application)

    return application


def main() -> FastAPI:
    # Nao deixa a API subir com configuracao faltando: e melhor falhar
    # agora, na hora de ligar, do que na cara do cliente mais tarde.
    check_variables()
    error_verification()
    setup_logging()

    # Garante que a fila existe antes da primeira requisicao chegar. O
    # consumer faz a mesma chamada quando sobe: criar fila que ja existe
    # nao da erro, e assim nenhum dos dois depende do outro ter subido
    # primeiro — nem de voce rodar comando nenhum na mao.
    create_queue()

    return create_app()


app = main()
