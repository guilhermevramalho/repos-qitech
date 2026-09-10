from abc import ABCMeta

from database import get_session
from utils.logger import get_logger


class BaseController(metaclass=ABCMeta):
    """O que todo controller tem em comum: a conexão com o banco e o log.

    A sessão não chega mais por parâmetro: o controller a pede ao
    contexto do trabalho em que está rodando. Quem preparou esse contexto
    foi o middleware (numa requisição) ou o consumer (numa mensagem).

    É por isso que construir um controller é a mesma coisa que dizer "eu
    uso banco" — e é a primeira linha do `get_or_create` que decide se a
    sessão nasce agora ou se já existia.
    """

    def __init__(self, class_name: str) -> None:
        self.session = get_session()
        self.logger = get_logger(class_name)
