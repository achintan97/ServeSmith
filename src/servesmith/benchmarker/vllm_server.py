"""vLLM server pod manager — creates, monitors, and cleans up inference server pods."""

import logging
import time

from kubernetes import client, config
from kubernetes.client import (
    V1Container,
    V1ObjectMeta,
    V1Pod,
    V1PodSpec,
    V1ResourceRequirements,
)

logger = logging.getLogger(__name__)

DEFAULT_VLLM_IMAGE = "vllm/vllm-openai:v0.18.0"
READINESS_TIMEOUT = 300  # 5 min for model download + load
READINESS_POLL_INTERVAL = 10


class VLLMServerManager:
    """Manage a vLLM inference server pod on Kubernetes."""

    def __init__(self, in_cluster: bool = True) -> None:
        if in_cluster:
            config.load_incluster_config()
        else:
            config.load_kube_config()
        self.core_v1 = client.CoreV1Api()

    def create_server_pod(
        self,
        name: str,
        model_name: str,
        instance_type: str,
        namespace: str = "default",
        image: str = DEFAULT_VLLM_IMAGE,
        tensor_parallel: int = 1,
        gpu_memory_utilization: float = 0.9,
        max_model_len: int = 2048,
        port: int = 8000,
        kv_cache_dtype: str | None = None,
        enable_prefix_caching: bool = False,
        quantization: str | None = None,
    ) -> str:
        """Create a vLLM server pod and return its name."""
        args = [
            "--model", model_name,
            "--tensor-parallel-size", str(tensor_parallel),
            "--gpu-memory-utilization", str(gpu_memory_utilization),
            "--max-model-len", str(max_model_len),
            "--dtype", "float16",
            "--port", str(port),
        ]
        if kv_cache_dtype:
            args.extend(["--kv-cache-dtype", kv_cache_dtype])
        if enable_prefix_caching:
            args.append("--enable-prefix-caching")
        if quantization:
            args.extend(["--quantization", quantization])

        container = V1Container(
            name=f"{name}-ctr",
            image=image,
            args=args,
            ports=[client.V1ContainerPort(container_port=port)],
            resources=V1ResourceRequirements(
                requests={"nvidia.com/gpu": "1", "cpu": "2", "memory": "11Gi"},
                limits={"nvidia.com/gpu": "1"},
            ),
        )

        pod = V1Pod(
            metadata=V1ObjectMeta(name=name, namespace=namespace, labels={"app": name}),
            spec=V1PodSpec(
                containers=[container],
                restart_policy="Never",
                node_selector={"node.kubernetes.io/instance-type": instance_type},
            ),
        )

        self.core_v1.create_namespaced_pod(namespace=namespace, body=pod)
        logger.info(f"Created vLLM server pod {name} with model {model_name}")
        return name

    def wait_for_ready(self, name: str, namespace: str = "default", port: int = 8000) -> str:
        """Wait for the vLLM server to be ready and return its pod IP."""
        start = time.time()
        pod_ip = None

        while time.time() - start < READINESS_TIMEOUT:
            pod = self.core_v1.read_namespaced_pod(name=name, namespace=namespace)

            # Wait for IP assignment
            if pod.status.pod_ip and not pod_ip:
                pod_ip = pod.status.pod_ip
                logger.info(f"Pod IP assigned: {pod_ip}")

            # Check if pod failed
            if pod.status.phase == "Failed":
                raise RuntimeError(f"vLLM server pod {name} failed")

            # Check if running
            if pod.status.phase == "Running" and pod_ip:
                # Try hitting the health endpoint
                try:
                    import urllib.request
                    url = f"http://{pod_ip}:{port}/health"
                    urllib.request.urlopen(url, timeout=5)
                    logger.info(f"vLLM server ready at {pod_ip}:{port}")
                    return pod_ip
                except Exception:
                    elapsed = int(time.time() - start)
                    logger.info(f"Model still loading... ({elapsed}s elapsed)")

            time.sleep(READINESS_POLL_INTERVAL)

        raise TimeoutError(f"vLLM server {name} not ready after {READINESS_TIMEOUT}s")

    def delete_server_pod(self, name: str, namespace: str = "default") -> None:
        """Delete the vLLM server pod and wait for it to be gone."""
        try:
            self.core_v1.delete_namespaced_pod(name=name, namespace=namespace)
            logger.info(f"Deleted vLLM server pod {name}")

            # Wait for pod to actually terminate — otherwise GPU stays occupied
            for _ in range(30):
                try:
                    self.core_v1.read_namespaced_pod(name=name, namespace=namespace)
                    time.sleep(2)
                except client.exceptions.ApiException as e:
                    if e.status == 404:
                        logger.info(f"Pod {name} fully terminated")
                        return
            logger.warning(f"Pod {name} still terminating after 60s")

        except client.exceptions.ApiException as e:
            if e.status != 404:
                raise
            logger.warning(f"Pod {name} already deleted")
