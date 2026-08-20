from abc import ABCMeta

from sqlalchemy.orm import Session

from utils.logger import get_logger


class BaseController(metaclass=ABCMeta):
    """O que todo controller tem em comum: a conexão com o banco e o log."""

    def __init__(self, db: Session, class_name: str) -> None:
        self.session = db
        self.logger = get_logger(class_name)
