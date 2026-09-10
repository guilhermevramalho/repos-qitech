import json
import traceback

from constants import check_variables
from controllers import SampleEntityController
from database import clear_session_context, open_session_context
from errors.base_error import error_verification
from sqs import PROCESS_SAMPLE_ENTITY, create_queue, delete_message, receive_messages
from utils.logger import get_logger, setup_logging


# "consumer" em vez de __name__: rodando como programa principal, o
# __name__ do Python vale "__main__" — e "__main__" não diz nada a quem
# lê o log.
logger = get_logger("consumer")


def process_message(message: dict) -> None:
    """Descobre o que fazer com uma mensagem, e faz.

    O `MessageType` diz qual regra chamar. Aqui existe um tipo só, e
    ainda assim o `else` no fim importa: mensagem de tipo desconhecido
    é um erro, não uma mensagem pra ignorar em silêncio.

    ────────────────────────────────────────────────────────────────
    POR QUE ESTE BLOCO PARECE TANTO COM O MIDDLEWARE DA SESSÃO
    ────────────────────────────────────────────────────────────────
    Porque é a mesma coisa, e agora dá pra ver.

    O controller que roda aqui é o MESMO que a rota HTTP chama, e ele
    pede a sessão ao contexto do trabalho em que está. Numa requisição,
    quem prepara esse contexto é o src/middlewares/session_manager.py.
    Aqui não existe requisição nenhuma — então quem prepara é este
    arquivo, na unha.

    Abra os dois lado a lado: abre o contexto, roda o trabalho, rollback
    se explodiu, close sempre, limpa o contexto. As mesmas cinco linhas.
    O consumer é o session_manager escrito à mão.
    """
    message_type = message["MessageAttributes"]["MessageType"]["StringValue"]
    message_body = json.loads(message["Body"])

    logger.info(f"Recebi a mensagem {message_type}: {message_body}")

    holder = open_session_context()

    try:
        controller = SampleEntityController()

        if message_type == PROCESS_SAMPLE_ENTITY:
            controller.consumer_process_sample_entity(message_body)
        else:
            raise Exception(f"Nao sei o que fazer com uma mensagem do tipo '{message_type}'")
    except Exception:
        # As duas perguntas `is not None` aqui são quase sempre
        # verdadeiras: o controller é construído na primeira linha do
        # `try` e já pede a sessão. Ficam mesmo assim, pelo mesmo motivo
        # que o rollback do middleware fica — o combinado continua
        # escrito pro dia em que a ordem daqui mudar.
        if holder.session is not None:
            holder.session.rollback()
        raise
    finally:
        if holder.session is not None:
            holder.session.close()

        # Esta linha importa MAIS aqui do que no middleware. O consumer é
        # um processo só, num laço eterno: sem limpar, entre uma mensagem
        # e a outra o contexto continuaria apontando pra um balcão com a
        # sessão já fechada. E sessão fechada do SQLAlchemy não reclama —
        # ela reabre sozinha na próxima query, tomando uma conexão que
        # ninguém mais fecharia. Vazamento silencioso, no processo que
        # roda pra sempre.
        clear_session_context()


def run() -> None:
    """O laço: pede mensagens, processa, apaga. Pra sempre.

    Isto aqui é o consumer inteiro. Um processo separado da API, que não
    atende requisição nenhuma e não tem porta: ele só olha a fila.

    ────────────────────────────────────────────────────────────────
    A LIÇÃO DESTE ARQUIVO — por que o `delete_message` está DEPOIS
    ────────────────────────────────────────────────────────────────
    Quando o consumer pega uma mensagem, ela não sai da fila: ela fica
    INVISÍVEL por um tempo (o `VisibilityTimeout`, 30 segundos, definido
    em src/sqs.py). Duas coisas podem acontecer nesses 30 segundos:

      • deu certo  → o `delete_message` abaixo apaga a mensagem, e
                     acabou;
      • deu erro   → o `delete_message` NÃO roda. Passados os 30
                     segundos a mensagem volta a ficar visível, e o
                     consumer a pega de novo.

    Ou seja: não existe nenhuma linha de código aqui escrita pra "tentar
    de novo". O retry nasce de graça, de NÃO apagar. E isso é de
    propósito: quantas vezes tentar, quanto esperar entre tentativas e
    pra onde mandar a mensagem que falhou muitas vezes (a "fila do
    desespero", ou DLQ) são configuração da fila — decisão de infra,
    mudada sem tocar neste arquivo.

    O contrário disso, escrever o retry na mão aqui dentro, é um erro
    comum e caro: o processo morre no meio e a contagem de tentativas
    morre com ele.

    Uma consequência honesta: se uma mensagem falha SEMPRE (por exemplo,
    pede uma entidade que não existe mais), ela volta pra sempre. Quem
    resolve isso é a DLQ — e este projeto de estudo não tem uma.
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
                # O consumer não pode morrer por causa de uma mensagem
                # ruim: as outras da fila continuam esperando. Anota o
                # que aconteceu e segue — sem apagar a mensagem.
                logger.error(f"Falhei ao processar a mensagem:\n{traceback.format_exc()}")


def main() -> None:
    check_variables()
    error_verification()
    setup_logging()

    # A mesma chamada que a API faz quando sobe. Criar uma fila que já
    # existe não dá erro, e por isso os dois podem fazer isso sem
    # combinar nada: quem chegar primeiro cria, o outro só encontra.
    create_queue()

    run()


if __name__ == "__main__":
    main()
