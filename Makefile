.PHONY: dev test lint run build push deploy

ACCOUNT ?= 063337766236
REGION ?= us-east-1
ECR = $(ACCOUNT).dkr.ecr.$(REGION).amazonaws.com
IMAGE = $(ECR)/servesmith:latest

dev:
	pip install -e ".[dev]"

run:
	python -m uvicorn servesmith.server:app --reload --port 8000

test:
	pytest -v --ignore=tests/test_k8s_executor.py

lint:
	ruff check src/ tests/

build:
	docker build -t servesmith:latest .

push: build
	aws ecr get-login-password --region $(REGION) | docker login --username AWS --password-stdin $(ECR)
	docker tag servesmith:latest $(IMAGE)
	docker push $(IMAGE)

deploy: push
	kubectl rollout restart deployment servesmith -n servesmith
