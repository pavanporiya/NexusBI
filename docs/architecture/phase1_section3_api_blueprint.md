# NexusBI Phase 1 Extension — Section 3: Enterprise API Blueprint

**Date:** July 1, 2026

---

## 1. API Design Principles

- **URL Path Versioning:** All endpoints prefixed with `/api/v1/`.
- **RESTful for CRUD, WebSocket for Streaming:** Dashboard and admin operations use REST. Chat uses WebSocket for real-time streaming.
- **JSON:API Response Envelope:** All responses wrapped in `{ "data": ..., "meta": ..., "errors": ... }`.
- **Idempotency:** All POST endpoints that create resources accept an `Idempotency-Key` header to prevent duplicate creation on network retries.
- **Pagination:** All list endpoints support cursor-based pagination via `?cursor=<opaque_token>&limit=25`.

---

## 2. Global API Policies

| Policy | Specification |
|:---|:---|
| **Authentication** | Bearer JWT in `Authorization` header (REST) or connection query param (WebSocket). Validated against OIDC provider public keys. |
| **Rate Limiting** | Per-user: 30 req/min, 500 req/day. Per-org: 200 req/min. Returns HTTP 429 with `Retry-After` header. |
| **Request Size** | Maximum 1 MB request body. Maximum 2,000 character NL query input. |
| **Timeouts** | API gateway: 30 seconds. Snowflake query: 30 seconds. LLM call: 15 seconds. |
| **Structured Logging** | Every request logged: `trace_id`, `user_id`, `method`, `path`, `status`, `duration_ms`. |
| **Error Format** | `{ "errors": [{ "code": "NBI-1002", "message": "...", "detail": "..." }] }` |

---

## 3. API Endpoint Catalog

### 3.1 Authentication API

#### `POST /api/v1/auth/callback`
- **Purpose:** Exchange OIDC authorization code for application JWT tokens.
- **Consumer:** Frontend (after SSO redirect).
- **Authentication:** None (this IS the authentication endpoint).
- **Authorization:** None.
- **Request Model:** `{ "code": "string", "redirect_uri": "string", "state": "string" }`
- **Response Model:** `{ "access_token": "jwt_string", "refresh_token": "jwt_string", "expires_in": 3600, "user": { "id", "email", "name", "role", "department" } }`
- **Validation:** Code must be valid and unexpired. State parameter must match session state (CSRF protection).
- **Rate Limiting:** 10 req/min per IP (brute force protection).
- **Error Responses:** `401 Invalid Code`, `403 User Disabled`, `429 Rate Limited`.
- **Idempotency:** Not applicable (code is single-use).

#### `POST /api/v1/auth/refresh`
- **Purpose:** Exchange refresh token for new access token.
- **Consumer:** Frontend (automatic token refresh).
- **Authentication:** Refresh token in HTTP-only cookie.
- **Request Model:** Empty body (token in cookie).
- **Response Model:** `{ "access_token": "jwt_string", "expires_in": 3600 }`
- **Error Responses:** `401 Invalid/Expired Refresh Token`.

#### `POST /api/v1/auth/logout`
- **Purpose:** Invalidate current session and tokens.
- **Consumer:** Frontend logout button.
- **Authentication:** Bearer JWT.
- **Response Model:** `{ "data": { "message": "Logged out successfully" } }`
- **Logging:** Login event recorded in `audit.login_events`.

---

### 3.2 Chat API (WebSocket)

#### `WS /api/v1/chat/ws`
- **Purpose:** Persistent bidirectional connection for conversational AI interactions.
- **Consumer:** Frontend ChatPanel component.
- **Authentication:** JWT passed as query parameter during WebSocket handshake. Validated on connection open.
- **Authorization:** User must have `ask_queries` permission.
- **Client → Server Message Model:** `{ "type": "query", "conversation_id": "uuid", "text": "string", "filters": {} }`
- **Server → Client Message Model (streaming):**
  - Progress: `{ "type": "progress", "stage": "generating_sql", "message": "Finding relevant tables..." }`
  - Result: `{ "type": "result", "chart_spec": {}, "data": [], "summary": "string", "insights": [], "recommendations": [], "sql": "string", "meta": { "execution_time_ms", "token_cost", "query_id" } }`
  - Error: `{ "type": "error", "code": "NBI-1002", "message": "string" }`
  - Clarification: `{ "type": "clarification", "question": "string", "options": ["option1", "option2"] }`
- **Validation:** Text length ≤ 2,000 characters. conversation_id must be valid UUID owned by the user.
- **Rate Limiting:** 30 messages/min per user. If exceeded, server sends error message and pauses for 60 seconds.
- **Retry Strategy:** Client reconnects with exponential backoff (1s, 2s, 4s, max 30s). Buffered responses served from Redis on reconnection.
- **Observability:** Every message exchange logged with `trace_id`, `conversation_id`, pipeline stage durations.

---

### 3.3 Query API (REST Fallback)

#### `POST /api/v1/query/execute`
- **Purpose:** Synchronous NL-to-SQL execution for non-WebSocket clients or simple integrations.
- **Consumer:** API integrations, mobile clients (future), automated testing.
- **Authentication:** Bearer JWT.
- **Authorization:** User must have `ask_queries` permission. Snowflake role enforcement applied.
- **Request Model:** `{ "text": "string", "conversation_id": "uuid (optional)", "filters": { "date_range": {}, "dimensions": {} } }`
- **Response Model:** `{ "data": { "chart_spec": {}, "rows": [], "columns": [], "summary": "string", "insights": [], "recommendations": [], "sql": "string" }, "meta": { "execution_time_ms", "snowflake_query_id", "token_cost", "cache_hit": boolean } }`
- **Validation:** Text required, max 2,000 chars. Filters must reference valid dimensions.
- **Rate Limiting:** Standard per-user limits.
- **Error Responses:** `400 Invalid Input`, `401 Unauthorized`, `403 Forbidden (Snowflake role denied)`, `408 Snowflake Timeout`, `429 Rate Limited`, `500 Internal Error`.
- **Idempotency:** Same query text + filters within cache TTL returns cached result.
- **Versioning:** V1 returns flat response. V2 (future) may add streaming support.

---

### 3.4 Analytics API

#### `POST /api/v1/analytics/forecast`
- **Purpose:** Generate time-series forecast from existing query result data.
- **Consumer:** Frontend ForecastOverlay component, AI Chat (when user requests forecast).
- **Authentication:** Bearer JWT.
- **Authorization:** User must have `run_forecasting` permission.
- **Request Model:** `{ "data": [{ "date": "string", "value": number }], "horizon": 6, "confidence_level": 0.95, "frequency": "monthly" }`
- **Response Model:** `{ "data": { "historical": [...], "forecast": [...], "upper_bound": [...], "lower_bound": [...], "model_used": "prophet", "metrics": { "mape": 0.05 } } }`
- **Validation:** Minimum 12 data points. Horizon ≤ 24 periods. Confidence level ∈ {0.80, 0.90, 0.95}.
- **Rate Limiting:** 10 forecasts/min per user (compute-intensive).
- **Error Responses:** `400 Insufficient Data Points`, `400 Invalid Frequency`, `408 Computation Timeout`.
- **Retry Strategy:** Not retryable (deterministic given same input). Client can resubmit.

#### `GET /api/v1/analytics/anomalies`
- **Purpose:** Retrieve detected anomalies from recent query results or scheduled scans.
- **Consumer:** Frontend Alerts panel, notification system.
- **Authentication:** Bearer JWT.
- **Authorization:** User sees only anomalies from their authorized data scope.
- **Request Model:** Query params: `?since=2026-06-01&severity=warning,critical&limit=25`
- **Response Model:** `{ "data": [{ "id", "detected_at", "metric", "expected_value", "actual_value", "deviation_pct", "severity", "description" }] }`

---

### 3.5 Dashboard API

#### `GET /api/v1/dashboards`
- **Purpose:** List user's dashboards (owned + shared with them).
- **Consumer:** Frontend Dashboard page.
- **Authentication:** Bearer JWT.
- **Authorization:** User sees only dashboards they own or are shared with.
- **Request Model:** Query params: `?cursor=abc&limit=25&filter=owned|shared|all`
- **Response Model:** `{ "data": [{ "id", "name", "created_at", "updated_at", "widget_count", "is_shared", "owner": { "id", "name" } }], "meta": { "next_cursor", "total" } }`

#### `POST /api/v1/dashboards`
- **Purpose:** Create a new dashboard.
- **Authentication:** Bearer JWT.
- **Authorization:** All authenticated users.
- **Request Model:** `{ "name": "string", "description": "string" }`
- **Response Model:** `{ "data": { "id", "name", "description", "created_at" } }`
- **Idempotency:** `Idempotency-Key` header prevents duplicate creation.

#### `PUT /api/v1/dashboards/{id}/widgets`
- **Purpose:** Update widget layout (positions, sizes, chart specs) for a dashboard.
- **Consumer:** Frontend DashboardGrid (on drag/resize/add).
- **Authentication:** Bearer JWT.
- **Authorization:** User must be dashboard owner or have edit permission.
- **Request Model:** `{ "widgets": [{ "id", "position": { "x", "y", "w", "h" }, "chart_spec": {}, "data_query": "string" }] }`
- **Validation:** Maximum 20 widgets per dashboard. Positions must not overlap.

#### `POST /api/v1/dashboards/{id}/share`
- **Purpose:** Share a dashboard with specific users or teams.
- **Request Model:** `{ "share_with": [{ "user_id": "uuid", "permission": "view|edit" }] }`

---

### 3.6 Administration API

#### `GET /api/v1/admin/users`
- **Purpose:** List all users in the organization.
- **Authorization:** Admin role only.
- **Response Model:** `{ "data": [{ "id", "email", "name", "role", "department", "snowflake_role", "last_login", "is_active", "query_count_30d" }] }`

#### `POST /api/v1/admin/users`
- **Purpose:** Invite a new user.
- **Request Model:** `{ "email": "string", "role": "string", "department": "string", "snowflake_role": "string" }`

#### `PUT /api/v1/admin/users/{id}`
- **Purpose:** Update user role, department, or Snowflake role mapping.
- **Authorization:** Admin only. Cannot modify own admin status (safety check).

#### `GET /api/v1/admin/costs`
- **Purpose:** Retrieve LLM and Snowflake cost breakdown.
- **Request Model:** Query params: `?period=daily|weekly|monthly&start=date&end=date`
- **Response Model:** `{ "data": { "llm_costs": { "total", "by_model": [...], "by_user": [...] }, "snowflake_costs": { "total", "by_warehouse": [...], "by_user": [...] } } }`
- **Authorization:** Admin and Data Analyst (read-only) roles.

#### `POST /api/v1/admin/sync/trigger`
- **Purpose:** Manually trigger metadata synchronization.
- **Authorization:** Admin and Data Analyst roles.
- **Response Model:** `{ "data": { "sync_id", "status": "started", "started_at" } }`
- **Rate Limiting:** 1 sync per hour (prevents Snowflake INFORMATION_SCHEMA abuse).

#### `GET /api/v1/admin/sync/status`
- **Purpose:** Retrieve latest sync status and schema diff summary.
- **Response Model:** `{ "data": { "last_sync_at", "status": "success|failed", "tables_synced", "tables_added", "tables_dropped", "columns_changed", "errors": [] } }`

---

### 3.7 Metadata API

#### `GET /api/v1/metadata/databases`
- **Purpose:** List available databases the user can query.
- **Authorization:** Filtered by user's Snowflake role permissions.

#### `GET /api/v1/metadata/databases/{db}/schemas`
- **Purpose:** List schemas within a database.

#### `GET /api/v1/metadata/tables/{table_id}`
- **Purpose:** Retrieve table details (columns, descriptions, relationships, PII flags).
- **Authorization:** Data Analyst and Admin roles only.

#### `PUT /api/v1/metadata/columns/{column_id}/description`
- **Purpose:** Update a column's business description (re-embeds in vector store).
- **Authorization:** Data Analyst and Admin roles only.
- **Request Model:** `{ "description": "string" }`
- **Side Effect:** Triggers re-embedding of the column's parent table in pgvector.

#### `GET /api/v1/metadata/glossary`
- **Purpose:** List all business glossary terms.

#### `POST /api/v1/metadata/glossary`
- **Purpose:** Add a new glossary term.
- **Authorization:** Data Analyst and Admin roles only.
- **Request Model:** `{ "term": "string", "definition": "string", "sql_fragment": "string (optional)" }`

---

### 3.8 Export API

#### `POST /api/v1/export/csv`
- **Purpose:** Export query result data as CSV.
- **Authorization:** All roles except CEO (per RBAC matrix).
- **Request Model:** `{ "query_execution_id": "uuid" }`
- **Response:** Streamed CSV file download (`Content-Type: text/csv`).

#### `POST /api/v1/export/png`
- **Purpose:** Export chart as PNG image.
- **Authorization:** All authenticated users.
- **Request Model:** `{ "chart_spec": {}, "data": [], "width": 1200, "height": 800 }`
- **Response:** PNG image binary (`Content-Type: image/png`).
- **Note:** Server-side chart rendering for consistent output across browsers.

---

### 3.9 Health API

#### `GET /api/v1/health`
- **Purpose:** Liveness probe — is the application process running?
- **Authentication:** None (must be accessible by load balancer).
- **Response Model:** `{ "status": "ok", "version": "1.0.0", "timestamp": "ISO8601" }`

#### `GET /api/v1/health/ready`
- **Purpose:** Readiness probe — can the application serve requests?
- **Authentication:** None.
- **Response Model:** `{ "status": "ready|degraded|unhealthy", "checks": { "postgres": "ok", "redis": "ok", "snowflake": "ok|unreachable", "llm_provider": "ok|degraded" } }`
- **Behavior:** Returns HTTP 200 if all checks pass. Returns HTTP 503 if any critical check fails.

#### `GET /api/v1/health/metrics`
- **Purpose:** Internal metrics endpoint for monitoring.
- **Authentication:** API key or internal network only.
- **Response Model:** `{ "uptime_seconds", "request_count", "error_rate", "avg_latency_ms", "active_websockets", "cache_hit_ratio", "connection_pool_usage" }`

---

### 3.10 Notification API

#### `GET /api/v1/notifications`
- **Purpose:** Retrieve user's unread notifications (anomaly alerts, shared dashboards).
- **Authentication:** Bearer JWT.
- **Response Model:** `{ "data": [{ "id", "type": "anomaly|share|system", "title", "body", "created_at", "is_read" }], "meta": { "unread_count" } }`

#### `PUT /api/v1/notifications/{id}/read`
- **Purpose:** Mark a notification as read.
- **Authentication:** Bearer JWT.
