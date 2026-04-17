# Project Overview
An inventory management system built with Flask, MongoDB, Elasticsearch, Docker, and Kubernetes. It supports product CRUD, full-text description searching, seeding sample data, and an analytics endpoint for inventory insights.


## Architecture Overview
Flask API handles all the requests, coordinating between MongoDB (primary data store) and Elasticsearch (search index) based on the request. Products sync to Elasticsearch on create/update/delete for search capability.
Kubernetes manages MongoDB and Elasticsearch as StatefulSets for data persistence and uses Deployments for the API. NetworkPolicies restrict access between Pods. Everything is isolated using the `feathr` namespace with resource limits, mostly non-root containers, and init containers for dependency ordering.

## Prerequisites
- Docker (for building the images)
- Kubernetes (for deploying to the cluster, can use `minikube` or similar local cluster tools)

## Features
- Complete product CRUD via REST API
- Full text search on product descriptions using Elasticsearch
- Analytics endpoint showing total count, top category, average prices, most viewed/searched products
- View and search tracking per product for analytics
- Kubernetes deployment with StatefulSets, NetworkPolicies, and resource limits isolated to the `feathr` namespace
- Multi-stage Docker builds for minimal, secure images
- Automated sample data generator for testing (`/seed`)

# Running The Application

## Quickstart
```bash
cp .env.example .env
make kube-deploy        # Freshly deploys to k8s
make kube-serve         # Port forward to localhost:5070
```

## Environment Variables

Copy `.env.example` to `.env` before deploying:

```env
MONGO_INITDB_ROOT_USERNAME=root
MONGO_INITDB_ROOT_PASSWORD=example
MONGO_USERNAME=root
MONGO_PASSWORD=example

# Optional
MONGO_HOST=mongo            # If hostname not provided, will default to `mongo`
MONGO_PORT=27017            # If port not provided, will default to `27017`
ES_URL=http://elastic:9200  # If hostname not provided, will default to `http://elastic:9200`
```

These values are used to initialize MongoDB and configure the API connection to the database.

**Test the full flow:**
```sh
curl localhost:5070/seed                            # Seed 10 products
curl localhost:5070/products                        # List products  
curl localhost:5070/products/P0001                  # Fetch single product
curl "localhost:5070/products/search?query=mouse"   # Search works (comma separated for multiple keywords)
curl localhost:5070/products/analytics              # Analytics
```

## Manual Kubernetes
```sh
# Generate secrets
kubectl create secret generic mongo-secret --from-env-file=.env --namespace feathr --dry-run=client -o yaml > .k8s/secrets/mongo-secret.yaml

# Deploy (dependency order)
kubectl apply -f .k8s/namespace.yaml
kubectl apply -f .k8s/secrets/ -R
kubectl apply -f .k8s/mongo/ -R
kubectl apply -f .k8s/elastic/ -R
kubectl apply -f .k8s/api/ -R
kubectl apply -f .k8s/networkpolicies/ -R

# Access
kubectl port-forward svc/api 5070:5070 -n feathr
```

## Makefile

This project contains a Makefile with some useful targets for building and deploying the application.

```sh
kube-deploy             # Create namespace, format secrets, and deploy the entire cluster using `kubectl create`
kube-apply              # Apply all resources at once
kube-delete             # Delete all resources
kube-serve              # Port forward to localhost:5070
kube-rollout            # Rollout the API deployment
kube-reboot             # Runs kube-delete and kube-apply commands

docker-build            # Build the API image and push to dockerhub
```

# API Reference
## Products Schema

Products require these minimum fields:

| Field | Type | Required | Editable | Description |
| --- | --- | --- | --- | --- |
| ProductName | String | Yes | Yes | The name of the product |
| ProductCategory | String | Yes | Yes | Category of the product (e.g., "Electronics", "Food") |
| Price | Float | Yes | Yes | Price of the product |
| AvailableQuantity | Int | Yes | Yes | Availabel quantity of the product |
| ProductDescription | String | Yes | Yes | Searchable, detailed description |
| ProductId | String | Auto | No | The unique identifier for the product (e.g., "P0001"), auto-generated |
| ViewCount | Int  | Auto | No | Incremented on GET |
| SearchCount | Int   | Auto | No | Incremented on search |

## Endpoints (todo: add expected fields)
```
Products:
GET    /products                    # List all products
POST   /products                    # Create product (expects Form Data with all fields above)
DELETE /products                    # Clear all products (testing only)

Product:
GET    /products/{ProductID}        # Fetch single product (increments ViewCount)
PUT    /products/{ProductID}        # Update product (partial updates OK, expects Form Data with at least one field)
DELETE /products/{ProductID}        # Delete product

Search & Analytics:
GET    /products/search?query=term  # Full-text search on descriptions (increments SearchCount of all resulting products)
GET    /products/analytics          # Aggregated metrics (total count, top category, avg price, top products)
GET    /seed                        # Generate 10 sample products (can be ran multiple times)
```

### Example POST /products:
```sh
curl --request POST \
  --url http://127.0.0.1:5070/products \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --data 'ProductName=Milk Steak' \
  --data ProductCategory=Testino123 \
  --data Price=12.34 \
  --data AvailableQuantity=10 \
  --data 'ProductDescription=She'\''ll know what it is'
```

**Response:**
```json
{
  "data": {
    "AvailableQuantity": 10,
    "Price": 12.34,
    "ProductCategory": "Food",
    "ProductDescription": "She'll know what it is.",
    "ProductId": "P0001",
    "ProductName": "Milk Steak",
    "SearchCount": 0,
    "ViewCount": 0
  },
  "status": "success"
}
```

# Project Review

## Design Decisions

| Decision | Why |
|----------|-----|
| **StatefulSets** (MongoDB/Elasticsearch) | Persistent data storage requires stable pod identity and durable volumes |
| **Headless Services** (`ClusterIP: None`) | Direct pod-to-pod communication without load balancer; predictable DNS for replica sets |
| **NetworkPolicies** | API-only access to databases |
| **Separate manifest folders** | Independent development/testing/deployment of components; clear organization |
| **Non-root containers** (`USER` in Dockerfile, `runAsNonRoot`) | Security best practice (except databases requiring root for volumes) |
| **Resource requests/limits** | Prevent OOM kills, guarantee scheduling |
| **Init containers** | Ensure MongoDB and Elasticsearch readiness before API startup |
| **No Kibana** | Outside assignment scope; analytics exposed via REST API instead |
| **ClusterIP on API** | Enables load-balancing capabilities between API. Can be set to LoadBalancer for external access |
| **Docker Compose Prototype** | Validated images/connections/configurations before K8s port; enabled fast debugging without cluster overhead |

## Assignment Requirements ✓

| Requirement | Implementation |
|-------------|----------------|
| **CRUD operations** | Full REST API (`/products`, `/product/{id}`) |
| **Full-text search** | `GET /products/search?query=` via Elasticsearch |
| **Product analytics** | `GET /products/analytics` (exceeds spec with usage tracking) |
| **Sample data** | `GET /seed` generates 10 realistic products |
| **Required schema** | All 5 fields + `ProductDescription` for search |
| **Kubernetes** | Production manifests with security/reliability best practices |
| **Documentation** | This README (hello there Feathr team! 👋) + inline code comments |

## Production Notes

- Form-encoded payloads (matches mobile/web form standards)
- Sequential ProductIDs prevent race conditions
- ViewCount/SearchCount enable usage analytics
- Error responses include specific validation messages
- Elasticsearch syncs automatically on all mutations

**Repo includes:** Flask API source code with Dockerfile, Kubernetes manifests (namespace/secrets/mongo/elastic/api/networkpolicies), Makefile, .env.example

# Next Steps
Given more time to work on the project and see it through beyond a demo, I would:
- Add proper HTTP status codes on responses
- Implement CI/CD pipeline for building, tagging, and publishing images to Docker Hub
- Add Kibana dashboard for analytics
- Use a non-root user for MongoDB operations
