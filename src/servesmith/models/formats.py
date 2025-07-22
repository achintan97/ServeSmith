"""Model format definitions for supported inference backends."""

from enum import Enum


class ModelFormat(str, Enum):
    """Supported model formats for inference optimization."""

    VLLM_LATEST = "vllm_latest"

    @property
    def is_vllm(self) -> bool:
        return self == ModelFormat.VLLM_LATEST


class InferenceServer(str, Enum):
    """Supported inference server types."""

    RAY = "ray"
    TRITON = "triton"


class InferenceProtocol(str, Enum):
    """Supported inference protocols."""

    JSON = "json"
    OPENAI = "openai"
