# NexusBI Phase 2 — Task 5: Version Planning & Technology Allocation

**Document Version:** 2.0.0  
**Date:** July 1, 2026

---

## Version Philosophy

Each version introduces complexity only when validated by user demand, operational maturity, and team capacity. Technologies are allocated based on the principle: **"Right-size infrastructure to the current stage of product-market fit."**

---

## Version 1 — MVP Foundation (Months 1-6)

**Goal:** Ship a working product that 10-50 pilot users can use daily to ask business questions and get accurate visualized answers from Snowflake.

### Technology Allocation

| Technology | Category | Justification |
|:---|:---|:---|
| **Python 3.11** | Language | Industry standard for AI/ML, data manipulation, and scientific computing. Non-negotiable for Prophet, pandas, and LLM SDK integration. |
| **FastAPI** | Web Framework | Async-native, automatic OpenAPI docs, pydantic validation. Fastest Python framework for building REST + WebSocket APIs. |
| **React 18** | Frontend | Component-based UI with massive ecosystem. Essential for interactive dashboard building. |
| **Redux Toolkit** | State Management | Predictable state container for complex chat + dashboard + filter state. RTK Query simplifies server state sync. |
| **Tailwind CSS** | Styling | Utility-first CSS for rapid, consistent UI development with built-in dark mode support. |
| **Apache ECharts** | Visualization | High-performance canvas rendering, rich interactivity, excellent dark mode theming. Single visualization library to reduce complexity. |
| **PostgreSQL 15+** | Database (Metadata) | ACID-compliant relational database for user accounts, audit logs, workspace layouts, schema cache. Already needed — no additional infra. |
| **pgvector extension** | Vector Search | Adds vector similarity search to PostgreSQL. Eliminates the need for a separate vector database at V1 scale (≤10,000 vectors). |
| **Snowflake** | Data Warehouse | The target analytical database. All business data resides here. Key-pair authentication for security. |
| **Redis (single instance)** | Cache | Session management, conversation memory TTL, semantic query cache. Single managed instance (e.g., ElastiCache) — not cluster mode. |
| **LangGraph** | AI Orchestration | Stateful agent workflows with loops (critical for SQL compilation, self-healing, intent routing). Single orchestration framework. |
| **Claude 3.5 Sonnet** | Primary LLM | Best-in-class code/SQL generation, 200K context window, structured output support. |
| **Claude 3 Haiku** | Lightweight LLM | Cost-efficient model for intent classification, chart type selection, and simple tasks. |
| **OpenAI text-embedding-3-small** | Embeddings | Compact, fast embeddings for schema metadata vectorization. Low cost per token. |
| **Docker** | Containerization | Standardized build/deploy environments. Required even for single-server deployment. |
| **Docker Compose** | Orchestration (V1) | Simple multi-container orchestration for local dev and single-server production. No Kubernetes needed yet. |
| **APScheduler** | Task Scheduling | Lightweight Python scheduler for daily metadata sync cron jobs. No Celery overhead. |
| **SQLGlot** | SQL Parser | Python library for SQL AST parsing, validation, and dialect transpilation. Used for security validation. |
| **GitHub Actions** | CI/CD | Automated testing, linting, Docker image building. Integrated with GitHub repository. |
| **OIDC/OAuth2** | Authentication | Enterprise SSO integration via Okta, Auth0, or Azure AD. JWT-based stateless auth. |
| **Prophet** | Forecasting | Facebook's time-series forecasting library. Handles seasonality, trends, and holidays out-of-the-box. |

### What is NOT in V1 (and why)
- **Kubernetes:** Operational complexity exceeds the needs of <50 concurrent users on a single server.
- **Terraform:** Infrastructure is a single VM + managed database. Shell scripts suffice.
- **Qdrant:** pgvector handles V1 vector scale. No need for a dedicated vector database.
- **Redis Cluster:** Single instance handles <500 sessions.
- **Celery:** APScheduler + FastAPI BackgroundTasks handle V1 async needs.
- **Vega-Lite:** ECharts covers all V1 chart types. One library is enough.
- **LlamaIndex:** LangGraph + direct embedding API calls cover V1 RAG needs.
- **OpenTelemetry:** Structured logging to PostgreSQL provides V1 observability.
- **Prometheus/Grafana:** Application health monitoring via simple health-check endpoints and log analysis.
- **Service Mesh:** Single monolithic application — no inter-service communication to manage.

---

## Version 2 — Growth & Collaboration (Months 7-12)

**Goal:** Scale to 500+ users, add collaboration features, introduce alerting, and support multiple data sources.

### New Technologies Added

| Technology | Category | Justification |
|:---|:---|:---|
| **Celery + Redis Broker** | Task Queue | Required for: scheduled alert evaluations, async report generation, background data quality checks. APScheduler cannot handle distributed task execution across multiple workers. |
| **WebSocket Rooms (Socket.IO)** | Real-time Collab | Enables multi-user dashboard editing. Users see each other's cursors and changes in real-time. |
| **Slack / Teams Webhooks** | Alert Delivery | Users configure alert thresholds. When KPIs breach thresholds, notifications are sent to Slack/Teams channels. |
| **BigQuery Connector** | Multi-Source | Extends data source support beyond Snowflake. Uses BigQuery's Python client library. |
| **Redshift Connector** | Multi-Source | Extends data source support to AWS Redshift via psycopg2 driver. |
| **SQLGlot Dialect Routing** | SQL Transpilation | SQLGlot transpiles generated SQL between Snowflake, BigQuery, and Redshift dialects. The LLM generates in one canonical dialect; SQLGlot handles translation. |
| **PDF Export (WeasyPrint)** | Reporting | Server-side PDF generation for scheduled email reports. Lighter than Headless Chrome. |
| **Vega-Lite** | Advanced Viz | Added alongside ECharts for grammar-of-graphics custom visualizations requested by advanced analysts. |
| **Rate Limiting (slowapi)** | Security | Per-user and per-org rate limiting middleware for the API. Essential at 500+ user scale. |
| **Nginx** | Reverse Proxy | Production-grade reverse proxy for TLS termination, WebSocket upgrade handling, and static asset serving. Replaces development server. |

### Architecture Changes in V2
- **Deployment:** Move from single Docker Compose to a multi-server setup: 1 API server, 1 worker server (Celery), 1 database server (PostgreSQL + Redis). Still no Kubernetes.
- **Database:** PostgreSQL remains primary. Consider read replica for audit log queries to avoid impacting production API performance.
- **Metadata Sync:** Enhanced to support BigQuery and Redshift INFORMATION_SCHEMA crawling via the provider-factory pattern designed in Phase 1.

---

## Version 3 — Enterprise Scale (Months 13-18)

**Goal:** Scale to 5,000+ users across multiple enterprise customers. Introduce production-grade infrastructure, observability, and high availability.

### New Technologies Added

| Technology | Category | Justification |
|:---|:---|:---|
| **Kubernetes (EKS/GKE)** | Orchestration | Required for: horizontal pod autoscaling, rolling deployments, self-healing containers, multi-replica API servers. User load now justifies the operational investment. |
| **Helm Charts** | K8s Packaging | Standardized deployment packaging for Kubernetes. Enables repeatable deployments across staging, QA, and production environments. |
| **Terraform** | IaC | Infrastructure-as-Code for provisioning cloud resources (VPCs, K8s clusters, RDS instances, ElastiCache). Prevents configuration drift at enterprise scale. |
| **Qdrant** | Vector Database | Schema counts now exceed 10,000+ tables across multi-tenant deployments. pgvector latency degrades above this scale. Dedicated vector DB provides sub-millisecond search. |
| **Redis Cluster** | Distributed Cache | Session counts exceed 5,000 concurrent. Redis Cluster provides horizontal sharding and failover for session and cache data. |
| **OpenTelemetry** | Distributed Tracing | Request tracing across multiple Kubernetes pods and services. Essential for debugging latency issues in a distributed system. |
| **Prometheus** | Metrics Collection | Time-series metrics collection from all services (CPU, memory, request rates, error rates, LLM latencies). |
| **Grafana** | Metrics Dashboard | Visualization of Prometheus metrics. Operational dashboards for SRE/DevOps team. |
| **Grafana Loki** | Log Aggregation | Centralized log aggregation from all Kubernetes pods. Replaces individual container log inspection. |
| **HashiCorp Vault** | Secrets Management | Enterprise-grade secrets management for Snowflake keys, LLM API keys, database passwords. Replaces environment variables and config files. |
| **Multi-Region Deploy** | High Availability | Active-passive deployment across two cloud regions for disaster recovery. RTO < 15 minutes. |

### Architecture Changes in V3
- **Monolith Decomposition:** Extract the forecasting engine and metadata sync service into separate microservices. The core API + chat + SQL generation remains a monolith (it's tightly coupled by design).
- **Multi-Tenancy:** Introduce tenant isolation at the PostgreSQL schema level. Each customer organization gets a dedicated schema. Vector namespaces in Qdrant are tenant-scoped.
- **HA SLA:** Upgrade from 99.5% (V1/V2) to 99.95% with multi-region failover.

---

## Version 4 — Cognitive Autonomous Enterprise (Months 19-24)

**Goal:** Transform NexusBI from a query tool into an autonomous business intelligence agent that proactively monitors, analyzes, and recommends actions across the enterprise.

### New Technologies Added

| Technology | Category | Justification |
|:---|:---|:---|
| **Istio / Linkerd** | Service Mesh | Inter-service mTLS, traffic management, circuit breaking, canary deployments. Required when service count exceeds 5. |
| **Apache Kafka** | Event Streaming | Event-driven architecture for real-time data change capture, alert event routing, and cross-service communication. Replaces Redis Streams for high-throughput event pipelines. |
| **Fine-Tuned Llama-3-70B** | Self-Hosted LLM | Fine-tuned on enterprise SQL patterns to eliminate dependency on third-party LLM APIs. Deployed on private GPU clusters (A100/H100). |
| **vLLM** | LLM Serving | High-performance LLM inference server with PagedAttention for efficient GPU memory management. |
| **Databricks Connector** | Multi-Source | Extends data source support to Databricks Lakehouse via Unity Catalog API. |
| **SAP/Salesforce Webhooks** | Write-Back | Enables the AI agent to trigger actions in external systems based on data findings (e.g., create purchase orders, update CRM records). |
| **Airflow** | Workflow Orchestration | Complex multi-step data pipeline orchestration for scheduled analytics jobs, data quality checks, and automated report generation. |
| **ArgoCD** | GitOps Deployment | Declarative Kubernetes deployments synced from Git repositories. Enables audit-trail-complete deployment history. |
| **PagerDuty Integration** | Incident Management | Automated alerting to on-call SRE teams when system health degrades beyond defined thresholds. |

### Architecture Changes in V4
- **Full Microservices:** All bounded contexts are extracted into independent services with dedicated databases (database-per-service pattern).
- **Event-Driven Architecture:** Kafka serves as the backbone for all inter-service communication. Services are loosely coupled via event topics.
- **Active-Active Multi-Region:** Full active-active deployment with global load balancing. RPO < 1 minute, RTO < 5 minutes.
- **Autonomous Agent Loops:** Background agents continuously monitor KPIs, detect anomalies, generate insights, and push notifications — without user initiation.

---

## Version Comparison Summary

| Capability | V1 | V2 | V3 | V4 |
|:---|:---|:---|:---|:---|
| **Users** | 10-50 | 50-500 | 500-5,000 | 5,000+ |
| **Data Sources** | Snowflake only | + BigQuery, Redshift | + custom connectors | + Databricks, SAP |
| **Deployment** | Docker Compose | Multi-server | Kubernetes | K8s + Service Mesh |
| **Vector Search** | pgvector | pgvector | Qdrant | Qdrant (sharded) |
| **Cache** | Redis single | Redis single | Redis Cluster | Redis Cluster |
| **Task Queue** | APScheduler | Celery | Celery | Celery + Kafka |
| **Observability** | PostgreSQL logs | Structured logging | OTel + Prometheus | Full observability stack |
| **HA SLA** | 99.5% | 99.5% | 99.95% | 99.99% |
| **LLM** | Cloud API | Cloud API | Cloud + fallback | Self-hosted fine-tuned |
| **IaC** | Shell scripts | Shell scripts | Terraform | Terraform + ArgoCD |
