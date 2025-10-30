# ServeSmith ⚡

**Optimize LLM inference costs in one click.**

ServeSmith automatically benchmarks LLM serving configurations and recommends the cheapest setup meeting your latency SLAs. Point it at a HuggingFace model, and it tests combinations of hardware, concurrency, and quantization to find the optimal price/performance config.

## How It Works

```
POST /experiment
  → Planner generates config combinations
  → Benchmarker tests each on K8s (vLLM pods)
  → Recommender ranks by cost/token
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

## Architecture

```
┌─────────────┐     ┌──────────┐     ┌─────────────┐     ┌─────────────┐
│   FastAPI    │────▶│  Planner │────▶│ Benchmarker │────▶│ Recommender │
│   Server     │     │          │     │  (K8s pods) │     │             │
└─────────────┘     └──────────┘     └─────────────┘     └─────────────┘
```

## Features

- [x] **Planner** — cartesian product of instance types × concurrency × quantization × TP
- [x] **Benchmarker** — vLLM server pod lifecycle, concurrent load, token metrics
- [x] **Recommender** — rank by cost/token, filter by latency/throughput SLAs
- [x] **Orchestrator** — end-to-end pipeline with partial failure handling
- [x] **Pricing API** — EC2 on-demand costs for cost/token calculation
- [x] TM99 latency metric
- [x] S3 results upload
- [ ] Web dashboard
- [ ] Multi-backend (TensorRT-LLM, Neuron)

## API Reference

See [docs/API.md](docs/API.md) for full endpoint documentation.

```bash
# Submit experiment
curl -X POST http://localhost:8000/experiment \
  -H "Content-Type: application/json" \
  -d '{
    "source_model_name": "Qwen/Qwen2.5-0.5B-Instruct",
    "test_data_path": "s3://bucket/prompts.json",
    "output_s3_path": "s3://bucket/results/",
    "resources": [{"instance_type": "g4dn.xlarge"}],
    "concurrencies": [1, 4, 8]
  }'

# Poll for results
curl http://localhost:8000/experiment/{id}
```

## Quick Start

```bash
pip install -e ".[dev]"
uvicorn servesmith.server:app --reload --port 8000
```

## Deployment

See [docs/DEPLOYING.md](docs/DEPLOYING.md) and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## License

MIT
