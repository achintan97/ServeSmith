"""Experiment planner — generates benchmark runs from a multi-config request.

Takes an ExperimentRequest with lists of configs (resources, concurrencies,
precisions, quantizations, etc.) and produces the cartesian product of
valid combinations, each becoming one benchmark run.
"""

import logging
from dataclasses import dataclass

from servesmith.models.experiment import ExperimentRequest, VLLMArgs
from servesmith.models.formats import ModelFormat
from servesmith.models.resource import Resource

logger = logging.getLogger(__name__)


@dataclass
class PlannedRun:
    """A single benchmark run to execute."""

    run_id: str
    model_name: str
    instance_type: str
    concurrency: int
    tensor_parallel: int
    gpu_memory_utilization: float
    max_model_len: int
    precision: str
    quantization: str | None
    kv_cache_dtype: str | None
    enable_prefix_caching: bool
    max_num_seqs: int
    test_data_path: str
    output_s3_path: str
    vllm_image: str | None = None


class ExperimentPlanner:
    """Generate benchmark runs from an experiment request."""

    def __init__(self, default_vllm_image: str | None = None) -> None:
        self.default_vllm_image = default_vllm_image

    def plan(self, request: ExperimentRequest, experiment_id: str) -> list[PlannedRun]:
        """Generate all valid runs from the request's config space."""
        runs: list[PlannedRun] = []
        run_counter = 0

        for model_format in request.target_model_format:
            if not model_format.is_vllm:
                logger.warning(f"Skipping unsupported format: {model_format}")
                continue

            vllm_args = request.target_model_format_args.get(model_format, VLLMArgs())

            for resource in request.resources:
                resource_populated = Resource(instance_type=resource.instance_type)

                for concurrency in request.concurrencies:
                    for tp in vllm_args.tensor_parallel_size:
                        # Skip invalid: TP > GPU count
                        if resource_populated.gpu and tp > resource_populated.gpu:
                            logger.debug(
                                f"Skipping TP={tp} on {resource.instance_type} (only {resource_populated.gpu} GPUs)"
                            )
                            continue

                        for gpu_mem in vllm_args.gpu_memory_utilizations:
                            for precision in vllm_args.target_precision:
                                for quant in vllm_args.quantization:
                                    for kv_dtype in vllm_args.kv_cache_dtype:
                                        for prefix_cache in vllm_args.enable_prefix_caching:
                                            for max_seqs in vllm_args.max_num_seqs:
                                                run_counter += 1
                                                run_id = f"{run_counter}"

                                                run = PlannedRun(
                                                    run_id=run_id,
                                                    model_name=request.source_model_name,
                                                    instance_type=resource.instance_type or "unknown",
                                                    concurrency=concurrency,
                                                    tensor_parallel=tp,
                                                    gpu_memory_utilization=gpu_mem,
                                                    max_model_len=vllm_args.max_model_len or 2048,
                                                    precision=precision,
                                                    quantization=quant,
                                                    kv_cache_dtype=kv_dtype,
                                                    enable_prefix_caching=prefix_cache,
                                                    max_num_seqs=max_seqs,
                                                    test_data_path=request.test_data_path,
                                                    output_s3_path=f"{request.output_s3_path}experiment_id={experiment_id}/run_{run_id}/",
                                                    vllm_image=self.default_vllm_image,
                                                )
                                                runs.append(run)

        logger.info(f"Planned {len(runs)} runs for experiment {experiment_id}")
        return runs
