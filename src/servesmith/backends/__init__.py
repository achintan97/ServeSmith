"""Backend abstraction — protocol for inference server backends."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol

logger = logging.getLogger(__name__)


@dataclass
class ServerHandle:
    """Reference to a running inference server."""
    name: str
    base_url: str
    backend: str
    namespace: str = "default"


class InferenceBackend(ABC):
    """Protocol for inference server backends (vLLM, TensorRT-LLM, Neuron)."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Backend identifier."""
        ...

    @abstractmethod
    def create_server(
        self,
        pod_name: str,
        model_name: str,
        instance_type: str,
        namespace: str = "default",
        **kwargs,
    ) -> str:
        """Create an inference server. Returns pod name."""
        ...

    @abstractmethod
    def wait_for_ready(self, pod_name: str, namespace: str = "default") -> str:
        """Wait for server to be ready. Returns base URL."""
        ...

    @abstractmethod
    def cleanup(self, pod_name: str, namespace: str = "default") -> None:
        """Delete the server."""
        ...

    def get_docker_command(self, model_name: str, **kwargs) -> str:
        """Generate a docker run command for this config."""
        return f"# No docker command available for {self.name}"
