import json

import boto3

from constants import (
    AWS_ACCESS_KEY_ID,
    AWS_REGION,
    AWS_SECRET_ACCESS_KEY,
    SAMPLE_ENTITY_QUEUE_NAME,
    SQS_ENDPOINT_URL,
)


# Este arquivo é pra fila o que o database.py é pro banco: o único lugar
# que sabe COMO falar com ela. Quem usa a fila (a rota que publica, o
# consumer que lê) chama as funções daqui e não vê boto3 nenhum.
#
# Detalhe de nome: este arquivo NÃO pode se chamar queue.py. Existe um
# módulo chamado "queue" dentro do próprio Python, e um arquivo nosso com
# esse nome tomaria o lugar dele — o boto3 usa esse módulo por dentro e
# para de funcionar. Nome de arquivo também é um endereço.
sqs_client = boto3.client(
    "sqs",
    region_name=AWS_REGION,
    endpoint_url=SQS_ENDPOINT_URL,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

PROCESS_SAMPLE_ENTITY = "process_sample_entity"


def create_queue() -> str:
    """Cria a fila, se ela ainda não existir, e devolve o endereço dela.

    Chamar de novo com o mesmo nome não dá erro nem cria uma segunda: o
    SQS devolve a fila que já existe. Isso tem nome — idempotente — e é o
    que permite a API e o consumer chamarem esta função no boot, os dois,
    sem combinar nada entre si e sem ninguém rodar comando na mão.
    """
    response = sqs_client.create_queue(
        QueueName=SAMPLE_ENTITY_QUEUE_NAME,
        Attributes={
            # Quantos segundos uma mensagem fica INVISÍVEL depois que
            # alguém a pega. É o coração do assunto — leia o comentário
            # sobre isso em src/consumer.py.
            "VisibilityTimeout": "30",
        },
    )

    return response["QueueUrl"]


def get_queue_url() -> str:
    return sqs_client.get_queue_url(QueueName=SAMPLE_ENTITY_QUEUE_NAME)["QueueUrl"]


def send_message(message_body: dict, message_type: str) -> None:
    """Publica uma mensagem na fila. Não espera resposta de ninguém."""
    sqs_client.send_message(
        QueueUrl=get_queue_url(),
        MessageBody=json.dumps(message_body),
        # Além do conteúdo, a mensagem carrega O QUE FAZER com ele. Aqui
        # existe um tipo só; num serviço de verdade são dezenas, e é por
        # este campo que o consumer sabe qual regra chamar.
        MessageAttributes={
            "MessageType": {"StringValue": message_type, "DataType": "String"},
        },
    )


def receive_messages() -> list:
    """Pede mensagens pra fila e espera até 5 segundos por elas.

    Esperar é de propósito: sem isso o consumer perguntaria "tem
    mensagem?" milhares de vezes por segundo, de graça, pra ouvir "não".
    """
    response = sqs_client.receive_message(
        QueueUrl=get_queue_url(),
        MaxNumberOfMessages=10,
        WaitTimeSeconds=5,
        MessageAttributeNames=["All"],
    )

    return response.get("Messages", [])


def delete_message(receipt_handle: str) -> None:
    """Apaga a mensagem da fila. Só depois de o trabalho ter dado certo."""
    sqs_client.delete_message(QueueUrl=get_queue_url(), ReceiptHandle=receipt_handle)
