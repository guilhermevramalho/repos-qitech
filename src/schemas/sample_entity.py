from typing import Literal

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
    """A resposta enxuta: so a chave da entidade."""

    sample_entity_key: str
