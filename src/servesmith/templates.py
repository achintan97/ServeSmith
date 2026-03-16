"""Experiment templates — common presets for quick start."""

TEMPLATES = {
    "quick-test": {
        "description": "Fast test with 1 concurrency, 30s duration",
        "concurrencies": [1],
        "test_duration": 30,
        "warmup_time": 5,
        "num_recommendations_to_return": 3,
    },
    "cost-sweep": {
        "description": "Find cheapest config across concurrency levels",
        "concurrencies": [1, 2, 4, 8, 16],
        "test_duration": 60,
        "num_recommendations_to_return": 5,
    },
    "latency-sensitive": {
        "description": "Optimize for low latency with SLA constraints",
        "concurrencies": [1, 2, 4],
        "test_duration": 60,
        "max_p99_latency_sec": 0.5,
        "num_recommendations_to_return": 5,
    },
    "high-throughput": {
        "description": "Maximize tokens/sec for batch workloads",
        "concurrencies": [4, 8, 16, 32],
        "test_duration": 120,
        "num_recommendations_to_return": 5,
    },
    "quantization-compare": {
        "description": "Compare FP16 vs AWQ vs GPTQ",
        "concurrencies": [4],
        "test_duration": 60,
        "num_recommendations_to_return": 10,
    },
}
