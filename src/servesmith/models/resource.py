"""Compute resource models and EC2 instance type registry."""

from pydantic import BaseModel, model_validator

# Instance type → (vCPU, memory_gb, gpu_count, gpu_memory_gb)
INSTANCE_REGISTRY: dict[str, tuple[float, float, float, float]] = {
    "g4dn.xlarge": (4, 16, 1, 16),
    "g4dn.2xlarge": (8, 32, 1, 16),
    "g4dn.12xlarge": (48, 192, 4, 64),
    "g5.xlarge": (4, 16, 1, 24),
    "g5.2xlarge": (8, 32, 1, 24),
    "g5.12xlarge": (48, 192, 4, 96),
    "g5.48xlarge": (192, 768, 8, 192),
    "g6e.xlarge": (4, 32, 1, 48),
    "g6e.12xlarge": (48, 384, 4, 192),
    "p4d.24xlarge": (96, 1152, 8, 320),
    "p5.48xlarge": (192, 2048, 8, 640),
    "inf2.xlarge": (4, 16, 0, 0),
    "inf2.8xlarge": (32, 128, 0, 0),
    "inf2.48xlarge": (192, 768, 0, 0),
}


class Resource(BaseModel):
    """Compute resource configuration for an experiment run."""

    instance_type: str | None = None
    cpu: float | None = None
    memory: float | None = None
    gpu: float | None = None
    gpu_memory: float | None = None

    @model_validator(mode="after")
    def populate_from_instance_type(self) -> "Resource":
        """Auto-populate cpu/memory/gpu from instance_type if not set."""
        if self.instance_type and self.instance_type in INSTANCE_REGISTRY:
            cpu, mem, gpu, gpu_mem = INSTANCE_REGISTRY[self.instance_type]
            if self.cpu is None:
                self.cpu = cpu
            if self.memory is None:
                self.memory = mem
            if self.gpu is None:
                self.gpu = gpu
            if self.gpu_memory is None:
                self.gpu_memory = gpu_mem
        return self

    def is_gpu_instance(self) -> bool:
        return self.gpu is not None and self.gpu > 0

    def is_inferentia_instance(self) -> bool:
        return self.instance_type is not None and self.instance_type.startswith("inf")
