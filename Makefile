# Local developer shortcuts. `make help` lists targets.
SERVICES := user-service product-service cart-service order-service payment-service notification-service
STRIPE_PK ?= pk_test_replace_me

.PHONY: help test lint build-local kind-load deploy-dev undeploy-dev

help:
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed 's/:.*## / — /'

test: ## run backend tests (needs Postgres on :5432 and Redis on :6379)
	@for s in $(SERVICES); do \
	  if [ -f services/$$s/test_app.py ]; then echo "== $$s"; (cd services/$$s && JWT_SECRET=test-secret INTERNAL_API_TOKEN=test-internal REDIS_URL=redis://localhost:6379/0 pytest -q); fi; \
	done

lint: ## flake8 + eslint
	@for s in $(SERVICES); do flake8 services/$$s --select=E9,F63,F7,F82; done
	@cd frontend && npm run lint

build-local: ## build all images with :local tags
	@for s in $(SERVICES); do docker build -t $$s:local services/$$s; done
	docker build --build-arg VITE_STRIPE_PUBLISHABLE_KEY=$(STRIPE_PK) -t frontend:local frontend

kind-load: ## load :local images into a kind cluster
	@for s in $(SERVICES) frontend; do kind load docker-image $$s:local; done

deploy-dev: ## apply the dev overlay
	kubectl apply -k k8s/overlays/dev

undeploy-dev:
	kubectl delete -k k8s/overlays/dev
