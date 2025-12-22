"""ServeSmith API server."""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from servesmith.auth import require_api_key
from servesmith.metrics import metrics

from servesmith.benchmarker.runner import BenchmarkRunner
from servesmith.logging_config import setup_logging
from servesmith.models.experiment import Experiment, ExperimentRequest
from servesmith.orchestrator import Orchestrator
from servesmith.planner.planner import ExperimentPlanner
from servesmith.recommender.recommender import Recommender
from servesmith.store import ExperimentStore

import os

logger = logging.getLogger(__name__)

setup_logging()

IN_CLUSTER = os.environ.get("KUBERNETES_SERVICE_HOST") is not None

store = ExperimentStore()
planner = ExperimentPlanner()
recommender = Recommender()
runner = BenchmarkRunner(in_cluster=IN_CLUSTER)

orchestrator = Orchestrator(store=store, planner=planner, runner=runner, recommender=recommender)

# Store recommendations and run details in memory (TODO: persist to DB)
_recommendations: dict[str, list] = {}
_run_details: dict[str, list] = {}

app = FastAPI(
    title="ServeSmith",
    description="Optimize LLM inference costs in one click",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/metrics")
def prometheus_metrics():
    """Prometheus metrics endpoint."""
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(metrics.prometheus_text(), media_type="text/plain")


@app.get("/templates")
def list_templates() -> dict:
    """List available experiment templates."""
    from servesmith.templates import TEMPLATES
    return TEMPLATES


@app.get("/backends")
def list_available_backends() -> dict:
    """List available inference backends."""
    from servesmith.backends.registry import list_backends
    return {"backends": list_backends()}


@app.post("/experiment")
def create_experiment(
    request: ExperimentRequest,
    background_tasks: BackgroundTasks,
    _: str = Depends(require_api_key),
) -> dict[str, str]:
    """Submit a new optimization experiment.

    The experiment runs asynchronously in the background. Poll GET /experiment/{id} for status.
    """
    exp = Experiment(request=request)
    store.save(exp)

    # Run in background so the API returns immediately
    background_tasks.add_task(_run_experiment, exp)

    return {"experiment_id": exp.experiment_id}


def _run_experiment(exp: Experiment) -> None:
    """Background task that executes the experiment pipeline.

    Runs in a thread pool to avoid blocking FastAPI's async event loop,
    since the orchestrator makes synchronous K8s API calls.
    """
    try:
        recs = orchestrator.execute(exp)
        _recommendations[exp.experiment_id] = [asdict(r) for r in recs]
        # Store per-run details from orchestrator
        _run_details[exp.experiment_id] = orchestrator.last_run_details
        logger.info(f"Experiment {exp.experiment_id} completed with {len(recs)} recommendations")
    except Exception as e:
        logger.error(f"Experiment {exp.experiment_id} failed: {e}", exc_info=True)


@app.get("/experiments")
def list_experiments() -> list[dict]:
    """List all experiments with status."""
    experiments = store.list_all()
    return [
        {
            "experiment_id": exp.experiment_id,
            "model": exp.request.source_model_name,
            "status": exp.status.value,
            "created_at": exp.created_at.isoformat(),
        }
        for exp in experiments
    ]


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


@app.get("/experiment/{experiment_id}/runs")
def get_experiment_runs(experiment_id: str) -> dict:
    """Get individual run details for an experiment."""
    runs = _run_details.get(experiment_id, [])
    return {"experiment_id": experiment_id, "total_count": len(runs), "runs": runs}


# Serve dashboard UI — check multiple possible locations
_UI_CANDIDATES = [
    Path(__file__).parent.parent.parent / "ui",  # dev: src/servesmith/../../ui
    Path("/app/ui"),  # docker
]
UI_DIR = next((p for p in _UI_CANDIDATES if (p / "index.html").exists()), _UI_CANDIDATES[0])


@app.get("/")
def dashboard() -> FileResponse:
    """Serve the ServeSmith dashboard."""
    return FileResponse(UI_DIR / "index.html", media_type="text/html")
