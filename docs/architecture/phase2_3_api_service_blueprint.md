# NexusBI Phase 2.3: Enterprise API & Service Blueprint

**Document Version:** 1.0.0  
**Status:** Approved for Implementation  
**Author:** Principal Backend Architect & AI Platform Architect  
**Target Architecture:** V1 (Modular Monolith) with V2/V3 Service Separation Boundaries  

---

## 1. Service Architecture

In alignment with ADR-001 (Modular Monolith), services are implemented as decoupled, logical packages inside the `backend/app/` repository directory. Each service represents a bounded context with zero circular imports.

```text
                        ┌───────────────────────────┐
                        │        API Gateway        │
                        └─────────────┬─────────────┘
                                      │ HTTP / WS
                                      ▼
                        ┌───────────────────────────┐
                        │    Orchestration Engine   │
                        └──────┬─────────────┬──────┘
                               │             │
              ┌────────────────┘             └────────────────┐
              ▼                                               ▼
┌───────────────────────────┐                   ┌───────────────────────────┐
│     AI Query Service      │                   │     Analytics Service     │
│  - Intent routing         │                   │  - Prophet forecasting    │
│  - SQL generation         │                   │  - Anomaly detection      │
│  - Self-healing loop      │                   │  - Statistical aggregates │
└─────────────┬─────────────┘                   └─────────────┬─────────────┘
              │                                               │
              └────────────────┐             ┌────────────────┘
                               ▼             ▼
                        ┌───────────────────────────┐
                        │    Infrastructure Core    │
                        │  - Postgres Metadata      │
                        │  - Snowflake Pooler       │
                        │  - Redis Memory Cache     │
                        └───────────────────────────┘
```

### 1.1 Authentication & User Service
* **Responsibility:** Manages OIDC state exchanges, JWT creation, user validation, and role-based permissions (RBAC).
* **Boundaries:** Does not contain database access drivers for Snowflake. Interfaces exclusively with PostgreSQL database for user settings storage.

### 1.2 AI Query Service
* **Responsibility:** Handles intent parsing, metadata vector search queries, Claude 3.5 prompt construction, and SQL syntax healing loops.
* **Boundaries:** Does not execute query plans against Snowflake directly. It compiles clean SQL text and hands it over to the Metadata/Snowflake Service.

### 1.3 Analytics & Forecasting Service
* **Responsibility:** Orchestrates statistical analysis, Facebook Prophet time-series calculations, and anomaly detection loops.
* **Boundaries:** Operates only on formatted aggregate datasets; does not interface with LLMs or run direct natural language parsing.

### 1.4 Database & Metadata Service
* **Responsibility:** Governs PostgreSQL pgvector schema metadata indexes, database connection pooling, user activity audit logs, and direct read-only query dispatch to Snowflake.
* **Boundaries:** Has zero knowledge of chat session states or user settings variables.

### 1.5 Dashboard & Report Service
* **Responsibility:** Stores and retrieves user-pinned dashboard layouts, widget positions, and manages CSV/PNG export generation.
* **Boundaries:** Relies on the Database Service to retrieve underlying widget datasets.

### 1.6 Notification & Alert Service
* **Responsibility:** Tracks anomaly notifications, dashboard shares, and system alerts. Houses notification queues and dispatch rules.
* **Boundaries:** Relies on the Analytics Service to trigger metric alert violations.

---

## 2. API Inventory

All API endpoints follow URL path versioning prefixed with `/api/v1/`.

### 2.1 Chat Service API

#### `WS /api/v1/chat/ws`
* **Purpose:** Bidirectional channel for real-time natural language query parsing and chart streaming.
* **Consumer:** React SPA ChatPanel.
* **Authentication:** JWT query parameter (`?token=jwt_string`) verified on connection.
* **Authorization:** Requires role permission `allow_chat`.
* **Request Schema (Client JSON):**
  ```json
  {
    "type": "query",
    "conversation_id": "UUID",
    "text": "String (Max 2,000 characters)",
    "filters": {
      "time_range": "String (e.g., 'last_365_days')",
      "dimensions": {}
    }
  }
  ```
* **Response Schema (Server Streaming JSON):**
  ```json
  {
    "type": "result",
    "payload": {
      "sql": "String",
      "chart_spec": {
        "type": "String (e.g., 'bar')",
        "options": {}
      },
      "data": [],
      "summary": "String",
      "insights": [],
      "recommendations": []
    },
    "meta": {
      "duration_ms": 2345,
      "cached": false
    }
  }
  ```
* **Validation Rules:** Query text cannot be empty or exceed 2,000 characters. Semicolons in inputs are rejected to prevent SQL injection attempts.
* **Error Responses:** Sends error payload over WebSocket with code `NBI-2001` (LLM timeout) or `NBI-3001` (Snowflake execution error).
* **Rate Limiting:** 30 messages/minute per user.
* **Caching Strategy:** No caching at the WebSocket connection layer; results are cached downstream in the SQL Gen use case.
* **Expected Performance:** p95 latency < 8 seconds (including LLM generation and Snowflake execution).

---

### 2.2 Analytics Service API

#### `POST /api/v1/analytics/forecast`
* **Purpose:** Run statistical time-series forecasting against historical values.
* **Consumer:** Next.js UI Chart components.
* **Authentication:** Bearer JWT in header.
* **Authorization:** Requires role permission `allow_forecast`.
* **Request Schema:**
  ```json
  {
    "metric": "String (e.g., 'gross_revenue')",
    "granularity": "String ('daily' | 'weekly' | 'monthly')",
    "horizon": 6,
    "historical_data": [
      { "date": "YYYY-MM-DD", "value": 1234.56 }
    ]
  }
  ```
* **Response Schema:**
  ```json
  {
    "data": {
      "historical": [{ "date": "YYYY-MM-DD", "value": 1234.56 }],
      "forecast": [{ "date": "YYYY-MM-DD", "value": 1300.00, "upper": 1350.00, "lower": 1250.00 }]
    },
    "meta": {
      "model": "prophet",
      "mape": 0.04
    }
  }
  ```
* **Validation Rules:** Historical data must contain a minimum of 12 data points. Horizon must not exceed 24 intervals.
* **Error Responses:** `400 Bad Request` (Insufficient data), `422 Unprocessable Entity` (Formatting errors).
* **Caching Strategy:** Cache results in Redis for 1 hour, keyed by the hash of the request payload.

---

### 2.3 Dashboard Service API

#### `GET /api/v1/dashboards`
* **Purpose:** Retrieve list of dashboards accessible to the user.
* **Authentication:** Bearer JWT in header.
* **Response Schema:**
  ```json
  {
    "dashboards": [
      {
        "id": "UUID",
        "name": "String",
        "owner_id": "UUID",
        "widget_count": 5,
        "updated_at": "ISO8601"
      }
    ]
  }
  ```
* **Caching Strategy:** Client-side caching via RTK Query. Server-side database queries cache-invalidated on dashboard updates.

#### `PUT /api/v1/dashboards/{id}/widgets`
* **Purpose:** Update the structural layout and pinned charts on a dashboard.
* **Request Schema:**
  ```json
  {
    "widgets": [
      {
        "id": "UUID",
        "position": { "x": 0, "y": 0, "w": 4, "h": 3 },
        "chart_spec": {}
      }
    ]
  }
  ```
* **Idempotency:** Employs standard REST semantics. Repeated PUT updates are idempotent.

---

## 3. Request Lifecycles

This section details the step-by-step processing paths for core platform interactions.

```text
[ User Prompt ]
      │
      ▼
1. API Gateway ─────────> Authenticate JWT & Resolve Snowflake Role
      │
      ▼
2. Intent Router ───────> Classify: Query vs Dashboard vs Forecast
      │
      ▼
3. Semantic Retrieval ──> Fetch Tables, Columns & KPIs from pgvector
      │
      ▼
4. SQL Compiler ────────> Inject Context & Generate Snowflake SQL
      │
      ▼
5. SQL Validator ───────> Parse AST (Enforce SELECT & LIMIT 50,000)
      │
      ▼
6. Snowflake Execution ─> Run query, fetch rows, stream results
      │
      ▼
7. Post-Processing ─────> Generate Summary, Insights & ECharts JSON
      │
      ▼
[ Client Browser ]
```

### 3.1 Natural Language Query to Chart Rendering
1. **API Gateway (FastAPI):** Receives WebSocket connection. Validates JWT, extracts the user's role (e.g., `finance_manager`), and maps it to the target Snowflake role (`FINANCE_READER`).
2. **Intent Router (LLM):** Classifies input. If user asks "Show me quarterly sales by region," intent is routed to the SQL Gen service.
3. **Semantic Retrieval (pgvector):** Searches the local PostgreSQL vector index to find schema context (e.g., tables `fct_orders`, `dim_customers`) matching "sales" and "region".
4. **SQL Compiler (LLM):** Injects schema metadata into the system prompt. Claude 3.5 compiles optimized Snowflake SQL.
5. **SQL Validator (SQLGlot):** Parses the generated SQL into an AST. Enforces: (1) only SELECT statements allowed, (2) injection of `LIMIT 50000`, (3) validates join conditions.
6. **Snowflake Execution (Snowflake Driver):** Checks the Redis semantic query cache. On a cache miss, it sends the query to Snowflake under the `FINANCE_READER` connection pool.
7. **Post-Processing (LLM):** Passes retrieved rows to Claude 3 Haiku to generate a business summary and select the best visualization layout (e.g., stacked bar chart).
8. **Response Streaming (WebSocket):** Sends the ECharts spec and raw rows back to the frontend to render the chart.

---

## 4. Service Communication

```text
                    [ API Request ]
                           │
                           ▼
             ┌───────────────────────────┐
             │       FastAPI API         │
             └─────────────┬─────────────┘
                           │
             ┌─────────────┴─────────────┐
      Sync   │                    Async  │ (FastAPI BackgroundTasks)
             ▼                           ▼
┌───────────────────────────┐     ┌───────────────────────────┐
│     Snowflake Query       │     │    Metadata Sync Job      │
│  (30s Timeout, Retry x1)  │     │  (Run in background)      │
└───────────────────────────┘     └───────────────────────────┘
```

* **Synchronous Communication:** Direct API client requests (e.g., fetching dashboard metadata, running quick analytical queries) run synchronously over HTTPS.
* **Asynchronous Background Processing:** Heavy operations, such as daily database schema crawler synchronization and email report generation, run in the background using FastAPI `BackgroundTasks`.
* **Timeout Policies:**
  * Snowflake query execution: **30 seconds**.
  * LLM API generation call: **15 seconds**.
  * Internal Postgres queries: **5 seconds**.
* **Retry Strategies:**
  * Snowflake queries: 1 automatic retry on connection failures.
  * LLM API requests: 2 automatic retries using exponential backoff (starting at 1 second) on HTTP 503 errors.
* **Circuit Breaker Policy:**
  * If the primary LLM provider (Anthropic) fails 5 consecutive times within a 3-minute window, the circuit breaker trips. The system automatically routes SQL generation queries to the secondary provider (OpenAI) and alerts the SRE team.

---

## 5. Error Handling Blueprint

All REST endpoints and WebSocket channels return a standardized error response envelope.

### 5.1 Error Payload Schema
```json
{
  "status": "error",
  "error": {
    "code": "NBI-XXXX",
    "message": "Friendly user-facing warning message",
    "detail": "Debugging context details for developer troubleshooting",
    "timestamp": "ISO8601"
  }
}
```

### 5.2 Error Code Registry

| Code | HTTP Status | Category | Description |
|:---|:---|:---|:---|
| **NBI-1001** | `400 Bad Request` | Validation | Request validation failed (missing parameters or bad formatting). |
| **NBI-1002** | `401 Unauthorized` | Security | JWT authentication failed or token has expired. |
| **NBI-1003** | `403 Forbidden` | Security | User does not have permission to access the requested resource. |
| **NBI-2001** | `504 Gateway Timeout` | AI Platform | Primary and fallback LLM services failed to respond within limits. |
| **NBI-2002** | `422 Unprocessable` | AI Platform | Generated SQL failed AST security validation checks. |
| **NBI-3001** | `500 Server Error` | Warehouse | Snowflake execution failed due to SQL syntax or database errors. |
| **NBI-3002** | `504 Gateway Timeout` | Warehouse | Snowflake query timed out before execution completed. |

---

## 6. API Security

* **JWT Authentication:** Tokens are signed using asymmetric RS256 algorithms. Private keys reside securely in the corporate identity provider (Okta/Auth0), and public keys are cached locally by NexusBI to verify incoming request signatures.
* **SSO & OAuth:** User registration and authentication are delegated entirely to corporate OIDC/SSO endpoints. NexusBI does not store passwords.
* **Role-Based Access Control (RBAC):** Users are assigned to application roles (CEO, Business Analyst, Data Analyst, Admin). These roles are mapped to specific database reading scopes (RLS) and API endpoint permissions.
* **Prompt Injection Protection:** The input sanitization layer strips out system override commands (e.g., "ignore previous instructions") before sending prompts to the LLM.
* **SQL Injection Protection:** Enforced by: (1) read-only Snowflake credentials, (2) AST parsing to block destructive statements like `DROP` or `DELETE`, (3) injecting a strict limit of 50,000 rows on all queries.

---

## 7. Observability

```text
[ Incoming Request ] ── (Assigns Trace ID: tx_8923a)
       │
       ├─> Log: "User 123 initiated query" (loki-config)
       ├─> Trace: app/api -> compile_sql -> execute_query (Prometheus)
       ▼
[ Snowflake Query ] ── (Injects tag: query_tag="tx_8923a")
```

### 7.1 Distributed Tracing
* **Trace ID Propagation:** Every request receives a unique `trace_id` header (`x-trace-id`) at the API Gateway. This ID is passed to all downstream operations, including database queries, and is injected into Snowflake query tags using `query_tag`.
* **System Metrics (Prometheus):** Tracks request latency (p50, p95, p99), active WebSocket connections, cache hit ratios, and API error rates.
* **Log Aggregation (Loki):** Consolidates logs from all containers. Logs are formatted as structured JSON containing `trace_id`, `user_id`, and `duration_ms`.
* **Audit Trails:** Logs every Snowflake query, including the user who initiated it, the tables accessed, and the row count returned, keeping the platform compliant with SOC 2 audit requirements.

---

## 8. API Versioning Strategy

### 8.1 Path-Based Versioning
* All APIs are versioned via the URL path (e.g., `/api/v1/`).
* **V1:** Represents the current production endpoint.
* **V2:** Used for testing breaking changes or introducing new request schemas.

### 8.2 Backward Compatibility
* Non-breaking changes (adding optional fields, adding new endpoints) do not increment the major version.
* Breaking changes (removing fields, changing data types) are deployed on a new path (e.g., `/api/v2/`). The older version remains active during the deprecation window.

### 8.3 Deprecation Policy
* When a newer API version is released, the older version is marked as deprecated.
* Deprecated responses include the HTTP `Sunset` header, indicating when the endpoint will be decommissioned (minimum 90-day notice).
* Automated system reports track usage on deprecated endpoints to help transition remaining clients.

---

## 9. Final Architecture Review

### 9.1 Strengths
* **Decoupled Monolith Layout:** Enables clean code organization. Modules are decoupled by design, making it easy to split them into independent microservices in the future.
* **Layered Security Validation:** Protects Snowflake data by combining OIDC login validation, AST parsing, and read-only connection limits.
* **Standardized Errors:** Simplifies troubleshooting for both frontend developers and system administrators.

### 9.2 Weaknesses & Risks
* **WebSocket Connection Drops:** Temporary network disruptions can disconnect WebSocket sessions, interrupting long-running queries.
* **LLM Vendor Dependency:** The SQL generation pipeline relies heavily on the Anthropic API. Outages or changes in model behavior present operational risks.

### 9.3 Recommendations
* **WebSocket Message Queuing:** Implement client-side message buffering to automatically resubmit query requests if the WebSocket connection drops during processing.
* **LLM Regression Testing:** Run automated SQL generation tests on new model versions before updating production API keys, ensuring prompt behaviors remain consistent.
