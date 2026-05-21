.DEFAULT_GOAL := help
.PHONY: help up down build test lint clean cluster deploy port-forward

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

# --- Milestone 2+: kubernetes ---

## cluster: create a local kind cluster
cluster:
	kind create cluster --name llm-platform --config k8s/kind-config.yaml

## deploy: deploy to the local cluster
deploy:
	kubectl apply -k k8s/overlays/local

## port-forward: expose the gateway locally
port-forward:
	kubectl port-forward svc/gateway 8080:80

## clean: delete the local cluster
clean:
	kind delete cluster --name llm-platform
