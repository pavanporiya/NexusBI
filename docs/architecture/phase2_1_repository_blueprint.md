# NexusBI Phase 2.1: Repository Blueprint & Module Design Specification

**Document Version:** 1.0.0  
**Status:** Approved for Implementation  
**Author:** Principal Software Architect  
**Target Phase:** V1 (MVP Foundation) transition to V2  

---

## 1. Complete Repository Directory Tree

Below is the complete production-grade repository tree, defined to the implementation file level for V1/V2 development.

```text
NexusBI/
├── .github/
│   ├── workflows/
│   │   ├── ci-backend.yml              # Lint, test, security scan for FastAPI
│   │   ├── ci-frontend.yml             # Lint, test, build scan for React/Next
│   │   ├── ci-dbt.yml                  # dbt compile and data tests check
│   │   ├── deploy-staging.yml          # Auto-deploy to Staging environment
│   │   ├── deploy-production.yml       # Manual/Tag-gated deploy to Prod
│   │   └── ai-evaluation.yml           # Runs periodic prompt regression suite
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   ├── feature_request.md
│   │   └── prompt_change.md
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── CODEOWNERS                      # Code ownership patterns
│
├── config/
│   ├── envs/
│   │   ├── .env.template               # Canonical environment variables definition
│   │   ├── .env.development            # Local development env overrides (gitignored)
│   │   ├── .env.testing                # CI/Mock unit-testing env overrides
│   │   └── .env.staging                # Staging credentials schema
│   ├── feature_flags.yaml              # App feature gates and model rollouts
│   ├── rate_limits.yaml                # Rate limit definitions by user tier/role
│   └── error_codes.yaml                # Standardized NBI-XXXX error codes registry
│
├── docs/
│   ├── architecture/
│   │   ├── nexusbi_architecture_planning.md
│   │   ├── phase2_task1_architecture_review.md
│   │   ├── phase2_task2_kpi_catalog.md
│   │   ├── phase2_task3_user_journeys.md
│   │   ├── phase2_task4_ai_pipeline.md
│   │   ├── phase2_task5_version_planning.md
│   │   ├── phase2_task6_risk_assessment.md
│   │   ├── phase2_task7_architecture_validation.md
│   │   └── phase2_1_repository_blueprint.md
│   ├── adrs/
│   │   ├── ADR-001-monolith-first.md
│   │   ├── ADR-002-pgvector-vector-cache.md
│   │   └── ADR-003-echarts-standardization.md
│   ├── developer/
│   │   ├── local_setup.md              # Docker Compose dev environment guide
│   │   ├── api_guidelines.md           # API design, JSON conventions
│   │   └── coding_standards.md         # Python / TypeScript styling rules
│   └── operations/
│       ├── deploy_guide.md             # Docker-to-cloud operational checklist
│       ├── runbook_sync_failure.md     # Resolving catalog metadata sync lag
│       └── runbook_llm_outage.md       # Triggering LLM provider failover
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── routers/
│   │   │   │   │   ├── auth.py         # OIDC login, refresh, logout
│   │   │   │   │   ├── chat.py         # WebSocket chat agent gateway
│   │   │   │   │   ├── query.py        # Ad-hoc text-to-SQL direct execution
│   │   │   │   │   ├── forecast.py     # Prophet time-series calculations
│   │   │   │   │   ├── dashboard.py    # Dashboard layout endpoints
│   │   │   │   │   ├── metadata.py     # Database schema/catalog explorer
│   │   │   │   │   ├── admin.py        # User control and cost configuration
│   │   │   │   │   ├── audit.py        # System audit log browser
│   │   │   │   │   └── health.py       # Liveness/Readiness endpoints
│   │   │   │   ├── schemas/
│   │   │   │   │   ├── requests/       # Pydantic input schemas
│   │   │   │   │   │   ├── auth_req.py
│   │   │   │   │   │   ├── chat_req.py
│   │   │   │   │   │   ├── forecast_req.py
│   │   │   │   │   │   └── dashboard_req.py
│   │   │   │   │   └── responses/      # Pydantic response envelopes
│   │   │   │   │       ├── auth_res.py
│   │   │   │   │       ├── chat_res.py
│   │   │   │   │       ├── forecast_res.py
│   │   │   │   │       └── dashboard_res.py
│   │   │   │   └── dependencies/
│   │   │   │       ├── auth_deps.py    # JWT extraction, OIDC validation
│   │   │   │       ├── db_deps.py      # Postgres transaction scope
│   │   │   │       └── limit_deps.py   # Rate limiting resolution
│   │   │   └── middleware/
│   │   │       ├── logging.py          # Structured JSON request logger
│   │   │       ├── error_handler.py    # Global exception mapping
│   │   │       └── cors.py             # Domain-allowed headers config
│   │   ├── core/
│   │   │   ├── config.py               # Pydantic-settings config broker
│   │   │   ├── security.py             # Key-pair auth, cryptography
│   │   │   ├── database.py             # Postgres DB pool engine instance
│   │   │   └── logger.py               # Structlog configuration engine
│   │   ├── domain/
│   │   │   ├── entities/               # Pure Domain data schemas
│   │   │   │   ├── user.py
│   │   │   │   ├── query.py
│   │   │   │   ├── forecast.py
│   │   │   │   └── dashboard.py
│   │   │   ├── interfaces/             # Abstract Ports (Symmetrical clean)
│   │   │   │   ├── i_snowflake.py      # Snowflake driver client
│   │   │   │   ├── i_vector.py         # Vector store search client
│   │   │   │   ├── i_llm.py            # AI text generators
│   │   │   │   ├── i_cache.py          # Memory/key-value caching
│   │   │   │   └── i_audit.py          # Security logger interface
│   │   │   └── use_cases/              # Core Domain execution logic
│   │   │       ├── sql_compile.py      # NL-to-SQL pipeline use case
│   │   │       ├── sql_execute.py      # Snowflake client manager use case
│   │   │       ├── generate_forecast.py# Statistical time-series use case
│   │   │       ├── render_chart.py     # ECharts specification builder use case
│   │   │       ├── extract_insights.py # Statistical insight parser use case
│   │   │       └── sync_catalog.py     # Ingest metadata crawler use case
│   │   └── infrastructure/             # Abstract Adapters (Implementation)
│   │       ├── snowflake_adapter.py    # Snowflake client driver pool
│   │       ├── pgvector_adapter.py     # PostgreSQL + pgvector search client
│   │       ├── llm_adapter.py          # Claude 3.5 Sonnet / Haiku client
│   │       ├── redis_adapter.py        # Redis cache manager client
│   │       └── audit_adapter.py        # Postgres audit logs writer
│   ├── alembic/
│   │   ├── versions/
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── pyproject.toml                  # Poetry package configuration
│   └── Dockerfile                      # FastAPI production build definition
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx              # Root Page Shell
│   │   │   ├── page.tsx                # Dashboard Home
│   │   │   ├── chat/
│   │   │   │   └── page.tsx            # Chat Workspace Page
│   │   │   ├── admin/
│   │   │   │   └── page.tsx            # Admin Panel Screen
│   │   │   ├── alerts/
│   │   │   │   └── page.tsx            # Anomaly Alerts Screen
│   │   │   └── login/
│   │   │       └── page.tsx            # SSO Login Entry Screen
│   │   ├── components/                 # Presentation Components
│   │   │   ├── chat/
│   │   │   │   ├── ChatPanel.tsx       # WebSocket chat viewport
│   │   │   │   ├── MessageBubble.tsx   # Chat message bubble
│   │   │   │   └── QueryInput.tsx      # Natural language input with chips
│   │   │   ├── charts/
│   │   │   │   ├── EChartsRenderer.tsx # Apache ECharts rendering canvas
│   │   │   │   └── ForecastOverlay.tsx # Dotted forecast overlays
│   │   │   ├── dashboard/
│   │   │   │   ├── DashboardGrid.tsx   # Pinned widget grid layout
│   │   │   │   └── KPICard.tsx         # Out-of-box KPI scorecards
│   │   │   └── layout/
│   │   │       ├── Sidebar.tsx
│   │   │       └── TopNavbar.tsx
│   │   ├── features/                   # Application State Management
│   │   │   ├── auth/
│   │   │   │   ├── authSlice.ts
│   │   │   │   └── authApi.ts
│   │   │   ├── chat/
│   │   │   │   ├── chatSlice.ts
│   │   │   │   └── chatWebSocket.ts    # WebSocket client thread handler
│   │   │   ├── dashboard/
│   │   │   │   ├── dashboardSlice.ts
│   │   │   │   └── dashboardApi.ts
│   │   │   └── query/
│   │   │       ├── querySlice.ts
│   │   │       └── queryApi.ts
│   │   ├── hooks/
│   │   │   ├── usePermissions.ts       # RBAC gating hook
│   │   │   └── useTheme.ts             # Light/Dark mode state hook
│   │   └── utils/
│   │       ├── chart_options.ts        # Maps JSON Schema to ECharts options
│   │       └── formatters.ts           # Number, date, currency display rules
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── package.json                    # NPM dependencies file
│   └── Dockerfile                      # Next.js multi-stage build image
│
├── dbt/
│   ├── models/
│   │   ├── staging/                    # Base table transformations
│   │   │   ├── stg_orders.sql
│   │   │   └── stg_customers.sql
│   │   ├── intermediate/               # Derived metrics and business dimensions
│   │   │   └── int_order_details.sql
│   │   └── marts/                      # Canonical analytics tables
│   │       ├── fct_orders.sql          # Fact table (Target of catalog sync)
│   │       └── dim_customers.sql       # Dimension table (Target of catalog sync)
│   ├── seeds/
│   │   ├── kpi_catalog.csv             # Injected KPI Definitions (Task 2)
│   │   └── business_glossary.csv       # Business terminologies mapping
│   ├── tests/
│   │   ├── schema.yml                  # Schema expectations (Not null, unique)
│   │   └── assert_positive_revenue.sql # Custom sql validations
│   ├── dbt_project.yml                 # dbt configurations file
│   └── profiles.yml.template           # Snowflake profile template
│
├── etl/
│   ├── app/
│   │   ├── crawler/
│   │   │   ├── snowflake_crawler.py    # Scrapes columns, views, keys, comments
│   │   │   └── dbt_crawler.py          # Scrapes seed metadata and semantic maps
│   │   ├── transformer/
│   │   │   └── schema_vectorizer.py    # Transforms schemas to text chunks
│   │   └── loader/
│   │       └── database_loader.py      # Upserts embeddings to pgvector
│   ├── run_sync.py                     # Execution Entry Point for Sync service
│   ├── pyproject.toml
│   └── Dockerfile                      # ETL Runner container definition
│
├── ai/
│   ├── prompts/
│   │   ├── system/
│   │   │   ├── sql_generator.md        # Natural language to SQL system instructions
│   │   │   ├── intent_classifier.md    # User query classification instructions
│   │   │   └── insight_analyst.md      # McKinsey-style business summary guide
│   │   └── few_shot/
│   │       ├── sql_examples.json       # Few-shot sql samples
│   │       └── insight_examples.json   # Few-shot insight summaries
│   ├── models/
│   │   └── routing.yaml                # Model tiering configuration maps
│   └── README.md
│
├── monitoring/
│   ├── prometheus/
│   │   └── prometheus.yml              # Systems scrapers configuration
│   ├── grafana/
│   │   └── dashboards/
│   │       ├── health_dashboard.json   # Container & API Latencies visual layouts
│   │       └── cost_dashboard.json     # LLM Token & Snowflake credits visual layouts
│   └── loki/
│       └── loki-config.yml             # Logs aggregation specifications
│
├── deployment/
│   ├── docker-compose.yml              # Local/Dev single-command cluster spin-up
│   ├── docker-compose.prod.yml         # Production architecture overrides
│   ├── nginx/
│   │   └── nginx.conf                  # Gateway routes & SSL proxy setup
│   └── scripts/
│       ├── seed.sh                     # Database seeding initialization
│       └── restore.sh                  # Postgres restoration automation
│
├── testing/
│   ├── integration/
│   │   ├── test_snowflake_adapter.py   # Dry-run integration on Snowflake DEV
│   │   └── test_pgvector_adapter.py    # DB vector similarities integration
│   ├── e2e/
│   │   └── test_chat_pipeline.py       # End-to-end WebSocket chat validation
│   ├── load/
│   │   └── locustfile.py               # Concurrency load simulation
│   └── ai_regression/
│       ├── test_golden_set.py          # Runs prompt validations on DEV LLM API
│       └── golden_set.json             # 200+ validated question-to-SQL expectations
└── scripts/
    ├── generate_mock_data.py           # Populates local Postgres schemas
    └── verify_pipeline_state.py        # System dependencies health audit
```

---

## 2. Module Responsibilities

### 2.1 `backend/app/api/` — Presentation/Interface Layer
* **Purpose:** Handles external boundaries, serialization, validation, and request life-cycle routing.
* **Responsibilities:**
  * Define HTTP and WebSocket paths, endpoints, and protocol upgrades.
  * Serialize and deserialize incoming requests and outgoing payloads using Pydantic models.
  * Extract authorization headers, parse JWT, map scopes, and enforce rate limits.
  * Map internal domain exceptions directly to HTTP response statuses.
* **What belongs here:** Routers, Pydantic schemas, dependency injectors, CORS configuration, response wrappers, WebSocket event handlers.
* **What must never belong here:** SQL queries, DB queries, LLM API calls, statistical forecasting algorithms, raw system business rules.
* **Dependencies:** `backend/app/domain/` (orchestrators and interfaces).
* **Public Interfaces:** Router HTTP endpoints (e.g., `POST /api/v1/auth/callback`), WebSocket connections (`WS /api/v1/chat/ws`).
* **Internal Components:** Pydantic validators, internal route dependency trees.

### 2.2 `backend/app/domain/` — Bounded Domain Logic Layer
* **Purpose:** The core business heart of NexusBI. Shielded, framework-agnostic, and purely operational.
* **Responsibilities:**
  * Define domain entities (e.g., User profiles, Forecast demands, Query executions).
  * Coordinate business workflows via Use Cases (e.g., executing the 19-stage AI pipeline, compiling statistical metrics).
  * Define Ports (Interfaces) for infrastructure adapters to implement (e.g., `i_snowflake.py`, `i_llm.py`).
  * Enforce business rules, such as maximum row egress limit (50,000) or few-shot injection priorities.
* **What belongs here:** Interfaces/abstract classes, use case orchestrators, domain exceptions, domain schemas.
* **What must never belong here:** Framework references (FastAPI app references), database clients (SQLAlchemy session calls, Redis clients), direct LLM SDK calls.
* **Dependencies:** Standard library, typing modules. Zero external dependencies.
* **Public Interfaces:** Use Case class execution pipelines (e.g., `CompileSQLQueryUseCase.execute()`).
* **Internal Components:** Abstract classes, domain entities.

### 2.3 `backend/app/infrastructure/` — Adapters Layer
* **Purpose:** Concrete implementations of Domain interfaces interfacing with external servers and databases.
* **Responsibilities:**
  * Implement connection handling to Snowflake and PostgreSQL databases.
  * Translate domain operations to database commands (pgvector search, database inserts/updates).
  * Handle API calls to Anthropic/OpenAI SDKs with connection retries and exception logging.
  * Write audit entries to database tables.
* **What belongs here:** SQLAlchemy ORM models, database engines, redis clients, LLM API adapters.
* **What must never belong here:** API route definition files, business logic rule declarations.
* **Dependencies:** `backend/app/domain/` (implements domain interfaces), external libraries (SQLAlchemy, snowflake-connector, openai, redis).
* **Public Interfaces:** Adapter classes matching domain ports (e.g., `SnowflakeAdapter(ISnowflakeClient)`).
* **Internal Components:** DB connection pools, HTTP client instances, raw queries.

### 2.4 `frontend/src/app/` & `features/` — UI Shell & State Layer
* **Purpose:** Manages user interfaces, views, and frontend client-side state.
* **Responsibilities:**
  * Route paths to React pages and layouts (Next.js layout rules).
  * Hold central state for chat history, dashboard widget locations, active filters, and session parameters.
  * Manage WebSocket connections to the API gateway.
* **What belongs here:** Next.js pages/layout components, Redux slices, WebSocket listener loop client.
* **What must never belong here:** SQL string parsing, raw database access keys, secret variables (stored client-side).
* **Dependencies:** NPM libraries (React, Redux, Tailwind, ECharts).
* **Public Interfaces:** URL routing layout.
* **Internal Components:** Redux selectors, custom hooks.

### 2.5 `etl/app/` — Metadata Sync Crawlers
* **Purpose:** Run asynchronous background jobs to update schema catalogs.
* **Responsibilities:**
  * Crawl database structures from Snowflake system views.
  * Chunk column and table information into descriptive markdown text.
  * Generate schema embeddings and write to the vector database.
* **What belongs here:** Crawlers, transformers, loaders, metadata sync scripts.
* **What must never belong here:** API route configurations, web UI components.
* **Dependencies:** `backend/app/infrastructure/` (uses the same db/vector adapter clients), Snowflake metadata catalog.
* **Public Interfaces:** CLI entry execution script (`run_sync.py`).
* **Internal Components:** Catalog diff calculators, chunking utilities.

---

## 3. Dependency Rules & Boundaries

To maintain Clean Architecture boundaries and allow clean service extraction in future versions:

```
┌────────────────────────────────────────────────────────┐
│                        api/ (API Layer)                │
└───────────────────────────┬────────────────────────────┘
                            │ imports
                            ▼
┌────────────────────────────────────────────────────────┐
│                     domain/use_cases/                  │
└───────────────────────────┬────────────────────────────┘
                            │ calls
                            ▼
┌────────────────────────────────────────────────────────┐
│                     domain/interfaces/                 │
└───────────────────────────▲────────────────────────────┘
                            │ implemented by
                            │
┌───────────────────────────┴────────────────────────────┐
│                    infrastructure/ (Adapters)          │
└────────────────────────────────────────────────────────┘
```

### 3.1 Allowed Imports & Directives
* **Presentation Layer (`app/api/`)** can import from `app/domain/` and `app/core/`.
* **Domain Layer (`app/domain/`)** can import only from `app/domain/entities/`, `app/domain/interfaces/`, and `app/domain/exceptions.py`. It is forbidden from importing from any other module.
* **Infrastructure Layer (`app/infrastructure/`)** can import from `app/domain/` and `app/core/`. It implements the ports in `app/domain/interfaces/`.
* **Core Layer (`app/core/`)** contains shared constants, database pools, and configuration parsers. Any layer can import from `app/core/`.

### 3.2 Dependency Inversion rules
Use cases do not instantiate infrastructure adapters directly. They accept them as parameters in the constructor (Dependency Injection). FastAPI dependencies handles the creation and injection of these adapters during request routing:

```python
# app/api/v1/routers/chat.py
# Example Injection flow (Conceptual)
@router.websocket("/ws")
async def chat_ws(
    websocket: WebSocket,
    use_case: CompileSQLQueryUseCase = Depends(get_compile_sql_use_case)
):
    ...
```

---

## 4. Naming Standards

### 4.1 Folder Naming
* **System folders:** Lowercase, snake_case (`app_configs`, `docker_files`, `domain_logic`).
* **Frontend directories:** Lowercase, kebab-case (`components`, `chat-workspace`, `kpi-dashboard`).
* **dbt directories:** Lowercase, snake_case (`staging`, `intermediate`, `marts`).

### 4.2 File Naming
* **Python files:** Lowercase, snake_case (`snowflake_adapter.py`, `sql_compile.py`).
* **TypeScript/React files:**
  * Components (functional modules): PascalCase (`KPICard.tsx`, `ChatPanel.tsx`).
  * Slices, hooks, utilities: camelCase (`chatSlice.ts`, `usePermissions.ts`, `formatters.ts`).
* **Markdown files:** Lowercase, snake_case (`nexusbi_architecture_planning.md`).
* **dbt sql models:** Prefix-driven lowercase snake_case:
  * Staging: `stg_{source}_{entity}.sql` (e.g., `stg_snowflake_orders.sql`).
  * Intermediate: `int_{logic_description}.sql`.
  * Marts: `fct_{entity}.sql` (fact) or `dim_{entity}.sql` (dimension).

### 4.3 Environment Variables
* **System scope:** Upper snake_case (`DATABASE_URL`, `REDIS_URL`, `SNOWFLAKE_ACCOUNT`).
* **Boolean flags:** Prefix `ENABLE_` or `ALLOW_` (`ENABLE_SEMANTIC_CACHE`, `ALLOW_ANALYST_EXPORT`).
* **LLM configurations:** Prefix `LLM_` (`LLM_PRIMARY_MODEL`, `LLM_API_KEY`).

### 4.4 Migration Naming
* **Alembic revisions:** Sequential timestamp prefix with snake_case description (`20260701_2232_init_auth_schema.py`).
* **dbt revisions:** Follow staging, intermediate, and marts definitions sequentially.

---

## 5. Configuration Strategy

### 5.1 Environment Configuration Matrix

| Variable | Development (Local) | Testing (CI) | Production (Cloud) |
|:---|:---|:---|:---|
| `ENVIRONMENT` | `"development"` | `"testing"` | `"production"` |
| `DEBUG` | `true` | `false` | `false` |
| `DATABASE_URL` | `postgresql://localhost/dev` | `postgresql://localhost/test` | AWS RDS instance URI |
| `REDIS_URL` | `redis://localhost:6379/0` | Mock Redis (in-memory) | AWS ElastiCache cluster URI |
| `LLM_API_KEY` | Developer's Sandbox Key | Mock LLM Responses fixture | AWS Vault Decrypted Key |
| `ENABLE_SEMANTIC_CACHE` | `false` | `false` | `true` |
| `LOG_LEVEL` | `"DEBUG"` | `"ERROR"` | `"INFO"` |

### 5.2 Secret Management (Vault Integration)
* No secrets are written to source control or container images.
* Local development secrets are loaded via `.env` (gitignored).
* Production secrets are injected dynamically into the container environment variables by AWS Secrets Manager or HashiCorp Vault during container startup.

### 5.3 Feature Flags Configuration
Feature flags are defined in `config/feature_flags.yaml`:
```yaml
features:
  enable_forecasting:
    default: true
    rollout_percentage: 100
  enable_recommendations:
    default: false
    rollout_percentage: 10
  use_fallback_llm:
    default: false
    rollout_percentage: 0
```
FastAPI loads this file on startup, parses it into Pydantic models, and exposes an endpoint for the frontend to adjust visible layout features based on active flags.

---

## 6. Logging Strategy

### 6.1 Logging Infrastructure
All logs are emitted to standard output (Stdout) in structured JSON format. In staging and production, the logging agent (Loki) scrapes these outputs, aggregates them, and forwards them to a centralized logs console.

### 6.2 Log Classifications

#### 6.2.1 Audit Logs (`audit.query_executions`)
* **Purpose:** Log every user query transaction, generated SQL, execution duration, and metadata results.
* **Volume:** Low/Medium (one log per user search).
* **Retention:** 2 years (SOC 2 audit compliance).
* **Storage:** Append-only relational PostgreSQL table.

#### 6.2.2 AI logs (`audit.llm_transactions`)
* **Purpose:** Log tokens, response latency, prompts, self-healing retries, and API costs.
* **Volume:** Medium (2-3 logs per user search due to pipeline steps).
* **Retention:** 1 year.
* **Storage:** Relational PostgreSQL table.

#### 6.2.3 Security Logs (`security.log`)
* **Purpose:** Record login failures, rate limit breaches, unauthorized schema access attempts, and prompt injection detections.
* **Volume:** Low.
* **Retention:** 2 years (SOC 2 audit compliance).
* **Storage:** PostgreSQL table, mirrored to Loki with alerts configured for security escalations.

#### 6.2.4 Pipeline Logs (`sync.log`)
* **Purpose:** Log metadata crawler sync runs, count of new schemas discovered, crawl durations, and sync failures.
* **Volume:** Low (daily sync jobs).
* **Retention:** 90 days.
* **Storage:** Loki.

---

## 7. Documentation Strategy

All system specifications live in the `docs/` folder. This keeps documentation versioned alongside the code:

```text
docs/
├── architecture/             # Architectural specifications
│   ├── nexusbi_architecture_planning.md  # Core plan
│   └── phase2_1_repository_blueprint.md   # This document
├── adrs/                     # Architecture Decision Records
│   ├── ADR-001-monolith-first.md
│   └── ADR-002-pgvector-vector-cache.md
├── developer/                # Technical guides for engineers
│   ├── local_setup.md        # Spin up local compose, seeds
│   └── api_guidelines.md     # REST and WebSocket patterns
└── operations/               # Production running parameters
    ├── deploy_guide.md       # Docker-to-cloud parameters
    └── runbook_sync_failure.md # Handling sync errors
```

---

## 8. Testing Strategy

NexusBI testing architecture enforces the following structure:

```text
testing/
├── integration/              # Tests adapters against real DB/Dev Snowflake
│   ├── test_snowflake_adapter.py
│   └── test_pgvector_adapter.py
├── e2e/                      # Tests full API paths (REST/WebSocket)
│   └── test_chat_pipeline.py
├── load/                     # Verifies API gateway under concurrency load
│   └── locustfile.py
└── ai_regression/            # Checks SQL output accuracy on model upgrades
    ├── test_golden_set.py
    └── golden_set.json       # 200+ validated test cases
```

### 8.1 Test Suites Definitions
* **Unit Tests (under `backend/tests/unit/`):** Test use cases and domain logic using mock adapter classes. Target execution speed: <5 seconds.
* **Integration Tests (under `testing/integration/`):** Test infrastructure adapters against database containers (Postgres, pgvector, Redis) and a test Snowflake sandbox schema.
* **AI Regression Tests (under `testing/ai_regression/`):** Validate prompt modifications. When prompt files (`ai/prompts/...`) are updated, the regression runner sends the 200 questions in `golden_set.json` to the LLM API, parses the SQL, executes it against Snowflake dev, and asserts that the results match expectations.
* **E2E Tests (under `testing/e2e/`):** Test full request flows (FastAPI, Redis session, database, and return websocket packet).

---

## 9. Final Repository Validation & Audit

As the Lead Software Architect, I have reviewed this repository structure and module design. Here is the evaluation:

### 9.1 Strengths
* **Symmetrical Domain Boundaries:** Enforces strict domain separation. API and Infrastructure layers depend on the core domain layer, but the domain has no outer dependencies. This enables clean service extraction in V3.
* **Co-located Documentation:** Co-locating documentation (ADRs, runbooks, setup guides) inside the repository ensures that it remains updated with every commit.
* **Integrated Testing Boundaries:** Prompts and AI evaluation tests are first-class citizens in the repository. Having the `ai_regression` test suite ensures that LLM behavior changes are verified in CI/CD.

### 9.2 Identified Weaknesses & Risks
* **Monolithic Build Latency:** As the frontend and backend live in the same repository, CI/CD pipeline triggers on the root repository can cause long test execution times.
* **dbt Manifest Sync Latency:** The ETL crawler depends on the dbt `manifest.json` file. If the dbt manifest isn't updated in the production sync path, the catalog database will drift.

### 9.3 Recommendations
* **Path-Scoped Workflows:** Configure GitHub Actions path filtering. API changes should trigger backend tests only. Frontend changes should trigger Next.js compilation tests only. This reduces build times.
* **Sync Verification:** In the metadata crawler use case, write a validation check that asserts `manifest.json` metadata timestamps match current Snowflake schema parameters. If drift exceeds 24 hours, generate a warning alert in Loki.
