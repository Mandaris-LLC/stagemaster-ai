import io
import json
from minio import Minio
from app.core.config import settings

class StorageService:
    def __init__(self):
        self.client = Minio(
            settings.STORAGE_ENDPOINT,
            access_key=settings.STORAGE_ACCESS_KEY,
            secret_key=settings.STORAGE_SECRET_KEY,
            secure=settings.STORAGE_USE_SSL
        )
        self._ensure_buckets()

    def _ensure_buckets(self):
        buckets = [
            settings.BUCKET_UPLOADS,
            settings.BUCKET_RESULTS,
            settings.BUCKET_THUMBNAILS
        ]
        public_buckets = [settings.BUCKET_RESULTS, settings.BUCKET_THUMBNAILS, settings.BUCKET_UPLOADS]
        
        for bucket in buckets:
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)
            
            if bucket in public_buckets:
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"AWS": ["*"]},
                            "Action": ["s3:GetObject"],
                            "Resource": [f"arn:aws:s3:::{bucket}/*"]
                        }
                    ]
                }
                self.client.set_bucket_policy(bucket, json.dumps(policy))

    async def upload_file(self, bucket: str, object_name: str, data: bytes, content_type: str):
        data_stream = io.BytesIO(data)
        self.client.put_object(
            bucket,
            object_name,
            data_stream,
            length=len(data),
            content_type=content_type
        )
        return self.get_url(bucket, object_name)

    def get_url(self, bucket: str, object_name: str):
        # For local development with MinIO in Docker, we might need to handle external vs internal URLs
        # For now, returning a direct URL. In production, this would be a signed URL or CDN URL.
        return f"http://{settings.STORAGE_PUBLIC_ENDPOINT}/{bucket}/{object_name}"

    def get_object_data(self, bucket: str, object_name: str) -> bytes:
        """
        Retrieves object data from MinIO.
        """
        response = None
        try:
            response = self.client.get_object(bucket, object_name)
            return response.read()
        finally:
            if response:
                response.close()
                response.release_conn()

storage_service = StorageService()
