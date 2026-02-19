from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import get_db
from app.models.job import Job
from app.schemas.job import JobCreate, JobRead, JobList
from app.core.config import settings
from app.services.worker import queue_staging_job
import uuid

router = APIRouter()

_TEST_PROMPT = (
    "Edit this room photograph by rendering the following furniture into the existing space "
    "WITHOUT altering the room's architecture, camera angle, wall positions, door locations, "
    "window placements, or any structural element. In the foreground, place a low-profile "
    "3-seater sofa upholstered in a light-grey woven fabric with slim black metal legs against "
    "the right wall, facing the closet. In the center, position a set of round nested coffee "
    "tables with black metal frames and white marble tops atop a 5'x8' monochrome geometric "
    "low-pile rug that leaves the honey-toned oak floor visible at the edges. Against the back "
    "wall, to the right of the existing window, place a low-slung modern TV console in light oak "
    "with white slatted doors, ensuring its height remains below the window sill and the "
    "electrical outlets remain accessible. On the back wall to the left of the window, mount a "
    "large 36\"x48\" framed abstract canvas featuring sage and gold tones. In the far back-left "
    "corner, place a 4ft Fiddle Leaf Fig in a white ceramic pot, ensuring it does not obscure "
    "the HVAC vent or window trim. Leaning against the narrow right wall closest to the camera, "
    "add a tall black-framed arched floor mirror. A slim black floor lamp stands behind the sofa "
    "near the lower-right outlet. All furniture must cast soft, realistic shadows toward the "
    "bottom right, matching the existing warm artificial light from the central bronze flush-mount "
    "fixture and the diffused natural light from the window. Render with 8K resolution, high-end "
    "architectural photography detail, ray-traced reflections on the marble and wood grain, and "
    "perfect perspective matching the wide-angle elevated lens. The room's walls, doors, windows, "
    "ceiling, floor, and all fixtures must remain at their exact original pixel positions."
)

_TEST_IMAGE_URL = "https://stagemaster-uploads.s3.us-east-1.amazonaws.com/04b40cb0-9bbe-4beb-a9bd-89235145d186.jpg"

@router.get("/test-generate")
async def test_generate():
    """Test endpoint: calls generate_image directly with a hardcoded prompt and image URL."""
    from app.services.llm_service import generate_image
    image_bytes = await generate_image(
        prompt=_TEST_PROMPT,
        original_image_url=_TEST_IMAGE_URL,
    )
    return Response(content=image_bytes, media_type="image/jpeg")

@router.post("/", response_model=JobRead)
async def create_job(
    job_in: JobCreate,
    db: AsyncSession = Depends(get_db)
):
    # Dummy user ID for MVP
    user_id = uuid.UUID(settings.DEFAULT_USER_ID)
    
    print(f"Received job creation request for image_id: {job_in.image_id}, room_type: {job_in.room_type}")
    
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
