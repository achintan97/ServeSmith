"""ServeSmith API server."""

from fastapi import FastAPI

from servesmith.models.experiment import Experiment, ExperimentRequest, ExperimentStatus

app = FastAPI(
    title="ServeSmith",
    description="Optimize LLM inference costs in one click",
    version="0.1.0",
)

# In-memory store for now
_experiments: dict[str, Experiment] = {}


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/experiment")
def create_experiment(request: ExperimentRequest) -> dict[str, str]:
    """Submit a new optimization experiment."""
    exp = Experiment(request=request)
    _experiments[exp.experiment_id] = exp
    return {"experiment_id": exp.experiment_id}


@app.get("/experiment/{experiment_id}")
def get_experiment(experiment_id: str) -> dict:
    """Get experiment status and results."""
    exp = _experiments.get(experiment_id)
    if not exp:
        return {"error": f"Experiment {experiment_id} not found"}
    return {"experiment_id": exp.experiment_id, "status": exp.status.value}
