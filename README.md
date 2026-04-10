# ServeSmith ⚡

[![CI](https://github.com/servesmith/servesmith/actions/workflows/ci.yml/badge.svg)](https://github.com/servesmith/servesmith/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)

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
  → Benchmarker tests each on K8s (vLLM / TensorRT-LLM / Neuron)
  → Recommender ranks by cost/token
  → GPU scales back to 0
  → GET /experiment/{id} returns recommendations with Docker commands
```

## Example Results

Benchmarking `Qwen/Qwen2.5-0.5B-Instruct` on g4dn.xlarge:

| Config | Tokens/sec | p99 Latency | Cost/M tokens |
|---|---|---|---|
| FP16, concurrency=1 | 122 | 309ms | $1.19 |
| FP16, concurrency=4 | 558 | 358ms | $0.15 |
| FP16, concurrency=8 | 933 | 363ms | $0.09 |

**7.6× throughput improvement** and **13× cost reduction** from a single experiment.

## Backends

| Backend | Status | Hardware |
|---|---|---|
| **vLLM** | ✅ Production | NVIDIA GPUs (T4, A10G, A100, H100) |
| **TensorRT-LLM** | ✅ Supported | NVIDIA GPUs |
| **Neuron** | ✅ Supported | AWS Inferentia2, Trainium |

```bash
# List available backends
curl http://localhost:8000/backends
```

## Features

- [x] **Multi-backend** — vLLM, TensorRT-LLM, Inferentia/Neuron
- [x] **Planner** — cartesian product of instance types × concurrency × quantization × TP
- [x] **Benchmarker** — server pod lifecycle, concurrent load, token metrics
- [x] **Recommender** — rank by cost/token with SLA constraint filtering
- [x] **GPU auto-scaling** — provision before benchmarks, scale to 0 after
- [x] **Dashboard** — experiment creation, status tracking, recommendation analysis
- [x] **Experiment templates** — quick-test, cost-sweep, latency-sensitive, high-throughput
- [x] **Webhook notifications** — Slack/webhook on experiment completion
- [x] **Prometheus metrics** — `/metrics` endpoint for monitoring
- [x] **Structured logging** — JSON logs with request ID tracking
- [x] Cost projections ($/month at 1K RPM)
- [x] Docker run commands in recommendations
- [x] Benchmark existing endpoints (skip pod creation)
- [x] KV-cache dtype and prefix caching support

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Run locally
make run

# Run tests
make test
```

## Deployment

### Docker

```bash
make build
docker run -p 8000:8000 servesmith
```

### EKS

```bash
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/storage.yaml
make deploy
```

See [docs/DEPLOYING.md](docs/DEPLOYING.md) for full setup.

## API

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/experiment` | POST | Submit experiment (requires `X-API-Key`) |
| `/experiment/{id}` | GET | Get status and recommendations |
| `/experiment/{id}/runs` | GET | Individual run details |
| `/experiments` | GET | List all experiments |
| `/templates` | GET | Available experiment presets |
| `/backends` | GET | Available inference backends |
| `/metrics` | GET | Prometheus metrics |
| `/docs` | GET | Swagger UI |

See [docs/API.md](docs/API.md) for request/response schemas.

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Run tests (`make test`)
4. Submit a PR

## License

MIT
