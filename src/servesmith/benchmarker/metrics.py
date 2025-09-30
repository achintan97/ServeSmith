"""Metrics computation — TM99, cost analysis, and derived metrics."""

from dataclasses import dataclass

from servesmith.benchmarker.load_generator import BenchmarkResult


@dataclass
class EnrichedMetrics:
    """Benchmark result enriched with derived metrics."""

    # From BenchmarkResult
    concurrency: int
    tokens_per_sec: float
    requests_per_sec: float
    p50_latency_sec: float
    p99_latency_sec: float
    avg_latency_sec: float

    # Derived
    tm99_latency_sec: float  # Trailing mean excluding top 1%
    cost_per_million_tokens: float
    tokens_per_sec_per_gpu: float
    total_tokens_per_sec: float  # input + output


def compute_tm99(sorted_latencies: list[float]) -> float:
    """Compute TM99 — mean of latencies excluding the top 1%.

    More stable than p99 for small sample sizes. Represents the average
    experience for 99% of requests.
    """
    if not sorted_latencies:
        return 0.0
    cutoff = int(len(sorted_latencies) * 0.99)
    if cutoff == 0:
        cutoff = len(sorted_latencies)
    return sum(sorted_latencies[:cutoff]) / cutoff


def enrich_result(result: BenchmarkResult, hourly_cost: float, gpu_count: int = 1) -> EnrichedMetrics:
    """Add derived metrics to a benchmark result."""
    total_tps = result.input_tokens_per_sec + result.tokens_per_sec

    cost_per_m = 0.0
    if total_tps > 0:
        tokens_per_hour = total_tps * 3600
        cost_per_m = (hourly_cost / tokens_per_hour) * 1_000_000

    return EnrichedMetrics(
        concurrency=result.concurrency,
        tokens_per_sec=result.tokens_per_sec,
        requests_per_sec=result.requests_per_sec,
        p50_latency_sec=result.p50_latency_sec,
        p99_latency_sec=result.p99_latency_sec,
        avg_latency_sec=result.avg_latency_sec,
        tm99_latency_sec=compute_tm99(result.latencies),
        cost_per_million_tokens=cost_per_m,
        tokens_per_sec_per_gpu=result.tokens_per_sec / max(gpu_count, 1),
        total_tokens_per_sec=total_tps,
    )
