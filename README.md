# ServeSmith

Optimize LLM inference costs in one click.

Give ServeSmith your model and latency target. It tests hundreds of configurations across hardware, quantization, and parallelism — then tells you the cheapest way to serve it, with a deployable container.

## Quick Start

```bash
make dev
make run
# API at http://localhost:8000/docs
```

## How It Works

1. You submit a model + constraints (latency SLA, budget)
2. ServeSmith generates experiment runs across configs
3. Each run benchmarks on real hardware with your traffic
4. Recommender ranks results by cost/token
5. You get the cheapest config that meets your SLA

## Status

Early development. Currently supports vLLM on GPU instances.
