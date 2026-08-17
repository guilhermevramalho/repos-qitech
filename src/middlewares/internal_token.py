from fastapi import FastAPI, Request

from constants import BYPASS_ENDPOINTS, INTERNAL_TOKEN
from errors.base_error import ForbiddenNotInternal
from errors.handlers import qi_exception_to_response


def register_internal_token_middleware(application: FastAPI) -> None:
    """Deixa passar so quem manda o header INTERNAL-TOKEN com o valor certo.

    O valor certo vem da variavel de ambiente INTERNAL_TOKEN, nunca do
    codigo. As rotas de BYPASS_ENDPOINTS (raiz e health check) sao publicas.

    Repare que aqui a gente DEVOLVE a resposta de erro em vez de levantar
    a excecao: dentro de um middleware, ninguem esta escutando pra traduzir
    o erro — quem traduz sao os exception handlers, que rodam mais pra
    dentro. Levantar aqui viraria um 500.
    """

    @application.middleware("http")
    async def check_internal_token(request: Request, call_next):
        is_public = request.url.path in BYPASS_ENDPOINTS

        if request.method == "OPTIONS" or is_public:
            return await call_next(request)

        if request.headers.get("INTERNAL-TOKEN") != INTERNAL_TOKEN:
            return qi_exception_to_response(ForbiddenNotInternal())

        return await call_next(request)
