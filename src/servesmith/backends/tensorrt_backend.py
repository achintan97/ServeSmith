"""TensorRT-LLM backend — builds optimized engines then serves with Triton."""

import logging
import time

from kubernetes import client
from kubernetes.client import V1Container, V1Pod, V1PodSpec, V1ObjectMeta, V1ResourceRequirements

from servesmith.backends import InferenceBackend

logger = logging.getLogger(__name__)

DEFAULT_TRTLLM_IMAGE = "nvcr.io/nvidia/tritonserver:24.12-trtllm-python-py3"


class TensorRTLLMBackend(InferenceBackend):
    """TensorRT-LLM backend — compile model to TRT engine, serve via Triton."""

    def __init__(self, in_cluster: bool = True) -> None:
        if in_cluster:
            from kubernetes import config
            config.load_incluster_config()
        else:
            from kubernetes import config
            config.load_kube_config()
        self.core_v1 = client.CoreV1Api()

    @property
    def name(self) -> str:
        return "tensorrt-llm"

    def create_server(self, pod_name, model_name, instance_type, namespace="default", **kwargs):
        max_batch_size = kwargs.get("max_batch_size", 8)
        tp_size = kwargs.get("tensor_parallel", 1)
        precision = kwargs.get("precision", "float16")
        max_input_len = kwargs.get("max_input_len", 1024)
        max_output_len = kwargs.get("max_output_len", 512)
        image = kwargs.get("trtllm_image", DEFAULT_TRTLLM_IMAGE)

        # TRT-LLM requires a two-phase process:
        # 1. Convert HF model to TRT engine (trtllm-build)
        # 2. Serve with Triton
        # For simplicity, we use the all-in-one Triton TRT-LLM image
        # which handles conversion at startup
        args = [
            "python3", "-c",
            f"from tensorrt_llm import LLM; "
            f"llm = LLM(model='{model_name}', tensor_parallel_size={tp_size}, "
            f"dtype='{precision}', max_batch_size={max_batch_size}); "
            f"llm.start_server(host='0.0.0.0', port=8000)"
        ]

        container = V1Container(
            name=f"{pod_name}-ctr",
            image=image,
            args=args,
            ports=[client.V1ContainerPort(container_port=8000)],
            resources=V1ResourceRequirements(
                requests={"nvidia.com/gpu": str(tp_size), "cpu": "4", "memory": "24Gi"},
                limits={"nvidia.com/gpu": str(tp_size)},
            ),
        )

        pod = V1Pod(
            metadata=V1ObjectMeta(name=pod_name, namespace=namespace, labels={"app": pod_name}),
            spec=V1PodSpec(
                containers=[container],
                restart_policy="Never",
                node_selector={"node.kubernetes.io/instance-type": instance_type},
            ),
        )

        self.core_v1.create_namespaced_pod(namespace=namespace, body=pod)
        logger.info(f"Created TensorRT-LLM server pod {pod_name}")
        return pod_name

    def wait_for_ready(self, pod_name, namespace="default", timeout_sec=600):
        """TRT-LLM takes longer — model compilation happens at startup."""
        import urllib.request
        start = time.time()
        while time.time() - start < timeout_sec:
            try:
                pod = self.core_v1.read_namespaced_pod(pod_name, namespace)
                if pod.status.pod_ip and pod.status.phase == "Running":
                    url = f"http://{pod.status.pod_ip}:8000/health"
                    try:
                        urllib.request.urlopen(url, timeout=3)
                        logger.info(f"TensorRT-LLM server {pod_name} ready")
                        return f"http://{pod.status.pod_ip}:8000"
                    except Exception:
                        pass
            except Exception:
                pass
            time.sleep(10)
        raise TimeoutError(f"TensorRT-LLM server {pod_name} not ready after {timeout_sec}s")

    def cleanup(self, pod_name, namespace="default"):
        try:
            self.core_v1.delete_namespaced_pod(pod_name, namespace)
            logger.info(f"Deleted TensorRT-LLM pod {pod_name}")
        except Exception as e:
            logger.warning(f"Failed to delete pod {pod_name}: {e}")

    def get_docker_command(self, model_name, **kwargs):
        tp = kwargs.get("tensor_parallel", 1)
        return (
            f"docker run --gpus all -p 8000:8000 {DEFAULT_TRTLLM_IMAGE} "
            f"python3 -c \"from tensorrt_llm import LLM; "
            f"llm = LLM(model='{model_name}', tensor_parallel_size={tp}); "
            f"llm.start_server(host='0.0.0.0', port=8000)\""
        )
