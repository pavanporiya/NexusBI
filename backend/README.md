# Backend Architecture Specification: FastAPI Application

This directory contains the FastAPI microservices codebase structured following Clean Architecture and Domain-Driven Design (DDD) principles.

## 🧱 Layered Architecture Responsibilities

```
┌────────────────────────────────────────────────────────┐
│                        INTERFACES                      │
│            (api/ routers, schemas, payloads)           │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                    APPLICATION CORE                    │
│            (core/ settings, auth middleware)           │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                      DOMAIN LAYER                      │
│     (domain/ use cases, entities, ports/interfaces)    │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                  INFRASTRUCTURE LAYER                  │
│       (infrastructure/ Snowflake, Qdrant, LLMs)        │
└────────────────────────────────────────────────────────┘
```

### 1. Interfaces Layer (`app/api/`)
* **Purpose:** Handles all HTTP, REST, and WebSocket request-response lifecycles.
* **Key Contents:**
  * `routers/`: Endpoint definitions (`auth.py`, `chat.py`, `query.py`, `forecast.py`).
  * `schemas/`: Pydantic input/output validation models ensuring payloads match runtime contract standards.
* **Rules:** Must never contain business logic or call database drivers directly. It routes requests to Use Cases in the Domain layer.

### 2. Core Application Layer (`app/core/`)
* **Purpose:** Defines global security, configuration, and app initialization components.
* **Key Contents:**
  * `config.py`: Environment variable validation using `pydantic-settings`.
  * `security.py`: JWT decoding, Okta validation, and password-less Snowflake credential handshakes.
  * `middleware/`: Rate limiting, CORS headers, logging, and error wrappers.

### 3. Domain Layer (`app/domain/`)
* **Purpose:** The heart of the business logic. Completely decoupled from external frameworks, database connections, and libraries.
* **Key Contents:**
  * `entities/`: Pure data schemas (e.g., `QueryContext`, `VisualSpec`, `ForecastModel`).
  * `interfaces/`: Abstract base classes (ports) defining repository and client contracts (e.g., `ISnowflakeClient`, `IVectorDbClient`, `ILlmClient`).
  * `use_cases/`: Core orchestration logic (e.g., `compile_sql_query.py`, `generate_forecast.py`).

### 4. Infrastructure Layer (`app/infrastructure/`)
* **Purpose:** Implements the interfaces (adapters) defined in the Domain layer.
* **Key Contents:**
  * `database/`: Snowflake connection pools and query executions under user-mapped database roles.
  * `vector_store/`: Qdrant search interfaces for catalog retrieval.
  * `ai/`: Implementations of prompt builders, tool calls, and LLM integrations (Claude 3.5 / OpenAI).

---

## 🔒 Security Gateways & Validation Logic
1. **OAuth2/JWT Verification:** Every request to `api/` must pass through the authentication middleware verifying JWT signatures issued by the corporate OIDC Provider.
2. **Access Policy Sync:** The backend maps token groups to local roles, assigning the corresponding Snowflake database role parameter on each statement execution thread.
3. **AST SQL Parser Filter:** The `compile_sql_query` use case runs SQL queries through a local parser check to ensure:
   * Only read-only operations (`SELECT`) are present.
   * Internal catalog tables (like `INFORMATION_SCHEMA` metadata schemas) are blocked from custom user-level modification queries.
