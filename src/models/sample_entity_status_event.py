from sqlalchemy import Column, ForeignKey, Integer, DateTime
from models.base import Base
from sqlalchemy.orm import relationship
from models import SampleEntity, SampleEntityStatus


class SampleEntityStatusEvent(Base):
    __tablename__ = "sample_entity_status_event"

    id = Column(Integer, primary_key=True)
    sample_entity_id = Column(Integer, ForeignKey(SampleEntity.id))
    status_id = Column(Integer, ForeignKey(SampleEntityStatus.id))
    event_datetime = Column(DateTime)

    sample_entity = relationship(
        "SampleEntity",
        foreign_keys=[sample_entity_id],
        back_populates="status_events",
        lazy="selectin",
    )
    status = relationship("SampleEntityStatus", foreign_keys=[status_id], lazy="selectin")
