"""ServeSmith API server."""

from fastapi import FastAPI

app = FastAPI(
    title="ServeSmith",
    description="Optimize LLM inference costs in one click",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
