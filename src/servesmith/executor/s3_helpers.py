"""S3 helpers — init containers and artifact management for K8s jobs."""

from kubernetes.client import V1Container, V1EnvVar, V1VolumeMount


S3_INIT_IMAGE = "amazon/aws-cli:2.8.12"


def make_s3_download_init_container(
    s3_path: str,
    local_path: str = "/input/data",
    volume_name: str = "input-data",
    region: str = "us-east-1",
) -> V1Container:
    """Create an init container that downloads data from S3 into a shared volume."""
    return V1Container(
        name="download-input-data",
        image=S3_INIT_IMAGE,
        command=["sh", "-c", f"aws s3 cp {s3_path} {local_path}/ --recursive --region {region}"],
        env=[V1EnvVar(name="AWS_DEFAULT_REGION", value=region)],
        volume_mounts=[V1VolumeMount(name=volume_name, mount_path=local_path)],
    )


def make_s3_upload_command(local_path: str, s3_path: str, region: str = "us-east-1") -> str:
    """Generate an S3 upload command for results."""
    return f"aws s3 cp {local_path} {s3_path} --recursive --region {region}"
