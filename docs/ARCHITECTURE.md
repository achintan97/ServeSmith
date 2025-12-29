# ServeSmith Architecture

```
User (Dashboard / API)
       │
       ▼
┌─────────────────┐
│  FastAPI Server  │  POST /experiment, GET /experiment/{id}
│  (server.py)     │  Auth via X-API-Key header
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Orchestrator    │  Coordinates the full pipeline
│  (orchestrator)  │  Handles partial failures gracefully
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌──────────┐
│Planner │ │Recommender│
│        │ │           │
│Generates│ │Ranks by   │
│runs from│ │cost/token │
│config   │ │with SLA   │
│space    │ │filtering  │
└────┬───┘ └─────┬────┘
     │           │
     ▼           │
┌─────────────┐  │
│ Benchmarker │  │
│             │  │
│ 1. Create   │  │
│    vLLM pod │  │
│ 2. Wait for │  │
│    ready    │  │
│ 3. Send     │  │
│    load     │  │
│ 4. Collect  │──┘
│    metrics  │
│ 5. Cleanup  │
└─────────────┘
```

## Key Design Decisions

1. **vLLM-first** — Skip compilation/container generation. Model loads at runtime.
2. **Sequential runs** — One benchmark at a time to avoid GPU contention.
3. **Partial failure tolerance** — If 3/5 runs succeed, recommend from those 3.
4. **Background execution** — API returns immediately, poll for results.
5. **Standard K8s labels** — No Karpenter dependency, works on any EKS cluster.
