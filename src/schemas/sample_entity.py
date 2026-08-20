from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CreateSampleEntityRequest(BaseModel):
    """O JSON que o cliente precisa mandar para criar uma entidade.

    O Pydantic lê esta classe e faz duas coisas de graça:
      1. valida o que chegou (e devolve 400 se estiver errado);
      2. converte o JSON num objeto Python de verdade.

    O `extra="forbid"` recusa campo que você não pediu — melhor avisar
    o cliente do que engolir um "hllo" com erro de digitação em silêncio.
    """

    model_config = ConfigDict(extra="forbid")

    hello: str = Field(min_length=1, max_length=255)


class UpdateSampleEntityStatusRequest(BaseModel):
    """O JSON para mudar o status de uma entidade.

    `Literal` diz que só estes dois valores existem. Qualquer outro
    vira 400 antes de chegar na regra de negócio.
    """

    model_config = ConfigDict(extra="forbid")

    status: Literal["success", "failed"]
