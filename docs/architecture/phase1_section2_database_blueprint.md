# NexusBI Phase 1 Extension — Section 2: Enterprise Database Blueprint

**Date:** July 1, 2026

---

## 1. Database Topology Overview

NexusBI uses a dual-database architecture:

| Database | Role | Purpose |
|:---|:---|:---|
| **PostgreSQL 15+** | System Database (OLTP) | User accounts, workspaces, audit logs, metadata cache, vector index (pgvector), configuration |
| **Snowflake** | Customer Data Warehouse (OLAP) | Business data — never written to by NexusBI. Read-only queries under customer-managed roles. |

NexusBI **never** creates tables in Snowflake. All system data resides in PostgreSQL. Snowflake is accessed exclusively as a read-only query target.

---

## 2. Business Domains & Schema Organization

PostgreSQL schemas are organized by business domain to enforce logical separation:

```
nexusbi_db/
├── auth/           # Authentication, users, roles, permissions
├── workspace/      # Dashboards, charts, layouts, shared boards
├── catalog/        # Schema metadata cache, glossary, KPI definitions
├── ai/             # Conversation history, prompt logs, LLM cost tracking
├── audit/          # Immutable audit trail (append-only)
├── config/         # System configuration, feature flags, rate limits
└── vector/         # pgvector schema for embedding storage
```

**Justification:** Schema-level separation enables independent access control (Data Analysts can read `catalog` but not `auth`), simplifies backup/restore granularity, and prepares for V3 multi-tenancy (each tenant gets their own schema set).

---

## 3. Table Classification & Catalog

### 3.1 Fact Tables (Event-Driven, Append-Heavy)

| Table | Domain | Purpose | Grain | Expected Volume |
|:---|:---|:---|:---|:---|
| `audit.query_executions` | Audit | Every NL query executed | One row per query | 100K+ rows/month |
| `audit.llm_transactions` | Audit | Every LLM API call (tokens, cost, model) | One row per LLM call | 200K+ rows/month |
| `audit.login_events` | Audit | Every login/logout event | One row per event | 10K rows/month |
| `audit.data_access_log` | Audit | Every Snowflake table/column accessed | One row per table access | 500K+ rows/month |
| `ai.conversations` | AI | Chat conversation turns | One row per message | 50K+ rows/month |
| `ai.feedback` | AI | User feedback (thumbs up/down) per response | One row per feedback | 10K rows/month |
| `workspace.chart_interactions` | Workspace | Chart click, zoom, export events | One row per interaction | 20K rows/month |

**Design Decisions:**
- **Append-only audit tables:** `audit.*` tables have database-level triggers preventing UPDATE and DELETE operations (ADR-015). This guarantees SOC 2 audit trail integrity.
- **Partitioning strategy:** Fact tables are partitioned by month using PostgreSQL declarative partitioning (`PARTITION BY RANGE (created_at)`). Old partitions can be detached and archived independently.
- **Retention:** Active partitions retained for 90 days (conversations) to 2 years (LLM cost logs). Archived partitions moved to compressed cold storage.

### 3.2 Dimension Tables (Slowly Changing, Low Volume)

| Table | Domain | Purpose | SCD Type | Expected Volume |
|:---|:---|:---|:---|:---|
| `auth.users` | Auth | User profiles (name, email, role, department) | SCD Type 2 | <10K rows |
| `auth.roles` | Auth | Application role definitions | SCD Type 1 | <20 rows |
| `auth.permissions` | Auth | Permission definitions per role | SCD Type 1 | <100 rows |
| `auth.snowflake_role_mappings` | Auth | User-to-Snowflake role mappings | SCD Type 2 | <10K rows |
| `catalog.databases` | Catalog | Synced Snowflake database definitions | SCD Type 1 | <50 rows |
| `catalog.schemas` | Catalog | Synced Snowflake schema definitions | SCD Type 1 | <500 rows |
| `catalog.tables` | Catalog | Synced table definitions (name, row count, description) | SCD Type 2 | <5K rows |
| `catalog.columns` | Catalog | Synced column definitions (name, type, description, PII flag) | SCD Type 2 | <50K rows |
| `catalog.relationships` | Catalog | Foreign key / join relationships between tables | SCD Type 1 | <10K rows |

**Slowly Changing Dimension Strategy:**
- **SCD Type 1 (Overwrite):** Used for system reference data where history is not important (roles, permissions, schema names). Old values are overwritten.
- **SCD Type 2 (Historical):** Used for user profiles and schema metadata where change history is valuable for auditing. Rows include `valid_from`, `valid_to`, and `is_current` columns. When a user's role changes or a column description is updated, the old row is closed (`valid_to = NOW()`, `is_current = false`) and a new row is inserted.
- **Justification:** SCD Type 2 on `catalog.tables` and `catalog.columns` enables the admin to see how schema definitions evolved over time, which is critical for debugging SQL generation regressions ("This query worked last week — what changed in the schema?").

### 3.3 Reference Tables (Static, Rarely Changed)

| Table | Domain | Purpose | Expected Volume |
|:---|:---|:---|:---|
| `catalog.kpi_definitions` | Catalog | KPI catalog from Task 2 (formulas, owners, data sources) | ~30 rows |
| `catalog.business_glossary` | Catalog | Business term definitions and SQL fragments | <500 rows |
| `catalog.pii_registry` | Catalog | Columns flagged as PII with masking rules | <1K rows |
| `config.feature_flags` | Config | Feature flag states (enabled/disabled, rollout %) | <50 rows |
| `config.rate_limits` | Config | Rate limit thresholds per role | <10 rows |
| `config.error_codes` | Config | NBI-XXXX error code definitions | <50 rows |
| `auth.departments` | Auth | Department definitions for RLS scoping | <50 rows |

### 3.4 Workspace Tables (User-Generated Content)

| Table | Domain | Purpose | Expected Volume |
|:---|:---|:---|:---|
| `workspace.dashboards` | Workspace | Dashboard definitions (name, owner, shared status) | <5K rows |
| `workspace.dashboard_widgets` | Workspace | Widget positions, sizes, chart specs within dashboards | <20K rows |
| `workspace.saved_queries` | Workspace | User-saved NL queries for re-execution | <10K rows |
| `workspace.favorites` | Workspace | User-favorited dashboards and queries | <10K rows |
| `workspace.shares` | Workspace | Dashboard sharing permissions (user/team/org) | <5K rows |

### 3.5 Vector Tables (pgvector)

| Table | Domain | Purpose | Expected Volume |
|:---|:---|:---|:---|
| `vector.schema_embeddings` | Vector | Embedded schema metadata for RAG retrieval | <50K vectors |
| `vector.glossary_embeddings` | Vector | Embedded business term definitions | <1K vectors |
| `vector.kpi_embeddings` | Vector | Embedded KPI definitions | <100 vectors |
| `vector.query_pattern_embeddings` | Vector | Embedded known query patterns for semantic cache | <10K vectors |

**Vector Index Strategy:** All vector tables use HNSW indexing (`CREATE INDEX ... USING hnsw (embedding vector_cosine_ops)`). HNSW provides O(log n) approximate nearest neighbor search with >95% recall, suitable for V1 scale.

---

## 4. Relationship Map

```
auth.users ──────────────┐
    │                    │
    │ 1:N                │ 1:N
    ▼                    ▼
ai.conversations    workspace.dashboards
    │                    │
    │ 1:N                │ 1:N
    ▼                    ▼
ai.feedback         workspace.dashboard_widgets

auth.users ──── N:1 ──── auth.roles
auth.users ──── 1:1 ──── auth.snowflake_role_mappings

catalog.databases ── 1:N ── catalog.schemas
catalog.schemas ──── 1:N ── catalog.tables
catalog.tables ───── 1:N ── catalog.columns
catalog.tables ───── N:M ── catalog.relationships (self-referencing via FK)

catalog.kpi_definitions ── N:M ── catalog.tables (via kpi_table_mappings)

audit.query_executions ── N:1 ── auth.users
audit.llm_transactions ── N:1 ── audit.query_executions
audit.data_access_log ─── N:1 ── audit.query_executions
```

**Cardinality Notes:**
- A user has many conversations, dashboards, and query executions (1:N).
- A dashboard contains many widgets (1:N). Widgets reference chart specifications stored as JSONB.
- KPI definitions map to multiple tables (N:M via junction table `catalog.kpi_table_mappings`).
- Query executions cascade to LLM transactions (1:N — one query may trigger multiple LLM calls due to self-healing).

---

## 5. Data Flow Through PostgreSQL

```
[Metadata Sync]                    [User Query]
      │                                 │
      ▼                                 ▼
catalog.tables ──────────────> vector.schema_embeddings
catalog.columns                        │
catalog.relationships                  │ (RAG retrieval)
      │                                ▼
      └──────────────────────> [SQL Generation Pipeline]
                                       │
                                       ▼
                              audit.query_executions
                              audit.llm_transactions
                              audit.data_access_log
                                       │
                                       ▼
                              workspace.dashboard_widgets
                              (if user pins the chart)
```

---

## 6. Indexing Strategy

| Table | Index Type | Columns | Purpose |
|:---|:---|:---|:---|
| `auth.users` | B-tree (unique) | `email` | Fast user lookup by email |
| `auth.users` | B-tree | `role_id, is_active` | RBAC filtering |
| `ai.conversations` | B-tree | `user_id, created_at DESC` | Retrieve user's recent conversations |
| `audit.query_executions` | B-tree | `user_id, created_at DESC` | User query history |
| `audit.query_executions` | B-tree | `created_at` | Partition pruning |
| `audit.llm_transactions` | B-tree | `query_execution_id` | Join to parent query |
| `catalog.tables` | B-tree | `schema_id, is_current` | Schema browser filtering |
| `catalog.columns` | B-tree | `table_id, is_current` | Column listing per table |
| `catalog.columns` | B-tree | `is_pii` | PII column quick lookup |
| `vector.schema_embeddings` | HNSW | `embedding` | Vector similarity search |
| `workspace.dashboards` | B-tree | `owner_id, is_deleted` | User's dashboard listing |

**Justification:** Indexes are designed around the primary query patterns identified in the user journey maps (Task 3). Every index serves a specific UI screen or API endpoint. No speculative indexes — they are added only when query patterns are proven.

---

## 7. Clustering & Partition Strategy

**Partitioning:**
- All `audit.*` fact tables: Range-partitioned by `created_at` (monthly partitions).
- `ai.conversations`: Range-partitioned by `created_at` (monthly partitions).
- **Justification:** Time-range queries (e.g., "show audit logs for last 30 days") skip irrelevant partitions entirely. Old partitions can be independently archived or dropped per retention policy.

**Clustering:**
- `catalog.columns` clustered on `(table_id, is_current)`: Most queries retrieve all current columns for a specific table.
- `audit.query_executions` clustered on `(created_at)`: Most queries are time-range scans.
- **Justification:** Clustering aligns physical storage order with dominant query access patterns, reducing I/O for sequential scans.

---

## 8. Data Quality Layers

| Layer | Purpose | Implementation |
|:---|:---|:---|
| **Schema Validation** | Ensure all required fields are populated | PostgreSQL NOT NULL constraints, CHECK constraints |
| **Referential Integrity** | Ensure foreign keys are valid | PostgreSQL FOREIGN KEY constraints with ON DELETE RESTRICT |
| **Business Rule Validation** | Ensure data conforms to business logic | Application-level Pydantic validators before INSERT |
| **Audit Integrity** | Ensure audit logs cannot be tampered with | Database triggers preventing UPDATE/DELETE on audit tables |
| **Vector Consistency** | Ensure every catalog entry has a corresponding vector | Post-sync validation job comparing catalog row count to vector count |

---

## 9. Naming Conventions

| Element | Convention | Example |
|:---|:---|:---|
| Schema names | Lowercase, domain-aligned | `auth`, `catalog`, `workspace` |
| Table names | Lowercase, snake_case, plural | `users`, `query_executions`, `dashboard_widgets` |
| Column names | Lowercase, snake_case | `created_at`, `user_id`, `is_active` |
| Primary keys | `id` (UUID v4) | `id UUID DEFAULT gen_random_uuid()` |
| Foreign keys | `{referenced_table_singular}_id` | `user_id`, `dashboard_id`, `table_id` |
| Timestamps | `created_at`, `updated_at` | UTC timezone, auto-populated |
| Booleans | `is_` or `has_` prefix | `is_active`, `is_pii`, `has_description` |
| JSONB columns | Descriptive noun | `chart_spec`, `filter_config`, `prompt_context` |
| Indexes | `idx_{table}_{columns}` | `idx_users_email`, `idx_conversations_user_created` |
| SCD columns | `valid_from`, `valid_to`, `is_current` | Standard SCD Type 2 pattern |

---

## 10. Migration & Versioning Strategy

- **Migration Tool:** Alembic (SQLAlchemy's migration framework).
- **Versioning:** Every schema change generates a numbered migration file in `backend/alembic/versions/`.
- **Forward-Only Migrations:** Migrations must be forward-compatible. Destructive changes (column drops, type changes) require a two-phase migration: (1) add new column, (2) migrate data, (3) drop old column in next release.
- **Migration Testing:** Every migration is tested against a copy of production schema before deployment. CI pipeline runs migrations against a clean database and a populated test database.
- **Rollback Strategy:** Every migration includes a `downgrade()` function. Rollback is tested in CI but used only as emergency procedure in production.
