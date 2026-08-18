from sqlalchemy.orm import Session

from controllers.base_controller import BaseController
from dtos import SampleEntityDTO
from errors import NotFoundSampleEntity, SampleEntityFinalStatus
from repositories import SampleEntityRepository
from schemas import SampleEntityKeyResponse, SampleEntityResponse


class SampleEntityController(BaseController):
    """As regras de negocio. Aqui mora o "pode" e o "nao pode"."""

    def __init__(self, db: Session) -> None:
        super().__init__(db, __name__)
        self.sample_entity_repository = SampleEntityRepository(db)

    def create(self, sample_entity_data: dict) -> SampleEntityKeyResponse:
        self.logger.debug("Criando uma nova Sample Entity")

        sample_entity = self.sample_entity_repository.create(sample_entity_data=sample_entity_data)
        self.sample_entity_repository.update_status(sample_entity, "pending")

        sample_entity_dto = SampleEntityDTO.to_key_response(sample_entity)
        self.session.commit()

        return sample_entity_dto

    def get_by_key(self, sample_entity_key: str) -> SampleEntityResponse:
        self.logger.debug(f"Buscando a entidade de chave {sample_entity_key}")

        sample_entity = self.sample_entity_repository.get_by_key(sample_entity_key)

        if sample_entity is None:
            raise NotFoundSampleEntity(sample_entity_key)

        return SampleEntityDTO.to_response(sample_entity)

    def get_list(self, limit: int, offset: int, status_enumerator: str) -> dict:
        sample_entities_list = self.sample_entity_repository.list_page(limit, offset, status_enumerator)

        # Pedimos um a mais que o limite so pra saber se existe proxima
        # pagina. Se veio o extra, ele nao entra na resposta.
        is_last_page = True
        if len(sample_entities_list) > limit:
            is_last_page = False
            sample_entities_list = sample_entities_list[:-1]

        return {
            "sample_entities_list_dto": SampleEntityDTO.to_response_list(sample_entities_list),
            "is_last_page": is_last_page,
        }

    def update_status(self, sample_entity_key: str, new_status: str) -> SampleEntityKeyResponse:
        sample_entity = self.sample_entity_repository.get_by_key(sample_entity_key)

        if sample_entity is None:
            raise NotFoundSampleEntity(sample_entity_key)

        old_status = sample_entity.status.enumerator

        if old_status != "pending":
            raise SampleEntityFinalStatus(old_status, new_status)

        self.sample_entity_repository.update_status(sample_entity, new_status)

        sample_entity_dto = SampleEntityDTO.to_key_response(sample_entity)
        self.session.commit()

        return sample_entity_dto

    def webhook_increment_counter(self, sample_entity_key: str) -> None:
        self.logger.debug(f"Processando webhook da entidade {sample_entity_key}")

        sample_entity = self.sample_entity_repository.get_by_key(sample_entity_key)

        if sample_entity is None:
            raise NotFoundSampleEntity(sample_entity_key)

        sample_entity.counter += 1

        self.session.commit()
