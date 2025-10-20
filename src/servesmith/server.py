"""ServeSmith API server."""

import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import asdict

from fastapi import FastAPI, BackgroundTasks

from servesmith.benchmarker.runner import BenchmarkRunner
from servesmith.logging_config import setup_logging
from servesmith.models.experiment import Experiment, ExperimentRequest
from servesmith.orchestrator import Orchestrator
from servesmith.planner.planner import ExperimentPlanner
from servesmith.recommender.recommender import Recommender
from servesmith.store import ExperimentStore

logger = logging.getLogger(__name__)

setup_logging()

store = ExperimentStore()
planner = ExperimentPlanner()
recommender = Recommender()

# Runner uses in_cluster=False for local dev, True when deployed to K8s
runner = BenchmarkRunner(in_cluster=False)

orchestrator = Orchestrator(store=store, planner=planner, runner=runner, recommender=recommender)

# Store recommendations in memory (TODO: persist to DB)
_recommendations: dict[str, list] = {}

app = FastAPI(
    title="ServeSmith",
    description="Optimize LLM inference costs in one click",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/experiment")
def create_experiment(request: ExperimentRequest, background_tasks: BackgroundTasks) -> dict[str, str]:
    """Submit a new optimization experiment.

    The experiment runs asynchronously in the background. Poll GET /experiment/{id} for status.
    """
    exp = Experiment(request=request)
    store.save(exp)

    # Run in background so the API returns immediately
    background_tasks.add_task(_run_experiment, exp)

    return {"experiment_id": exp.experiment_id}


def _run_experiment(exp: Experiment) -> None:
    """Background task that executes the experiment pipeline."""
    try:
        recs = orchestrator.execute(exp)
        _recommendations[exp.experiment_id] = [asdict(r) for r in recs]
    except Exception as e:
        logger.error(f"Experiment {exp.experiment_id} failed: {e}")


@app.get("/experiment/{experiment_id}")
def get_experiment(experiment_id: str) -> dict:
    """Get experiment status and recommendations."""
    exp = store.get(experiment_id)
    if not exp:
        return {"error": f"Experiment {experiment_id} not found"}

    response = {
        "experiment_id": exp.experiment_id,
        "status": exp.status.value,
    }

    recs = _recommendations.get(experiment_id)
    if recs:
        response["recommendations"] = recs

    return response
