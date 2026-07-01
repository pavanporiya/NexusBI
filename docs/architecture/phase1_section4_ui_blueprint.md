# NexusBI Phase 1 Extension — Section 4: Enterprise UI Blueprint

**Date:** July 1, 2026

---

## 1. Design System Foundations

- **Typography:** Inter (primary), JetBrains Mono (code/SQL display)
- **Color Palette:** Dark mode default. Primary: Indigo-500. Accent: Emerald-400. Error: Rose-500. Warning: Amber-500.
- **Spacing:** 4px grid system (Tailwind default spacing scale)
- **Border Radius:** 8px for cards, 6px for inputs, 12px for modals
- **Shadows:** Subtle elevation shadows for cards and modals. No heavy drop shadows.
- **Motion:** 150ms ease-out transitions for hover states. 300ms for panel open/close.

---

## 2. Screen Specifications

### 2.1 Login Page

- **Purpose:** Redirect users to corporate SSO and handle the OIDC callback.
- **Target User:** All users (unauthenticated).
- **Navigation:** No sidebar. No top bar. Full-screen centered layout.
- **Widgets:** NexusBI logo (centered), "Sign in with your organization" button, animated background gradient.
- **Interactions:** Click "Sign In" → redirect to OIDC provider. On callback → validate token → redirect to Dashboard.
- **Loading State:** Spinner with "Authenticating..." text after SSO redirect return.
- **Error State:** Banner: "Authentication failed. Please try again or contact your administrator." with retry button.
- **Permissions:** None (public page).

---

### 2.2 Dashboard Page (Home)

- **Purpose:** The primary landing page after login. Displays the user's personalized dashboard with pinned KPI cards and charts.
- **Target User:** All authenticated users (content varies by role).
- **Navigation:** Left sidebar visible. Top bar with search, notifications, avatar.
- **Widgets:**
  - **KPI Row (top):** 4-6 KPI scorecards (Revenue, Net Profit, Profit Margin, AOV, Retention Rate, NPS). Each card shows: current value, trend arrow (↑/↓), % change vs prior period, sparkline chart.
  - **Chart Grid (body):** Drag-and-drop grid of pinned charts from AI Chat sessions. Each chart widget has: title, chart rendering, "Expand" button, "Remove" button, "Refresh" button, timestamp ("Data as of...").
  - **Quick Actions (right sidebar or floating):** "Ask a question" button, "New Dashboard" button, "View all dashboards" link.
- **Tables:** None on default dashboard. Tables appear inside expanded chart widgets when user clicks "View Data."
- **Charts:** ECharts renderings from pinned ChartSpec JSON. Support: line, bar, grouped bar, scatter, gauge, heatmap.
- **Buttons:** "Add Widget" (opens chat to generate a new chart), "Edit Layout" (enables drag/resize mode), "Share Dashboard" (opens share modal).
- **Filters:** Global date range picker in top bar (applies to all dashboard charts). Per-widget filter override available in widget settings.
- **Search:** Global search in top bar — searches across dashboards, saved queries, and glossary terms.
- **Loading State:** Skeleton loaders for KPI cards and chart widgets during initial data fetch.
- **Error State:** If a specific chart fails to load, that widget shows: "Failed to load chart. Click to retry." Other widgets continue rendering.
- **Empty State:** New user with no pinned charts sees: "Welcome to NexusBI! Start by asking a question." with large "Open AI Chat" button and 5 suggested query chips.
- **Permissions:** CEO sees pre-configured Executive dashboard. Manager sees department-specific dashboard. Analyst sees personal workspace. Admin sees system health dashboard.

---

### 2.3 Chat Workspace

- **Purpose:** The conversational AI interface where users ask natural language questions and receive data visualizations, insights, and recommendations.
- **Target User:** All authenticated users.
- **Navigation:** Full-width or split-screen (chat left, visualization right). Toggle between modes.
- **Widgets:**
  - **Chat Panel (left):** Message history with user bubbles (right-aligned) and AI response bubbles (left-aligned). AI responses contain: text summary, embedded chart, insight bullets, recommendation cards.
  - **Visualization Panel (right):** Large interactive chart rendering. Toolbar with: chart type switcher, fullscreen, download PNG, pin to dashboard.
  - **Input Bar (bottom):** Text input field with: placeholder suggestions, send button, voice input icon (V3), file upload icon (V3). Suggestion chips above input bar showing contextual follow-up queries.
  - **Progress Indicator:** Animated step tracker during query processing: "Understanding question" → "Finding data" → "Generating SQL" → "Executing query" → "Building visualization" → "Generating insights."
- **Tables:** "View Data" toggle on any chart response reveals the raw data table (sortable, searchable, paginated).
- **Charts:** Dynamically rendered ECharts based on server-provided ChartSpec. User can switch chart type (line ↔ bar ↔ table) via toolbar.
- **Buttons:** "New Conversation" (clears context), "Pin Chart" (adds to dashboard), "Export CSV" (downloads data), "View SQL" (shows generated SQL), "Copy SQL" (copies to clipboard), "Thumbs Up/Down" (feedback).
- **Filters:** Filter chips above the visualization panel showing currently active filters. Clicking a chip opens an edit dropdown. "Clear All Filters" link.
- **Interactions:**
  - Click on a bar in a bar chart → triggers contextual drill-down ("Show breakdown for [clicked category]").
  - Click "Forecast" button → adds forecast overlay to current chart.
  - Click "Explain" button → generates detailed insight text for the current visualization.
- **Loading State:** Typing indicator ("NexusBI is thinking...") with animated dots. Progress steps shown below.
- **Error State:** Friendly error bubble: "I couldn't find the right data for that question. Here's what I tried: [brief explanation]. Try rephrasing or adding more detail." With suggested alternative queries.
- **Empty State:** "Ask me anything about your business data" with 6 categorized suggestion chips: Revenue, Customers, Operations, Marketing, Products, Custom.
- **Permissions:** Data Analyst and Admin see additional "Debug Panel" toggle showing: full system prompt, retrieved schemas, raw LLM response, SQL execution plan, token count, cost.

---

### 2.4 Analytics & Forecast Page

- **Purpose:** Dedicated space for time-series analysis, forecasting, and trend exploration.
- **Target User:** Business Analyst, Data Analyst, Manager.
- **Widgets:**
  - **Metric Selector:** Dropdown to select KPI from catalog (Revenue, Profit, AOV, etc.).
  - **Time Range Selector:** Start date, end date, granularity (daily, weekly, monthly, quarterly).
  - **Forecast Controls:** Horizon slider (1-24 periods), confidence level selector (80/90/95%), "Run Forecast" button.
  - **Chart Area:** Large line chart with historical data (solid line) + forecast data (dotted line) + confidence band (shaded area).
  - **Insight Panel:** Below chart — automatically generated trend insights, seasonal patterns, anomaly annotations.
- **Loading State:** Chart skeleton with "Generating forecast..." progress bar.
- **Error State:** "Not enough data to generate a reliable forecast. At least 12 data points are required. Currently: [N] points."
- **Empty State:** "Select a metric and time range to begin analysis."

---

### 2.5 Alerts & Notifications Page

- **Purpose:** Central hub for viewing anomaly alerts, system notifications, and shared dashboard notifications.
- **Target User:** All authenticated users.
- **Widgets:**
  - **Alert List:** Sortable, filterable table: Timestamp, Alert Type (anomaly/system/share), Severity (info/warning/critical), Title, Status (new/read/dismissed).
  - **Alert Detail Panel:** Clicking an alert opens: description, affected metric, chart showing the anomaly, AI-generated explanation, recommended action.
- **Filters:** Filter by: type, severity, date range, status.
- **Empty State:** "No alerts at this time. We'll notify you when something needs your attention." with a checkmark icon.

---

### 2.6 Admin Panel

- **Purpose:** System administration for user management, data source configuration, cost monitoring, and schema management.
- **Target User:** Admin role only.
- **Navigation:** Admin-specific sub-navigation tabs: Users, Data Sources, Schema Manager, Glossary, Costs, Sync Status, System Health.

#### 2.6.1 Users Tab
- **Widgets:** User table (name, email, role, department, Snowflake role, last login, status). Action buttons: Invite, Edit, Disable.
- **Interactions:** Click "Invite" → modal with email, role selector, department selector, Snowflake role selector.

#### 2.6.2 Data Sources Tab
- **Widgets:** Snowflake connection configuration form (account URL, warehouse, database, auth method, key upload). "Test Connection" button. Connection status indicator.

#### 2.6.3 Schema Manager Tab
- **Widgets:** Tree view of Database → Schema → Tables. Toggle switches to enable/disable tables from the search index. Column-level detail panel with description editor and PII flag toggle.

#### 2.6.4 Glossary Tab
- **Widgets:** Searchable glossary term table. "Add Term" button opens form: Term name, definition, optional SQL fragment.

#### 2.6.5 Costs Tab
- **Widgets:** Cost dashboard with: daily/weekly/monthly LLM cost line chart, Snowflake credit consumption chart, per-user cost breakdown table, cost budget gauge with alert threshold.

#### 2.6.6 Sync Status Tab
- **Widgets:** Last sync timestamp, tables synced count, schema diff summary, "Sync Now" button, sync history table (last 30 syncs with status).

#### 2.6.7 System Health Tab
- **Widgets:** Health check grid (PostgreSQL, Redis, Snowflake, LLM Provider) — each with green/yellow/red indicator. API latency chart (p50, p95, p99). Active WebSocket connections count. Cache hit ratio gauge.

---

### 2.7 Profile & Settings Page

- **Purpose:** User profile management and personal preferences.
- **Target User:** All authenticated users.
- **Widgets:**
  - **Profile Section:** Name, email, role, department (read-only — managed by Admin/SSO).
  - **Preferences:** Default date range, default chart theme, notification preferences (email/in-app toggle per alert type).
  - **Theme Toggle:** Light/Dark mode switch.
  - **Session Info:** Current session start time, last activity, active devices.
  - **Query History:** Searchable list of user's past AI Chat queries with: query text, timestamp, status, "Re-run" button.

---

### 2.8 Knowledge Base / Help Page

- **Purpose:** In-app documentation and self-service help for users.
- **Target User:** All authenticated users.
- **Widgets:**
  - **Getting Started Guide:** Interactive walkthrough of core features.
  - **Example Queries:** Categorized example questions users can click to auto-populate the chat input.
  - **KPI Dictionary:** Searchable list of all KPIs with definitions and formulas (read from the KPI catalog).
  - **FAQ:** Common questions about data accuracy, access permissions, and feature usage.
  - **Contact Support:** Link to support channel or feedback form.
- **Empty State:** Not applicable (always has content).

---

## 3. Responsive Design Strategy

| Breakpoint | Layout | Key Changes |
|:---|:---|:---|
| **Desktop (≥1280px)** | Full sidebar + content area | Chat split-screen available |
| **Tablet (768-1279px)** | Collapsible sidebar + full content | Chart grid reduces to 2 columns |
| **Mobile (< 768px)** | Bottom navigation + full content | Chat full-screen only. Dashboard stacks vertically. V1 is desktop-optimized; mobile is functional but not primary. |

---

## 4. Accessibility Standards

- All interactive elements must be keyboard navigable (Tab order, Enter/Space activation).
- Color contrast ratio ≥ 4.5:1 for text (WCAG AA).
- All charts must include an accessible data table alternative (toggled via "View Data" button).
- Screen reader labels on all buttons, inputs, and navigation elements.
- Focus indicators visible on all interactive elements.
