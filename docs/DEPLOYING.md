# Deploying ServeSmith on EKS

## Prerequisites

- AWS CLI configured
- `eksctl` installed
- `kubectl` installed

## 1. Create EKS Cluster

```bash
eksctl create cluster \
  --name servesmith \
  --region us-east-1 \
  --nodegroup-name system \
  --node-type t3.medium \
  --nodes 2
```

## 2. Add GPU Node Group (spot for cost savings)

```bash
eksctl create nodegroup \
  --cluster servesmith \
  --name gpu \
  --node-type g4dn.xlarge \
  --nodes 1 --nodes-min 0 --nodes-max 2 \
  --spot
```

## 3. Install EBS CSI Driver

```bash
eksctl create addon --name aws-ebs-csi-driver --cluster servesmith
```

## 4. Apply RBAC and Storage

```bash
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/storage.yaml
```

## 5. Create S3 Bucket for Experiments

```bash
aws s3 mb s3://servesmith-experiments-$(aws sts get-caller-identity --query Account --output text)
```

## 6. Set Up IAM for Job Pods (IRSA)

```bash
eksctl create iamserviceaccount \
  --cluster servesmith \
  --name servesmith-job-sa \
  --namespace default \
  --attach-policy-arn <your-s3-policy-arn> \
  --approve
```

## Cost Estimate (idle)

| Resource | Monthly |
|---|---|
| EKS control plane | $73 |
| 2× t3.medium | ~$60 |
| NAT gateway | ~$33 |
| **Total** | **~$166/month** |

GPU nodes at 0 when not running experiments.

## Scale Down GPU When Done

```bash
eksctl scale nodegroup --cluster servesmith --name gpu --nodes 0 --nodes-min 0
```
