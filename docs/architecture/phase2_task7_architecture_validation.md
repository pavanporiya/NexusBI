# NexusBI Phase 2 — Task 7: Architecture Validation & Design Review

**Document Version:** 2.0.0  
**Review Type:** Principal Architect Pre-Development Design Validation  
**Date:** July 1, 2026

---

## 1. Design Review Summary

This document represents the final architecture validation checkpoint before development begins. It consolidates all findings from Tasks 1-6 into actionable architectural recommendations organized by engineering discipline.

---

## 2. Maintainability Recommendations

### M-1: Enforce Modular Monolith Boundaries with Python Packages
- **Recommendation:** Structure the FastAPI application as a Python package hierarchy that enforces domain boundaries at the import level. Each domain module (auth, chat, sql_gen, analytics, forecast, admin) is a self-contained package with its own `models.py`, `services.py`, `routes.py`, and `interfaces.py`. Cross-domain imports are only allowed through explicitly defined interfaces.
- **Justification:** When V3 requires microservice extraction, clean package boundaries enable splitting a module into its own service by extracting the package, replacing interface implementations with RPC/HTTP calls, and deploying independently. Without these boundaries, the monolith becomes a "distributed monolith" that is worse than either pattern.

### M-2: Define a Strict Dependency Inversion Rule
- **Recommendation:** The Domain layer (`app/domain/`) must have ZERO imports from Infrastructure (`app/infrastructure/`), API (`app/api/`), or external libraries (Snowflake connector, LLM SDKs, Redis). All external dependencies are accessed through abstract interfaces defined in the Domain layer and implemented in Infrastructure.
- **Justification:** This enables unit testing of business logic without database connections or API mocks. It also enables swapping infrastructure components (e.g., replacing pgvector with Qdrant in V3) without touching business logic.

### M-3: Implement Feature Flags from Day One
- **Recommendation:** Use a simple feature flag system (configuration-based, not a third-party service) to gate experimental features, model changes, and rollout percentages.
- **Justification:** Feature flags enable safe deployment of new capabilities (e.g., a new chart type, a different LLM model) to a subset of users without code deployment. Critical for AI systems where model behavior changes require gradual rollout and monitoring.

### M-4: Standardize Error Handling with a Domain Exception Hierarchy
- **Recommendation:** Define a base `NexusBIError` exception class with subclasses for each error category (from Task 1, Finding 11): `SchemaNotFoundError`, `SQLCompilationError`, `SnowflakeTimeoutError`, `PermissionDeniedError`, `RateLimitError`, `ResultSetTooLargeError`. Each exception carries an error code (NBI-XXXX), user-facing message, and internal debug context.
- **Justification:** Standardized exceptions ensure consistent error responses across all endpoints, simplify logging/monitoring, and provide clear developer guidance on how to handle each error type.

---

## 3. Scalability Recommendations

### SC-1: Design the Query Cache as a First-Class Subsystem
- **Recommendation:** The semantic query cache should not be a simple key-value TTL store. Design it as a subsystem with: (1) semantic hash computation (normalize synonyms, ignore word order), (2) parameterized cache keys (same question + different date range = different cache entry), (3) cache invalidation hooks triggered by metadata sync (when schemas change, invalidate affected cache entries), (4) cache hit/miss metrics exposed via health endpoint.
- **Justification:** A well-designed cache can reduce LLM API costs by 30-50% and Snowflake compute costs by 15-20%. These savings directly impact unit economics and are essential for profitability at scale.

### SC-2: Implement Connection Pool Monitoring
- **Recommendation:** The Snowflake connection pool must expose metrics: active connections, idle connections, wait queue depth, connection creation rate, and average query execution time per pool. These metrics must be accessible via a health check endpoint and logged to PostgreSQL for trend analysis.
- **Justification:** Connection pool exhaustion is a common cause of production incidents in database-backed applications. Early detection of pool saturation (via monitoring) prevents cascading failures.

### SC-3: Design WebSocket State for Horizontal Scaling
- **Recommendation:** Even in V1 (single server), design WebSocket session state to be stored externally in Redis rather than in-process memory. This means: (1) WebSocket connection registry in Redis, (2) message delivery via Redis pub/sub, (3) stateless WebSocket handler that can be load-balanced in V2+.
- **Justification:** Retrofitting WebSocket state externalization is extremely painful after launch. Building it correctly from day one (at minimal additional cost) eliminates a major scaling obstacle later.

---

## 4. Observability Recommendations

### OB-1: Implement Structured Logging from Day One
- **Recommendation:** All log entries must be structured JSON (not free-text). Every log entry includes: `timestamp`, `level`, `service`, `trace_id`, `user_id`, `action`, `duration_ms`, `error` (if applicable). Use Python's `structlog` library for zero-effort structured logging.
- **Justification:** Structured logs are searchable, filterable, and aggregatable. Free-text logs require regex parsing and are effectively useless at scale. Starting with structured logging avoids a painful migration later.

### OB-2: Define SLIs, SLOs, and Error Budgets
- **Recommendation:** Define Service Level Indicators and Objectives for V1:

| SLI | SLO (V1) | Measurement |
|:---|:---|:---|
| API availability | 99.5% monthly | Uptime checks every 60 seconds |
| Query response latency (p95) | < 8 seconds (including Snowflake) | Measured from WebSocket message received to response sent |
| NexusBI overhead latency (p95) | < 3 seconds (excluding Snowflake) | Measured from WebSocket message received to Snowflake query dispatch |
| SQL generation accuracy | > 90% (first attempt) | Tracked via user feedback (thumbs up/down) |
| LLM API error rate | < 2% | Tracked via LLM provider response codes |

- **Justification:** Without defined SLOs, there is no objective way to measure system health or make trade-off decisions between reliability and feature velocity. SLOs also set customer expectations accurately.

### OB-3: Implement an AI-Specific Observability Dashboard
- **Recommendation:** Beyond standard application metrics, create a dedicated AI observability view tracking: (1) LLM call success/failure rates by model, (2) average tokens per query (input, output, total), (3) daily LLM cost (aggregated and per-user), (4) semantic cache hit ratio, (5) self-healing trigger rate (how often the SQL correction loop activates), (6) SQL generation accuracy (based on user feedback).
- **Justification:** AI systems have unique failure modes (hallucination, prompt injection, cost spikes) that are invisible to standard APM tools. Dedicated AI observability enables early detection of model degradation and cost anomalies.

---

## 5. Security Recommendations

### SEC-1: Implement Content Security Policy (CSP) Headers
- **Recommendation:** The frontend must serve strict CSP headers preventing: inline scripts, external script loading (except from approved CDNs for ECharts), iframe embedding (clickjacking prevention), and form action to external URLs.
- **Justification:** CSP is a critical defense against XSS attacks. Enterprise security teams will reject applications without CSP headers during security review.

### SEC-2: Implement Audit Log Tamper Protection
- **Recommendation:** Audit logs in PostgreSQL must be append-only. No application-level user (including Admin) should have DELETE or UPDATE permissions on audit tables. Implement a database trigger that rejects any non-INSERT operations on audit tables.
- **Justification:** SOC 2 auditors require evidence that audit logs cannot be tampered with. Append-only enforcement provides this guarantee at the database level.

### SEC-3: Implement Request Signing for Internal APIs
- **Recommendation:** If V2+ introduces inter-service communication (e.g., API server calling forecasting service), implement HMAC request signing to prevent unauthorized internal API calls.
- **Justification:** In a microservice architecture, internal APIs are attack surfaces. Without request signing, a compromised container can impersonate other services.

### SEC-4: Conduct LLM Red-Team Testing Before Launch
- **Recommendation:** Before V1 launch, conduct a structured adversarial testing session where the security team attempts: (1) prompt injection to exfiltrate system prompts, (2) SQL injection via crafted natural language, (3) privilege escalation via role manipulation in prompts, (4) data exfiltration by requesting unauthorized tables. Document all findings and patch before GA.
- **Justification:** AI systems have novel attack surfaces that traditional penetration testing does not cover. Red-team testing specific to LLM vulnerabilities is essential for enterprise security certification.

---

## 6. Developer Experience Recommendations

### DX-1: Create a Local Development Environment Specification
- **Recommendation:** Document a complete local development setup that runs entirely on a developer's laptop: Docker Compose with PostgreSQL (+ pgvector), Redis, and a mock Snowflake service (or a shared dev Snowflake account). Include seed scripts that populate the database with sample schema metadata and test user accounts.
- **Justification:** If developers cannot run the full system locally in <10 minutes, development velocity suffers dramatically. A well-documented local setup is the single highest-ROI investment for developer productivity.

### DX-2: Implement a Mock LLM Mode for Development
- **Recommendation:** Create a "mock LLM" mode that returns pre-configured SQL responses for known test queries. This eliminates LLM API costs during development and enables deterministic unit/integration testing.
- **Justification:** Developers should not need an Anthropic API key to work on frontend features, database schema changes, or authentication flows. Mock mode decouples AI development from everything else.

### DX-3: Define API Contract First with OpenAPI Specifications
- **Recommendation:** Before writing any backend route handler, define the complete API contract using OpenAPI 3.1 specifications. FastAPI generates these automatically from Pydantic models, but the models should be designed first (input schemas, output schemas, error schemas) and reviewed before implementation begins.
- **Justification:** API-first development enables frontend and backend teams to work in parallel. The frontend team can build against the OpenAPI spec using mock servers while the backend team implements the actual logic.

### DX-4: Establish Code Review Standards for AI Components
- **Recommendation:** Any change to: (1) system prompts, (2) prompt construction logic, (3) LLM model selection, (4) SQL validation rules, or (5) semantic cache logic must require review by at least two engineers, one of whom is a senior/staff engineer. These components are the highest-risk parts of the system.
- **Justification:** A single-character change in a system prompt can fundamentally alter SQL generation behavior. These components require higher review scrutiny than standard CRUD endpoints.

---

## 7. Long-Term Evolution Recommendations

### EV-1: Build the Semantic Layer as an Independent Data Product
- **Recommendation:** The KPI catalog, business glossary, and schema metadata should be designed as an independent data product that can be consumed by systems beyond NexusBI (e.g., data quality tools, dbt documentation, data governance platforms). Expose a read-only API for the semantic catalog.
- **Justification:** The semantic layer is the most valuable intellectual property NexusBI creates. Making it a standalone data product increases the platform's strategic value and creates integration opportunities.

### EV-2: Plan for Multi-Modal Input (V3+)
- **Recommendation:** Design the intent classification and chat interfaces with awareness that future versions may accept: (1) voice input (speech-to-text → NL query), (2) image input (screenshot of a chart with "explain this"), (3) file upload (CSV with "analyze this data"). The input pipeline should have a clear abstraction point where raw input is normalized to a text query before entering the AI pipeline.
- **Justification:** Multi-modal AI is the clear industry direction. Designing the abstraction boundary now avoids a major refactoring effort when multi-modal features are added.

### EV-3: Design for Embedded Analytics (V3+)
- **Recommendation:** Design the visualization and dashboard components to be embeddable in external applications via iframe or Web Components. This enables enterprise customers to embed NexusBI charts directly into their internal portals, CRMs, or operational dashboards.
- **Justification:** Embedded analytics is a major revenue multiplier. Customers who embed NexusBI into their workflows have significantly higher retention rates because switching costs increase.

### EV-4: Establish a Model Evaluation Framework
- **Recommendation:** Build a regression test framework that can evaluate SQL generation accuracy across different LLM models and prompt strategies. The framework should: (1) maintain a dataset of 200+ validated (question, expected SQL, expected result) triples, (2) automatically run the dataset against new models/prompts, (3) report accuracy metrics (exact match, execution match, semantic match), (4) flag regressions before deployment.
- **Justification:** The LLM landscape evolves rapidly. New models are released quarterly. Without an evaluation framework, model upgrades are based on vibes rather than data. This framework is the foundation for continuous AI quality improvement.

---

## 8. Architecture Decision Records (ADRs) — Required Before Development

The following architectural decisions must be formally documented as ADRs before the first line of code is written:

| ADR # | Decision | Status |
|:---|:---|:---|
| ADR-001 | V1 deploys as a modular monolith on Docker Compose, not Kubernetes | **Approved (Task 1)** |
| ADR-002 | pgvector replaces Qdrant for V1 vector search | **Approved (Task 1)** |
| ADR-003 | Single Redis instance replaces Redis Cluster for V1 | **Approved (Task 1)** |
| ADR-004 | ECharts is the sole visualization library for V1 | **Approved (Task 1)** |
| ADR-005 | LangGraph is the sole AI orchestration framework for V1 | **Approved (Task 1)** |
| ADR-006 | Single-tenant deployment model for V1 | **Approved (Task 1)** |
| ADR-007 | API versioning uses URL path strategy (/api/v1/) | **Approved (Task 1)** |
| ADR-008 | Data retention policies (90-day chat, 1-year audit) | **Approved (Task 1)** |
| ADR-009 | Rate limiting tiers (30/min/user, 500/day/user) | **Approved (Task 1)** |
| ADR-010 | Snowflake connection pooling strategy (per-role pools) | **Approved (Task 1)** |
| ADR-011 | KPI formulas are injected from catalog, not LLM knowledge | **Approved (Task 2)** |
| ADR-012 | Error taxonomy with NBI-XXXX error codes | **Approved (Task 1)** |
| ADR-013 | Feature flags for AI model rollouts | **Approved (Task 7)** |
| ADR-014 | Structured JSON logging with structlog | **Approved (Task 7)** |
| ADR-015 | Append-only audit tables with database-level protection | **Approved (Task 7)** |

---

## 9. Pre-Development Checklist

Before writing the first line of code, the following items must be completed:

- [ ] All 15 ADRs documented and signed off by tech lead
- [ ] OpenAPI 3.1 specification for all V1 endpoints defined and reviewed
- [ ] Local development environment Docker Compose file created and tested
- [ ] Snowflake dev/staging account provisioned with sample data
- [ ] OIDC test identity provider configured (Auth0 free tier or Keycloak local)
- [ ] Mock LLM response fixtures created for 20 standard test queries
- [ ] KPI catalog (Task 2) loaded into seed data for PostgreSQL
- [ ] CI/CD pipeline configured (lint, test, build, deploy to staging)
- [ ] Error code registry (NBI-1001 through NBI-1007) documented in developer wiki
- [ ] Security threat model reviewed with at least one security engineer
- [ ] SLI/SLO definitions reviewed and agreed upon by product and engineering leads

---

## 10. Final Architectural Verdict

**The NexusBI architecture, as revised through this Phase 2 review, is approved for development with the following conditions:**

1. **V1 scope must be strictly enforced.** Any feature creep toward V2/V3 technologies (Kubernetes, Qdrant, Celery, multi-region) must be rejected during sprint planning.
2. **The AI Decision Pipeline (Task 4) is the product's core competitive advantage.** It must receive disproportionate engineering investment (60% of backend effort) in V1.
3. **The KPI Catalog (Task 2) is the product's moat.** It must be populated with customer-specific definitions during every onboarding engagement.
4. **Observability is not optional.** Structured logging, AI metrics tracking, and cost monitoring must ship in V1, not deferred.
5. **Security red-team testing must occur before the first customer pilot.**

The architecture is implementation-ready. Proceed to development.
