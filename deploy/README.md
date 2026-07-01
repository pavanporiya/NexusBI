# Deployment & Infrastructure Specification

This directory contains the configurations and automation scripts for deploying NexusBI on enterprise cloud infrastructure using Terraform, Kubernetes, and Helm.

## 🏗️ Cloud Infrastructure Layout (Terraform)

The `deploy/terraform/` directory should house modules to deploy the following services:

* **EKS / GKE Container Cluster:** Auto-scaling Kubernetes node pools to host API gateway and compiler services.
* **Qdrant Vector DB:** Self-hosted or managed Qdrant cloud instances to serve semantic metadata embeddings.
* **PostgreSQL RDS instance:** Managed relational database storing workspace states, user roles, and audit trail metrics.
* **Redis Cache Cluster:** Elasticache instances serving session caches and WebSocket event queues.

---

## ☸️ Container Orchestration & Autoscaling (Kubernetes)

The `deploy/kubernetes/` directory defines:

* **Helm Chart Values:** Custom charts for deploying `backend`, `frontend`, and metadata sync pipelines.
* **Horizontal Pod Autoscaling (HPA):**
  * Target CPU utilization: $70\%$
  * Target Request Concurrency: 150 concurrent connections per pod.
  * Auto-scale range: 3 pods (baseline) to 30 pods (peak load failover).

---

## 📈 Observability, Monitoring, & Auditing
NexusBI tracks performance, AI service costs, and Snowflake driver states using:

1. **Prometheus & Grafana:** Captures API latency, WebSocket queue depths, and container health metrics.
2. **OpenTelemetry (OTel):** Injects tracing context between the API gateway, Python AST compiler service, and Snowflake DB client driver.
3. **Audit Ledger:** Every SQL query generated is stored in the Postgres system database alongside LLM token costs, query execution durations, and target schema metadata records to maintain security audits.
