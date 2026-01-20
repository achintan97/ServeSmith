"""Orchestrator — runs the full experiment pipeline.

Planner → Benchmarker → Recommender
"""

import json
import logging
from pathlib import Path

from servesmith.benchmarker.load_generator import BenchmarkResult
from servesmith.benchmarker.runner import BenchmarkRunner, save_results_csv, upload_results_to_s3
from servesmith.executor.gpu_scaler import ensure_gpu_node, scale_down_gpu
from servesmith.models.experiment import Experiment, ExperimentStatus
from servesmith.planner.planner import ExperimentPlanner, PlannedRun
from servesmith.recommender.recommender import Recommendation, Recommender
from servesmith.store import ExperimentStore

logger = logging.getLogger(__name__)


class Orchestrator:
    """Execute an experiment end-to-end."""

    def __init__(
        self,
        store: ExperimentStore,
        planner: ExperimentPlanner,
        runner: BenchmarkRunner,
        recommender: Recommender,
    ) -> None:
        self.store = store
        self.planner = planner
        self.runner = runner
        self.recommender = recommender

    def execute(self, experiment: Experiment) -> list[Recommendation]:
        """Run the full pipeline: plan → benchmark → recommend."""
        exp_id = experiment.experiment_id
        request = experiment.request

        # 1. Update status
        self.store.update_status(exp_id, ExperimentStatus.ACTIVE)
        logger.info(f"Experiment {exp_id}: starting")

        try:
            # 2. Plan runs
            planned_runs = self.planner.plan(request, exp_id)
            logger.info(f"Experiment {exp_id}: planned {len(planned_runs)} runs")

            if not planned_runs:
                logger.warning(f"Experiment {exp_id}: no valid runs planned")
                self.store.update_status(exp_id, ExperimentStatus.FAILED)
                return []

            # 3. Load test prompts
            prompts = self._load_prompts(request.test_data_path)

            # 4. Ensure GPU node is available
            logger.info(f"Experiment {exp_id}: ensuring GPU node is ready")
            if not ensure_gpu_node():
                logger.error(f"Experiment {exp_id}: GPU node failed to provision")
                self.store.update_status(exp_id, ExperimentStatus.FAILED)
                return []

            # 5. Execute each run sequentially
            results: list[BenchmarkResult] = []
            successful_runs: list[PlannedRun] = []

            for run in planned_runs:
                logger.info(f"Experiment {exp_id}, run {run.run_id}: "
                           f"{run.instance_type}, concurrency={run.concurrency}, "
                           f"quant={run.quantization}")
                try:
                    result = self.runner.run(
                        experiment_id=exp_id,
                        run_id=run.run_id,
                        model_name=run.model_name,
                        instance_type=run.instance_type,
                        prompts=prompts,
                        concurrency=run.concurrency,
                        duration_sec=request.test_duration,
                        warmup_sec=request.warmup_time,
                        tensor_parallel=run.tensor_parallel,
                        gpu_memory_utilization=run.gpu_memory_utilization,
                        max_model_len=run.max_model_len,
                        vllm_image=run.vllm_image,
                    )
                    results.append(result)
                    successful_runs.append(run)
                    logger.info(f"Run {run.run_id}: {result.tokens_per_sec:.1f} tok/s, "
                               f"p99={result.p99_latency_sec*1000:.0f}ms")
                except Exception as e:
                    logger.error(f"Run {run.run_id} failed: {e}")
                    # Continue with remaining runs — partial results are still useful

            # 5. Save results
            if results:
                csv_path = f"/tmp/{exp_id}_results.csv"
                save_results_csv(results, csv_path)
                try:
                    s3_dest = f"{request.output_s3_path}experiment_id={exp_id}/benchmark_results.csv"
                    upload_results_to_s3(csv_path, s3_dest)
                except Exception as e:
                    logger.error(f"Failed to upload results to S3: {e}")

            # 6. Recommend
            recommendations = self.recommender.recommend(
                successful_runs, results, top_k=request.num_recommendations_to_return
            )

            # 7. Done
            status = ExperimentStatus.SUCCEEDED if results else ExperimentStatus.FAILED
            self.store.update_status(exp_id, status)
            logger.info(f"Experiment {exp_id}: {status.value} — {len(results)} runs completed, "
                        f"{len(recommendations)} recommendations")

            return recommendations

        except Exception as e:
            logger.error(f"Experiment {exp_id} failed: {e}")
            self.store.update_status(exp_id, ExperimentStatus.FAILED)
            raise
        finally:
            # Scale down GPU to avoid idle costs
            logger.info(f"Experiment {exp_id}: scaling down GPU node")
            scale_down_gpu()

    def _load_prompts(self, test_data_path: str) -> list[dict]:
        """Load test prompts from local file or S3."""
        if test_data_path.startswith("s3://"):
            import boto3
            parts = test_data_path.replace("s3://", "").split("/", 1)
            bucket, key = parts[0], parts[1]
            s3 = boto3.client("s3")
            obj = s3.get_object(Bucket=bucket, Key=key)
            data = json.loads(obj["Body"].read())
        else:
            data = json.loads(Path(test_data_path).read_text())

        if isinstance(data, list):
            return data
        return [data]
