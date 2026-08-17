from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from models.base import Base
from models import SampleEntityStatus


class SampleEntity(Base):
    __tablename__ = "sample_entity"

    id = Column(Integer, primary_key=True)
    sample_entity_key = Column(String)
    sample_entity_data = Column(JSON)
    counter = Column(Integer)
    status_id = Column(Integer, ForeignKey(SampleEntityStatus.id))

    status = relationship("SampleEntityStatus", foreign_keys=[status_id], lazy="selectin")

    status_events = relationship(
        "SampleEntityStatusEvent",
        back_populates="sample_entity",
        order_by="asc(SampleEntityStatusEvent.event_datetime)",
    )
