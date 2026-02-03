from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import get_db
from app.models.job import Job
from app.schemas.job import JobCreate, JobRead, JobList
from app.core.config import settings
from app.services.worker import queue_staging_job
import uuid

router = APIRouter()

@router.post("/", response_model=JobRead)
async def create_job(
    job_in: JobCreate,
    db: AsyncSession = Depends(get_db)
):
    # Dummy user ID for MVP
    user_id = uuid.UUID(settings.DEFAULT_USER_ID)
    
    db_job = Job(
        id=uuid.uuid4(),
        user_id=user_id,
        image_id=job_in.image_id,
        room_type=job_in.room_type,
        style_preset=job_in.style_preset,
        fix_white_balance=job_in.fix_white_balance,
        wall_decorations=job_in.wall_decorations,
        include_tv=job_in.include_tv,
        room_id=job_in.room_id,
        status="queued"
    )
    
    db.add(db_job)
    await db.commit()
    await db.refresh(db_job)
    
    # Queue the job
    queue_staging_job(str(db_job.id))
    
    return db_job

@router.get("/", response_model=JobList)
async def list_jobs(
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import select
    result = await db.execute(select(Job).order_by(Job.created_at.desc()))
    jobs = result.scalars().all()
    return {"jobs": jobs}

@router.get("/{job_id}", response_model=JobRead)
async def get_job_status(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    # Status endpoint for polling
    from sqlalchemy import select
    from app.models.image import Image
    
    # query to join job and image to get the original url
    stmt = select(Job, Image).join(Image, Job.image_id == Image.id).where(Job.id == job_id)
    result = await db.execute(stmt)
    record = result.one_or_none()
    
    if not record:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job, image = record
    
    # We need to convert the SQLAlchemy model to the Pydantic schema
    # but manually inject the original_image_url
    job_dict = {c.name: getattr(job, c.name) for c in job.__table__.columns}
    job_dict['original_image_url'] = image.original_url
    
    return job_dict

@router.delete("/{job_id}")
async def delete_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import delete
    result = await db.execute(delete(Job).where(Job.id == job_id))
    await db.commit()
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return {"message": "Job deleted successfully"}
