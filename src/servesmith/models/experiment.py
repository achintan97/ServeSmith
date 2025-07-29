"""Experiment models — the core data structures for optimization runs."""

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field

from servesmith.models.formats import InferenceServer, InferenceProtocol, ModelFormat
from servesmith.models.resource import Resource


class VLLMArgs(BaseModel):
    """vLLM-specific experiment parameters."""

    target_precision: list[str] = ["float16"]
    tensor_parallel_size: list[int] = [1]
    gpu_memory_utilizations: list[float] = [0.9]
    quantization: list[str | None] = [None]
    max_num_seqs: list[int] = [16]
    max_model_len: int | None = None
    kv_cache_dtype: list[str | None] = [None]
    enable_prefix_caching: list[bool] = [False]


class InferenceServerConfig(BaseModel):
    """Inference server configuration."""

    server: InferenceServer = InferenceServer.RAY
    protocol: InferenceProtocol = InferenceProtocol.JSON
    endpoint: str = "/v1/chat/completions"


class ExperimentRequest(BaseModel):
    """What the user submits to start an optimization experiment."""

    source_model_name: str
    source_model_s3_path: str | None = None
    test_data_path: str
    output_s3_path: str

    target_model_format: list[ModelFormat] = [ModelFormat.VLLM_LATEST]
    target_model_format_args: dict[ModelFormat, VLLMArgs] = {}

    inference_server_configuration: InferenceServerConfig = InferenceServerConfig()
    resources: list[Resource]
    concurrencies: list[int] = [1]

    enable_external_model_loading: bool = True
    batch_size: list[int] = [-1]
    test_duration: int = 60
    warmup_time: int = 10
    num_recommendations_to_return: int = 5


class ExperimentStatus(str, Enum):
    """Experiment lifecycle states."""

    PENDING = "pending"
    ACTIVE = "active"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class Experiment(BaseModel):
    """An experiment with its request, status, and metadata."""

    experiment_id: str = Field(default_factory=lambda: f"ss-{uuid.uuid4().hex[:12]}")
    request: ExperimentRequest
    status: ExperimentStatus = ExperimentStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
