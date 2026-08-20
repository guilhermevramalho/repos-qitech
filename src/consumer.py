import json
import traceback

from constants import check_variables
from controllers import SampleEntityController
from database import SessionLocal
from errors.base_error import error_verification
from sqs import PROCESS_SAMPLE_ENTITY, create_queue, delete_message, receive_messages
from utils.logger import get_logger, setup_logging


# "consumer" em vez de __name__: rodando como programa principal, o
# __name__ do Python vale "__main__" — e "__main__" nao diz nada a quem
# le o log.
logger = get_logger("consumer")


def process_message(message: dict) -> None:
    """Descobre o que fazer com uma mensagem, e faz.

    O `MessageType` diz qual regra chamar. Aqui existe um tipo so, e
    ainda assim o `else` no fim importa: mensagem de tipo desconhecido
    e um erro, nao uma mensagem pra ignorar em silencio.
    """
    message_type = message["MessageAttributes"]["MessageType"]["StringValue"]
    message_body = json.loads(message["Body"])

    logger.info(f"Recebi a mensagem {message_type}: {message_body}")

    session = SessionLocal()

    try:
        controller = SampleEntityController(session)

        if message_type == PROCESS_SAMPLE_ENTITY:
            controller.consumer_process_sample_entity(message_body)
        else:
            raise Exception(f"Nao sei o que fazer com uma mensagem do tipo '{message_type}'")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def run() -> None:
    """O laco: pede mensagens, processa, apaga. Pra sempre.

    Isto aqui e o consumer inteiro. Um processo separado da API, que nao
    atende requisicao nenhuma e nao tem porta: ele so olha a fila.

    ────────────────────────────────────────────────────────────────
    A LICAO DESTE ARQUIVO — por que o `delete_message` esta DEPOIS
    ────────────────────────────────────────────────────────────────
    Quando o consumer pega uma mensagem, ela nao sai da fila: ela fica
    INVISIVEL por um tempo (o `VisibilityTimeout`, 30 segundos, definido
    em src/sqs.py). Duas coisas podem acontecer nesses 30 segundos:

      • deu certo  → o `delete_message` abaixo apaga a mensagem, e
                     acabou;
      • deu erro   → o `delete_message` NAO roda. Passados os 30
                     segundos a mensagem volta a ficar visivel, e o
                     consumer a pega de novo.

    Ou seja: nao existe nenhuma linha de codigo aqui escrita pra "tentar
    de novo". O retry nasce de graca, de NAO apagar. E isso e de
    proposito: quantas vezes tentar, quanto esperar entre tentativas e
    pra onde mandar a mensagem que falhou muitas vezes (a "fila do
    desespero", ou DLQ) sao configuracao da fila — decisao de infra,
    mudada sem tocar neste arquivo.

    O contrario disso, escrever o retry na mao aqui dentro, e um erro
    comum e caro: o processo morre no meio e a contagem de tentativas
    morre com ele.

    Uma consequencia honesta: se uma mensagem falha SEMPRE (por exemplo,
    pede uma entidade que nao existe mais), ela volta pra sempre. Quem
    resolve isso e a DLQ — e este projeto de estudo nao tem uma.
    """
    logger.info("Consumer no ar, olhando a fila")

    while True:
        messages = receive_messages()

        for message in messages:
            try:
                process_message(message)
                delete_message(message["ReceiptHandle"])
                logger.info("Mensagem processada e apagada da fila")
            except Exception:
                # O consumer nao pode morrer por causa de uma mensagem
                # ruim: as outras da fila continuam esperando. Anota o
                # que aconteceu e segue — sem apagar a mensagem.
                logger.error(f"Falhei ao processar a mensagem:\n{traceback.format_exc()}")


def main() -> None:
    check_variables()
    error_verification()
    setup_logging()

    # A mesma chamada que a API faz quando sobe. Criar uma fila que ja
    # existe nao da erro, e por isso os dois podem fazer isso sem
    # combinar nada: quem chegar primeiro cria, o outro so encontra.
    create_queue()

    run()


if __name__ == "__main__":
    main()
