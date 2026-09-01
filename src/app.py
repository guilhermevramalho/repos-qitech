from fastapi import FastAPI

from constants import check_variables
from errors import register_error_handlers
from errors.base_error import error_verification
from middlewares import (
    register_internal_token_middleware,
    register_request_context_middleware,
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

    # ────────────────────────────────────────────────────────────────
    # Os middlewares — e a ordem deles, que é regra e não gosto
    # ────────────────────────────────────────────────────────────────
    # Middleware é uma camada por fora da aplicação: toda requisição
    # atravessa todas elas na ida, e todas de novo na volta. São como
    # cascas de cebola, e o ÚLTIMO registrado é a casca de FORA.
    #
    # Ou seja: destas quatro linhas, a de BAIXO é a primeira que a
    # requisição encontra, e a de CIMA é a última. Lendo de fora para
    # dentro, acontece isto:
    #
    #     requisição chega
    #           ↓
    #     secure_headers    põe os cabeçalhos de segurança na volta
    #           ↓
    #     request_context   dá um identificador único a esta requisição
    #           ↓
    #     request_logger    escreve "ENTROU" e, na volta, "SAIU"
    #           ↓
    #     internal_token    confere o INTERNAL-TOKEN. Sem ele, para aqui
    #           ↓
    #     as rotas
    #
    # Cada posição tem um porquê, e trocar duas linhas muda o que a API
    # faz:
    #
    # • Segurança fica por FORA de tudo, para que os cabeçalhos entrem
    #   até nas respostas que nunca chegam na rota — como o 403 que o
    #   middleware de token devolve. Justo a resposta que um atacante
    #   recebe é a que sairia pelada.
    # • O identificador vem ANTES do log: se viesse depois, as linhas de
    #   log da requisição sairiam sem o nome dela, e o middleware
    #   existiria para nada.
    # • O log vem ANTES do token: assim a tentativa recusada com 403
    #   também aparece no log — e essa é justamente a que você quer ver,
    #   porque mil delas seguidas é alguém tentando adivinhar o token.
    #
    # Isso não é teoria: os testes em tests/integration/ guardam esta
    # ordem. Inverta duas linhas e algum deles fica vermelho dizendo
    # qual combinado você quebrou.
    #
    # ATENÇÃO, e é aqui que quase todo mundo tropeça: as quatro linhas
    # abaixo são o DIAGRAMA ACIMA DE TRÁS PRA FRENTE. O FastAPI embrulha
    # a aplicação de dentro pra fora, então o ÚLTIMO registrado é o
    # PRIMEIRO a executar. Leia de baixo pra cima e o diagrama volta.
    register_internal_token_middleware(application)
    register_request_logger_middleware(application)
    register_request_context_middleware(application)
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
