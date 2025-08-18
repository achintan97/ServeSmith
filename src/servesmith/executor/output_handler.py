"""Job output handler — uploads job artifacts to S3 after completion."""

import logging
import os

import boto3

logger = logging.getLogger(__name__)


def upload_directory_to_s3(local_dir: str, s3_path: str, region: str = "us-east-1") -> int:
    """Upload all files from a local directory to S3.

    Returns the number of files uploaded.
    """
    s3 = boto3.client("s3", region_name=region)

    # Parse s3://bucket/prefix
    parts = s3_path.replace("s3://", "").split("/", 1)
    bucket = parts[0]
    prefix = parts[1] if len(parts) > 1 else ""

    uploaded = 0
    for root, _, files in os.walk(local_dir):
        for filename in files:
            local_path = os.path.join(root, filename)
            relative_path = os.path.relpath(local_path, local_dir)
            s3_key = os.path.join(prefix, relative_path).replace("\\", "/")

            logger.info(f"Uploading {local_path} to s3://{bucket}/{s3_key}")
            s3.upload_file(local_path, bucket, s3_key)
            uploaded += 1

    logger.info(f"Uploaded {uploaded} files to s3://{bucket}/{prefix}")
    return uploaded
