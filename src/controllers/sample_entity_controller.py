from controllers.base_controller import BaseController
from dtos import SampleEntityDTO
from errors import NotFoundSampleEntity, SampleEntityFinalStatus
from models import SampleEntity
from repositories import SampleEntityRepository
from sqs import PROCESS_SAMPLE_ENTITY, send_message


# Em que status a entidade fica quando o processamento da fila termina.
PROCESSED_STATUS = "success"

# Antes de qual status a entidade ainda pode mudar de estado. O nome
# aparece nas duas pontas — na regra do PUT e na do processamento — e
# por isso mora aqui, escrito uma vez.
CHANGEABLE_STATUS = "pending"


class SampleEntityController(BaseController):
    """As regras de negócio. Aqui mora o "pode" e o "não pode"."""

    def __init__(self) -> None:
        super().__init__(__name__)
        self.sample_entity_repository = SampleEntityRepository(self.session)

    def create(self, sample_entity_data: dict) -> dict:
        self.logger.debug("Criando uma nova Sample Entity")

        sample_entity = self.sample_entity_repository.create(sample_entity_data=sample_entity_data)
        self.sample_entity_repository.update_status(sample_entity, "pending")

        sample_entity_dto = SampleEntityDTO.only_obj_key(sample_entity)
        self.session.commit()

        return sample_entity_dto

    def get_by_key(self, sample_entity_key: str) -> dict:
        self.logger.debug(f"Buscando a entidade de chave {sample_entity_key}")

        sample_entity = self.sample_entity_repository.get_by_key(sample_entity_key)

        if sample_entity is None:
            raise NotFoundSampleEntity(sample_entity_key)

        return SampleEntityDTO.obj_to_dict(sample_entity)

    def get_list(self, limit: int, offset: int, status_enumerator: str) -> dict:
        sample_entities_list = self.sample_entity_repository.list_page(limit, offset, status_enumerator)

        # Pedimos um a mais que o limite só pra saber se existe próxima
        # página. Se veio o extra, ele não entra na resposta.
        is_last_page = True
        if len(sample_entities_list) > limit:
            is_last_page = False
            sample_entities_list = sample_entities_list[:-1]

        return {
            "sample_entities_list_dto": SampleEntityDTO.list_obj_to_list_dict(sample_entities_list),
            "is_last_page": is_last_page,
        }

    def update_status(self, sample_entity_key: str, new_status: str) -> dict:
        sample_entity = self.sample_entity_repository.get_by_key(sample_entity_key)

        if sample_entity is None:
            raise NotFoundSampleEntity(sample_entity_key)

        self._check_status_can_change(sample_entity, new_status)

        self.sample_entity_repository.update_status(sample_entity, new_status)

        sample_entity_dto = SampleEntityDTO.only_obj_key(sample_entity)
        self.session.commit()

        return sample_entity_dto

    def request_processing(self, sample_entity_key: str) -> dict:
        """Aceita o pedido de processamento e vai embora.

        Repare no que esta função NÃO faz: ela não processa nada. Ela
        confere o que dá pra conferir agora, põe um recado na fila e
        devolve. Quem faz o trabalho é o consumer, depois — e é por isso
        que a rota responde 202 ("aceitei") em vez de 200 ("pronto").
        """
        self.logger.debug(f"Pedido de processamento da entidade {sample_entity_key}")

        sample_entity = self.sample_entity_repository.get_by_key(sample_entity_key)

        if sample_entity is None:
            raise NotFoundSampleEntity(sample_entity_key)

        self._check_status_can_change(sample_entity, PROCESSED_STATUS)

        send_message({"sample_entity_key": sample_entity_key}, PROCESS_SAMPLE_ENTITY)

        return SampleEntityDTO.only_obj_key(sample_entity)

    def consumer_process_sample_entity(self, message_body: dict) -> None:
        """O trabalho de verdade — chamado pelo consumer, nunca por uma rota.

        Tudo que ele sabe da requisição original é o que veio na mensagem:
        uma chave. O resto ele busca no banco, como qualquer outro código.
        """
        sample_entity_key = message_body["sample_entity_key"]
        self.logger.debug(f"Processando a entidade {sample_entity_key}")

        sample_entity = self.sample_entity_repository.get_by_key(sample_entity_key)

        if sample_entity is None:
            raise NotFoundSampleEntity(sample_entity_key)

        # A fila promete entregar a mensagem AO MENOS uma vez — não
        # exatamente uma vez. A mesma mensagem pode chegar duas vezes, e
        # não é defeito: é como filas funcionam.
        #
        # Por isso o trabalho confere o estado antes de agir, em vez de
        # confiar no que veio escrito na mensagem. Na segunda vez não há
        # nada a fazer, e não fazer nada é a resposta certa. Código que
        # aguenta receber o mesmo pedido duas vezes sem estragar nada
        # tem nome: é idempotente.
        if sample_entity.status.enumerator != CHANGEABLE_STATUS:
            self.logger.info(f"A entidade {sample_entity_key} ja saiu de '{CHANGEABLE_STATUS}'. Nada a fazer.")
            return

        self.sample_entity_repository.update_status(sample_entity, PROCESSED_STATUS)

        self.session.commit()

    def _check_status_can_change(self, sample_entity: SampleEntity, new_status: str) -> None:
        old_status = sample_entity.status.enumerator

        if old_status != CHANGEABLE_STATUS:
            raise SampleEntityFinalStatus(old_status, new_status)

    def webhook_increment_counter(self, sample_entity_key: str) -> None:
        self.logger.debug(f"Processando webhook da entidade {sample_entity_key}")

        sample_entity = self.sample_entity_repository.get_by_key(sample_entity_key)

        if sample_entity is None:
            raise NotFoundSampleEntity(sample_entity_key)

        sample_entity.counter += 1

        self.session.commit()
