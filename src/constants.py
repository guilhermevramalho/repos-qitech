import os


SERVICE_ROOT = os.path.abspath(os.path.dirname(__file__))

APP_ENV = os.environ.get("APP_ENV", "local")
SERVICE_NAME = os.environ.get("SERVICE_NAME", "bootcamp-api")

DATABASE_URL = os.environ.get("DATABASE_URL")
INTERNAL_TOKEN = os.environ.get("INTERNAL_TOKEN")

# A fila. Na QI Tech a fila de verdade é o SQS, da Amazon; aqui na sua
# máquina quem faz o papel dele é o localstack — um programa que imita
# os serviços da Amazon localmente, e que sobe junto no docker compose.
#
# O código que usa a fila não sabe a diferença, e esse é o ponto: muda o
# endereço (o SQS_ENDPOINT_URL), o resto continua igual.
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
SQS_ENDPOINT_URL = os.environ.get("SQS_ENDPOINT_URL", "http://localstack:4566")
SAMPLE_ENTITY_QUEUE_NAME = os.environ.get("SAMPLE_ENTITY_QUEUE_NAME", "sample-entity-processing")

# A Amazon exige um par de chaves em toda chamada, e o localstack também
# — mas ele não confere o valor. Por isso aqui elas são "test": não existe
# conta da Amazon nenhuma neste projeto, e não há o que vazar.
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "test")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "test")

# A API de boletos: o serviço de fora que este projeto chama pra emitir
# uma cobrança (veja src/connectors/). O endereço vem do ambiente, como
# tudo aqui — na sua máquina ele aponta pro mock server do sábado 4; em
# produção, apontaria pro serviço de verdade. O código não sabe a
# diferença, e esse é o ponto.
BANKSLIP_API_URL = os.environ.get("BANKSLIP_API_URL", "http://localhost:8080")
BANKSLIP_API_INTERNAL_TOKEN = os.environ.get("BANKSLIP_API_INTERNAL_TOKEN", "default_token")

# Quantos segundos esperar pelo serviço de boletos antes de desistir.
# Todo connector TEM um timeout — o porquê está em
# src/connectors/rest_connector.py.
BANKSLIP_API_TIMEOUT = int(os.environ.get("BANKSLIP_API_TIMEOUT", "5"))

# Rotas públicas: não exigem o header INTERNAL-TOKEN. São as duas que
# precisam responder pra quem ainda não tem token nenhum: a raiz, que
# diz quem é este serviço, e o health check, que o Docker consulta pra
# saber se a API já está de pé.
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
            f"Faltam variáveis de ambiente: {', '.join(missing)}. "
            "Rodando com 'docker compose up' elas já vêm preenchidas. "
            "Fora do Docker, copie o .env.example para .env."
        )
