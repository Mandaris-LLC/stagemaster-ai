import asyncio
import logging
from datetime import datetime
from sqlalchemy import update
from app.models.base import AsyncSessionLocal
from app.models.job import Job
from app.core.config import settings
import httpx

logger = logging.getLogger(__name__)

from sqlalchemy import select
from app.models.image import Image
from app.services.llm_service import analyze_room, plan_furniture_placement, generate_staged_image_prompt, generate_image
from app.services.storage import storage_service

async def _process_staging_job_async(job_id: str):
    """
    Internal async implementation of the staging job.
    """
    async with AsyncSessionLocal() as session:
        # Fetch job and associated image
        stmt = select(Job, Image).join(Image, Job.image_id == Image.id).where(Job.id == job_id)
        result = await session.execute(stmt)
        record = result.one_or_none()
        
        if not record:
            logger.error(f"Job {job_id} or associated image not found")
            return

        db_job, db_image = record

        # Update status to in_progress
        db_job.status = "in_progress"
        db_job.started_at = datetime.utcnow()
        db_job.progress_percent = 10.0
        db_job.current_step = "Analyzing room layout..."
        await session.commit()

        try:
            # 0. Check for reference image if in a room
            reference_image_url = None
            ref_analysis = None
            ref_plan = None
            
            if db_job.room_id:
                from app.models.room import Room
                room_stmt = select(Room).where(Room.id == db_job.room_id)
                room_result = await session.execute(room_stmt)
                db_room = room_result.scalar_one_or_none()
                
                if db_room and db_room.reference_image_id and db_room.reference_image_id != db_image.id:
                    # Get the reference image
                    ref_img_stmt = select(Image).where(Image.id == db_room.reference_image_id)
                    ref_img_result = await session.execute(ref_img_stmt)
                    db_ref_image = ref_img_result.scalar_one_or_none()
                    
                    if db_ref_image:
                        reference_image_url = db_ref_image.original_url
                        
                        # Find the latest successful job for the reference image to inherit the plan
                        ref_job_stmt = select(Job).where(
                            Job.image_id == db_room.reference_image_id,
                            Job.status == "completed"
                        ).order_by(Job.created_at.desc()).limit(1)
                        ref_job_result = await session.execute(ref_job_stmt)
                        db_ref_job = ref_job_result.scalar_one_or_none()
                        
                        if db_ref_job:
                            ref_analysis = db_ref_job.analysis
                            ref_plan = db_ref_job.placement_plan
                            # PRIORITIZE STAGED IMAGE FOR CONSISTENCY
                            if db_ref_job.result_url:
                                reference_image_url = db_ref_job.result_url
                                logger.info(f"Using STAGED reference image for consistency: {reference_image_url}")
                            else:
                                reference_image_url = db_ref_image.original_url
                                logger.info(f"Using ORIGINAL reference image for consistency (no staged version found): {reference_image_url}")
                            
                            logger.info(f"Inheriting furniture plan from reference job: {db_ref_job.id}")

            # 1. Analyze Room
            logger.info(f"Analyzing room for job {job_id}")
            analysis = await analyze_room(
                db_image.original_url, 
                reference_image_url=reference_image_url,
                reference_analysis=ref_analysis
            )
            db_job.analysis = analysis
            
            db_job.progress_percent = 30.0
            db_job.current_step = "Detecting surfaces and depth..."
            await session.commit()

            # 2. Plan Furniture Placement
            logger.info(f"Planning furniture placement for job {job_id}")
            placement_plan = await plan_furniture_placement(
                analysis,
                db_job.room_type,
                db_job.style_preset,
                wall_decorations=db_job.wall_decorations,
                include_tv=db_job.include_tv,
                target_image_url=db_image.original_url,
                reference_image_url=reference_image_url,
                reference_plan=ref_plan
            )
            db_job.placement_plan = placement_plan
            
            db_job.progress_percent = 60.0
            db_job.current_step = "Generating furniture placement plan..."
            await session.commit()
            
            # 3. Generate Staged Image Prompt
            logger.info(f"Generating staged image prompt for job {job_id}")
            generation_prompt = await generate_staged_image_prompt(
                db_image.original_url,
                analysis,
                placement_plan,
                db_job.style_preset,
                fix_white_balance=db_job.fix_white_balance,
                wall_decorations=db_job.wall_decorations,
                include_tv=db_job.include_tv,
                reference_image_url=reference_image_url,
                reference_plan=ref_plan # Prompt generation also benefits from the source plan
            )
            db_job.generation_prompt = generation_prompt
            
            db_job.progress_percent = 80.0
            db_job.current_step = "Rendering final image..."
            await session.commit()
            
            # Real Image Generation
            logger.info(f"Generating image for job {job_id}")
            image_data = await generate_image(
                generation_prompt,
                db_image.original_url,
                fix_white_balance=db_job.fix_white_balance,
                reference_image_url=reference_image_url
            )
            # image_data is now bytes (decoded from base64 or downloaded)
                
            # Upload to results bucket
            result_url = await storage_service.upload_file(
                settings.BUCKET_RESULTS,
                f"{job_id}.jpg",
                image_data,
                "image/jpeg"
            )
            
            db_job.status = "completed"
            db_job.progress_percent = 100.0
            db_job.current_step = "Final rendering complete"
            db_job.completed_at = datetime.utcnow()
            db_job.result_url = result_url
            await session.commit()
            
            logger.info(f"Job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error processing job {job_id}: {str(e)}")
            db_job.status = "error"
            db_job.error_message = str(e)
            await session.commit()

def process_staging_job(job_id: str):
    """
    Sync wrapper for RQ worker to run the async job processing.
    """
    # Force import all models to ensure SQLAlchemy relationships are registered
    import app.models
    asyncio.run(_process_staging_job_async(job_id))
