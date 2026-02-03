from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.base import get_db
from app.models.property import Property
from app.models.room import Room
from app.schemas.property import PropertyCreate, PropertyRead, PropertyWithRooms, RoomCreate, RoomRead
from app.core.config import settings
import uuid
from typing import List

router = APIRouter()

@router.get("", response_model=List[PropertyRead])
async def list_properties(db: AsyncSession = Depends(get_db)):
    user_id = uuid.UUID(settings.DEFAULT_USER_ID)
    result = await db.execute(select(Property).where(Property.user_id == user_id))
    return result.scalars().all()

@router.post("", response_model=PropertyRead)
async def create_property(prop: PropertyCreate, db: AsyncSession = Depends(get_db)):
    user_id = uuid.UUID(settings.DEFAULT_USER_ID)
    db_prop = Property(
        id=uuid.uuid4(),
        user_id=user_id,
        name=prop.name,
        address=prop.address
    )
    db.add(db_prop)
    await db.commit()
    await db.refresh(db_prop)
    return db_prop

@router.get("/{property_id}", response_model=PropertyWithRooms)
async def get_property(property_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Property).where(Property.id == property_id))
    db_prop = result.scalar_one_or_none()
    if not db_prop:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # SQLAlchemy will handle the rooms relationship if eager loaded or accessed
    # For async we must use selectinload for nested relationships
    from sqlalchemy.orm import selectinload
    from app.models.image import Image
    from app.models.job import Job
    
    stmt = select(Property).options(
        selectinload(Property.rooms).selectinload(Room.images).selectinload(Image.jobs)
    ).where(Property.id == property_id)
    
    result = await db.execute(stmt)
    db_prop = result.scalar_one()
    
    # Manually populate latest_result_url and settings for each image in each room
    for room in db_prop.rooms:
        for img in room.images:
            completed_jobs = [j for j in img.jobs if j.status == "completed" and j.result_url]
            if completed_jobs:
                latest_job = completed_jobs[0]
                img.latest_result_url = latest_job.result_url
                img.latest_settings = {
                    "style_preset": latest_job.style_preset,
                    "fix_white_balance": latest_job.fix_white_balance,
                    "wall_decorations": latest_job.wall_decorations,
                    "include_tv": latest_job.include_tv
                }
    
    return db_prop

@router.post("/{property_id}/rooms", response_model=RoomRead)
async def create_room(property_id: uuid.UUID, room: RoomCreate, db: AsyncSession = Depends(get_db)):
    # Check if property exists
    prop_result = await db.execute(select(Property).where(Property.id == property_id))
    if not prop_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Property not found")
        
    db_room = Room(
        id=uuid.uuid4(),
        property_id=property_id,
        name=room.name,
        room_type=room.room_type
    )
    db.add(db_room)
    await db.commit()
    
    # Fetch back with selectinload to ensure images collection is initialized and safe for async serialization
    from sqlalchemy.orm import selectinload
    stmt = select(Room).options(selectinload(Room.images)).where(Room.id == db_room.id)
    result = await db.execute(stmt)
    return result.scalar_one()

@router.get("/rooms/{room_id}", response_model=RoomRead)
async def get_room(room_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    from sqlalchemy.orm import selectinload
    from app.models.image import Image
    from app.models.job import Job
    stmt = select(Room).options(
        selectinload(Room.images).selectinload(Image.jobs)
    ).where(Room.id == room_id)
    result = await db.execute(stmt)
    db_room = result.scalar_one_or_none()
    if not db_room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Manually populate latest_result_url and settings for each image
    for img in db_room.images:
        completed_jobs = [j for j in img.jobs if j.status == "completed" and j.result_url]
        if completed_jobs:
            # Jobs are ordered by created_at desc in model relationship
            latest_job = completed_jobs[0]
            img.latest_result_url = latest_job.result_url
            img.latest_settings = {
                "style_preset": latest_job.style_preset,
                "fix_white_balance": latest_job.fix_white_balance,
                "wall_decorations": latest_job.wall_decorations,
                "include_tv": latest_job.include_tv
            }
            
    return db_room
@router.delete("/rooms/{room_id}")
async def delete_room(room_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    from app.models.image import Image
    
    # Check if room exists
    stmt = select(Room).where(Room.id == room_id)
    result = await db.execute(stmt)
    db_room = result.scalar_one_or_none()
    if not db_room:
        raise HTTPException(status_code=404, detail="Room not found")
        
    # Check for associated images
    img_stmt = select(Image).where(Image.room_id == room_id)
    img_result = await db.execute(img_stmt)
    if img_result.first():
        raise HTTPException(status_code=400, detail="Cannot delete room that contains images")
        
    await db.delete(db_room)
    await db.commit()
    return {"message": "Room deleted successfully"}
