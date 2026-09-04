# What changed in this revision

Summary of the review fixes applied across the repo. Everything below was verified locally:
backend tests pass against real Postgres/Redis, the frontend lints and builds, all three
Kustomize overlays render, and the Terraform parses/formats cleanly.

## Security
- **Removed committed credentials**: `argocd/token`, `argocd/github-repo-secret.yaml`, and the Stripe secret key in `k8s/base/kustomization.yaml`. Added `.gitignore`. **Rotate the Stripe key and the GitHub PAT that were in git history**, then purge history (`git filter-repo`).
- `JWT_SECRET`, `INTERNAL_API_TOKEN`, `STRIPE_SECRET_KEY` no longer have hardcoded defaults — services fail fast if unset.
- user-service: unsalted SHA-256 → `werkzeug.security` salted hashing; input validation; UTC-aware JWT `iat`/`exp`.
- product-service: `POST /products` requires a JWT; `PATCH /products/{id}/stock` requires the internal token.
- order-service: `PATCH /orders/{id}/status` requires the internal token (was fully open).
- Ingress moved to `/api/*` with rewrite; internal endpoints are not routed at all.
- Pods run as non-root with dropped capabilities.

## Correctness
- **CI tests were failing**: product test fixture created a table without `stock`. All tests now use the service's own `init_db()`.
- Added order-service tests covering reservation, rollback, auth, status update.
- order-service: prices looked up first, stock reserved per item and **released on any failure**, order + items written in one transaction, real `amount` (paise) sent to payment-service, new `GET /orders`, `total_amount`/`unit_price`/`transaction_id` columns (idempotent `ALTER TABLE ... IF NOT EXISTS`).
- payment-service: charges the real order amount instead of a hardcoded 5000; idempotency key per order; retries on status update; timeouts on every HTTP call.
- cart-service: returns `product_id` as an int (fixes "Product #N / N/A / $0.00" in the cart).
- Frontend: Stripe checkout actually wired (`@stripe/*` deps added, `Elements` provider, `CheckoutForm` rendered on cart page, `payment_method_id` sent); `/orders` route + history page; Mantine v6 props (`sx`, `weight`, `leftIcon`, `position="apart"`, …) migrated to v9; axios uses `/api` and surfaces backend error messages; Vite proxy fixed; products fetched on hard refresh of cart/detail pages.

## Kubernetes
- One `shopsphere-secrets` secret per overlay (dev: safe literals; prod/azure: git-ignored `secrets.env`).
- Every base resource is now in `kustomization.yaml` (NetworkPolicies, ServiceMonitor, PrometheusRule, AnalysisTemplate were never applied before).
- NetworkPolicies rewritten: default-deny + explicit allows, including ingress-nginx and Prometheus namespaces (the old set would have blocked the ingress controller and restricted egress to DNS only).
- All 7 images set in prod/azure overlays (5 were left as `:latest` locals → ImagePullBackOff).
- Service ports named `http` so the ServiceMonitor works; `prometheus-flask-exporter` added to all Flask services.
- AnalysisTemplate queries real 5xx rate (was `vector(0)`); demo `AlwaysFiring` alert replaced with real alerts.
- Postgres → StatefulSet with password from the secret; duplicate/typo'd policy files removed; `kustomize-config.yaml` (no-op) removed.
- Argo CD Application renamed `shopsphere` (it deploys the whole overlay, not just product-service).

## Terraform
- AWS: fixed invalid `%/*` interpolation (`dirname()`), two AZs (EKS requirement), `eks_managed_node_group_defaults` (old key was invalid), EBS CSI addon for the PVC, ECR repos for all 7 services via `for_each`, lifecycle policy, ELB subnet tags, split into files, real S3 backend config.
- Azure: removed non-existent `acr_attachment` block → `azurerm_role_assignment` AcrPull; Redis Basic SKU can't be VNet-injected (removed `subnet_id`/empty static IP); Azure CNI + network policy enabled; tfvars example.

## CI
- Single workflow: tests all 6 services (+ Redis service), lints/builds the frontend, renders every overlay, `terraform validate`s both stacks, builds each image **once**, Trivy-scans it, pushes to ECR and ACR, then bumps overlay tags in **one** commit with `paths-ignore` to prevent a rebuild loop.
- Fixed: shell variable `ECR_REPO` used across steps (was empty), `sed` that never matched the overlay format, 7 parallel jobs pushing the same file, unpinned `trivy-action@master`.
