import os


SERVICE_ROOT = os.path.abspath(os.path.dirname(__file__))

APP_ENV = os.environ.get("APP_ENV", "local")
SERVICE_NAME = os.environ.get("SERVICE_NAME", "bootcamp-api")

DATABASE_URL = os.environ.get("DATABASE_URL")
INTERNAL_TOKEN = os.environ.get("INTERNAL_TOKEN")

# Rotas publicas: nao exigem o header INTERNAL-TOKEN. Sao as duas que
# precisam responder pra quem ainda nao tem token nenhum: a raiz, que
# diz quem e este servico, e o health check, que o Docker consulta pra
# saber se a API ja esta de pe.
BYPASS_ENDPOINTS = [
    "/",
    "/health_check",
]

REQUIRED_VARIABLES = ["DATABASE_URL", "INTERNAL_TOKEN"]


def check_variables():
    missing = []
    for name in REQUIRED_VARIABLES:
        if not globals().get(name):
            missing.append(name)

    if missing:
        raise EnvironmentError(
            f"Faltam variaveis de ambiente: {', '.join(missing)}. "
            "Rodando com 'docker compose up' elas ja vem preenchidas. "
            "Fora do Docker, copie o .env.example para .env."
        )
