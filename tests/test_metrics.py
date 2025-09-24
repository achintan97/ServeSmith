"""Tests for benchmarker metrics computation."""

from servesmith.benchmarker.load_generator import BenchmarkResult
from servesmith.benchmarker.metrics import compute_tm99, enrich_result


def test_tm99_excludes_top_1_percent():
    latencies = sorted([0.1] * 99 + [10.0])  # 99 fast, 1 outlier
    tm99 = compute_tm99(latencies)
    assert tm99 < 0.2  # Should exclude the 10.0 outlier


def test_tm99_empty():
    assert compute_tm99([]) == 0.0


def test_enrich_result_cost_calculation():
    result = BenchmarkResult(
        concurrency=4,
        tokens_per_sec=500.0,
        input_tokens_per_sec=100.0,
        requests_per_sec=10.0,
        p50_latency_sec=0.3,
        p99_latency_sec=0.4,
        avg_latency_sec=0.35,
        latencies=[0.3, 0.35, 0.4],
    )
    enriched = enrich_result(result, hourly_cost=0.526)  # g4dn.xlarge on-demand

    assert enriched.total_tokens_per_sec == 600.0  # 500 + 100
    assert enriched.cost_per_million_tokens > 0
    assert enriched.cost_per_million_tokens < 1.0  # Should be cents, not dollars


def test_enrich_result_zero_throughput():
    result = BenchmarkResult(tokens_per_sec=0, input_tokens_per_sec=0)
    enriched = enrich_result(result, hourly_cost=1.0)
    assert enriched.cost_per_million_tokens == 0.0  # No division by zero
