from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "StageMasterAI"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/stage_db"
    REDIS_URL: str = "redis://redis:6379/0"
    
    STORAGE_ENDPOINT: str = "minio:9000"
    STORAGE_ACCESS_KEY: str = "minioadmin"
    STORAGE_SECRET_KEY: str = "minioadmin"
    STORAGE_USE_SSL: bool = False
    STORAGE_USE_IAM: bool = False  # Use IAM instance profile for AWS
    STORAGE_REGION: str = "us-east-1"
    STORAGE_PUBLIC_ENDPOINT: str = "localhost:9000"
    
    BUCKET_UPLOADS: str = "stage-uploads"
    BUCKET_RESULTS: str = "stage-results"
    BUCKET_THUMBNAILS: str = "stage-thumbnails"
    
    OPENROUTER_API_KEY: str = ""
    LITELLM_ANALYSIS_MODEL: str = "openrouter/google/gemini-2.0-flash-exp:free"
    LITELLM_GENERATION_MODEL: str = "openrouter/google/gemini-2.0-flash-exp:free"

    GOOGLE_CLOUD_PROJECT: str = ""
    GOOGLE_CLOUD_LOCATION: str = "us-central1"
    VERTEX_IMAGEN_MODEL: str = "imagen-3.0-capability-001"
    GOOGLE_SERVICE_ACCOUNT_JSON: str = ""  # Full service account JSON string (alternative to GOOGLE_APPLICATION_CREDENTIALS file)
    
    DEFAULT_USER_ID: str = "d7e45013-a883-4f63-8534-e1136093ba7a"
    
    class Config:
        env_file = ".env"

settings = Settings()
