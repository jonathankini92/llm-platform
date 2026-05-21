# llm-platform

A self-hosted LLM inference platform, built as a platform engineering product:
it does more than serve a model — it builds the industrialization layer around
it (routing, autoscaling, observability, cost control, and reproducible
deployment).

The project runs on any machine, with no GPU, thanks to a mock backend by
default. A real vLLM backend is provided as an option, enabled when a GPU is
available. The infrastructure never depends on the model being served: that is
the core principle.

## Why this project

Serving an LLM is easy. Serving an LLM reliably, at scale, with full
observability and a known per-request cost is a discipline of its own — the work
of an AI Platform Engineer. This repository shows that layer, which is usually
missing from "I called an API" demos.

What sets this project apart is its FinOps layer: every request is measured
(tokens consumed, latency, estimated cost) and cost is attributed per model and
per user. This is rarely implemented in open-source inference platforms, even
though it is the first question asked in production.

## Architecture

```
Clients (curl, load tests)
        |
   API gateway          multi-model routing, auth, rate limiting
        |
   Model serving (Kubernetes)
   +-- backend A (mock by default / vLLM optional)
   +-- backend B
        |
   +----+----------------------------+
   |                                  |
Observability                     FinOps
Prometheus + Grafana              cost per token / model / user
p99 latency, tokens/sec

Everything deployed via GitOps: Terraform + Helm + CI/CD.
```

The contract between the gateway and a backend is a simple HTTP interface. Any
component that honors this contract (mock, vLLM, or other) is interchangeable.

## Tech stack

| Layer           | Tool                                   |
|-----------------|----------------------------------------|
| Serving         | vLLM (GPU) or mock backend (CPU)       |
| Gateway         | FastAPI                                |
| Orchestration   | Kubernetes (kind locally)              |
| Observability   | Prometheus, Grafana                    |
| IaC / GitOps    | Terraform, Helm, GitHub Actions        |
| Language        | Python 3.11                            |

## Quick start

```bash
# Prerequisites: docker, make
make build      # build the images
make up         # start mock backend + gateway locally
make test       # run the tests
make down       # stop everything
```

For the Kubernetes version (Milestone 2 onward):

```bash
make cluster        # create a local kind cluster
make deploy         # deploy the platform
make port-forward   # expose the gateway on localhost:8080
```

## Roadmap

The project is built in milestones. Each milestone leaves a repository that runs.

- [x] **Milestone 0** — Repository skeleton, architecture, tooling
- [ ] **Milestone 1** — Mock backend serving an inference endpoint locally
- [ ] **Milestone 2** — Kubernetes deployment (Deployment, Service, kind cluster)
- [ ] **Milestone 3** — Multi-model routing gateway (auth, rate limiting)
- [ ] **Milestone 4** — Observability (Prometheus + Grafana, p99 latency, tokens/sec)
- [ ] **Milestone 5** — FinOps layer (cost per token, per model, per user)
- [ ] **Milestone 6** — GitOps / IaC (Terraform, Helm, full CI/CD)

## Repository structure

```
backends/        backend implementations (mock, vllm)
gateway/         routing and entry-point service
observability/   prometheus configs and grafana dashboards
finops/          cost measurement and attribution middleware
k8s/             kubernetes manifests (base + overlays)
terraform/       infrastructure as code
docs/            architecture documentation
scripts/         utility scripts
```

## License

MIT — see [LICENSE](LICENSE).
