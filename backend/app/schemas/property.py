import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.image import ImageRead

class PropertyBase(BaseModel):
    name: str
    address: Optional[str] = None

class PropertyCreate(PropertyBase):
    pass

class PropertyRead(PropertyBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class RoomBase(BaseModel):
    name: str
    room_type: str

class RoomCreate(RoomBase):
    pass

class RoomRead(RoomBase):
    id: uuid.UUID
    property_id: uuid.UUID
    reference_image_id: Optional[uuid.UUID] = None
    images: List[ImageRead] = []
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class PropertyWithRooms(PropertyRead):
    rooms: List[RoomRead] = []
