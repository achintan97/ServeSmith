# ServeSmith ⚡

**Optimize LLM inference costs in one click.**

ServeSmith automatically benchmarks LLM serving configurations and recommends the cheapest setup meeting your latency SLAs. Point it at a HuggingFace model, and it tests combinations of hardware, concurrency, and quantization to find the optimal price/performance config.

## Dashboard

ServeSmith includes a web dashboard for creating experiments and viewing results:

- **Experiment wizard** — 2-step form with configuration review
- **Executive summary** — best cost, throughput, and latency at a glance
- **Smart recommendations** — rank by cost, throughput, or latency with filters
- **Auto-refresh** — live status updates while experiments run

Access at `http://your-server/` after deployment.

## How It Works

```
POST /experiment
  → GPU auto-scales (0 → 1 node)
  → Planner generates config combinations
  → Benchmarker tests each on K8s (vLLM pods)
  → Recommender ranks by cost/token
  → GPU scales back to 0
  → GET /experiment/{id} returns recommendations
```

## Example Results

Benchmarking `Qwen/Qwen2.5-0.5B-Instruct` on g4dn.xlarge:

| Config | Tokens/sec | p99 Latency | Cost/M tokens |
|---|---|---|---|
| FP16, concurrency=1 | 122 | 309ms | $1.19 |
| FP16, concurrency=4 | 558 | 358ms | $0.15 |
| FP16, concurrency=8 | 933 | 363ms | $0.09 |

**7.6× throughput improvement** and **13× cost reduction** from a single experiment.

## Features

- [x] **Planner** — cartesian product of instance types × concurrency × quantization × TP
- [x] **Benchmarker** — vLLM server pod lifecycle, concurrent load, token metrics
- [x] **Recommender** — rank by cost/token with SLA constraint filtering
- [x] **Orchestrator** — end-to-end pipeline with partial failure handling
- [x] **GPU auto-scaling** — provision before benchmarks, scale to 0 after
- [x] **Dashboard** — experiment creation, status tracking, recommendation analysis
- [x] **API key auth** — secure experiment submission
- [x] Cost projections ($/month at 1K RPM)
- [x] Docker run commands in recommendations
- [x] Prometheus metrics at `/metrics`
- [ ] Multi-backend (TensorRT-LLM, Neuron)

## Deployment

### Docker

```bash
docker build -t servesmith .
docker run -p 8000:8000 servesmith
```

### EKS

```bash
# Apply RBAC and storage
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/storage.yaml

# Deploy
make deploy
```

See [docs/DEPLOYING.md](docs/DEPLOYING.md) for full setup.

## API Reference

See [docs/API.md](docs/API.md). Interactive docs at `/docs` (Swagger UI).

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## License

MIT
