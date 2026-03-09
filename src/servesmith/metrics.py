"""Prometheus metrics for ServeSmith."""

import time
from collections import defaultdict


class Metrics:
    """Simple in-process metrics collector exposed at /metrics."""

    def __init__(self) -> None:
        self.experiments_total = 0
        self.experiments_succeeded = 0
        self.experiments_failed = 0
        self.runs_total = 0
        self.runs_succeeded = 0
        self.runs_failed = 0
        self.gpu_scale_ups = 0
        self.last_experiment_duration_sec = 0.0

    def prometheus_text(self) -> str:
        """Render metrics in Prometheus text exposition format."""
        lines = [
            "# HELP servesmith_experiments_total Total experiments submitted",
            "# TYPE servesmith_experiments_total counter",
            f"servesmith_experiments_total {self.experiments_total}",
            "# HELP servesmith_experiments_succeeded Experiments that succeeded",
            "# TYPE servesmith_experiments_succeeded counter",
            f"servesmith_experiments_succeeded {self.experiments_succeeded}",
            "# HELP servesmith_experiments_failed Experiments that failed",
            "# TYPE servesmith_experiments_failed counter",
            f"servesmith_experiments_failed {self.experiments_failed}",
            "# HELP servesmith_runs_total Total benchmark runs executed",
            "# TYPE servesmith_runs_total counter",
            f"servesmith_runs_total {self.runs_total}",
            "# HELP servesmith_runs_succeeded Runs that succeeded",
            "# TYPE servesmith_runs_succeeded counter",
            f"servesmith_runs_succeeded {self.runs_succeeded}",
            "# HELP servesmith_runs_failed Runs that failed",
            "# TYPE servesmith_runs_failed counter",
            f"servesmith_runs_failed {self.runs_failed}",
            "# HELP servesmith_gpu_scale_ups GPU nodegroup scale-up events",
            "# TYPE servesmith_gpu_scale_ups counter",
            f"servesmith_gpu_scale_ups {self.gpu_scale_ups}",
            "# HELP servesmith_last_experiment_duration_seconds Duration of last experiment",
            "# TYPE servesmith_last_experiment_duration_seconds gauge",
            f"servesmith_last_experiment_duration_seconds {self.last_experiment_duration_sec:.2f}",
        ]
        return "\n".join(lines) + "\n"


# Singleton
metrics = Metrics()
