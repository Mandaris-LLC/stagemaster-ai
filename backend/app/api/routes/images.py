from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import get_db
from app.models.image import Image
from app.schemas.image import ImageRead, ImageRead
from app.services.storage import storage_service
from app.core.config import settings
import uuid

router = APIRouter()

@router.post("/upload", response_model=ImageRead)
async def upload_image(
    file: UploadFile = File(...),
    room_id: uuid.UUID = None,
    db: AsyncSession = Depends(get_db)
):
    # For MVP, assume a fixed user ID if not provided
    # In a real app, this would come from auth
    user_id = uuid.UUID(settings.DEFAULT_USER_ID)
    
    file_content = await file.read()
    file_extension = file.filename.split(".")[-1]
    object_name = f"{uuid.uuid4()}.{file_extension}"
    
    url = await storage_service.upload_file(
        settings.BUCKET_UPLOADS,
        object_name,
        file_content,
        file.content_type
    )
    
    db_image = Image(
        id=uuid.uuid4(),
        user_id=user_id,
        room_id=room_id,
        original_filename=file.filename,
        original_url=url,
        file_size=len(file_content),
        format=file.content_type
    )
    
    db.add(db_image)
    await db.flush() # Flush to get image ID

    if room_id:
        from sqlalchemy import select
        from app.models.room import Room
        result = await db.execute(select(Room).where(Room.id == room_id))
        db_room = result.scalar_one_or_none()
        if db_room and db_room.reference_image_id is None:
            db_room.reference_image_id = db_image.id
            db.add(db_room)
    await db.commit()
    await db.refresh(db_image)
    
    return db_image

@router.get("/{image_id}", response_model=ImageRead)
async def get_image(image_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    result = await db.execute(select(Image).where(Image.id == image_id))
    db_image = result.scalar_one_or_none()
    if not db_image:
        raise HTTPException(status_code=404, detail="Image not found")
    return db_image

@router.delete("/{image_id}")
async def delete_image(image_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select, delete, update
    from app.models.room import Room
    
    # Fetch image
    result = await db.execute(select(Image).where(Image.id == image_id))
    db_image = result.scalar_one_or_none()
    if not db_image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    room_id = db_image.room_id
    
    # If this image was a reference image for its room, we must clear/update the room FIRST
    # to avoid ForeignKeyViolationError during commit.
    if room_id:
        room_stmt = select(Room).where(Room.reference_image_id == image_id)
        room_result = await db.execute(room_stmt)
        db_room = room_result.scalar_one_or_none()
        
        if db_room:
            # Find a fallback image (the oldest remaining)
            new_ref_stmt = select(Image).where(
                Image.room_id == room_id,
                Image.id != image_id
            ).order_by(Image.created_at.asc()).limit(1)
            new_ref_result = await db.execute(new_ref_stmt)
            new_ref = new_ref_result.scalar_one_or_none()
            
            db_room.reference_image_id = new_ref.id if new_ref else None
            db.add(db_room)
            await db.flush() # Ensure the room update is flushed before image deletion
    
    # Delete from storage (original)
    if db_image.original_url:
        try:
            object_name = db_image.original_url.split("/")[-1]
            await storage_service.delete_file(settings.BUCKET_UPLOADS, object_name)
        except Exception as e:
            print(f"Error deleting original from storage: {e}")

    # Delete the image record (this will also delete associated jobs if cascade is set, or we should handle it)
    from app.models.job import Job
    # Delete associated jobs first to avoid foreign key issues
    await db.execute(delete(Job).where(Job.image_id == image_id))
    
    await db.delete(db_image)
    await db.commit()

    return {"message": "Image deleted successfully"}
