# NexusBI – Enterprise Analytics Copilot

This repository contains the architecture, directory layout, and planning specifications for **NexusBI**, an enterprise-grade AI-powered Business Intelligence platform.

NexusBI translates business questions in natural language into optimized Snowflake SQL, executes the queries securely, formats the results, runs predictive statistical forecasting, and displays interactive data visualizations with AI-driven prescriptive recommendations.

---

## 📘 Architecture Documentation

### Phase 1 — Software Planning & Architecture
- [nexusbi_architecture_planning.md](./docs/architecture/nexusbi_architecture_planning.md) — Executive summary, functional/non-functional requirements, system scope, user roles, core modules, high-level architecture, technology stack, risks, and roadmap.

### Phase 2 — Architecture Review & Implementation-Ready Specifications

| Task | Document | Summary |
|:---|:---|:---|
| **Task 1** | [Architecture Review](./docs/architecture/phase2_task1_architecture_review.md) | 13 findings simplifying V1 (removed K8s, Qdrant, Celery). Added rate limiting, tenant isolation, error taxonomy. |
| **Task 2** | [KPI Catalog](./docs/architecture/phase2_task2_kpi_catalog.md) | 25 enterprise KPIs with formulas, owners, visualizations, and example interpretations. |
| **Task 3** | [User Journeys](./docs/architecture/phase2_task3_user_journeys.md) | 5 complete role-based journeys (CEO, Analyst, Data Engineer, Ops Manager, Admin). |
| **Task 4** | [AI Decision Pipeline](./docs/architecture/phase2_task4_ai_pipeline.md) | 19-stage pipeline from NL input to rendered chart with failure/recovery strategies. |
| **Task 5** | [Version Planning](./docs/architecture/phase2_task5_version_planning.md) | 4-version technology roadmap (V1 MVP → V4 Cognitive Enterprise). |
| **Task 6** | [Risk Assessment](./docs/architecture/phase2_task6_risk_assessment.md) | 28 risks across 9 categories, prioritized P0–P3. |
| **Task 7** | [Architecture Validation](./docs/architecture/phase2_task7_architecture_validation.md) | Final design review, 15 ADRs, SLI/SLOs, and pre-development checklist. |
| **Phase 2.1** | [Repository Blueprint](./docs/architecture/phase2_1_repository_blueprint.md) | Full implementation-ready repository structure, module responsibilities, logging, testing, and configurations. |
| **Phase 2.2** | [Data Warehouse Blueprint](./docs/architecture/phase2_2_data_warehouse_blueprint.md) | Enterprise data model, business domains, star schemas, Snowflake optimizations, and data governance. |
| **Phase 2.3** | [API & Service Blueprint](./docs/architecture/phase2_3_api_service_blueprint.md) | Backend service design, REST/WebSocket contracts, request lifecycles, service communication rules, and error registries. |
| **Phase 2.4** | [AI Intelligence Blueprint](./docs/architecture/phase2_4_ai_intelligence_blueprint.md) | AI vision, capability matrix, prompt engineering flow, memory caches, reasoning strategies, and model selection patterns. |
| **Phase 2.5** | [Product Experience Blueprint](./docs/architecture/phase2_5_product_experience_blueprint.md) | Executive UX principles, detailed user personas, navigation layout trees, component design systems, and interaction standards. |
| **Phase 2.8** | [Enterprise Readiness Package](./docs/architecture/phase2_8_enterprise_readiness_package.md) | 20 Architecture Decision Records, 25 system diagrams (Mermaid), a 12-sprint project plan, Definition of Done checklists, and interview prep guides. |

### Missing Sections Added to Blueprint

| Section | Document | Summary |
|:---|:---|:---|
| **Section 1** | [Repository Blueprint](./docs/architecture/phase1_section1_repository_blueprint.md) | Full enterprise directory layout specifications with folder-level ownership and guidelines. |
| **Section 2** | [Database Blueprint](./docs/architecture/phase1_section2_database_blueprint.md) | Relational + vector schema topology, index/partition rules, SCD strategies, and naming standards. |
| **Section 3** | [API Blueprint](./docs/architecture/phase1_section3_api_blueprint.md) | REST and WebSocket endpoints complete with request/response models, rate limiting, and errors. |
| **Section 4** | [UI Blueprint](./docs/architecture/phase1_section4_ui_blueprint.md) | Complete frontend page designs, widgets, responsive layout behavior, and accessibility policies. |

---

## 📂 Repository Structure

```text
NexusBI/
├── docs/                               # System Documentation
│   └── architecture/                   # Architecture & Review Documents
│       ├── nexusbi_architecture_planning.md
│       ├── phase1_section1_repository_blueprint.md
│       ├── phase1_section2_database_blueprint.md
│       ├── phase1_section3_api_blueprint.md
│       ├── phase1_section4_ui_blueprint.md
│       ├── phase2_1_repository_blueprint.md
│       ├── phase2_2_data_warehouse_blueprint.md
│       ├── phase2_3_api_service_blueprint.md
│       ├── phase2_4_ai_intelligence_blueprint.md
│       ├── phase2_5_product_experience_blueprint.md
│       ├── phase2_8_enterprise_readiness_package.md
│       ├── phase2_task1_architecture_review.md
│       ├── phase2_task2_kpi_catalog.md
│       ├── ...
│
├── backend/                            # FastAPI Backend Service (Python)
│   ├── app/
│   │   ├── api/                        # Routers, request validators
│   │   ├── core/                       # Security, config, middleware
│   │   ├── domain/                     # Business entities, use cases, interfaces
│   │   └── infrastructure/             # DB drivers, LLM clients, vector search
│   └── README.md
│
├── frontend/                           # React SPA (Tailwind, Redux, ECharts)
│   ├── src/
│   │   ├── components/                 # Reusable UI widgets
│   │   ├── features/                   # State slices, RTK Query hooks
│   │   └── routes/                     # Page routing and layouts
│   └── README.md
│
├── dbt/                                # Semantic Layer & Data Transformations
│   ├── models/                         # Warehouse model definitions
│   ├── seeds/                          # Business glossary seeds
│   └── README.md
│
├── deploy/                             # Deployment Configurations
│   ├── kubernetes/                     # K8s manifests (V3+)
│   ├── terraform/                      # IaC configurations (V3+)
│   └── README.md
│
└── README.md                           # This file
```

---

## 🏗️ V1 Technology Stack (Approved)

| Layer | Technology | Justification |
|:---|:---|:---|
| **Backend** | Python 3.11 + FastAPI | Async-native, AI/ML ecosystem, auto OpenAPI docs |
| **Frontend** | React 18 + Redux Toolkit + Tailwind CSS | Component reuse, predictable state, utility-first CSS |
| **Visualization** | Apache ECharts | Single library, canvas rendering, rich interactivity |
| **Database** | PostgreSQL 15 + pgvector | Metadata, audit logs, AND vector search in one DB |
| **Cache** | Redis (single instance) | Sessions, conversation memory, semantic query cache |
| **Data Warehouse** | Snowflake | Target analytical database with native RLS/CLS |
| **AI Orchestration** | LangGraph | Stateful agent workflows with self-healing loops |
| **Primary LLM** | Claude 3.5 Sonnet | Best-in-class SQL generation, 200K context window |
| **Lightweight LLM** | Claude 3 Haiku | Cost-efficient intent classification and chart selection |
| **Deployment** | Docker Compose | Simple orchestration for V1 scale (<50 users) |

---

## 🚀 Pre-Development Checklist

- [ ] All 15 ADRs documented and signed off
- [ ] OpenAPI 3.1 specification defined for all V1 endpoints
- [ ] Local dev Docker Compose file created and tested
- [ ] Snowflake dev account provisioned with sample data
- [ ] OIDC test identity provider configured
- [ ] Mock LLM response fixtures created for 20 test queries
- [ ] KPI catalog loaded into PostgreSQL seed data
- [ ] CI/CD pipeline configured (lint, test, build)
- [ ] Error code registry (NBI-1001–1007) documented
- [ ] Security threat model reviewed
- [ ] SLI/SLO definitions agreed upon
