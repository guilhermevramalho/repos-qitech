from fastapi import Query, Response, status

from controllers import SampleEntityController
from utils.schema_handler import SchemaHandler


class SampleEntityResource:
    """A porta de entrada HTTP da Sample Entity.

    ────────────────────────────────────────────────────────────────
    O QUE UM RESOURCE FAZ — E O QUE ELE NÃO FAZ
    ────────────────────────────────────────────────────────────────
    Ele faz três coisas, nesta ordem, e nada além disso:

      1. confere o corpo da requisição (o decorator do schema);
      2. chama o controller;
      3. devolve o que o controller respondeu.

    Repare no que NÃO está aqui: nenhuma regra de negócio, nenhum
    `if` sobre o estado da entidade, nenhuma linha de SQL. Um método
    daqui cabe em três linhas, e quando não couber é sinal de que uma
    regra vazou da camada de baixo pra cá.

    ────────────────────────────────────────────────────────────────
    POR QUE OS MÉTODOS SE CHAMAM `on_post`, `on_get_by_key`...
    ────────────────────────────────────────────────────────────────
    Porque é assim nos serviços da QI Tech, e a semelhança é de
    propósito — você vai abrir um deles na segunda-feira e encontrar
    exatamente estes nomes.

    Vale saber a diferença, porque ela é boa: lá o framework é o
    Falcon, que DESCOBRE o método pelo nome — chegou um POST, ele
    procura um `on_post`. Aqui o FastAPI não faz isso; quem liga o
    endereço ao método é o `src/app.py`, uma linha por rota, à vista.
    O nome é uma escolha nossa, e escolhemos o que o time já lê.

    ────────────────────────────────────────────────────────────────
    UMA REGRA QUE O CÓDIGO NÃO CONSEGUE COBRAR SOZINHO
    ────────────────────────────────────────────────────────────────
    O `src/app.py` cria UM resource e ele vive enquanto a API estiver
    no ar — não nasce um por requisição. Repare que não existe
    `__init__` aqui, e que nenhum método escreve `self.alguma_coisa`:
    isso é de propósito.

    No dia em que um método guardar algo no `self`, esse algo passa a
    ser compartilhado por TODAS as requisições ao mesmo tempo — e o
    sintoma é uma resposta levando o dado de outra pessoa, sob carga,
    sem erro nenhum no log. O que é de uma requisição fica no
    contexto dela (veja o `get_session` em src/database.py); o que
    fica aqui é de todo mundo.

    ────────────────────────────────────────────────────────────────
    O STATUS DE SUCESSO É DECLARADO NO src/app.py
    ────────────────────────────────────────────────────────────────
    O 201 do POST, o 202 do PUT e o 200 do GET estão lá, na linha que
    registra a rota — e não aqui. É um lugar só, e a lista inteira se
    lê de uma vez.

    Os dois métodos que devolvem `Response(status_code=...)` — o
    webhook aqui e o /health_check — não são exceção a isso: o
    `Response` existe porque o FastAPI precisa dele pra mandar uma
    resposta SEM CORPO, que é o que 204 quer dizer. Quem declara o
    status continua sendo o app.py.
    """

    @SchemaHandler.validate("post_sample_entity.json")
    def on_post(self, payload: dict) -> dict:
        # Se o código chegou até aqui, o payload JÁ foi conferido contra
        # o src/schemas/post_sample_entity.json. O resource não checa
        # nada: ele só chama a regra de negócio.
        controller = SampleEntityController()
        return controller.create(payload)

    def on_get_by_key(self, sample_entity_key: str) -> dict:
        controller = SampleEntityController()
        return controller.get_by_key(sample_entity_key)

    @SchemaHandler.validate("put_sample_entity.json")
    def on_put_by_key(self, sample_entity_key: str, payload: dict) -> dict:
        controller = SampleEntityController()
        return controller.update_status(sample_entity_key, payload["status"])

    def on_post_process(self, sample_entity_key: str) -> dict:
        # 202, e não 201 nem 200: "recebi seu pedido e vou fazer", não
        # "está feito". Quando esta linha responde, o trabalho ainda não
        # aconteceu — ele está num recado na fila, esperando o consumer.
        controller = SampleEntityController()
        return controller.request_processing(sample_entity_key)

    def on_put_increment_counter(self, sample_entity_key: str) -> Response:
        controller = SampleEntityController()
        controller.webhook_increment_counter(sample_entity_key)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    def on_get_list(
        self,
        limit: int = Query(default=10, ge=0, le=100),
        page: int = Query(default=0, ge=0),
        status_filter: str = Query(default=None, alias="status"),
    ) -> dict:
        controller = SampleEntityController()

        offset = page * limit
        sample_entities_page = controller.get_list(limit, offset, status_filter)

        # A paginação é assunto do endereço (?limit=&page=), não da
        # entidade: por isso quem monta o envelope da página é o
        # resource, e não o DTO.
        #
        # É a exceção ao "um método daqui cabe em três linhas", e é
        # deliberada: o envelope fala de limit e page, que são
        # vocabulário de HTTP. Empurrá-lo pro controller obrigaria a
        # regra de negócio a saber o que é uma página.
        return {
            "data": sample_entities_page["sample_entities_list_dto"],
            "limit": limit,
            "page": page,
            "is_last_page": sample_entities_page["is_last_page"],
        }
