import json
import boto3
from botocore.config import Config
from app.core.config import settings

class StorageService:
    def __init__(self):
        boto_config = Config(
            signature_version='s3v4',
            region_name=settings.STORAGE_REGION,
        )

        if settings.STORAGE_USE_IAM:
            # Use IAM instance profile - boto3 picks up credentials automatically
            self.client = boto3.client(
                's3',
                region_name=settings.STORAGE_REGION,
                config=boto_config,
            )
        else:
            # Use explicit credentials (for local MinIO)
            protocol = "https" if settings.STORAGE_USE_SSL else "http"
            endpoint_url = f"{protocol}://{settings.STORAGE_ENDPOINT}"
            self.client = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=settings.STORAGE_ACCESS_KEY,
                aws_secret_access_key=settings.STORAGE_SECRET_KEY,
                region_name=settings.STORAGE_REGION,
                config=boto_config,
            )

        #self._ensure_buckets()

    def _ensure_buckets(self):
        buckets = [
            settings.BUCKET_UPLOADS,
            settings.BUCKET_RESULTS,
            settings.BUCKET_THUMBNAILS
        ]
        public_buckets = [settings.BUCKET_RESULTS, settings.BUCKET_THUMBNAILS, settings.BUCKET_UPLOADS]

        existing = {b['Name'] for b in self.client.list_buckets().get('Buckets', [])}

        for bucket in buckets:
            if bucket not in existing:
                self.client.create_bucket(
                    Bucket=bucket,
                    CreateBucketConfiguration={'LocationConstraint': settings.STORAGE_REGION}
                ) if settings.STORAGE_REGION != 'us-east-1' else self.client.create_bucket(Bucket=bucket)

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
                self.client.put_bucket_policy(Bucket=bucket, Policy=json.dumps(policy))

    async def upload_file(self, bucket: str, object_name: str, data: bytes, content_type: str):
        print(f"Uploading to bucket: {bucket}, object: {object_name}, content_type: {content_type}")
        self.client.put_object(
            Bucket=bucket,
            Key=object_name,
            Body=data,
            ContentType=content_type,
        )
        return self.get_url(bucket, object_name)

    async def delete_file(self, bucket: str, object_name: str):
        self.client.delete_object(Bucket=bucket, Key=object_name)

    def get_url(self, bucket: str, object_name: str):
        return f"http://{settings.STORAGE_PUBLIC_ENDPOINT}/{bucket}/{object_name}"

    def get_object_data(self, bucket: str, object_name: str) -> bytes:
        """Retrieves object data from S3."""
        response = self.client.get_object(Bucket=bucket, Key=object_name)
        return response['Body'].read()

storage_service = StorageService()
