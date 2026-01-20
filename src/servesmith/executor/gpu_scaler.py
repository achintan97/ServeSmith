"""GPU node scaling — auto-provision and deprovision GPU nodes for experiments."""

import logging
import time

import boto3

logger = logging.getLogger(__name__)

CLUSTER_NAME = "cortex"
NODEGROUP_NAME = "cortex-gpu"
REGION = "us-east-1"


def ensure_gpu_node(timeout_sec: int = 300) -> bool:
    """Scale GPU nodegroup to 1 if at 0, wait until node is Ready."""
    eks = boto3.client("eks", region_name=REGION)

    ng = eks.describe_nodegroup(clusterName=CLUSTER_NAME, nodegroupName=NODEGROUP_NAME)
    desired = ng["nodegroup"]["scalingConfig"]["desiredSize"]

    if desired >= 1:
        logger.info("GPU nodegroup already has %d node(s)", desired)
        return True

    logger.info("Scaling GPU nodegroup to 1...")
    eks.update_nodegroup_config(
        clusterName=CLUSTER_NAME,
        nodegroupName=NODEGROUP_NAME,
        scalingConfig={"minSize": 0, "maxSize": 1, "desiredSize": 1},
    )

    # Wait for node to join
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        ng = eks.describe_nodegroup(clusterName=CLUSTER_NAME, nodegroupName=NODEGROUP_NAME)
        status = ng["nodegroup"]["status"]
        if status == "ACTIVE" and ng["nodegroup"]["scalingConfig"]["desiredSize"] >= 1:
            # Check if node count matches
            health = ng["nodegroup"].get("health", {}).get("issues", [])
            if not health:
                logger.info("GPU node ready")
                return True
        logger.info("Waiting for GPU node... (status=%s)", status)
        time.sleep(15)

    logger.error("GPU node did not become ready within %ds", timeout_sec)
    return False


def scale_down_gpu() -> None:
    """Scale GPU nodegroup back to 0."""
    try:
        eks = boto3.client("eks", region_name=REGION)
        eks.update_nodegroup_config(
            clusterName=CLUSTER_NAME,
            nodegroupName=NODEGROUP_NAME,
            scalingConfig={"minSize": 0, "maxSize": 1, "desiredSize": 0},
        )
        logger.info("GPU nodegroup scaled to 0")
    except Exception as e:
        logger.error("Failed to scale down GPU: %s", e)
