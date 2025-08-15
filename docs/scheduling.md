# Node Scheduling

ServeSmith routes benchmark jobs to the correct hardware using Kubernetes node selectors.

## How it works

When a job specifies `instance_type` in its resource config, the executor sets:

```yaml
nodeSelector:
  node.kubernetes.io/instance-type: g4dn.xlarge
```

This is a standard EKS label — no Karpenter or custom node pools required.

## Prerequisites

- GPU nodes must have the NVIDIA device plugin installed
- EBS CSI driver must be installed for ephemeral volumes: `eksctl create addon --name aws-ebs-csi-driver --cluster <name>`
- Apply RBAC: `kubectl apply -f k8s/rbac.yaml`
- Apply storage class: `kubectl apply -f k8s/storage.yaml`
