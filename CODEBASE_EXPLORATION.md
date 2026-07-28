# NexusBI Backend Codebase Exploration Overview

**Date:** July 28, 2026  
**Focus:** Universal Connector Framework Architecture & Backend Organization

---

## 1. Connector Framework Location & Structure

### Directory Layout
```
backend/app/domain/connectors/
├── __init__.py           (Public API exports)
├── interface.py          (DatabaseConnector ABC - CORE INTERFACE)
├── config.py             (ConnectorConfig dataclass)
├── types.py              (ConnectorType enum)
└── exceptions.py         (Domain exceptions)
```

### Framework Status
- **Status:** Newly implemented universal framework (framework commit: `feat(connectors): implement universal connector framework`)
- **Location:** Domain layer (NOT infrastructure) - follows Clean Architecture
- **Pattern:** Hexagonal/Ports & Adapters architecture
- **Real Implementations:** Currently NONE - framework is foundation only

---

## 2. Base Interface: `DatabaseConnector`

### Location
📍 [backend/app/domain/connectors/interface.py](backend/app/domain/connectors/interface.py)

### Class Definition
```python
class DatabaseConnector(ABC):
    """Technology-neutral contract for database connectivity and discovery."""
```

### Core Methods

#### Connection Management
```python
@abstractmethod
def connect(self) -> None:
    """Open a connection to the configured data source."""

@abstractmethod
def disconnect(self) -> None:
    """Close the active connection, if any."""

@abstractmethod
def test_connection(self) -> bool:
    """Test whether the configured data source can be reached."""
```

#### Query Execution
```python
@abstractmethod
def execute(
    self, query: str, parameters: Mapping[str, object] | None = None
) -> Sequence[Mapping[str, object]]:
    """Execute a query and return its result rows."""
```

#### Transaction Management
```python
@abstractmethod
def begin_transaction(self) -> None:
    """Begin a database transaction."""

@abstractmethod
def commit(self) -> None:
    """Commit the active transaction."""

@abstractmethod
def rollback(self) -> None:
    """Roll back the active transaction."""
```

#### Metadata Discovery
```python
@abstractmethod
def list_schemas(self) -> Sequence[str]:
    """List schemas exposed by the configured data source."""

@abstractmethod
def list_tables(self, schema: str | None = None) -> Sequence[str]:
    """List tables, optionally restricted to one schema."""

@abstractmethod
def list_views(self, schema: str | None = None) -> Sequence[str]:
    """List views, optionally restricted to one schema."""

@abstractmethod
def list_columns(
    self, table_name: str, schema: str | None = None
) -> Sequence[Mapping[str, object]]:
    """List column metadata for a table or view."""
```

**Total Methods:** 11 abstract methods

---

## 3. Supporting Framework Components

### 3.1 ConnectorConfig
📍 [backend/app/domain/connectors/config.py](backend/app/domain/connectors/config.py)

**Type:** Immutable dataclass (frozen with slots)

**Purpose:** Framework-independent configuration value object for all connector types

**Key Fields:**
```python
@dataclass(frozen=True, slots=True)
class ConnectorConfig:
    id: str                              # Unique identifier
    name: str                            # Human-readable name
    connector_type: ConnectorType        # Type enum
    host: str | None = None
    port: int | None = None
    database: str | None = None
    username: str | None = None
    password: str | None = None
    schema: str | None = None
    warehouse: str | None = None         # For Snowflake, BigQuery
    account: str | None = None           # For Snowflake
    ssl_enabled: bool = False
    extra_options: Mapping[str, object] = field(default_factory=dict)
```

**Key Features:**
- Comprehensive validation in `__post_init__()`
- Recursive freezing of mutable option values (dict → MappingProxyType)
- Port range validation: 1-65535
- Non-empty string normalization

### 3.2 ConnectorType Enum
📍 [backend/app/domain/connectors/types.py](backend/app/domain/connectors/types.py)

**Supported Database Types:**
```python
class ConnectorType(StrEnum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    SQLSERVER = "sqlserver"
    SNOWFLAKE = "snowflake"
    BIGQUERY = "bigquery"
    DUCKDB = "duckdb"
```

### 3.3 Exception Hierarchy
📍 [backend/app/domain/connectors/exceptions.py](backend/app/domain/connectors/exceptions.py)

**Base Exception:**
```python
class ConnectorError(Exception):
    """Base exception for all connector-related failures."""
```

**Derived Exception Types:**
```python
class ConnectionFailedError(ConnectorError)
    """Raised when connection cannot be established."""

class AuthenticationFailedError(ConnectionFailedError)
    """Raised when credentials are rejected."""

class UnsupportedConnectorError(ConnectorError)
    """Raised when no implementation supports a connector type."""

class QueryExecutionError(ConnectorError)
    """Raised when a connector cannot execute a query."""

class MetadataDiscoveryError(ConnectorError)
    """Raised when schemas, objects, or columns cannot be discovered."""
```

### 3.4 Public API Export
📍 [backend/app/domain/connectors/__init__.py](backend/app/domain/connectors/__init__.py)

```python
__all__ = [
    "AuthenticationFailedError",
    "ConnectionFailedError",
    "ConnectorConfig",
    "ConnectorError",
    "ConnectorType",
    "DatabaseConnector",      # ← Primary interface
    "MetadataDiscoveryError",
    "QueryExecutionError",
    "UnsupportedConnectorError",
]
```

---

## 4. Infrastructure/Connectors Directory

### Current Structure
```
backend/app/infrastructure/
├── __init__.py (public exports)
├── connectors/              # ← EMPTY - Ready for implementations
│   ├── __init__.py
│   └── __pycache__/
├── database/
│   ├── base.py             (SQLAlchemy declarative base)
│   └── models.py           (ORM models: users, roles, permissions, sessions)
├── mappers/                (DTO ↔ ORM model converters)
│   ├── user_mapper.py
│   ├── session_mapper.py
│   └── [8 other mappers]
├── repositories/           (Data access patterns)
│   ├── user_repository.py
│   ├── session_repository.py
│   └── [8 other repositories]
├── services/               (Infrastructure services)
│   ├── authorization_service.py
│   ├── bcrypt_password_hasher.py
│   └── jwt_token_service.py
├── query/                  (Query execution for BI)
│   ├── sqlalchemy_executor.py
│   ├── sqlalchemy_planner.py
│   └── sqlalchemy_validator.py
└── chart/                  (Chart generation)
    ├── registry.py
    ├── validator.py
    ├── formatter.py
    └── builders/
```

**Key Observations:**
- `connectors/` directory exists but is empty (ready for implementations)
- Infrastructure layer follows adapter pattern
- Clear separation: mappers (DTO↔ORM), repositories (data access), services (business logic)

---

## 5. App/Infrastructure Module Organization

### Current Infrastructure Exports
📍 [backend/app/infrastructure/__init__.py](backend/app/infrastructure/__init__.py)

```python
from app.infrastructure.database.base import Base
from app.infrastructure.mappers.session_mapper import SessionMapper
from app.infrastructure.mappers.user_mapper import UserMapper
from app.infrastructure.repositories.session_repository import (
    SQLAlchemySessionRepository,
)
from app.infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from app.infrastructure.services.bcrypt_password_hasher import BcryptPasswordHasher
from app.infrastructure.services.jwt_token_service import JWTTokenService

__all__ = [
    "Base",                              # SQLAlchemy declarative base
    "BcryptPasswordHasher",
    "JWTTokenService",
    "SQLAlchemySessionRepository",
    "SQLAlchemyUserRepository",
    "SessionMapper",
    "UserMapper",
]
```

### Database Layer Architecture

#### SQLAlchemy Base
📍 [backend/app/infrastructure/database/base.py](backend/app/infrastructure/database/base.py)

```python
class Base(DeclarativeBase):
    """Application-wide SQLAlchemy 2.0 declarative base."""
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
```

**Naming Convention:** Ensures deterministic constraint names for Alembic migrations
- `ix_` — indexes
- `uq_` — unique constraints
- `ck_` — check constraints
- `fk_` — foreign keys
- `pk_` — primary keys

#### ORM Models
📍 [backend/app/infrastructure/database/models.py](backend/app/infrastructure/database/models.py)

**Models for RBAC System:**
- `PermissionModel` — Composed of (resource, action) pair
- `RoleModel` — Set of permissions (M2M via role_permissions)
- `UserModel` — User accounts (M2M roles via user_roles)
- `SessionModel` — JWT refresh token sessions

All models explicitly inherit from `Base` and follow SQLAlchemy 2.0 mapped_column pattern.

---

## 6. Dependency Wiring: `app/core/dependencies.py`

📍 [backend/app/core/dependencies.py](backend/app/core/dependencies.py)

### Architecture Pattern
**Container Pattern:** `dependency-injector` library
**Scope:** Clean Architecture layers

### Dependency Resolution Order

#### Core Layer Services
```python
config = providers.Singleton(get_settings)
    # → Settings singleton from app.core.config.get_settings()

audit_logger = providers.Singleton(AuditLogger)
    # → Compliance audit logging service
```

#### Infrastructure Layer: Database

```python
db_engine = providers.Singleton(
    _create_engine,
    settings=config,
)
    # → Creates SQLAlchemy Engine from postgres_dsn in settings
    # → Uses connection pooling:
    #    - pool_size = POSTGRES_POOL_SIZE (default: 10)
    #    - max_overflow = POSTGRES_MAX_OVERFLOW (default: 20)
    #    - pool_timeout = POSTGRES_POOL_TIMEOUT (default: 30s)
    #    - pool_recycle = 3600s (prevents idle connection drops)

db_session_factory = providers.Singleton(
    _create_session_factory,
    engine=db_engine,
)
    # → Sessionmaker bound to engine
    # → Configuration: autocommit=False, autoflush=False

db_session = providers.Resource(get_db)
    # → Scoped session yielded to FastAPI routes
    # → Auto-closed after request completes
```

### Container Wiring Configuration

```python
class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.api.health",
            "app.api.v1.routers.health",
        ],
    )
```

**Currently Wired Modules:**
- `app.api.health` — Health check endpoint
- `app.api.v1.routers.health` — Versioned health endpoint

**Wiring Pattern:** FastAPI `Depends()` resolves container providers at request time

### Session Dependency

```python
def get_db() -> Generator[Session]:
    """FastAPI dependency that yields a scoped database session."""
    settings = get_settings()
    engine = _create_engine(settings)
    session_factory = _create_session_factory(engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
```

---

## 7. Test Structure & Patterns

### Configuration
📍 [backend/tests/conftest.py](backend/tests/conftest.py)

### Scope & Purpose
**Module Level:** Pytest global configuration  
**Coverage:** Entire backend test suite  
**Key Pattern:** Fixture-based test isolation

### Core Fixtures

#### 1. Session-Scoped: `test_settings`
```python
@pytest.fixture(scope="session")
def test_settings() -> Generator[Settings]:
    """Provide test-specific settings overrides."""
```

**Features:**
- Clears settings cache before and after session
- Overrides key environment variables for testing:
  - `ENV = "testing"`
  - `DEBUG = "true"`
  - `POSTGRES_DB = "nexusbi_testing"` (separate test database)
  - `SECRET_KEY = "test_secret_key_not_for_production"`

**Cache Management:**
```python
get_settings.cache_clear()  # Before test
# ... run all tests ...
get_settings.cache_clear()  # After test
```

#### 2. Function-Scoped: `mock_db_session`
```python
@pytest.fixture
def mock_db_session() -> MagicMock:
    """Provide a mock database session for unit tests."""
```

**Pre-configured Mocks:**
- `session.execute()` — Returns pre-configured MagicMock
- Ready for unit test assertions without real DB

#### 3. Function-Scoped: `app`
```python
@pytest.fixture
def app(test_settings: Settings, mock_db_session: MagicMock) -> Generator[FastAPI]:
    """Create a test application instance with mocked dependencies."""
```

**Setup Process:**
1. Initializes FastAPI application via `create_app()`
2. Overrides `get_db` dependency with mock version:
   ```python
   application.dependency_overrides[get_db] = override_get_db
   ```
3. Ensures mock session is properly closed after each test

**Lifecycle:**
```python
def override_get_db() -> Generator[MagicMock]:
    try:
        yield mock_db_session
    finally:
        mock_db_session.close()
```

#### 4. Function-Scoped: `client`
```python
@pytest.fixture
def client(app: FastAPI) -> Generator[TestClient]:
    """Provide an HTTP test client bound to the test application."""
```

**Implementation:**
```python
with TestClient(app) as test_client:
    yield test_client
```

### Fixture Dependency Chain

```
test_settings (session-scoped)
    ↓
mock_db_session (function-scoped)
    ↓
app (function-scoped)
    ↓
    ├→ Clears settings cache
    ├→ Creates test FastAPI app via create_app()
    └→ Overrides get_db with mock
        ↓
        client (function-scoped)
            ↓
            TestClient wraps app
```

### Test Patterns in Existing Suite

**Test Files by Domain:**
```
tests/
├── conftest.py                    (Shared fixtures)
├── test_health.py                 (System health checks)
├── test_auth_api.py               (Authentication endpoints)
├── test_users_api.py              (User CRUD)
├── test_roles_api.py              (RBAC role management)
├── test_rbac_api.py               (RBAC enforcement)
├── test_organizations_api.py      (Organization management)
├── test_workspaces_api.py         (Multi-tenant workspaces)
├── test_dashboard_api.py          (Dashboard CRUD)
├── test_widget_api.py             (Dashboard widget management)
├── test_report_api.py             (Report creation/execution)
├── test_dataset_api.py            (Dataset definitions)
├── test_query_engine_api.py       (Query execution API)
├── test_query_engine_validator.py (Query safety validation)
├── test_query_engine_security.py  (Query security policies)
├── test_query_engine_executor.py  (Query execution logic)
├── test_chart_api.py              (Chart generation)
├── test_bi_foundation_api.py      (BI platform integration)
└── unit/                          (Unit tests subdirectory)
```

### Common Testing Pattern

**Use case:** Testing with mocked database
```python
def test_example_endpoint(client: TestClient, mock_db_session: MagicMock):
    # Arrange
    mock_db_session.execute.return_value = [...]
    
    # Act
    response = client.get("/api/v1/example")
    
    # Assert
    assert response.status_code == 200
```

---

## 8. Application Bootstrap & DI Wiring

📍 [backend/app/main.py](backend/app/main.py)

### Key Initialization Steps

```python
def create_app() -> FastAPI:
    """Bootstrap the FastAPI application."""
    
    # 1. Load configuration
    settings = get_settings()
    
    # 2. Configure logging
    configure_logging(settings)
    
    # 3. Wire dependency container
    container = Container()
    container.wire(
        modules=[
            "app.api.health",
            "app.api.v1.routers.health",
        ]
    )
    
    # 4. Register middleware stack
    setup_middleware(app)
    
    # 5. Register exception handlers
    register_exception_handlers(app)
    
    # 6. Mount routers
    app.include_router(health_router)
    app.include_router(api_v1_router)
    
    # 7. Configure OpenAPI schema
    setup_openapi_schema(app)
```

### API Routers (v1)

```
app/api/v1/routers/
├── health.py          (System health checks)
├── auth.py            (Login, token refresh, logout)
├── users.py           (User CRUD operations)
├── roles.py           (RBAC role management)
├── organizations.py   (Organization management)
├── workspaces.py      (Multi-tenant workspace management)
├── dashboards.py      (Dashboard CRUD)
├── widgets.py         (Widget management for dashboards)
├── reports.py         (Report creation/execution)
├── datasets.py        (Dataset definitions)
├── query.py           (Universal query execution)
└── charts.py          (Chart model generation)
```

---

## 9. Architecture Reference Documents

Key architecture planning documents referenced throughout:
- `docs/architecture/phase2_1_repository_blueprint.md` — Repository/DI patterns
- `docs/architecture/phase2_3_api_service_blueprint.md` — API layer design
- `docs/architecture/ADR-005: Clean Architecture` — Boundary rules
- `docs/architecture/ADR-011: Repository Pattern` — Data access patterns

---

## Summary Table

| Component | Location | Type | Status | Notes |
|-----------|----------|------|--------|-------|
| **Base Interface** | `domain/connectors/interface.py` | ABC | ✅ Complete | 11 abstract methods |
| **Config Model** | `domain/connectors/config.py` | Dataclass | ✅ Complete | Immutable, frozen |
| **Type Enum** | `domain/connectors/types.py` | Enum | ✅ Complete | 7 supported types |
| **Exceptions** | `domain/connectors/exceptions.py` | Exception Classes | ✅ Complete | 5 exception types |
| **Implementations** | `infrastructure/connectors/` | (empty) | ❌ Pending | Ready for Add implementations |
| **DI Container** | `core/dependencies.py` | Singleton pattern | ✅ Complete | Database layer wired |
| **Test Fixtures** | `tests/conftest.py` | Pytest fixtures | ✅ Complete | 4 core fixtures |

