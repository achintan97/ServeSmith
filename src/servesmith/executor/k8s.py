"""Kubernetes job executor — creates and monitors K8s Jobs."""

import logging
import time

from kubernetes import client, config
from kubernetes.client import (
    V1Container,
    V1EnvVar,
    V1Job,
    V1JobSpec,
    V1ObjectMeta,
    V1PodSpec,
    V1PodTemplateSpec,
    V1ResourceRequirements,
)

from servesmith.models.job import JobSpec, JobStatus

logger = logging.getLogger(__name__)


class K8sJobExecutor:
    """Submit and monitor Kubernetes Jobs."""

    def __init__(self, in_cluster: bool = True) -> None:
        if in_cluster:
            config.load_incluster_config()
        else:
            config.load_kube_config()
        self.batch_v1 = client.BatchV1Api()
        self.core_v1 = client.CoreV1Api()

    def submit(self, spec: JobSpec) -> str:
        """Create a K8s Job and return its name."""
        container = V1Container(
            name=f"{spec.name}-ctr",
            image=spec.image,
            args=spec.args,
            env=[V1EnvVar(name=k, value=v) for k, v in spec.env.items()],
            resources=V1ResourceRequirements(
                requests={
                    "cpu": str(spec.resources.cpu or 1),
                    "memory": f"{int(spec.resources.memory or 2)}Gi",
                },
                limits={
                    "cpu": str(spec.resources.cpu or 1),
                    "memory": f"{int(spec.resources.memory or 2)}Gi",
                },
            ),
        )

        # Add GPU request if needed
        if spec.resources.gpu and spec.resources.gpu > 0:
            container.resources.limits["nvidia.com/gpu"] = str(int(spec.resources.gpu))
            container.resources.requests["nvidia.com/gpu"] = str(int(spec.resources.gpu))

        # Node selector — route to correct instance type
        node_selector = spec.node_selector
        if not node_selector and spec.resources.instance_type:
            node_selector = {"node.kubernetes.io/instance-type": spec.resources.instance_type}
        elif not node_selector:
            # No instance type specified — let K8s scheduler decide
            # Do NOT fall back to karpenter labels or custom node pools
            logger.warning(f"Job {spec.name} has no instance_type — scheduler will pick any available node")
            node_selector = None

        job = V1Job(
            metadata=V1ObjectMeta(name=spec.name, namespace=spec.namespace),
            spec=V1JobSpec(
                template=V1PodTemplateSpec(
                    metadata=V1ObjectMeta(labels={"job-name": spec.name}),
                    spec=V1PodSpec(
                        service_account_name=spec.service_account,
                        restart_policy="Never",
                        containers=[container],
                        node_selector=node_selector or None,
                    ),
                ),
                backoff_limit=0,
                ttl_seconds_after_finished=3600,
            ),
        )

        self.batch_v1.create_namespaced_job(namespace=spec.namespace, body=job)
        logger.info(f"Created job {spec.name} in namespace {spec.namespace}")
        return spec.name

    def wait_for_completion(self, name: str, namespace: str = "default", timeout: int = 600) -> JobStatus:
        """Poll job status until completion or timeout."""
        start = time.time()
        while time.time() - start < timeout:
            job = self.batch_v1.read_namespaced_job(name=name, namespace=namespace)
            if job.status.succeeded and job.status.succeeded > 0:
                logger.info(f"Job {name} succeeded")
                return JobStatus.SUCCEEDED
            if job.status.failed and job.status.failed > 0:
                logger.error(f"Job {name} failed")
                return JobStatus.FAILED
            time.sleep(10)
        logger.error(f"Job {name} timed out after {timeout}s")
        return JobStatus.FAILED

    def get_pod_logs(self, job_name: str, namespace: str = "default") -> str:
        """Get logs from the job's pod."""
        pods = self.core_v1.list_namespaced_pod(
            namespace=namespace, label_selector=f"job-name={job_name}"
        )
        if not pods.items:
            return "No pods found for job"
        pod_name = pods.items[0].metadata.name
        return self.core_v1.read_namespaced_pod_log(name=pod_name, namespace=namespace, tail_lines=100)

    def delete_job(self, name: str, namespace: str = "default") -> None:
        """Clean up a completed job."""
        self.batch_v1.delete_namespaced_job(
            name=name, namespace=namespace, propagation_policy="Background"
        )
        logger.info(f"Deleted job {name}")
