import os
import io
import json
import boto3
from PIL import Image

s3 = boto3.client("s3")

# Fallback if dest bucket not passed in event
DEFAULT_DEST_BUCKET = os.environ.get("DEST_BUCKET", "")

def lambda_handler(event, context):
    """
    Expected event from Step Functions / API Gateway:

    {
      "bucket": "my-source-bucket",
      "key": "uploads/example.jpg",
      "dest_bucket": "my-resized-bucket",
      "width": 200,
      "height": 200
    }
    """

    try:
        bucket = event["bucket"]
        key = event["key"]
    except KeyError as e:
        return {
            "status": "FAILED",
            "errorMessage": f"Missing required field: {str(e)}",
        }

    dest_bucket = event.get("dest_bucket") or DEFAULT_DEST_BUCKET
    if not dest_bucket:
        return {
            "status": "FAILED",
            "errorMessage": "Destination bucket not provided in event or environment.",
        }

    width = int(event.get("width", 128))
    height = int(event.get("height", 128))

    try:
        # 1) Download image from S3
        obj = s3.get_object(Bucket=bucket, Key=key)
        body = obj["Body"].read()

        # 2) Load with Pillow
        img = Image.open(io.BytesIO(body))

        # 3) Resize to thumbnail
        img.thumbnail((width, height))

        # 4) Save into memory buffer
        buffer = io.BytesIO()
        img_format = img.format if img.format else "JPEG"
        img.save(buffer, format=img_format)
        buffer.seek(0)

        # 5) Build new key for thumbnail
        base, ext = os.path.splitext(key)
        if not ext:
            ext = ".jpg"
        thumb_key = f"{base}_thumbnail{ext}"

        # 6) Upload resized image to destination bucket
        content_type = obj.get("ContentType", "image/jpeg")
        s3.put_object(
            Bucket=dest_bucket,
            Key=thumb_key,
            Body=buffer,
            ContentType=content_type,
        )

        # 7) Return structured result for Step Functions
        return {
            "status": "SUCCESS",
            "source_bucket": bucket,
            "source_key": key,
            "dest_bucket": dest_bucket,
            "dest_key": thumb_key,
            "width": width,
            "height": height,
        }

    except Exception as e:
        return {
            "status": "FAILED",
            "errorMessage": str(e),
            "bucket": bucket,
            "key": key,
        }
