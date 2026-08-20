import os

from fastapi import APIRouter, Response, status

from constants import SERVICE_NAME


router = APIRouter()


@router.get("/")
def home() -> dict:
    return {"service": SERVICE_NAME, "id": str(os.getpid())}


@router.get("/health_check", status_code=status.HTTP_204_NO_CONTENT)
def health_check() -> Response:
    # 204 quer dizer "deu tudo certo e não tenho nada a dizer".
    # Por isso a resposta não tem corpo nenhum.
    return Response(status_code=status.HTTP_204_NO_CONTENT)
