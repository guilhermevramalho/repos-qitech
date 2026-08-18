from typing import List

from models import SampleEntity
from schemas import SampleEntityKeyResponse, SampleEntityResponse


class SampleEntityDTO:
    """Traduz o objeto do banco no formato que a API devolve.

    O repository entrega um `SampleEntity` — o espelho da tabela, com
    coluna JSON e chave estrangeira. Nada disso sai para o cliente: aqui
    esse objeto vira um dos schemas de resposta de `src/schemas/`.

    Quem descreve a FORMA e o schema; quem faz a TRANSFORMACAO e esta
    classe. Campo novo na resposta se declara la, e se preenche aqui.
    """

    @staticmethod
    def to_response(sample_entity: SampleEntity) -> SampleEntityResponse:
        return SampleEntityResponse(
            sample_entity_key=sample_entity.sample_entity_key,
            hello=sample_entity.sample_entity_data["hello"],
            status=sample_entity.status.enumerator,
            counter=sample_entity.counter,
        )

    @staticmethod
    def to_response_list(sample_entities: List[SampleEntity]) -> List[SampleEntityResponse]:
        sample_entities_response = []

        for sample_entity in sample_entities:
            sample_entities_response.append(SampleEntityDTO.to_response(sample_entity))

        return sample_entities_response

    @staticmethod
    def to_key_response(sample_entity: SampleEntity) -> SampleEntityKeyResponse:
        return SampleEntityKeyResponse(sample_entity_key=sample_entity.sample_entity_key)
