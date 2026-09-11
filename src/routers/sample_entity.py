from fastapi import APIRouter, Query, Response, status

from controllers import SampleEntityController
from utils.schema_handler import SchemaHandler


router = APIRouter()


@router.post("/sample_entity", status_code=status.HTTP_201_CREATED)
@SchemaHandler.validate("post_sample_entity.json")
def create_sample_entity(payload: dict) -> dict:
    # Se o código chegou até aqui, o payload JÁ foi validado contra o
    # src/schemas/post_sample_entity.json. A rota não precisa checar
    # nada: ela só chama a regra de negócio.
    controller = SampleEntityController()
    return controller.create(payload)


@router.get("/sample_entity/{sample_entity_key}", status_code=status.HTTP_200_OK)
def get_sample_entity(sample_entity_key: str) -> dict:
    controller = SampleEntityController()
    return controller.get_by_key(sample_entity_key)


@router.put("/sample_entity/{sample_entity_key}", status_code=status.HTTP_202_ACCEPTED)
@SchemaHandler.validate("put_sample_entity.json")
def update_sample_entity(sample_entity_key: str, payload: dict) -> dict:
    controller = SampleEntityController()
    return controller.update_status(sample_entity_key, payload["status"])


@router.post("/sample_entity/{sample_entity_key}/process", status_code=status.HTTP_202_ACCEPTED)
def process_sample_entity(sample_entity_key: str) -> dict:
    # 202, e não 201 nem 200: "recebi seu pedido e vou fazer", não
    # "está feito". Quando esta linha responde, o trabalho ainda não
    # aconteceu — ele está num recado na fila, esperando o consumer.
    controller = SampleEntityController()
    return controller.request_processing(sample_entity_key)


@router.put(
    "/webhook/sample_entity/{sample_entity_key}/increment_counter",
    status_code=status.HTTP_204_NO_CONTENT,
)
def increment_counter(sample_entity_key: str) -> Response:
    controller = SampleEntityController()
    controller.webhook_increment_counter(sample_entity_key)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/sample_entities", status_code=status.HTTP_200_OK)
def list_sample_entities(
    limit: int = Query(default=10, ge=0, le=100),
    page: int = Query(default=0, ge=0),
    status_filter: str = Query(default=None, alias="status"),
) -> dict:
    controller = SampleEntityController()

    offset = page * limit
    sample_entities_page = controller.get_list(limit, offset, status_filter)

    # A paginação é assunto do endereço (?limit=&page=), não da entidade:
    # por isso quem monta o envelope da página é a rota, e não o DTO.
    return {
        "data": sample_entities_page["sample_entities_list_dto"],
        "limit": limit,
        "page": page,
        "is_last_page": sample_entities_page["is_last_page"],
    }
