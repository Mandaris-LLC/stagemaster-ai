import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    image_id = Column(UUID(as_uuid=True), ForeignKey("images.id"), nullable=False)
    room_type = Column(String, nullable=False)
    style_preset = Column(String, nullable=False)
    fix_white_balance = Column(Boolean, default=True)
    wall_decorations = Column(Boolean, default=True)
    status = Column(String, default="queued") # queued, in_progress, completed, error
    retry_count = Column(Integer, default=0)
    error_message = Column(String, nullable=True)
    progress_percent = Column(Float, default=0.0)
    current_step = Column(String, nullable=True)
    generation_time_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    result_url = Column(String, nullable=True)
