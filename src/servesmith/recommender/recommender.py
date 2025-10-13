"""Recommender — ranks benchmark results by cost efficiency."""

import logging
from dataclasses import dataclass

from servesmith.benchmarker.load_generator import BenchmarkResult
from servesmith.benchmarker.metrics import EnrichedMetrics, enrich_result
from servesmith.planner.planner import PlannedRun
from servesmith.recommender.pricing import get_hourly_cost

logger = logging.getLogger(__name__)


@dataclass
class Recommendation:
    """A ranked recommendation with config details and metrics."""

    rank: int
    run_id: str
    instance_type: str
    concurrency: int
    precision: str
    quantization: str | None
    tensor_parallel: int
    tokens_per_sec: float
    p99_latency_sec: float
    cost_per_million_tokens: float
    hourly_cost: float
    metrics: EnrichedMetrics


@dataclass
class Constraints:
    """User-defined SLA constraints for filtering results."""

    max_p99_latency_sec: float | None = None
    min_tokens_per_sec: float | None = None
    max_cost_per_million_tokens: float | None = None


class Recommender:
    """Rank benchmark results by cost efficiency, filtered by constraints."""

    def recommend(
        self,
        runs: list[PlannedRun],
        results: list[BenchmarkResult],
        constraints: Constraints | None = None,
        top_k: int = 5,
    ) -> list[Recommendation]:
        """Rank results by cost/token, optionally filtered by constraints."""
        if len(runs) != len(results):
            logger.warning(f"Mismatch: {len(runs)} runs but {len(results)} results")

        recommendations: list[Recommendation] = []

        for run, result in zip(runs, results):
            if result.total_requests == 0:
                logger.debug(f"Skipping run {run.run_id} — no completed requests")
                continue

            hourly_cost = get_hourly_cost(run.instance_type)
            gpu_count = 1  # TODO: derive from resource

            enriched = enrich_result(result, hourly_cost, gpu_count)

            # Apply constraints
            if constraints:
                if constraints.max_p99_latency_sec and enriched.p99_latency_sec > constraints.max_p99_latency_sec:
                    continue
                if constraints.min_tokens_per_sec and enriched.tokens_per_sec < constraints.min_tokens_per_sec:
                    continue
                if (
                    constraints.max_cost_per_million_tokens
                    and enriched.cost_per_million_tokens > constraints.max_cost_per_million_tokens
                ):
                    continue

            recommendations.append(
                Recommendation(
                    rank=0,  # Set after sorting
                    run_id=run.run_id,
                    instance_type=run.instance_type,
                    concurrency=run.concurrency,
                    precision=run.precision,
                    quantization=run.quantization,
                    tensor_parallel=run.tensor_parallel,
                    tokens_per_sec=enriched.tokens_per_sec,
                    p99_latency_sec=enriched.p99_latency_sec,
                    cost_per_million_tokens=enriched.cost_per_million_tokens,
                    hourly_cost=hourly_cost,
                    metrics=enriched,
                )
            )

        # Sort by cost/token (cheapest first), break ties by throughput
        recommendations.sort(key=lambda r: (r.cost_per_million_tokens, -r.tokens_per_sec))

        # Assign ranks
        for i, rec in enumerate(recommendations):
            rec.rank = i + 1

        return recommendations[:top_k]
