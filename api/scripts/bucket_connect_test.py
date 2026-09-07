import boto3
from halide_api.config import settings

s3 = boto3.client(
    service_name="s3",
    endpoint_url=settings.endpoint_url,
    aws_access_key_id=settings.r2_access_key_id,
    aws_secret_access_key=settings.r2_secret_access_key,
    region_name="auto",
)


with open("./test-assets/frog-test.png", "rb") as f:
    s3.upload_fileobj(f, "fishfish-halide", "frog-test.png")
