from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, List

class JobBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    room_type: str
    style_preset: str
    fix_white_balance: bool = False
    wall_decorations: bool = True
    include_tv: bool = False
    room_id: Optional[UUID] = None

class JobCreate(JobBase):
    image_id: UUID

class JobRead(JobBase):
    id: UUID
    user_id: UUID
    image_id: UUID
    status: str
    progress_percent: float
    current_step: Optional[str] = None
    result_url: Optional[str] = None
    original_image_url: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class JobList(BaseModel):
    jobs: List[JobRead]
