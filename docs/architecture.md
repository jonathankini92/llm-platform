# Architecture & design decisions

This document explains the structural choices behind the project. The goal is to
keep decisions traceable, the way a real platform team would.

## Core principle: the infra does not depend on the model

The backend that serves the model is interchangeable. The gateway,
observability, FinOps, and deployment all work identically whether the backend
is a CPU mock or a GPU vLLM. This is achieved by defining a minimal HTTP contract
that any backend must honor:

- `POST /infer`: takes a prompt, returns a completion plus metadata
  (input tokens, output tokens, duration).
- `GET /healthz`: liveness probe for Kubernetes.
- `GET /metrics`: metrics in Prometheus format.

As long as this contract is honored, the rest of the platform does not need to
know what runs behind it.

## Why a mock backend by default

A portfolio project must be runnable by anyone, immediately. A mock backend that
simulates latency, token volume, and error rate in a configurable way makes it
possible to:

- clone and run the repo with no GPU and no model download;
- test autoscaling and dashboards under realistic load, on demand;
- iterate quickly on the platform without waiting for multi-GB model loads.

The real vLLM backend is still provided to demonstrate portability to a
production backend.

## Key decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Orchestrator | Kubernetes (kind locally) | Industry standard, portable to GKE/EKS |
| Gateway | FastAPI | Lightweight, async, native Prometheus metrics |
| Local cluster | kind | Reproducible, fast, zero cloud dependency |
| Cost measurement | middleware on the gateway | Single choke point for every request |

## FinOps layer

Inference cost is computed from tokens consumed and a per-model unit price. The
FinOps middleware intercepts every response, reads the token metadata returned
by the backend, applies the model's pricing, and exposes the result as a
Prometheus metric labeled by model and by user. This is what answers "how much
does this usage cost me" — the recurring question in production.
