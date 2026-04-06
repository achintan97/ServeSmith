"""AWS Inferentia/Neuron backend — serves models on Trainium/Inferentia chips."""

import logging
import time

from kubernetes import client
from kubernetes.client import V1Container, V1Pod, V1PodSpec, V1ObjectMeta, V1ResourceRequirements

from servesmith.backends import InferenceBackend

logger = logging.getLogger(__name__)

DEFAULT_NEURON_IMAGE = "public.ecr.aws/neuron/pytorch-inference-neuronx:2.1.2-neuronx-py310-sdk2.20.2-ubuntu20.04"


class NeuronBackend(InferenceBackend):
    """AWS Inferentia/Neuron backend using transformers-neuronx."""

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
        return "neuron"

    def create_server(self, pod_name, model_name, instance_type, namespace="default", **kwargs):
        tp_degree = kwargs.get("tensor_parallel", 2)
        batch_size = kwargs.get("batch_size", 1)
        image = kwargs.get("neuron_image", DEFAULT_NEURON_IMAGE)

        # Neuron cores needed = tp_degree
        neuron_cores = tp_degree

        # Use vLLM with Neuron backend (vLLM supports Neuron natively)
        args = [
            "python3", "-m", "vllm.entrypoints.openai.api_server",
            "--model", model_name,
            "--device", "neuron",
            "--tensor-parallel-size", str(tp_degree),
            "--max-model-len", str(kwargs.get("max_model_len", 2048)),
            "--block-size", "8",
            "--port", "8000",
        ]

        container = V1Container(
            name=f"{pod_name}-ctr",
            image=image,
            args=args,
            ports=[client.V1ContainerPort(container_port=8000)],
            resources=V1ResourceRequirements(
                requests={
                    "aws.amazon.com/neuron": str(neuron_cores),
                    "cpu": "4", "memory": "16Gi",
                },
                limits={"aws.amazon.com/neuron": str(neuron_cores)},
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
        logger.info(f"Created Neuron server pod {pod_name} with {neuron_cores} cores")
        return pod_name

    def wait_for_ready(self, pod_name, namespace="default", timeout_sec=600):
        """Neuron compilation can take several minutes."""
        import urllib.request
        start = time.time()
        while time.time() - start < timeout_sec:
            try:
                pod = self.core_v1.read_namespaced_pod(pod_name, namespace)
                if pod.status.pod_ip and pod.status.phase == "Running":
                    try:
                        urllib.request.urlopen(f"http://{pod.status.pod_ip}:8000/health", timeout=3)
                        logger.info(f"Neuron server {pod_name} ready")
                        return f"http://{pod.status.pod_ip}:8000"
                    except Exception:
                        pass
            except Exception:
                pass
            time.sleep(10)
        raise TimeoutError(f"Neuron server {pod_name} not ready after {timeout_sec}s")

    def cleanup(self, pod_name, namespace="default"):
        try:
            self.core_v1.delete_namespaced_pod(pod_name, namespace)
        except Exception as e:
            logger.warning(f"Failed to delete pod {pod_name}: {e}")

    def get_docker_command(self, model_name, **kwargs):
        tp = kwargs.get("tensor_parallel", 2)
        return (
            f"docker run --device=/dev/neuron0 -p 8000:8000 {DEFAULT_NEURON_IMAGE} "
            f"python3 -m vllm.entrypoints.openai.api_server "
            f"--model {model_name} --device neuron --tensor-parallel-size {tp}"
        )
