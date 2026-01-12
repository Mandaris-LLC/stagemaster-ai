from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class ImageBase(BaseModel):
    room_type: Optional[str] = None
    original_filename: str

class ImageCreate(ImageBase):
    user_id: UUID
    original_url: str
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None
    format: Optional[str] = None

class ImageRead(ImageBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    original_url: str
    created_at: datetime
