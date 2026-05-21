"""
Mock Backend - Simulates an LLM inference server.

This backend implements the HTTP contract that all backends must follow:
- POST /infer   : receives a prompt, returns a completion
- GET /healthz  : health check for Kubernetes
- GET /metrics  : metrics in Prometheus format

The mock does not perform real inference - it returns a fixed response
after a simulated delay. This allows developing and testing the entire
platform without a GPU.
"""

import time
import random
from fastapi import FastAPI
from pydantic import BaseModel

# =============================================================================
# DATA MODELS (Pydantic)
# =============================================================================
# Pydantic automatically validates incoming and outgoing data.
# If a client sends malformed JSON, FastAPI returns a 422 error.


class InferRequest(BaseModel):
    """Inference request sent by the gateway."""
    prompt: str                     # The input text
    max_tokens: int = 100           # Maximum number of tokens to generate
    temperature: float = 0.7        # Creativity (0 = deterministic, 1 = creative)


class InferResponse(BaseModel):
    """Inference response returned to the gateway."""
    completion: str                 # The generated text
    model: str                      # Which model responded
    prompt_tokens: int              # Tokens in the prompt
    completion_tokens: int          # Generated tokens
    total_tokens: int               # Total (for billing)
    latency_ms: float               # Processing time


# =============================================================================
# METRICS (global counters)
# =============================================================================
# In production, we would use prometheus_client. Here we keep it simple.

metrics = {
    "requests_total": 0,            # Total number of requests
    "tokens_generated_total": 0,    # Total tokens generated
    "latency_sum_ms": 0.0,          # Sum of latencies (to calculate average)
}


# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

app = FastAPI(
    title="Mock LLM Backend",
    description="Simulates an LLM inference backend for development",
    version="0.1.0",
)


@app.post("/infer", response_model=InferResponse)
async def infer(request: InferRequest) -> InferResponse:
    """
    Inference endpoint - the core of the backend.

    Simulates the behavior of a real LLM:
    1. Receives a prompt
    2. Waits for a simulated delay (as if doing inference)
    3. Returns a response with metadata

    In production (vLLM), this is where we would call the model.
    """
    start_time = time.time()

    # Simulate inference delay (50-150ms per requested token, divided by 100)
    # The more tokens requested, the "slower" it is
    simulated_delay = random.uniform(0.05, 0.15) * (request.max_tokens / 100)
    time.sleep(simulated_delay)

    # Simulate token counting (approximation: 1 token ≈ 4 characters)
    prompt_tokens = len(request.prompt) // 4 + 1
    completion_tokens = min(request.max_tokens, random.randint(10, 50))

    # Generate a fixed response (a real LLM would generate text)
    completion = f"[MOCK] Simulated response for: '{request.prompt[:50]}...'"

    # Calculate actual latency
    latency_ms = (time.time() - start_time) * 1000

    # Update metrics
    metrics["requests_total"] += 1
    metrics["tokens_generated_total"] += completion_tokens
    metrics["latency_sum_ms"] += latency_ms

    return InferResponse(
        completion=completion,
        model="mock-model-v1",
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        latency_ms=round(latency_ms, 2),
    )


@app.get("/healthz")
async def healthz() -> dict:
    """
    Health check for Kubernetes.

    Kubernetes calls this endpoint regularly (liveness probe).
    If the server doesn't respond, Kubernetes restarts the pod.

    Simply returns {"status": "ok"} if the server is running.
    """
    return {"status": "ok"}


@app.get("/metrics")
async def get_metrics() -> str:
    """
    Metrics in Prometheus format.

    Prometheus scrapes this endpoint periodically to collect metrics.
    The format is simple: metric_name value

    These metrics allow creating Grafana dashboards:
    - Requests per second
    - Tokens generated per second
    - Average latency
    """
    # Prometheus format: each line = "metric_name value"
    lines = [
        f"# HELP requests_total Total number of inference requests",
        f"# TYPE requests_total counter",
        f"requests_total {metrics['requests_total']}",
        f"",
        f"# HELP tokens_generated_total Total number of tokens generated",
        f"# TYPE tokens_generated_total counter",
        f"tokens_generated_total {metrics['tokens_generated_total']}",
        f"",
        f"# HELP latency_sum_ms Sum of latencies in milliseconds",
        f"# TYPE latency_sum_ms counter",
        f"latency_sum_ms {metrics['latency_sum_ms']:.2f}",
    ]
    return "\n".join(lines)


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    # Start the server on port 8000
    # host="0.0.0.0" allows connections from outside the container
    uvicorn.run(app, host="0.0.0.0", port=8000)
