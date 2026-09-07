import boto3
from halide_api.config import settings
from botocore.exceptions import ClientError
import logging

s3 = boto3.client(
    service_name="s3",
    endpoint_url=settings.endpoint_url,
    aws_access_key_id=settings.r2_access_key_id,
    aws_secret_access_key=settings.r2_secret_access_key,
    region_name="auto",
)

def presign_put(key: str, expires: int = 900) -> str:
    return s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.r2_bucket, "Key": key}, # type: ignore
        ExpiresIn=expires,
    )
    
def get_meta_object(key: str) -> dict | None:
    try:
        response = s3.head_object(Bucket=settings.r2_bucket, Key=key)
        return response
    except ClientError as e:
            logging.warning("head_object failed for %s: %s", key, e.response["Error"]["Code"])
            if e.response['Error']['Code'] == "404":
                return None
            raise
    
    