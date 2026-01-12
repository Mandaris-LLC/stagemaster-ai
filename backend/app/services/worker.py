from redis import Redis
from rq import Queue
from app.core.config import settings

redis_conn = Redis.from_url(settings.REDIS_URL)
job_queue = Queue("staging", connection=redis_conn)

def queue_staging_job(job_id: str):
    # This will be imported in the routes to queue a job
    from app.services.generation import process_staging_job
    job = job_queue.enqueue(
        process_staging_job,
        job_id,
        job_timeout="5m",
        result_ttl=86400
    )
    return job
