"""
API Gateway - Single entry point for all LLM backends.

The gateway handles:
- Routing: directs requests to the appropriate backend based on model
- Authentication: validates API keys
- Rate limiting: prevents abuse (X requests per minute per user)
- Metrics: exposes stats for Prometheus
"""

import time
import httpx
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from config import settings, get_backend_url
from middleware import verify_api_key, RateLimiter

# =============================================================================
# DATA MODELS
# =============================================================================


class ChatMessage(BaseModel):
    """A single message in the conversation."""
    role: str          # "system", "user", or "assistant"
    content: str       # The message text


class ChatRequest(BaseModel):
    """OpenAI-compatible chat completion request."""
    model: str                           # Which model to use
    messages: list[ChatMessage]          # Conversation history
    max_tokens: Optional[int] = 100      # Max tokens to generate
    temperature: Optional[float] = 0.7   # Creativity level


class ChatResponse(BaseModel):
    """OpenAI-compatible chat completion response."""
    id: str
    object: str = "chat.completion"
    model: str
    choices: list[dict]
    usage: dict


# =============================================================================
# METRICS
# =============================================================================

metrics = {
    "requests_total": 0,
    "requests_by_model": {},
    "errors_total": 0,
    "latency_sum_ms": 0.0,
}


# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

app = FastAPI(
    title="LLM Gateway",
    description="API Gateway for LLM inference backends",
    version="0.1.0",
)

rate_limiter = RateLimiter(
    requests_per_minute=settings.rate_limit_rpm
)


@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatRequest,
    api_key: str = Depends(verify_api_key),
):
    """
    OpenAI-compatible chat completions endpoint.

    Routes the request to the appropriate backend based on the model.
    """
    start_time = time.time()

    # Check rate limit
    client_id = api_key[:8]  # Use first 8 chars as identifier
    if not rate_limiter.allow(client_id):
        metrics["errors_total"] += 1
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {settings.rate_limit_rpm} requests per minute."
        )

    # Get backend URL for the requested model
    backend_url = get_backend_url(request.model)
    if not backend_url:
        metrics["errors_total"] += 1
        raise HTTPException(
            status_code=400,
            detail=f"Unknown model: {request.model}. Available: {list(settings.model_backends.keys())}"
        )

    # Convert chat format to simple prompt for our backend
    # (Our mock backend uses a simple prompt, not chat messages)
    prompt = "\n".join([f"{m.role}: {m.content}" for m in request.messages])

    # Forward request to backend
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{backend_url}/infer",
                json={
                    "prompt": prompt,
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            backend_response = response.json()
    except httpx.RequestError as e:
        metrics["errors_total"] += 1
        raise HTTPException(status_code=502, detail=f"Backend error: {str(e)}")
    except httpx.HTTPStatusError as e:
        metrics["errors_total"] += 1
        raise HTTPException(status_code=e.response.status_code, detail="Backend returned an error")

    # Calculate latency
    latency_ms = (time.time() - start_time) * 1000

    # Update metrics
    metrics["requests_total"] += 1
    metrics["requests_by_model"][request.model] = metrics["requests_by_model"].get(request.model, 0) + 1
    metrics["latency_sum_ms"] += latency_ms

    # Format as OpenAI-compatible response
    return ChatResponse(
        id=f"chatcmpl-{int(time.time())}",
        model=request.model,
        choices=[{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": backend_response["completion"],
            },
            "finish_reason": "stop",
        }],
        usage={
            "prompt_tokens": backend_response["prompt_tokens"],
            "completion_tokens": backend_response["completion_tokens"],
            "total_tokens": backend_response["total_tokens"],
        },
    )


@app.get("/v1/models")
async def list_models(_api_key: str = Depends(verify_api_key)):
    """List available models (requires authentication)."""
    return {
        "object": "list",
        "data": [
            {"id": model, "object": "model", "owned_by": "llm-platform"}
            for model in settings.model_backends.keys()
        ]
    }


@app.get("/healthz")
async def healthz():
    """Health check for Kubernetes."""
    return {"status": "ok"}


@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint."""
    lines = [
        f"# HELP gateway_requests_total Total requests through gateway",
        f"# TYPE gateway_requests_total counter",
        f"gateway_requests_total {metrics['requests_total']}",
        f"",
        f"# HELP gateway_errors_total Total errors",
        f"# TYPE gateway_errors_total counter",
        f"gateway_errors_total {metrics['errors_total']}",
        f"",
        f"# HELP gateway_latency_sum_ms Sum of latencies in milliseconds",
        f"# TYPE gateway_latency_sum_ms counter",
        f"gateway_latency_sum_ms {metrics['latency_sum_ms']:.2f}",
    ]

    # Add per-model metrics
    for model, count in metrics["requests_by_model"].items():
        lines.append(f"")
        lines.append(f"# HELP gateway_requests_by_model Requests per model")
        lines.append(f"# TYPE gateway_requests_by_model counter")
        lines.append(f'gateway_requests_by_model{{model="{model}"}} {count}')

    return "\n".join(lines)


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
