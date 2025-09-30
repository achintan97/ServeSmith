"""Load generator — sends concurrent requests to an LLM server and collects metrics."""

import json
import logging
import time
from dataclasses import dataclass, field

import urllib.request

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run."""

    concurrency: int = 0
    total_requests: int = 0
    total_duration_sec: float = 0.0
    requests_per_sec: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    tokens_per_sec: float = 0.0
    input_tokens_per_sec: float = 0.0
    latencies: list[float] = field(default_factory=list)
    p50_latency_sec: float = 0.0
    p90_latency_sec: float = 0.0
    p99_latency_sec: float = 0.0
    avg_latency_sec: float = 0.0
    errors: int = 0


def _send_chat_completion(base_url: str, prompt: dict, timeout: int = 300) -> tuple[float, int, int]:
    """Send a single chat completion request. Returns (latency_sec, input_tokens, output_tokens)."""
    payload = json.dumps(prompt).encode()
    req = urllib.request.Request(
        f"{base_url}/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    start = time.time()
    resp = urllib.request.urlopen(req, timeout=timeout)
    latency = time.time() - start

    body = json.loads(resp.read())
    usage = body.get("usage", {})
    input_tokens = usage.get("prompt_tokens", 0)
    output_tokens = usage.get("completion_tokens", 0)
    # Don't use "total_tokens" — it includes both input and output
    return latency, input_tokens, output_tokens


def run_benchmark(
    base_url: str,
    prompts: list[dict],
    concurrency: int = 1,
    duration_sec: int = 60,
    warmup_sec: int = 10,
) -> BenchmarkResult:
    """Run a load test against an LLM server.

    Sends requests sequentially per worker (concurrency simulated via threading).
    Collects latency, throughput, and token metrics.
    """
    import concurrent.futures

    result = BenchmarkResult(concurrency=concurrency)
    latencies: list[float] = []
    total_in = 0
    total_out = 0
    errors = 0
    prompt_idx = 0

    logger.info(f"Starting benchmark: concurrency={concurrency}, duration={duration_sec}s, warmup={warmup_sec}s")

    # Warmup phase
    warmup_end = time.time() + warmup_sec
    while time.time() < warmup_end:
        try:
            prompt = prompts[prompt_idx % len(prompts)]
            prompt_idx += 1
            _send_chat_completion(base_url, prompt)
        except Exception as e:
            logger.debug(f"Warmup request failed: {e}")
        time.sleep(0.1)

    logger.info("Warmup complete. Starting measurement.")

    # Measurement phase
    measurement_start = time.time()
    measurement_end = measurement_start + duration_sec

    def worker():
        nonlocal prompt_idx, total_in, total_out, errors
        local_latencies = []
        local_in = 0
        local_out = 0
        local_errors = 0

        while time.time() < measurement_end:
            try:
                prompt = prompts[prompt_idx % len(prompts)]
                prompt_idx += 1
                lat, inp, out = _send_chat_completion(base_url, prompt)
                local_latencies.append(lat)
                local_in += inp
                local_out += out
            except Exception as e:
                local_errors += 1
                logger.debug(f"Request failed: {e}")

        return local_latencies, local_in, local_out, local_errors

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [pool.submit(worker) for _ in range(concurrency)]
        for f in concurrent.futures.as_completed(futures):
            lats, inp, out, errs = f.result()
            latencies.extend(lats)
            total_in += inp
            total_out += out
            errors += errs

    actual_duration = time.time() - measurement_start

    # Compute metrics
    result.total_requests = len(latencies)
    result.total_duration_sec = actual_duration
    result.total_input_tokens = total_in
    result.total_output_tokens = total_out
    result.errors = errors
    result.latencies = sorted(latencies)

    if latencies:
        result.requests_per_sec = len(latencies) / actual_duration
        result.tokens_per_sec = total_out / actual_duration
        result.input_tokens_per_sec = total_in / actual_duration
        result.avg_latency_sec = sum(latencies) / len(latencies)
        result.p50_latency_sec = _percentile(latencies, 50)
        result.p90_latency_sec = _percentile(latencies, 90)
        result.p99_latency_sec = _percentile(latencies, 99)

    logger.info(
        f"Benchmark complete: {result.total_requests} requests, "
        f"{result.tokens_per_sec:.1f} tok/s, p99={result.p99_latency_sec*1000:.0f}ms"
    )
    return result


def _percentile(sorted_data: list[float], pct: int) -> float:
    """Compute percentile from sorted data."""
    if not sorted_data:
        return 0.0
    idx = int(len(sorted_data) * pct / 100)
    return sorted_data[min(idx, len(sorted_data) - 1)]
