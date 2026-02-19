from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from app.api.routes import images, jobs, properties
from app.models import Base
from app.models.base import engine

app = FastAPI(title="StageMasterAI API")

# Trust X-Forwarded-Proto/X-Forwarded-For from the load balancer
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    # Create tables on startup for the MVP with retry logic
    import asyncio
    retries = 5
    while retries > 0:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                # Manual migration for room_id column in images table
                from sqlalchemy import text
                try:
                    await conn.execute(text("ALTER TABLE images ADD COLUMN IF NOT EXISTS room_id UUID REFERENCES rooms(id)"))
                    await conn.execute(text("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS room_id UUID REFERENCES rooms(id)"))
                    await conn.execute(text("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS analysis TEXT"))
                    await conn.execute(text("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS placement_plan TEXT"))
                    await conn.execute(text("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS generation_prompt TEXT"))
                except Exception as e:
                    print(f"Migration error (already exists?): {e}")
            
            # Ensure default user exists
            from sqlalchemy.ext.asyncio import AsyncSession
            from sqlalchemy.orm import sessionmaker
            from app.models.user import User
            from app.core.config import settings
            import uuid
            
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            async with async_session() as session:
                from sqlalchemy import select
                result = await session.execute(select(User).where(User.id == uuid.UUID(settings.DEFAULT_USER_ID)))
                user = result.scalar_one_or_none()
                if not user:
                    user = User(
                        id=uuid.UUID(settings.DEFAULT_USER_ID),
                        email="demo@stagemaster.ai",
                        hashed_password="hashed_placeholder"
                    )
                    session.add(user)
                    await session.commit()
            break
        except Exception as e:
            retries -= 1
            print(f"Database connection failed, retrying in 5s... ({retries} retries left)")
            if retries == 0:
                raise e
            await asyncio.sleep(5)

app.include_router(images.router, prefix="/api/v1/images", tags=["images"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(properties.router, prefix="/api/v1/properties", tags=["properties"])

@app.get("/")
async def root():
    return {"message": "Welcome to StageMasterAI API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
