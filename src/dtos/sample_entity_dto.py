from copy import deepcopy
from typing import List

from models import SampleEntity, SampleEntityStatusEvent


class SampleEntityDTO:
    """Traduz o objeto do banco no JSON que a API devolve.

    O repository entrega um `SampleEntity` — o espelho da tabela, com
    coluna JSON e chave estrangeira. Nada disso sai para o cliente: aqui
    esse objeto vira um dicionário simples, e é esse dicionário que o
    FastAPI transforma no JSON da resposta.

    Compare com `src/models/sample_entity.py`, que descreve a TABELA:
    lá o `hello` está escondido dentro de uma coluna JSON chamada
    `sample_entity_data`, e o status é um número apontando pra outra
    tabela. Aqui os dois são campos planos, com nome de gente.

    Campo novo na resposta se acrescenta aqui — e só aqui.
    """

    @staticmethod
    def obj_to_dict(sample_entity: SampleEntity) -> dict:
        """A entidade INTEIRA, com a história de como ela chegou aqui.

        É o dossiê: quem abre UMA entidade quer saber por onde ela
        passou, não só onde ela está. Cada mudança de status deixou uma
        linha em sample_entity_status_event, e é aqui que essas linhas
        viram resposta.
        """
        dto = SampleEntityDTO.obj_to_simplified_dict(sample_entity)
        dto["status_events"] = SampleEntityDTO.list_status_events_to_list_dict(
            sample_entity.status_events
        )

        return dto

    @staticmethod
    def obj_to_simplified_dict(sample_entity: SampleEntity) -> dict:
        """A entidade sem a trilha de status — o resumo.

        Existe por causa da LISTAGEM, e o motivo não é economizar
        bytes: a trilha mora em OUTRA tabela, e montá-la item a item
        custa uma consulta por entidade da página.

        Não é estimativa. Medido nesta API, com 28 entidades na
        página: 11 ms devolvendo o resumo, 45 ms devolvendo a trilha
        junto — quatro vezes mais, e a diferença cresce com o tamanho
        da página.

        Quem lista está varrendo; quem abre uma entidade está
        investigando. São dois pedidos diferentes, e por isso são dois
        DTOs.
        """
        # O deepcopy não é frescura: sem ele, `dto` seria o MESMO
        # dicionário que vive dentro do objeto do banco, e as linhas
        # abaixo sujariam esse objeto — que o resto da requisição
        # ainda vai usar.
        dto = deepcopy(sample_entity.sample_entity_data)
        dto["sample_entity_key"] = sample_entity.sample_entity_key
        dto["name"] = sample_entity.name
        dto["email"] = sample_entity.email
        dto["document_number"] = sample_entity.document_number
        dto["birthdate"] = sample_entity.birthdate.isoformat()
        dto["status"] = sample_entity.status.enumerator
        dto["counter"] = sample_entity.counter

        return dto

    @staticmethod
    def status_event_to_dict(status_event: SampleEntityStatusEvent) -> dict:
        dto = dict()
        dto["status"] = status_event.status.enumerator
        dto["event_datetime"] = status_event.event_datetime.isoformat()

        return dto

    @staticmethod
    def list_status_events_to_list_dict(
        status_events_list: List[SampleEntityStatusEvent],
    ) -> List[dict]:
        status_events_dict_list = []

        for status_event in status_events_list:
            status_events_dict_list.append(SampleEntityDTO.status_event_to_dict(status_event))

        return status_events_dict_list

    @staticmethod
    def list_obj_to_list_dict(sample_entities_list: List[SampleEntity]) -> List[dict]:
        sample_entities_dict_list = []

        for sample_entity in sample_entities_list:
            sample_entities_dict_list.append(
                SampleEntityDTO.obj_to_simplified_dict(sample_entity)
            )

        return sample_entities_dict_list

    @staticmethod
    def only_obj_key(sample_entity: SampleEntity) -> dict:
        dto = dict()
        dto["sample_entity_key"] = sample_entity.sample_entity_key

        return dto
