from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from models import SampleEntity, SampleEntityStatus, SampleEntityStatusEvent


class SampleEntityRepository:
    """A camada que fala com o banco. So aqui existe query.

    Nenhuma regra de negocio mora aqui: esta classe busca, guarda e
    atualiza — quem decide o que fazer com isso e o controller.
    """

    def __init__(self, db: Session) -> None:
        self.session = db

    def create(self, sample_entity_data: dict) -> SampleEntity:
        sample_entity = SampleEntity()
        sample_entity.sample_entity_data = sample_entity_data
        sample_entity.sample_entity_key = str(uuid4())
        sample_entity.counter = 0
        sample_entity.status = self.get_sample_entity_status("created")

        self.session.add(sample_entity)
        return sample_entity

    def update_status(self, sample_entity: SampleEntity, new_status_enumerator: str) -> None:
        new_status = self.get_sample_entity_status(new_status_enumerator)
        sample_entity.status = new_status

        new_status_event = SampleEntityStatusEvent()
        new_status_event.status = new_status
        new_status_event.event_datetime = datetime.now()

        sample_entity.status_events.append(new_status_event)

    def get_by_key(self, sample_entity_key: str) -> SampleEntity:
        return self.session.query(SampleEntity).filter(SampleEntity.sample_entity_key == sample_entity_key).first()

    def get_sample_entity_status(self, enumerator: str) -> SampleEntityStatus:
        return self.session.query(SampleEntityStatus).filter(SampleEntityStatus.enumerator == enumerator).one()

    def list_page(self, limit: int, offset: int, status_enumerator: str) -> list:
        query = self.session.query(SampleEntity)

        if status_enumerator is not None:
            status_model = self.get_sample_entity_status(status_enumerator)
            query = query.filter(SampleEntity.status == status_model)

        return query.limit(limit + 1).offset(offset).all()
