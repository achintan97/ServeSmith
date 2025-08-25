# ServeSmith ⚡

**Optimize LLM inference costs in one click.**

ServeSmith automatically benchmarks LLM serving configurations and recommends the cheapest setup meeting your latency SLAs.

> 🚧 Early development — API is unstable.

## Features

- [x] FastAPI server with experiment submission
- [x] Kubernetes job executor
- [x] S3 integration for test data and results
- [ ] vLLM benchmarker
- [ ] Cost recommendations
- [ ] Web dashboard

## Prerequisites

- Python 3.12+
- Kubernetes cluster (EKS recommended)
- AWS credentials with S3 and EKS access
- `kubectl` configured for your cluster

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Run locally
uvicorn servesmith.server:app --reload --port 8000

# Health check
curl http://localhost:8000/health
```

## Kubernetes Setup

ServeSmith runs benchmark jobs on your K8s cluster. You need:

1. **RBAC** — apply `k8s/rbac.yaml` for job creation permissions
2. **Storage** — apply `k8s/storage.yaml` for EBS volumes (model weights)
3. **GPU nodes** — at least one GPU node (g4dn.xlarge or larger)

```bash
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/storage.yaml
```

See [docs/DEPLOYING.md](docs/DEPLOYING.md) for full EKS setup instructions.

## API

```bash
# Submit an experiment
curl -X POST http://localhost:8000/experiment \
  -H "Content-Type: application/json" \
  -d '{"source_model_name": "Qwen/Qwen2.5-0.5B-Instruct", ...}'

# Check status
curl http://localhost:8000/experiment/{id}
```

## License

MIT
