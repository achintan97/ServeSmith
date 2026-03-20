"""GPU metrics collection via nvidia-smi inside vLLM pods."""

import json
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GPUMetrics:
    """GPU hardware metrics from nvidia-smi."""
    utilization_pct: float = 0.0
    memory_used_mb: float = 0.0
    memory_total_mb: float = 0.0
    memory_utilization_pct: float = 0.0
    temperature_c: float = 0.0
    power_draw_w: float = 0.0


def collect_gpu_metrics(core_v1, pod_name: str, namespace: str = "default") -> GPUMetrics | None:
    """Run nvidia-smi inside a pod and parse GPU metrics."""
    try:
        cmd = [
            "nvidia-smi",
            "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw",
            "--format=csv,noheader,nounits",
        ]
        resp = core_v1.connect_get_namespaced_pod_exec(
            pod_name, namespace,
            command=cmd,
            stderr=True, stdout=True, stdin=False, tty=False,
        )
        # Parse: "85, 12045, 16384, 62, 120.5"
        parts = [p.strip() for p in resp.strip().split(",")]
        if len(parts) >= 5:
            mem_used = float(parts[1])
            mem_total = float(parts[2])
            return GPUMetrics(
                utilization_pct=float(parts[0]),
                memory_used_mb=mem_used,
                memory_total_mb=mem_total,
                memory_utilization_pct=(mem_used / mem_total * 100) if mem_total > 0 else 0,
                temperature_c=float(parts[3]),
                power_draw_w=float(parts[4]),
            )
    except Exception as e:
        logger.debug(f"GPU metrics collection failed for {pod_name}: {e}")
    return None
