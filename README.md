# ServeSmith ⚡

**Optimize LLM inference costs in one click.**

ServeSmith automatically benchmarks LLM serving configurations and recommends the cheapest setup meeting your latency SLAs. Point it at a HuggingFace model, and it tests combinations of hardware, concurrency, and quantization to find the optimal price/performance config.

## How It Works

```
POST /experiment → Planner generates runs → Benchmarker tests each config → Results
```

1. You submit a model name and test parameters
2. ServeSmith launches vLLM server pods on your K8s cluster
3. Sends concurrent load with your test prompts
4. Measures tokens/sec, latency percentiles, cost/token
5. Returns ranked results

## First Results

Benchmarking `Qwen/Qwen2.5-0.5B-Instruct` on g4dn.xlarge:

| Config | Tokens/sec | p99 Latency | Cost/M tokens |
|---|---|---|---|
| FP16, concurrency=1 | 122 | 309ms | $1.19 |
| FP16, concurrency=4 | 456 | 353ms | $0.32 |
| FP16, concurrency=8 | 820 | 400ms | $0.054 |

**6.7× throughput improvement** just by tuning concurrency.

## Features

- [x] vLLM backend with automatic pod lifecycle
- [x] Concurrent load generation with token counting
- [x] TM99 latency metric (trailing mean, 99% cutoff)
- [x] Cost-per-token calculation
- [x] S3 upload for results CSV
- [ ] Experiment planner (multi-config sweeps)
- [ ] Cost recommendations
- [ ] Web dashboard

## Quick Start

```bash
pip install -e ".[dev]"
uvicorn servesmith.server:app --reload --port 8000
```

## Kubernetes Setup

See [docs/DEPLOYING.md](docs/DEPLOYING.md) for full setup.

```bash
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/storage.yaml
```

## License

MIT
