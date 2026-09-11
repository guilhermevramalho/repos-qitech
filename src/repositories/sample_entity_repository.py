from datetime import date, datetime
from uuid import uuid4

from database import Context
from models import SampleEntity, SampleEntityStatus, SampleEntityStatusEvent


class SampleEntityRepository:
    """A camada que fala com o banco. Só aqui existe query.

    Nenhuma regra de negócio mora aqui: esta classe busca, guarda e
    atualiza — quem decide o que fazer com isso é o controller.

    Repare no que ele recebe: o CONTEXTO do trabalho, e não a sessão
    solta. A sessão é o que ele tira de lá na linha seguinte, e é tudo de
    que precisa hoje — mas a assinatura já fala a língua do que viaja
    entre as camadas. No dia em que o contexto carregar também o
    identificador da requisição, nenhum construtor daqui até o resource
    muda de forma.

    É assim nos serviços da QI, e a linha é a mesma lá e aqui:
    `self.session = context.db_session`.
    """

    def __init__(self, context: Context) -> None:
        self.session = context.db_session

    def create(self, sample_entity_data: dict) -> SampleEntity:
        sample_entity = SampleEntity()

        sample_entity.sample_entity_data = {"hello": sample_entity_data["hello"]}
        sample_entity.name = sample_entity_data["name"]
        sample_entity.email = sample_entity_data["email"]
        sample_entity.document_number = sample_entity_data["document_number"]
        sample_entity.birthdate = date.fromisoformat(sample_entity_data["birthdate"])
        sample_entity.sample_entity_key = str(uuid4())
        sample_entity.counter = 0
        sample_entity.status = self.get_status(SampleEntityStatus.CREATED)

        self.session.add(sample_entity)
        return sample_entity

    def update_status(self, sample_entity: SampleEntity, new_status_enumerator: str) -> None:
        new_status = self.get_status(new_status_enumerator)
        sample_entity.status = new_status

        new_status_event = SampleEntityStatusEvent()
        new_status_event.status = new_status
        new_status_event.event_datetime = datetime.now()

        sample_entity.status_events.append(new_status_event)

    def increment_counter(self, sample_entity: SampleEntity) -> None:
        sample_entity.counter = sample_entity.counter + 1

    def get_by_key(self, sample_entity_key: str) -> SampleEntity:
        return self.session.query(SampleEntity).filter(SampleEntity.sample_entity_key == sample_entity_key).first()

    def get_by_document_number(self, document_number: str) -> SampleEntity:
        return self.session.query(SampleEntity).filter(SampleEntity.document_number == document_number).first()

    def get_by_email(self, email: str) -> SampleEntity:
        return self.session.query(SampleEntity).filter(SampleEntity.email == email).first()

    def get_status(self, enumerator: str) -> SampleEntityStatus:
        return self.session.query(SampleEntityStatus).filter(SampleEntityStatus.enumerator == enumerator).one()

    def list_page(self, limit: int, offset: int, status_enumerator: str) -> list:
        query = self.session.query(SampleEntity)

        if status_enumerator is not None:
            status_model = self.get_status(status_enumerator)
            query = query.filter(SampleEntity.status == status_model)

        return query.limit(limit + 1).offset(offset).all()
