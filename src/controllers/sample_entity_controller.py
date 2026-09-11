from controllers.base_controller import BaseController
from dtos import SampleEntityDTO
from errors import NotFoundSampleEntity, SampleEntityFinalStatus
from models import SampleEntity
from repositories import SampleEntityRepository


# Antes de qual status a entidade ainda pode mudar de estado.
CHANGEABLE_STATUS = "pending"


class SampleEntityController(BaseController):
    """As regras de negócio. Aqui mora o "pode" e o "não pode"."""

    def __init__(self) -> None:
        super().__init__(__name__)
        self.sample_entity_repository = SampleEntityRepository(self.context)

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
