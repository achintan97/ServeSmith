"""Job models — units of work that run on Kubernetes."""

from enum import Enum

from pydantic import BaseModel, Field

from servesmith.models.resource import Resource


class JobKind(str, Enum):
    """Types of jobs ServeSmith can run."""

    BENCHMARK = "benchmark"
    COMPILE = "compile"
    GENERATE = "generate"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class JobSpec(BaseModel):
    """Specification for a Kubernetes job."""

    name: str
    image: str
    args: list[str] = []
    resources: Resource = Resource()
    namespace: str = "default"
    service_account: str = "servesmith-job-sa"
    node_selector: dict[str, str] = {}
    env: dict[str, str] = {}
    volumes: dict[str, str] = {}  # mount_path -> claim/source
