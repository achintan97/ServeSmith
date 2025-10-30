# ServeSmith API Reference

## Endpoints

### GET /health
Health check.

**Response:** `{"status": "ok"}`

### POST /experiment
Submit an optimization experiment. Runs asynchronously.

**Request:**
```json
{
  "source_model_name": "Qwen/Qwen2.5-0.5B-Instruct",
  "test_data_path": "s3://bucket/prompts.json",
  "output_s3_path": "s3://bucket/results/",
  "resources": [{"instance_type": "g4dn.xlarge"}],
  "concurrencies": [1, 4, 8],
  "target_model_format_args": {
    "vllm_latest": {
      "tensor_parallel_size": [1],
      "quantization": [null, "awq"],
      "gpu_memory_utilizations": [0.9]
    }
  },
  "test_duration": 60,
  "num_recommendations_to_return": 5
}
```

**Response:** `{"experiment_id": "ss-abc123def456"}`

### GET /experiment/{experiment_id}
Poll experiment status and get recommendations.

**Response (in progress):**
```json
{"experiment_id": "ss-abc123", "status": "active"}
```

**Response (completed):**
```json
{
  "experiment_id": "ss-abc123",
  "status": "succeeded",
  "recommendations": [
    {
      "rank": 1,
      "instance_type": "g4dn.xlarge",
      "concurrency": 8,
      "tokens_per_sec": 820.0,
      "p99_latency_sec": 0.4,
      "cost_per_million_tokens": 0.054
    }
  ]
}
```
