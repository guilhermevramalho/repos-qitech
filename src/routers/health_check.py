import os

from fastapi import APIRouter, Response, status

from constants import SERVICE_NAME


router = APIRouter(tags=["Health"])


@router.get("/", summary="Diz quem e este servico")
def home() -> dict:
    return {"service": SERVICE_NAME, "id": str(os.getpid())}


@router.get(
    "/health_check",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Responde se a API esta de pe",
)
def health_check() -> Response:
    # 204 quer dizer "deu tudo certo e nao tenho nada a dizer".
    # Por isso a resposta nao tem corpo nenhum.
    return Response(status_code=status.HTTP_204_NO_CONTENT)
