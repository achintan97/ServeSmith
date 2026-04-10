"""Tests for backend registry and recommender."""

from servesmith.backends.registry import get_backend, list_backends
from servesmith.recommender.recommender import Recommender, Constraints, _build_docker_cmd
from servesmith.benchmarker.load_generator import BenchmarkResult
from servesmith.planner.planner import PlannedRun
import pytest


def test_list_backends():
    backends = list_backends()
    assert "vllm" in backends
    assert "tensorrt-llm" in backends
    assert "neuron" in backends


def test_get_backend_unknown():
    with pytest.raises(ValueError, match="Unknown backend"):
        get_backend("nonexistent", in_cluster=False)


def test_docker_command_basic():
    run = PlannedRun(
        run_id="1", model_name="meta-llama/Llama-3-8B", instance_type="g5.xlarge",
        concurrency=4, precision="float16", quantization=None, tensor_parallel=1,
        gpu_memory_utilization=0.9, max_model_len=2048, vllm_image=None,
        kv_cache_dtype=None, enable_prefix_caching=False, max_num_seqs=16,
        test_data_path="s3://test/data.json", output_s3_path="s3://test/out/",
    )
    cmd = _build_docker_cmd(run)
    assert "meta-llama/Llama-3-8B" in cmd
    assert "--quantization" not in cmd


def test_docker_command_with_quantization():
    run = PlannedRun(
        run_id="1", model_name="TheBloke/Llama-3-8B-AWQ", instance_type="g5.xlarge",
        concurrency=4, precision="float16", quantization="awq", tensor_parallel=2,
        kv_cache_dtype=None, enable_prefix_caching=False, max_num_seqs=16,
        test_data_path="s3://t/d.json", output_s3_path="s3://t/o/",
        gpu_memory_utilization=0.9, max_model_len=4096, vllm_image=None,
    )
    cmd = _build_docker_cmd(run)
    assert "--quantization awq" in cmd
    assert "--tensor-parallel-size 2" in cmd
    assert "--max-model-len 4096" in cmd


def test_recommender_with_constraints():
    runs = [
        PlannedRun(run_id="1", model_name="m", instance_type="g4dn.xlarge",
                   concurrency=1, precision="fp16", quantization=None,
                   tensor_parallel=1, gpu_memory_utilization=0.9, max_model_len=2048, vllm_image=None,
                   kv_cache_dtype=None, enable_prefix_caching=False, max_num_seqs=16,
                   test_data_path="s3://t/d", output_s3_path="s3://t/o/"),
        PlannedRun(run_id="2", model_name="m", instance_type="g4dn.xlarge",
                   concurrency=4, precision="fp16", quantization=None,
                   tensor_parallel=1, gpu_memory_utilization=0.9, max_model_len=2048, vllm_image=None,
                   kv_cache_dtype=None, enable_prefix_caching=False, max_num_seqs=16,
                   test_data_path="s3://t/d", output_s3_path="s3://t/o/"),
    ]
    results = [
        BenchmarkResult(concurrency=1, total_requests=100, total_duration_sec=60,
                        requests_per_sec=1.67, tokens_per_sec=50, input_tokens_per_sec=25,
                        total_input_tokens=1500, total_output_tokens=3000,
                        avg_latency_sec=0.6, p50_latency_sec=0.5, p90_latency_sec=0.8,
                        p99_latency_sec=1.2, errors=0),
        BenchmarkResult(concurrency=4, total_requests=400, total_duration_sec=60,
                        requests_per_sec=6.67, tokens_per_sec=200, input_tokens_per_sec=100,
                        total_input_tokens=6000, total_output_tokens=12000,
                        avg_latency_sec=0.3, p50_latency_sec=0.25, p90_latency_sec=0.4,
                        p99_latency_sec=0.5, errors=0),
    ]

    rec = Recommender()

    # Without constraints — both should appear
    recs = rec.recommend(runs, results)
    assert len(recs) == 2

    # With latency constraint — only concurrency=4 passes (p99=0.5s < 1.0s)
    recs = rec.recommend(runs, results, constraints=Constraints(max_p99_latency_sec=1.0))
    assert len(recs) == 1
    assert recs[0].concurrency == 4

    # With throughput constraint — only concurrency=4 passes (200 > 100)
    recs = rec.recommend(runs, results, constraints=Constraints(min_tokens_per_sec=100))
    assert len(recs) == 1
    assert recs[0].concurrency == 4
