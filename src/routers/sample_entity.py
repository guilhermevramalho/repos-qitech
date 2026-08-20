from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from controllers import SampleEntityController
from database import get_db
from schemas import CreateSampleEntityRequest, UpdateSampleEntityStatusRequest


router = APIRouter()


@router.post("/sample_entity", status_code=status.HTTP_201_CREATED)
def create_sample_entity(
    payload: CreateSampleEntityRequest,
    db: Session = Depends(get_db),
) -> dict:
    # Se o codigo chegou ate aqui, o payload JA foi validado pelo Pydantic.
    # A rota nao precisa checar nada: ela so chama a regra de negocio.
    controller = SampleEntityController(db)
    return controller.create(payload.model_dump())


@router.get("/sample_entity/{sample_entity_key}", status_code=status.HTTP_200_OK)
def get_sample_entity(
    sample_entity_key: str,
    db: Session = Depends(get_db),
) -> dict:
    controller = SampleEntityController(db)
    return controller.get_by_key(sample_entity_key)


@router.put("/sample_entity/{sample_entity_key}", status_code=status.HTTP_202_ACCEPTED)
def update_sample_entity(
    sample_entity_key: str,
    payload: UpdateSampleEntityStatusRequest,
    db: Session = Depends(get_db),
) -> dict:
    controller = SampleEntityController(db)
    return controller.update_status(sample_entity_key, payload.status)


@router.post("/sample_entity/{sample_entity_key}/process", status_code=status.HTTP_202_ACCEPTED)
def process_sample_entity(
    sample_entity_key: str,
    db: Session = Depends(get_db),
) -> dict:
    # 202, e nao 201 nem 200: "recebi seu pedido e vou fazer", nao
    # "esta feito". Quando esta linha responde, o trabalho ainda nao
    # aconteceu — ele esta num recado na fila, esperando o consumer.
    controller = SampleEntityController(db)
    return controller.request_processing(sample_entity_key)


@router.put(
    "/webhook/sample_entity/{sample_entity_key}/increment_counter",
    status_code=status.HTTP_204_NO_CONTENT,
)
def increment_counter(
    sample_entity_key: str,
    db: Session = Depends(get_db),
) -> Response:
    controller = SampleEntityController(db)
    controller.webhook_increment_counter(sample_entity_key)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/sample_entities", status_code=status.HTTP_200_OK)
def list_sample_entities(
    db: Session = Depends(get_db),
    limit: int = Query(default=10, ge=0, le=100),
    page: int = Query(default=0, ge=0),
    status_filter: str = Query(default=None, alias="status"),
) -> dict:
    controller = SampleEntityController(db)

    offset = page * limit
    sample_entities_page = controller.get_list(limit, offset, status_filter)

    # A paginacao e assunto do endereco (?limit=&page=), nao da entidade:
    # por isso quem monta o envelope da pagina e a rota, e nao o DTO.
    return {
        "data": sample_entities_page["sample_entities_list_dto"],
        "limit": limit,
        "page": page,
        "is_last_page": sample_entities_page["is_last_page"],
    }
