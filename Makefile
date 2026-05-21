.DEFAULT_GOAL := help
.PHONY: help up down build test lint clean cluster build-k8s deploy port-forward logs

## help: show this help
help:
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/## //' | awk -F': ' '{printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# --- Milestone 1: mock backend locally (docker compose) ---

## build: build docker images
build:
	docker compose build

## up: start the stack locally (mock backend + gateway)
up:
	docker compose up -d

## down: stop the local stack
down:
	docker compose down

# --- Quality ---

## test: run tests
test:
	pytest -q

## lint: check code style
lint:
	ruff check .

# --- Milestone 2: kubernetes ---

## cluster: create a local kind cluster
cluster:
	kind create cluster --name llm-platform --config k8s/kind-config.yaml

## build-k8s: build and load image into kind
build-k8s:
	docker build -t mock-backend:latest ./backends/mock
	kind load docker-image mock-backend:latest --name llm-platform

## deploy: build image and deploy to the local cluster
deploy: build-k8s
	kubectl apply -k k8s/overlays/local
	kubectl rollout status deployment/mock-backend

## port-forward: expose the mock backend locally
port-forward:
	kubectl port-forward svc/mock-backend 8080:80

## logs: show mock backend logs
logs:
	kubectl logs -l app=mock-backend -f

## clean: delete the local cluster
clean:
	kind delete cluster --name llm-platform
