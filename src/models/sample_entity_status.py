from sqlalchemy import Column, Integer, String
from models.base import Base


class SampleEntityStatus(Base):
    __tablename__ = "sample_entity_status"

    id = Column(Integer, primary_key=True)
    enumerator = Column(String)
