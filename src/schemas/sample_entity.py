from typing import List, Literal

from pydantic import BaseModel, ConfigDict, Field


class CreateSampleEntityRequest(BaseModel):
    """O JSON que o cliente precisa mandar para criar uma entidade.

    O Pydantic le esta classe e faz tres coisas de graca:
      1. valida o que chegou (e devolve 400 se estiver errado);
      2. converte o JSON num objeto Python de verdade;
      3. documenta o endpoint la no /docs.

    O `extra="forbid"` recusa campo que voce nao pediu — melhor avisar
    o cliente do que engolir um "hllo" com erro de digitacao em silencio.
    """

    model_config = ConfigDict(extra="forbid")

    hello: str = Field(min_length=1, max_length=255)


class UpdateSampleEntityStatusRequest(BaseModel):
    """O JSON para mudar o status de uma entidade.

    `Literal` diz que so estes dois valores existem. Qualquer outro
    vira 400 antes de chegar na regra de negocio.
    """

    model_config = ConfigDict(extra="forbid")

    status: Literal["success", "failed"]


class SampleEntityKeyResponse(BaseModel):
    """A resposta enxuta: so a chave da entidade.

    Quem cria ou muda o status recebe so isto. A chave basta para
    buscar a entidade inteira depois, no GET.
    """

    sample_entity_key: str


class SampleEntityResponse(BaseModel):
    """A entidade inteira, do jeito que o mundo la fora ve.

    Compare com `src/models/sample_entity.py`, que descreve a TABELA:
    la o `hello` esta escondido dentro de uma coluna JSON chamada
    `sample_entity_data`, e o status e um numero apontando pra outra
    tabela. Aqui os dois sao campos planos, com nome de gente.

    Essa diferenca e o motivo de existir a pasta `src/dtos/`: e la que
    um formato vira o outro.
    """

    sample_entity_key: str
    hello: str
    status: str
    counter: int


class SampleEntityPageResponse(BaseModel):
    """Uma pagina da listagem: os itens e o que ajuda a navegar.

    `is_last_page` responde de graca a pergunta que viria em seguida —
    "tem mais?" — sem custar uma segunda requisicao.
    """

    data: List[SampleEntityResponse]
    limit: int
    page: int
    is_last_page: bool
