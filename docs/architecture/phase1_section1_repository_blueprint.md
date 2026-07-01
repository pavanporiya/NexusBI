# NexusBI Phase 1 Extension — Section 1: Enterprise Repository Blueprint

**Date:** July 1, 2026

---

## 1. Repository Root Structure

```
NexusBI/
├── backend/               # FastAPI application (Python monolith)
├── frontend/              # React SPA application
├── ai/                    # AI prompt templates, evaluation, and model configs
├── etl/                   # Metadata ingestion pipelines and sync services
├── dbt/                   # Semantic layer, data models, business glossary seeds
├── docs/                  # Architecture docs, ADRs, runbooks, onboarding guides
├── deployment/            # Docker Compose, environment configs, deployment scripts
├── monitoring/            # Health check definitions, alerting rules, dashboards
├── testing/               # End-to-end tests, load tests, AI regression suites
├── scripts/               # Developer utilities, seed scripts, migration helpers
├── infrastructure/        # Cloud provisioning configs (V3: Terraform, Helm)
├── .github/               # CI/CD workflows, PR templates, issue templates
├── docker/                # Dockerfiles for all services
└── config/                # Shared configuration schemas and environment templates
```

---

## 2. Detailed Folder Specifications

### 2.1 `backend/` — FastAPI Application Service

```
backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── routers/
│   │   │   │   ├── auth.py            # Login, logout, token refresh
│   │   │   │   ├── chat.py            # WebSocket chat endpoint
│   │   │   │   ├── query.py           # NL-to-SQL query execution
│   │   │   │   ├── forecast.py        # Forecasting endpoints
│   │   │   │   ├── dashboard.py       # Dashboard CRUD
│   │   │   │   ├── admin.py           # Admin panel endpoints
│   │   │   │   ├── metadata.py        # Schema browser endpoints
│   │   │   │   ├── health.py          # Health and readiness probes
│   │   │   │   └── export.py          # CSV/JSON/PNG export
│   │   │   └── schemas/
│   │   │       ├── requests/          # Pydantic input models per router
│   │   │       ├── responses/         # Pydantic output models per router
│   │   │       └── errors.py          # Standardized error response schemas
│   │   └── dependencies.py            # Shared FastAPI dependencies (auth, rate limit)
│   ├── core/
│   │   ├── config.py                  # Pydantic settings (env var validation)
│   │   ├── security.py                # JWT decode, OIDC verification, RBAC check
│   │   ├── rate_limiter.py            # Per-user/per-org rate limiting
│   │   ├── middleware/
│   │   │   ├── cors.py                # CORS configuration
│   │   │   ├── logging.py             # Structured request/response logging
│   │   │   ├── error_handler.py       # Global exception-to-HTTP-response mapper
│   │   │   └── timing.py              # Request duration tracking
│   │   └── events.py                  # Application startup/shutdown hooks
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── query_context.py       # QueryContext, ResolvedContext models
│   │   │   ├── visual_spec.py         # ChartSpec, DashboardLayout models
│   │   │   ├── forecast_model.py      # ForecastRequest, PredictionResult models
│   │   │   ├── kpi.py                 # KPI definition entities
│   │   │   └── user.py                # User, Role, Permission entities
│   │   ├── interfaces/
│   │   │   ├── i_snowflake_client.py  # Abstract Snowflake query interface
│   │   │   ├── i_vector_store.py      # Abstract vector search interface
│   │   │   ├── i_llm_client.py        # Abstract LLM call interface
│   │   │   ├── i_cache.py             # Abstract cache interface
│   │   │   └── i_audit_logger.py      # Abstract audit logging interface
│   │   ├── use_cases/
│   │   │   ├── compile_sql_query.py   # Text-to-SQL compilation orchestrator
│   │   │   ├── execute_query.py       # Snowflake query execution
│   │   │   ├── generate_forecast.py   # Forecasting pipeline
│   │   │   ├── generate_insights.py   # Anomaly detection and insight extraction
│   │   │   ├── recommend_chart.py     # Chart type recommendation engine
│   │   │   ├── manage_dashboard.py    # Dashboard CRUD operations
│   │   │   └── sync_metadata.py       # Metadata sync orchestrator
│   │   └── exceptions.py              # Domain exception hierarchy (NBI-XXXX)
│   └── infrastructure/
│       ├── database/
│       │   ├── postgres.py            # PostgreSQL connection and session management
│       │   ├── snowflake_client.py     # Snowflake connector with role-based pooling
│       │   └── models/                # SQLAlchemy ORM models for system tables
│       ├── vector_store/
│       │   └── pgvector_client.py     # pgvector search implementation
│       ├── cache/
│       │   └── redis_client.py        # Redis session and query cache
│       ├── ai/
│       │   ├── llm_client.py          # Claude/OpenAI API client with failover
│       │   ├── embedding_client.py    # Embedding generation client
│       │   └── prompt_builder.py      # Prompt assembly from templates
│       └── external/
│           └── oidc_provider.py       # OIDC token verification client
├── tests/
│   ├── unit/                          # Unit tests (mocked dependencies)
│   ├── integration/                   # Integration tests (real DB, mock LLM)
│   └── fixtures/                      # Test data factories and mock responses
├── alembic/                           # Database migration scripts
│   ├── versions/                      # Migration version files
│   └── env.py                         # Alembic configuration
├── pyproject.toml                     # Python project config (dependencies, linting)
└── Dockerfile                         # Backend container definition
```

- **Purpose:** Houses all server-side business logic, API routing, database interactions, and AI integration.
- **Responsibilities:** HTTP/WebSocket request handling, authentication enforcement, SQL compilation orchestration, Snowflake query execution, forecasting, audit logging.
- **Ownership:** Backend engineering team.
- **Dependencies:** PostgreSQL, Redis, Snowflake, LLM API provider, OIDC provider.
- **Why it exists:** The modular monolith design (ADR-001) consolidates all backend concerns into a single deployable unit while maintaining clean domain boundaries via Python packages.
- **Development guidelines:** All new features start with a use case in `domain/use_cases/`. Infrastructure adapters implement domain interfaces. No direct database calls from routers. Every router method must call exactly one use case.

---

### 2.2 `frontend/` — React Single Page Application

```
frontend/
├── public/
│   ├── index.html                     # Root HTML template
│   ├── favicon.ico                    # NexusBI brand icon
│   └── manifest.json                  # PWA manifest
├── src/
│   ├── app/
│   │   ├── App.tsx                    # Root component with router
│   │   ├── store.ts                   # Redux store configuration
│   │   └── theme.ts                   # Light/dark theme definitions
│   ├── components/
│   │   ├── common/
│   │   │   ├── Spinner.tsx            # Loading spinner
│   │   │   ├── ErrorBanner.tsx        # Error notification banner
│   │   │   ├── EmptyState.tsx         # Empty state placeholder
│   │   │   ├── KPICard.tsx            # KPI scorecard widget
│   │   │   └── ConfirmDialog.tsx      # Confirmation modal
│   │   ├── chat/
│   │   │   ├── ChatPanel.tsx          # Main chat container
│   │   │   ├── MessageBubble.tsx      # Individual message display
│   │   │   ├── QueryInput.tsx         # User input field with suggestions
│   │   │   ├── ProgressSteps.tsx      # AI pipeline progress indicator
│   │   │   └── SQLViewer.tsx          # Syntax-highlighted SQL display
│   │   ├── dashboard/
│   │   │   ├── DashboardGrid.tsx      # Drag-and-drop chart grid
│   │   │   ├── ChartWidget.tsx        # Individual chart container
│   │   │   ├── DashboardHeader.tsx    # Dashboard title, share, export controls
│   │   │   └── WidgetResizer.tsx      # Widget resize handles
│   │   ├── charts/
│   │   │   ├── EChartsRenderer.tsx    # Universal ECharts rendering wrapper
│   │   │   ├── ForecastOverlay.tsx    # Forecast projection overlay
│   │   │   └── AnomalyMarker.tsx      # Anomaly annotation markers
│   │   ├── admin/
│   │   │   ├── UserTable.tsx          # User management table
│   │   │   ├── SchemaManager.tsx      # Schema enable/disable panel
│   │   │   ├── GlossaryEditor.tsx     # Business term editor
│   │   │   ├── CostDashboard.tsx      # LLM and Snowflake cost tracking
│   │   │   └── SyncStatus.tsx         # Metadata sync health display
│   │   └── layout/
│   │       ├── Sidebar.tsx            # Left navigation sidebar
│   │       ├── TopBar.tsx             # Top navigation bar with notifications
│   │       └── RoleGuard.tsx          # Permission-based component visibility
│   ├── features/
│   │   ├── auth/
│   │   │   ├── authSlice.ts           # Authentication state (JWT, user info)
│   │   │   └── authApi.ts             # RTK Query auth endpoints
│   │   ├── chat/
│   │   │   ├── chatSlice.ts           # Conversation state, message history
│   │   │   └── chatWebSocket.ts       # WebSocket connection manager
│   │   ├── dashboard/
│   │   │   ├── dashboardSlice.ts      # Dashboard layout state
│   │   │   └── dashboardApi.ts        # RTK Query dashboard CRUD
│   │   ├── query/
│   │   │   ├── querySlice.ts          # Active query state, filters
│   │   │   └── queryApi.ts            # RTK Query for query execution
│   │   └── admin/
│   │       ├── adminSlice.ts          # Admin panel state
│   │       └── adminApi.ts            # RTK Query admin endpoints
│   ├── routes/
│   │   ├── ProtectedRoute.tsx         # Auth-gated route wrapper
│   │   ├── DashboardPage.tsx          # Dashboard page layout
│   │   ├── ChatPage.tsx               # Chat workspace page
│   │   ├── AdminPage.tsx              # Admin panel page
│   │   ├── LoginPage.tsx              # OIDC redirect login page
│   │   └── NotFoundPage.tsx           # 404 error page
│   ├── hooks/
│   │   ├── useWebSocket.ts           # WebSocket connection hook
│   │   ├── usePermissions.ts         # RBAC permission check hook
│   │   └── useTheme.ts               # Theme toggle hook
│   └── utils/
│       ├── formatters.ts             # Number, date, currency formatters
│       ├── chartMapper.ts            # Maps ChartSpec JSON to ECharts options
│       └── exportUtils.ts            # CSV/PNG export helpers
├── tailwind.config.js                 # Tailwind CSS configuration
├── tsconfig.json                      # TypeScript configuration
├── package.json                       # NPM dependencies
├── vite.config.ts                     # Vite build configuration
└── Dockerfile                         # Frontend container definition
```

- **Purpose:** Delivers the interactive user interface for all NexusBI personas.
- **Responsibilities:** Authentication flow, chat interface, dashboard rendering, chart visualization, admin panels, export functionality.
- **Ownership:** Frontend engineering team.
- **Dependencies:** Backend API (REST + WebSocket), ECharts library, Redux Toolkit.
- **Why it exists:** React provides component reuse across all personas (CEO, Analyst, Admin) while Redux Toolkit manages complex cross-cutting state (chat history, active filters, dashboard layouts).
- **Development guidelines:** Every component must handle 3 states: loading, error, and empty. Permission-gated components use `RoleGuard`. All API calls go through RTK Query (no raw fetch). Tailwind utility classes only — no custom CSS files.

---

### 2.3 `ai/` — AI Prompt Engineering & Model Configuration

```
ai/
├── prompts/
│   ├── system/
│   │   ├── sql_generator.md           # System prompt for Text-to-SQL
│   │   ├── intent_classifier.md       # System prompt for intent detection
│   │   ├── insight_generator.md       # System prompt for business insights
│   │   ├── recommendation_engine.md   # System prompt for prescriptive recs
│   │   └── chart_selector.md          # System prompt for chart type selection
│   ├── few_shot/
│   │   ├── sql_examples.json          # Curated NL-to-SQL example pairs
│   │   ├── insight_examples.json      # Example insight generation outputs
│   │   └── chart_examples.json        # Example data-to-chart mappings
│   └── guardrails/
│       ├── safety_rules.md            # Prompt injection prevention rules
│       ├── output_format.md           # Structured output formatting rules
│       └── snowflake_dialect.md       # Snowflake-specific SQL syntax rules
├── evaluation/
│   ├── test_suite.json                # 200+ validated query/SQL/result triples
│   ├── eval_runner.py                 # Evaluation script (accuracy, latency)
│   ├── regression_report.md           # Latest regression test results
│   └── benchmarks/                    # Historical benchmark comparisons
├── models/
│   ├── model_registry.yaml            # Model identifiers, versions, cost tables
│   ├── routing_rules.yaml             # Which model handles which task
│   └── fallback_chain.yaml            # Failover order when primary model is down
└── README.md                          # Prompt engineering guidelines and standards
```

- **Purpose:** Centralizes all AI prompt engineering assets, model configurations, and evaluation tooling.
- **Responsibilities:** Prompt template management, few-shot example curation, model version control, accuracy evaluation, prompt regression testing.
- **Ownership:** AI/ML engineering team.
- **Dependencies:** LLM API providers (Anthropic, OpenAI), backend prompt builder module.
- **Why it exists:** Prompts are the most sensitive part of the AI pipeline. A single-word change in a system prompt can alter SQL generation accuracy by 10%. Centralizing prompts in version-controlled Markdown files enables rigorous review, A/B testing, and rollback.
- **Development guidelines:** All prompt changes require 2-reviewer approval (ADR from Task 7). Every prompt change must include updated evaluation results. Few-shot examples must be validated against actual Snowflake execution.

---

### 2.4 `etl/` — Metadata Ingestion Pipelines

```
etl/
├── crawlers/
│   ├── snowflake_crawler.py           # INFORMATION_SCHEMA metadata extractor
│   ├── dbt_manifest_parser.py         # dbt manifest.json semantic layer parser
│   └── base_crawler.py                # Abstract crawler interface (provider-factory)
├── transformers/
│   ├── schema_chunker.py              # Text chunking for embedding
│   ├── description_enricher.py        # Auto-generate descriptions for undocumented cols
│   └── diff_detector.py               # Schema change detection (new/dropped/renamed)
├── loaders/
│   ├── postgres_loader.py             # Upsert metadata cache to PostgreSQL
│   └── vector_loader.py               # Upsert embeddings to pgvector
├── scheduler/
│   └── sync_scheduler.py              # APScheduler job definitions (daily cron)
├── tests/
│   └── test_crawlers.py               # Unit tests with mock Snowflake responses
└── README.md                          # ETL pipeline documentation
```

- **Purpose:** Extracts metadata from Snowflake and semantic layers, transforms it into searchable text, and loads it into PostgreSQL and pgvector.
- **Responsibilities:** Schema discovery, change detection, text chunking, embedding generation, vector upsert, sync status reporting.
- **Ownership:** Data engineering team.
- **Dependencies:** Snowflake INFORMATION_SCHEMA, dbt manifest files, OpenAI embeddings API, PostgreSQL + pgvector.
- **Why it exists:** The quality of Text-to-SQL generation is directly proportional to the quality of schema metadata available in the vector store. The ETL pipeline is the foundation of the entire AI system.
- **Development guidelines:** All crawlers implement `base_crawler.py` interface. New data source connectors (BigQuery, Redshift in V2) are added as new crawler implementations without modifying existing code. Schema diffs are always logged for admin review.

---

### 2.5 `dbt/` — Semantic Layer & Data Transformations

```
dbt/
├── models/
│   ├── staging/                       # Raw-to-clean transformations (stg_ prefix)
│   ├── intermediate/                  # Business logic transformations (int_ prefix)
│   └── marts/                         # Final fact/dimension tables (fct_, dim_ prefix)
├── seeds/
│   ├── kpi_catalog.csv                # KPI definitions from Task 2
│   ├── business_glossary.csv          # Business term definitions
│   └── pii_column_registry.csv        # PII-flagged columns
├── macros/                            # Reusable SQL macros
├── tests/                             # dbt data quality tests
├── dbt_project.yml                    # dbt project configuration
├── profiles.yml.template              # Snowflake connection template
└── README.md                          # Semantic layer documentation
```

- **Purpose:** Defines the canonical data transformations and business semantics that NexusBI uses to generate accurate SQL.
- **Ownership:** Data engineering team (shared with analytics team).
- **Why it exists:** dbt models serve as the ground truth for business metric calculations. The KPI catalog (Task 2) is seeded here and synced to PostgreSQL during deployment.

---

### 2.6 `docs/` — Architecture & Engineering Documentation

```
docs/
├── architecture/
│   ├── nexusbi_architecture_planning.md    # Phase 1 planning document
│   ├── phase2_task1_architecture_review.md # Architecture review findings
│   ├── phase2_task2_kpi_catalog.md         # KPI catalog
│   ├── phase2_task3_user_journeys.md       # User journey maps
│   ├── phase2_task4_ai_pipeline.md         # AI decision pipeline
│   ├── phase2_task5_version_planning.md    # Version roadmap
│   ├── phase2_task6_risk_assessment.md     # Risk assessment
│   └── phase2_task7_architecture_validation.md # Design validation
├── adrs/
│   ├── ADR-001-modular-monolith.md         # Monolith over microservices
│   ├── ADR-002-pgvector-over-qdrant.md     # pgvector for V1
│   └── ...                                 # ADRs 003-015
├── runbooks/
│   ├── incident-response.md                # On-call incident procedures
│   ├── metadata-sync-failure.md            # Sync failure recovery
│   ├── snowflake-connection-issues.md      # Connection pool troubleshooting
│   └── llm-failover.md                     # LLM provider failover procedures
├── onboarding/
│   ├── developer-setup.md                  # Local development environment guide
│   ├── architecture-overview.md            # Architecture overview for new hires
│   └── coding-standards.md                 # Link to engineering standards
└── api/
    └── openapi.yaml                        # Generated OpenAPI 3.1 specification
```

- **Purpose:** Single source of truth for all project documentation.
- **Ownership:** Entire engineering team (architecture docs owned by tech lead).
- **Why it exists:** Documentation co-located with code stays current. External wikis diverge from reality. ADRs preserve decision rationale for future engineers.

---

### 2.7 `deployment/` — Deployment Configurations

```
deployment/
├── docker-compose.yml                 # V1 full-stack local/production deployment
├── docker-compose.dev.yml             # Development overrides (hot reload, debug)
├── docker-compose.test.yml            # Test environment (mock LLM, test DB)
├── envs/
│   ├── .env.template                  # Environment variable template with docs
│   ├── .env.development               # Development defaults (gitignored)
│   ├── .env.staging                   # Staging environment config
│   └── .env.production                # Production environment config (gitignored)
├── nginx/
│   ├── nginx.conf                     # Reverse proxy config (V2+)
│   └── ssl/                           # TLS certificate storage
└── scripts/
    ├── deploy.sh                      # Deployment automation script
    ├── rollback.sh                    # Rollback to previous version
    └── health-check.sh                # Post-deployment health verification
```

- **Purpose:** Everything needed to deploy NexusBI to any environment.
- **Ownership:** Backend engineering + DevOps.
- **Why it exists:** Deployment must be repeatable, automated, and environment-aware. Docker Compose is the V1 orchestrator (ADR-001). Environment configs are templated to prevent secret leakage.

---

### 2.8 `monitoring/` — Observability Configurations

```
monitoring/
├── health/
│   ├── health_checks.yaml             # Health check endpoint definitions
│   └── readiness_probes.yaml          # Readiness probe configurations
├── alerts/
│   ├── cost_alerts.yaml               # LLM and Snowflake cost thresholds
│   ├── error_rate_alerts.yaml         # API error rate thresholds
│   └── sync_alerts.yaml               # Metadata sync failure alerts
├── dashboards/
│   ├── system_health.json             # System health dashboard definition
│   ├── ai_metrics.json                # AI-specific metrics dashboard
│   └── cost_tracking.json             # Cost tracking dashboard
└── README.md                          # Monitoring setup and standards
```

- **Purpose:** Defines all monitoring, alerting, and observability configurations.
- **Ownership:** Backend engineering + SRE (V3+).
- **Why it exists:** Observability is a V1 requirement (Phase 2, Task 7). Alert definitions are version-controlled to prevent silent degradation.

---

### 2.9 `testing/` — Cross-Cutting Test Suites

```
testing/
├── e2e/
│   ├── test_query_flow.py             # End-to-end NL query to chart rendering
│   ├── test_auth_flow.py              # End-to-end login to dashboard access
│   └── test_admin_flow.py             # End-to-end admin operations
├── load/
│   ├── locustfile.py                  # Load test definitions (Locust)
│   ├── scenarios/
│   │   ├── concurrent_queries.py      # 100 concurrent NL queries
│   │   └── sustained_load.py          # 8-hour sustained usage simulation
│   └── reports/                       # Load test result reports
├── ai_regression/
│   ├── regression_runner.py           # Runs AI eval suite against current prompts
│   ├── golden_set.json                # 200+ validated query/SQL pairs
│   └── reports/                       # Regression test reports
└── README.md                          # Testing strategy and standards
```

- **Purpose:** Houses test suites that span multiple system components.
- **Ownership:** QA engineering + backend team.
- **Why it exists:** Unit and integration tests live in their respective service directories. This folder contains cross-cutting tests (E2E, load, AI regression) that validate the system as a whole.

---

### 2.10 `scripts/` — Developer Utilities

```
scripts/
├── seed_database.py                   # Populate PostgreSQL with sample data
├── seed_kpi_catalog.py                # Load KPI catalog into database
├── generate_mock_llm_responses.py     # Generate mock LLM fixtures for testing
├── run_metadata_sync.py               # Manual metadata sync trigger
├── reset_dev_environment.sh           # Wipe and rebuild dev environment
└── README.md                          # Script usage documentation
```

---

### 2.11 `infrastructure/` — Cloud Provisioning (V3+)

```
infrastructure/
├── terraform/
│   ├── modules/
│   │   ├── vpc/                       # Network configuration
│   │   ├── eks/                       # Kubernetes cluster
│   │   ├── rds/                       # PostgreSQL RDS instance
│   │   ├── elasticache/               # Redis instance
│   │   └── iam/                       # IAM roles and policies
│   ├── environments/
│   │   ├── staging/                   # Staging environment variables
│   │   └── production/                # Production environment variables
│   └── main.tf                        # Root Terraform configuration
├── kubernetes/
│   ├── helm/
│   │   ├── nexusbi/                   # NexusBI Helm chart
│   │   └── values/                    # Per-environment Helm values
│   └── manifests/                     # Raw K8s manifests (if not using Helm)
└── README.md                          # Infrastructure provisioning guide
```

- **Purpose:** Cloud infrastructure provisioning (empty in V1, populated in V3).
- **Why it exists:** The folder structure is created now so that V3 infrastructure work has a clear home. Prevents ad-hoc infrastructure scripts from scattering across the repository.

---

### 2.12 `.github/` — CI/CD & Repository Governance

```
.github/
├── workflows/
│   ├── ci.yml                         # Lint, test, build on every PR
│   ├── deploy-staging.yml             # Deploy to staging on merge to develop
│   ├── deploy-production.yml          # Deploy to production on release tag
│   └── ai-regression.yml              # Weekly AI regression test suite
├── PULL_REQUEST_TEMPLATE.md           # PR template with checklist
├── ISSUE_TEMPLATE/
│   ├── bug_report.md                  # Bug report template
│   ├── feature_request.md             # Feature request template
│   └── ai_prompt_change.md            # Prompt change request template
├── CODEOWNERS                         # File ownership definitions
└── dependabot.yml                     # Automated dependency updates
```

---

### 2.13 `docker/` — Container Definitions

```
docker/
├── backend.Dockerfile                 # Python FastAPI container
├── frontend.Dockerfile                # Node.js build + Nginx serve container
├── etl.Dockerfile                     # ETL pipeline container (shared Python base)
└── base-python.Dockerfile             # Shared Python base image with common deps
```

- **Purpose:** Centralizes all Dockerfiles for consistent build management.
- **Why it exists:** Separating Dockerfiles from application code enables shared base images, multi-stage builds, and centralized security scanning.

---

### 2.14 `config/` — Shared Configuration Schemas

```
config/
├── feature_flags.yaml                 # Feature flag definitions and defaults
├── rate_limits.yaml                   # Rate limiting configuration per role
├── error_codes.yaml                   # NBI-XXXX error code registry
├── kpi_chart_mappings.yaml            # KPI-to-default-chart-type mappings
└── snowflake_dialect_rules.yaml       # Snowflake SQL syntax validation rules
```

- **Purpose:** Configuration that is shared across multiple services or referenced by documentation.
- **Why it exists:** Centralizing configuration prevents drift between services and ensures consistency. YAML format is human-readable and version-controllable.
