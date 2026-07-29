/**
 * TypeScript interfaces mirroring backend DTOs.
 * These types define the contract between frontend and backend API.
 */

// ─── Pagination ──────────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ─── Authentication ──────────────────────────────────────────────────────────

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface TokenRefreshRequest {
  refresh_token: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  roles: string[];
  permissions: string[];
  created_at: string;
  updated_at: string;
}

export interface LogoutResponse {
  message: string;
}

// ─── Organizations ───────────────────────────────────────────────────────────

export interface Organization {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateOrganizationRequest {
  name: string;
  slug: string;
  description?: string;
}

export interface UpdateOrganizationRequest {
  name?: string;
  slug?: string;
  description?: string;
  is_active?: boolean;
}

// ─── Workspaces ──────────────────────────────────────────────────────────────

export interface Workspace {
  id: string;
  organization_id: string;
  name: string;
  slug: string;
  description: string | null;
  is_default: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateWorkspaceRequest {
  organization_id: string;
  name: string;
  slug: string;
  description?: string;
  is_default?: boolean;
}

export interface UpdateWorkspaceRequest {
  name?: string;
  slug?: string;
  description?: string;
  is_default?: boolean;
  is_active?: boolean;
}

// ─── Datasets ────────────────────────────────────────────────────────────────

export interface Dataset {
  id: string;
  name: string;
  source_type: string;
  object_type: string;
  object_name: string | null;
  sql_query: string | null;
  connection_id: string | null;
  query_or_table: string;
  owner_id: string;
  description: string | null;
  schema_metadata: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateDatasetRequest {
  name: string;
  source_type: string;
  object_type?: string;
  object_name?: string;
  sql_query?: string;
  connection_id?: string;
  query_or_table?: string;
  description?: string;
  schema_metadata?: Record<string, unknown>;
  is_active?: boolean;
}

export interface UpdateDatasetRequest {
  name?: string;
  source_type?: string;
  object_type?: string;
  object_name?: string;
  sql_query?: string;
  connection_id?: string;
  query_or_table?: string;
  description?: string;
  schema_metadata?: Record<string, unknown>;
  is_active?: boolean;
}

// ─── Dashboards ──────────────────────────────────────────────────────────────

export interface Dashboard {
  id: string;
  name: string;
  owner_id: string;
  dataset_id: string;
  description: string | null;
  layout_json: Record<string, unknown>;
  is_public: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateDashboardRequest {
  name: string;
  dataset_id: string;
  description?: string;
  layout_json?: Record<string, unknown>;
  is_public?: boolean;
  is_active?: boolean;
}

export interface UpdateDashboardRequest {
  name?: string;
  dataset_id?: string;
  description?: string;
  layout_json?: Record<string, unknown>;
  is_public?: boolean;
  is_active?: boolean;
}

// ─── Reports ─────────────────────────────────────────────────────────────────

export interface Report {
  id: string;
  name: string;
  owner_id: string;
  dataset_id: string;
  description: string | null;
  sql_query: string | null;
  config_json: Record<string, unknown>;
  is_public: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateReportRequest {
  name: string;
  dataset_id: string;
  description?: string;
  sql_query?: string;
  config_json?: Record<string, unknown>;
  is_public?: boolean;
}

export interface UpdateReportRequest {
  name?: string;
  dataset_id?: string;
  description?: string;
  sql_query?: string;
  config_json?: Record<string, unknown>;
  is_public?: boolean;
  is_active?: boolean;
}

// ─── Roles & Permissions ─────────────────────────────────────────────────────

export interface Role {
  id: string;
  name: string;
  description: string | null;
  permissions: string[];
  is_system: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateRoleRequest {
  name: string;
  description?: string;
  permissions: string[];
}

export interface UpdateRoleRequest {
  name?: string;
  description?: string;
  permissions?: string[];
}

// ─── Query Engine ────────────────────────────────────────────────────────────

export interface QueryColumn {
  name: string;
  type: string;
}

export interface QueryStatistics {
  query_plan: string | null;
  rows_scanned: number | null;
  bytes_processed: number | null;
  cache_hit: boolean | null;
}

export interface QueryMetadata {
  statistics: QueryStatistics;
  execution_time: number | null;
  row_count: number | null;
  columns: QueryColumn[];
  truncated: boolean;
  limit: number | null;
  offset: number | null;
}

export interface QueryResult {
  rows: Record<string, unknown>[];
  columns: QueryColumn[];
  column_types: Record<string, string>;
  execution_time: number | null;
  row_count: number | null;
  metadata: QueryMetadata;
}

export interface ExecuteQueryRequest {
  sql: string;
  parameters?: Record<string, unknown>;
  page?: number;
  page_size?: number;
  limit?: number;
  offset?: number;
  timeout?: number;
}

export interface ValidateQueryRequest {
  sql: string;
  parameters?: Record<string, unknown>;
}

export interface ValidateQueryResponse {
  valid: boolean;
  message: string;
}

export interface ExplainQueryRequest {
  sql: string;
  parameters?: Record<string, unknown>;
}

// ─── Connectors ──────────────────────────────────────────────────────────────

export interface ConnectorConfig {
  id?: string;
  name?: string;
  connector_type: string;
  host?: string | null;
  port?: number | null;
  database?: string | null;
  username?: string | null;
  password?: string | null;
  default_schema?: string | null;
  warehouse?: string | null;
  account?: string | null;
  ssl_enabled?: boolean;
  extra_options?: Record<string, unknown>;
}

export interface ConnectorTestResponse {
  success: boolean;
  message: string;
}

export interface ConnectorColumn {
  name: string;
  type: string;
  nullable: boolean;
  primary_key: boolean;
}

export interface ConnectorDiscoveryResponse {
  schemas: string[];
  tables: string[];
  columns: ConnectorColumn[];
}

// ─── Health ──────────────────────────────────────────────────────────────────

export type HealthStatus = "healthy" | "degraded" | "unhealthy" | "unavailable";

export interface ComponentHealth {
  name: string;
  status: HealthStatus;
  latency_ms?: number;
  detail?: string;
}

export interface HealthResponse {
  status: HealthStatus;
  version: string;
  timestamp: string;
  service: string;
  environment: string;
  uptime_seconds: number;
  checks: ComponentHealth[];
}

export interface VersionResponse {
  service: string;
  version: string;
  environment: string;
  python_version: string;
  platform: string;
  api_version: string;
  started_at: string;
}

// ─── Charts ──────────────────────────────────────────────────────────────────

export interface ChartPoint {
  x: unknown;
  y: unknown;
  label?: string;
  value?: unknown;
  metadata?: Record<string, unknown>;
}

export interface ChartSeries {
  name: string;
  data: ChartPoint[];
  color?: string;
  chart_type?: string;
  metadata?: Record<string, unknown>;
}

export interface ChartResult {
  title: string;
  subtitle?: string;
  labels: string[];
  series: ChartSeries[];
  metadata: Record<string, unknown>;
  statistics: Record<string, unknown>;
  recommended_colors: string[];
}

export interface ChartConfiguration {
  chart_type: string;
  x_axis_column?: string;
  y_axis_columns: string[];
  group_by_column?: string;
  aggregation?: string;
  title?: string;
  subtitle?: string;
}

// ─── Widgets ─────────────────────────────────────────────────────────────────

export interface Widget {
  id: string;
  dashboard_id: string;
  name: string;
  widget_type: string;
  config_json: Record<string, unknown>;
  position_x: number;
  position_y: number;
  width: number;
  height: number;
  is_visible: boolean;
  created_at: string;
  updated_at: string;
}

// ─── API Error ───────────────────────────────────────────────────────────────

export interface ApiError {
  error_code: string;
  message: string;
  detail?: string;
  timestamp?: string;
  path?: string;
}
