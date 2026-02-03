import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base

class Room(Base):
    __tablename__ = "rooms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id"), nullable=False)
    name = Column(String, nullable=False)
    room_type = Column(String, nullable=False)
    reference_image_id = Column(UUID(as_uuid=True), ForeignKey("images.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    property = relationship("Property", back_populates="rooms")
    images = relationship("Image", back_populates="room", foreign_keys="Image.room_id")
    reference_image = relationship("Image", foreign_keys=[reference_image_id])
