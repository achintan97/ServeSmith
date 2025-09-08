"""Benchmark runner — orchestrates vLLM server + load generator for a single run."""

import csv
import json
import logging
import os
from dataclasses import asdict

from servesmith.benchmarker.load_generator import BenchmarkResult, run_benchmark
from servesmith.benchmarker.vllm_server import VLLMServerManager

logger = logging.getLogger(__name__)


class BenchmarkRunner:
    """Run a complete benchmark: start vLLM server → send load → collect results → cleanup."""

    def __init__(self, in_cluster: bool = True) -> None:
        self.server_mgr = VLLMServerManager(in_cluster=in_cluster)

    def run(
        self,
        experiment_id: str,
        run_id: str,
        model_name: str,
        instance_type: str,
        prompts: list[dict],
        concurrency: int = 1,
        duration_sec: int = 60,
        warmup_sec: int = 10,
        tensor_parallel: int = 1,
        gpu_memory_utilization: float = 0.9,
        max_model_len: int = 2048,
        vllm_image: str | None = None,
        namespace: str = "default",
    ) -> BenchmarkResult:
        """Execute a full benchmark run."""
        pod_name = f"{experiment_id}-{run_id}-srv".lower().replace("_", "-")

        try:
            # 1. Start vLLM server
            logger.info(f"Starting vLLM server: {model_name} on {instance_type}")
            self.server_mgr.create_server_pod(
                name=pod_name,
                model_name=model_name,
                instance_type=instance_type,
                namespace=namespace,
                tensor_parallel=tensor_parallel,
                gpu_memory_utilization=gpu_memory_utilization,
                max_model_len=max_model_len,
                image=vllm_image or "vllm/vllm-openai:v0.18.0",
            )

            # 2. Wait for model to load
            pod_ip = self.server_mgr.wait_for_ready(pod_name, namespace=namespace)
            base_url = f"http://{pod_ip}:8000"

            # 3. Run benchmark
            result = run_benchmark(
                base_url=base_url,
                prompts=prompts,
                concurrency=concurrency,
                duration_sec=duration_sec,
                warmup_sec=warmup_sec,
            )

            return result

        finally:
            # 4. Always cleanup server pod
            logger.info(f"Cleaning up server pod {pod_name}")
            self.server_mgr.delete_server_pod(pod_name, namespace=namespace)


def save_results_csv(results: list[BenchmarkResult], output_path: str) -> str:
    """Save benchmark results to a CSV file."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    fieldnames = [
        "concurrency", "total_requests", "total_duration_sec",
        "requests_per_sec", "tokens_per_sec", "input_tokens_per_sec",
        "total_input_tokens", "total_output_tokens",
        "avg_latency_sec", "p50_latency_sec", "p90_latency_sec", "p99_latency_sec",
        "errors",
    ]

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            row = {k: round(v, 4) if isinstance(v, float) else v for k, v in asdict(r).items() if k in fieldnames}
            writer.writerow(row)

    logger.info(f"Results saved to {output_path}")
    return output_path
