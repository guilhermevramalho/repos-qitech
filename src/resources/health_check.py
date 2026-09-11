import os

from fastapi import Response, status

from constants import SERVICE_NAME


class HealthCheckResource:
    """As duas rotas que respondem sem token: quem é este serviço, e se ele está vivo."""

    def on_get_home(self) -> dict:
        return {"service": SERVICE_NAME, "id": str(os.getpid())}

    def on_get_health_check(self) -> Response:
        # 204 quer dizer "deu tudo certo e não tenho nada a dizer".
        # Por isso a resposta não tem corpo nenhum — e é só pra isso
        # que o `Response` está aqui. Quem declara o 204 é o
        # src/app.py, na linha que registra esta rota.
        return Response(status_code=status.HTTP_204_NO_CONTENT)
