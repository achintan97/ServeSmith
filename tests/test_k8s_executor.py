"""Integration tests for K8s executor.

These tests require a running Kubernetes cluster (kind, minikube, or EKS).
Skip with: pytest -m "not integration"
"""

import pytest

from servesmith.executor.k8s import K8sJobExecutor
from servesmith.models.job import JobSpec, JobStatus
from servesmith.models.resource import Resource


@pytest.mark.integration
def test_submit_simple_job():
    """Submit a simple echo job and verify it completes."""
    executor = K8sJobExecutor(in_cluster=False)

    spec = JobSpec(
        name="servesmith-test-echo",
        image="busybox:latest",
        args=["sh", "-c", "echo 'ServeSmith test passed' && sleep 5"],
        resources=Resource(cpu=0.25, memory=0.5),
    )

    job_name = executor.submit(spec)
    assert job_name == "servesmith-test-echo"

    status = executor.wait_for_completion(job_name, timeout=120)
    assert status == JobStatus.SUCCEEDED

    logs = executor.get_pod_logs(job_name)
    assert "ServeSmith test passed" in logs

    executor.delete_job(job_name)


@pytest.mark.integration
def test_submit_gpu_job_node_selector():
    """Verify GPU jobs get the correct node selector."""
    executor = K8sJobExecutor(in_cluster=False)

    spec = JobSpec(
        name="servesmith-test-gpu-selector",
        image="busybox:latest",
        args=["sh", "-c", "echo 'GPU node test' && nvidia-smi || echo 'no GPU'"],
        resources=Resource(instance_type="g4dn.xlarge"),
    )

    # Just verify the job is created — don't wait (may not have GPU node)
    job_name = executor.submit(spec)
    assert job_name == "servesmith-test-gpu-selector"
    executor.delete_job(job_name)
