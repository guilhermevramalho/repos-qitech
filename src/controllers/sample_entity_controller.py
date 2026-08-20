from sqlalchemy.orm import Session

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
    """As regras de negocio. Aqui mora o "pode" e o "nao pode"."""

    def __init__(self, db: Session) -> None:
        super().__init__(db, __name__)
        self.sample_entity_repository = SampleEntityRepository(db)

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

        # Pedimos um a mais que o limite so pra saber se existe proxima
        # pagina. Se veio o extra, ele nao entra na resposta.
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

        Repare no que esta funcao NAO faz: ela nao processa nada. Ela
        confere o que da pra conferir agora, poe um recado na fila e
        devolve. Quem faz o trabalho e o consumer, depois — e e por isso
        que a rota responde 202 ("aceitei") em vez de 200 ("pronto").
        """
        self.logger.debug(f"Pedido de processamento da entidade {sample_entity_key}")

        sample_entity = self.sample_entity_repository.get_by_key(sample_entity_key)

        if sample_entity is None:
            raise NotFoundSampleEntity(sample_entity_key)

        self._check_status_can_change(sample_entity, PROCESSED_STATUS)

        send_message({"sample_entity_key": sample_entity_key}, PROCESS_SAMPLE_ENTITY)

        return SampleEntityDTO.only_obj_key(sample_entity)

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
