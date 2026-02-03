import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base

class Image(Base):
    __tablename__ = "images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=True)
    original_filename = Column(String, nullable=False)
    original_url = Column(String, nullable=False)
    room_type = Column(String)
    width = Column(Integer)
    height = Column(Integer)
    file_size = Column(Integer)
    format = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    room = relationship("Room", back_populates="images", foreign_keys=[room_id])
    jobs = relationship("Job", back_populates="image", order_by="desc(Job.created_at)")
