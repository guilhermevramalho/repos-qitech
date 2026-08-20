import json

import boto3

from constants import (
    AWS_ACCESS_KEY_ID,
    AWS_REGION,
    AWS_SECRET_ACCESS_KEY,
    SAMPLE_ENTITY_QUEUE_NAME,
    SQS_ENDPOINT_URL,
)


# Este arquivo e pra fila o que o database.py e pro banco: o unico lugar
# que sabe COMO falar com ela. Quem usa a fila (a rota que publica, o
# consumer que le) chama as funcoes daqui e nao vê boto3 nenhum.
#
# Detalhe de nome: este arquivo NAO pode se chamar queue.py. Existe um
# modulo chamado "queue" dentro do proprio Python, e um arquivo nosso com
# esse nome tomaria o lugar dele — o boto3 usa esse modulo por dentro e
# para de funcionar. Nome de arquivo tambem e um endereco.
sqs_client = boto3.client(
    "sqs",
    region_name=AWS_REGION,
    endpoint_url=SQS_ENDPOINT_URL,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

PROCESS_SAMPLE_ENTITY = "process_sample_entity"


def create_queue() -> str:
    """Cria a fila, se ela ainda nao existir, e devolve o endereco dela.

    Chamar de novo com o mesmo nome nao da erro nem cria uma segunda: o
    SQS devolve a fila que ja existe. Isso tem nome — idempotente — e e o
    que permite a API e o consumer chamarem esta funcao no boot, os dois,
    sem combinar nada entre si e sem ninguem rodar comando na mao.
    """
    response = sqs_client.create_queue(
        QueueName=SAMPLE_ENTITY_QUEUE_NAME,
        Attributes={
            # Quantos segundos uma mensagem fica INVISIVEL depois que
            # alguem a pega. E o coracao do assunto — leia o comentario
            # sobre isso em src/consumer.py.
            "VisibilityTimeout": "30",
        },
    )

    return response["QueueUrl"]


def get_queue_url() -> str:
    return sqs_client.get_queue_url(QueueName=SAMPLE_ENTITY_QUEUE_NAME)["QueueUrl"]


def send_message(message_body: dict, message_type: str) -> None:
    """Publica uma mensagem na fila. Nao espera resposta de ninguem."""
    sqs_client.send_message(
        QueueUrl=get_queue_url(),
        MessageBody=json.dumps(message_body),
        # Alem do conteudo, a mensagem carrega O QUE FAZER com ele. Aqui
        # existe um tipo so; num servico de verdade sao dezenas, e e por
        # este campo que o consumer sabe qual regra chamar.
        MessageAttributes={
            "MessageType": {"StringValue": message_type, "DataType": "String"},
        },
    )


def receive_messages() -> list:
    """Pede mensagens pra fila e espera ate 5 segundos por elas.

    Esperar e de proposito: sem isso o consumer perguntaria "tem
    mensagem?" milhares de vezes por segundo, de graca, pra ouvir "nao".
    """
    response = sqs_client.receive_message(
        QueueUrl=get_queue_url(),
        MaxNumberOfMessages=10,
        WaitTimeSeconds=5,
        MessageAttributeNames=["All"],
    )

    return response.get("Messages", [])


def delete_message(receipt_handle: str) -> None:
    """Apaga a mensagem da fila. So depois de o trabalho ter dado certo."""
    sqs_client.delete_message(QueueUrl=get_queue_url(), ReceiptHandle=receipt_handle)
