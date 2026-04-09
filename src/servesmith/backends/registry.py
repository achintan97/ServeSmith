"""Backend registry — resolve backend by name."""

from servesmith.backends import InferenceBackend
from servesmith.backends.vllm_backend import VLLMBackend
from servesmith.backends.tensorrt_backend import TensorRTLLMBackend
from servesmith.backends.neuron_backend import NeuronBackend

_REGISTRY: dict[str, type[InferenceBackend]] = {
    "vllm": VLLMBackend,
    "tensorrt-llm": TensorRTLLMBackend,
    "neuron": NeuronBackend,
}


def get_backend(name: str, in_cluster: bool = True) -> InferenceBackend:
    """Get a backend instance by name."""
    cls = _REGISTRY.get(name)
    if not cls:
        available = ", ".join(_REGISTRY.keys())
        raise ValueError(f"Unknown backend '{name}'. Available: {available}")
    return cls(in_cluster=in_cluster)


def list_backends() -> list[str]:
    """List available backend names."""
    return list(_REGISTRY.keys())
