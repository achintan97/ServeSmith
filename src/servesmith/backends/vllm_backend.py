"""vLLM backend — wraps existing VLLMServerManager as an InferenceBackend."""

from servesmith.backends import InferenceBackend
from servesmith.benchmarker.vllm_server import VLLMServerManager


class VLLMBackend(InferenceBackend):
    """vLLM inference backend."""

    def __init__(self, in_cluster: bool = True) -> None:
        self._mgr = VLLMServerManager(in_cluster=in_cluster)

    @property
    def name(self) -> str:
        return "vllm"

    def create_server(self, pod_name, model_name, instance_type, namespace="default", **kwargs):
        self._mgr.create_server_pod(
            name=pod_name, model_name=model_name, instance_type=instance_type,
            namespace=namespace,
            tensor_parallel=kwargs.get("tensor_parallel", 1),
            gpu_memory_utilization=kwargs.get("gpu_memory_utilization", 0.9),
            max_model_len=kwargs.get("max_model_len", 2048),
            image=kwargs.get("vllm_image", "vllm/vllm-openai:v0.18.0"),
            kv_cache_dtype=kwargs.get("kv_cache_dtype"),
            enable_prefix_caching=kwargs.get("enable_prefix_caching", False),
            quantization=kwargs.get("quantization"),
        )
        return pod_name

    def wait_for_ready(self, pod_name, namespace="default"):
        ip = self._mgr.wait_for_ready(pod_name, namespace=namespace)
        return f"http://{ip}:8000"

    def cleanup(self, pod_name, namespace="default"):
        self._mgr.delete_server_pod(pod_name, namespace=namespace)

    def get_docker_command(self, model_name, **kwargs):
        args = [f"--model {model_name}"]
        if kwargs.get("tensor_parallel", 1) > 1:
            args.append(f"--tensor-parallel-size {kwargs['tensor_parallel']}")
        if kwargs.get("quantization"):
            args.append(f"--quantization {kwargs['quantization']}")
        if kwargs.get("max_model_len"):
            args.append(f"--max-model-len {kwargs['max_model_len']}")
        return f"docker run --gpus all -p 8000:8000 vllm/vllm-openai:latest {' '.join(args)}"
