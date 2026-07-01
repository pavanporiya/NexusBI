# NexusBI Phase 2 — Task 3: Complete User Journey Maps

**Document Version:** 2.0.0  
**Date:** July 1, 2026

---

## 1. CEO User Journey

### 1.1 Login
1. CEO opens `app.nexusbi.com` in browser.
2. Redirected to corporate Okta SSO login page.
3. Authenticates via password + MFA (push notification to Okta Verify).
4. Redirected back to NexusBI. JWT issued with role `EXECUTIVE`.
5. **Screen:** Landing page shows the CEO's personalized "Executive Command Center" dashboard.

### 1.2 Navigation
- **Top Bar:** NexusBI logo, global search bar, notification bell (anomaly alerts), user avatar with settings dropdown.
- **Left Sidebar:** Dashboard (home), AI Chat, Favorites, Shared With Me.
- **No admin panels, schema editors, or technical tools visible.** The CEO interface is deliberately simplified.

### 1.3 AI Chat
1. CEO clicks "AI Chat" in the sidebar. Chat panel opens (full-width or split-screen with dashboard).
2. **Empty state:** Pre-populated suggestion chips: "How is revenue trending?", "Show profit margins by region", "Compare this quarter vs last quarter."
3. CEO types: "How are we doing this month compared to last month?"
4. **Loading state:** Animated progress steps: "Understanding your question..." → "Finding relevant data..." → "Generating analysis..." → "Preparing visualization..."
5. **Response:** NexusBI returns a grouped bar chart comparing key metrics (Revenue, Gross Profit, AOV, Order Count) for current month vs. prior month. Below the chart: a 3-bullet executive summary with recommendations.
6. CEO follows up: "Why did the North region drop?" — The system preserves context, drills into North region data, returns a line chart with an anomaly annotation and root-cause hypothesis.

### 1.4 Dashboard
1. CEO returns to the Executive Command Center dashboard.
2. **Layout:** 4-6 pinned KPI cards at the top (Revenue, Net Profit, Profit Margin, Customer Count, NPS). Below: 2-3 pinned charts from previous AI Chat sessions.
3. CEO clicks the "Forecast" button on the Revenue KPI card.
4. A 6-month revenue forecast overlays the existing trend line with confidence bands.
5. CEO clicks a chart, selects "Share with VP Operations" from the context menu. The chart appears in the VP's "Shared With Me" section.

### 1.5 Reports
- CEO does not generate reports directly. They pin charts and share dashboard links.
- If the CEO asks the AI Chat "Send me a summary of this week's performance," the system compiles the visible dashboard KPIs into a formatted email digest (V2 feature — in V1, the CEO can screenshot or export the dashboard as PNG).

### 1.6 Forecast
- Forecasting is accessed through the AI Chat ("Forecast revenue for next quarter") or via the "Forecast" button on any time-series chart.
- CEO sees: historical line + dotted forecast line + shaded 95% confidence interval.
- Below the chart: plain-English interpretation ("Revenue is projected to reach $16.1M next quarter, representing 13% YoY growth, assuming current trends continue.").

### 1.7 Alerts
- **V1:** CEO sees a notification bell icon with a red badge when anomalies are detected during scheduled data refreshes.
- Clicking the bell shows a dropdown: "Revenue dropped 18% day-over-day in the North region (detected at 6:00 AM UTC)."
- CEO can click to view the anomaly chart or dismiss.

### 1.8 Recommendations
- Recommendations appear automatically below every AI Chat response containing data analysis.
- Format: 3 numbered action items with supporting data points.
- Example: "1. Investigate North region shipping cost increase (+22% in Q2). 2. Consider expanding the premium bundle to the APAC market (AOV uplift potential: $35). 3. Monitor churn rate — trending upward for 3 consecutive months."

### 1.9 Export
- CEO can export any chart as PNG (right-click context menu).
- CEO can copy a dashboard share link to send via Slack or email.
- CSV/JSON export is NOT available for the CEO role (to prevent accidental raw data exposure).

### 1.10 Logout
- CEO clicks avatar → "Sign Out."
- JWT is invalidated server-side. Session removed from Redis.
- Redirected to Okta logout page, then back to NexusBI login screen.

---

## 2. Business Analyst User Journey

### 2.1 Login
- Same SSO flow as CEO. JWT role: `ANALYST`.
- **Screen:** Landing page shows the Analyst's workspace with recent conversations, pinned dashboards, and a prominent AI Chat entry point.

### 2.2 Navigation
- **Left Sidebar:** Dashboard, AI Chat, My Queries (history of past SQL generations), Favorites, Shared With Me, Data Explorer.
- **Additional feature vs. CEO:** "Data Explorer" panel showing available schemas and tables the analyst has access to.

### 2.3 AI Chat
1. Analyst types: "Show me customer cohort retention rates for the last 12 months by acquisition channel."
2. System identifies this requires a cohort analysis. RAG retrieves `dim_customers`, `fct_orders`, `dim_channels`.
3. SQL is generated with `DATE_TRUNC`, window functions, and cohort bucketing logic.
4. **Response:** Cohort heatmap showing retention percentages. Each cell is color-coded (green = high retention, red = low).
5. Analyst follows up: "Filter to only organic channels and export the data."
6. System regenerates SQL with `WHERE channel_type = 'organic'`, returns updated heatmap.
7. Analyst clicks "Export CSV" — downloads the raw data table behind the chart.

### 2.4 Dashboard
- Analyst has personal dashboards and shared team dashboards.
- Can create new dashboards: Click "New Dashboard" → name it → drag charts from AI Chat history into the dashboard grid.
- Can rearrange, resize, and delete chart widgets.

### 2.5 Reports
- Analyst can view the generated SQL for any AI Chat response by clicking "View SQL" below the chart.
- The SQL is displayed in a syntax-highlighted panel. Analyst can copy it, modify it externally, or flag it as incorrect (feedback loop for model improvement).

### 2.6 Forecast
- Analyst triggers forecasts from AI Chat or from chart context menus.
- Can customize forecast parameters: horizon (3, 6, 12 months), confidence level (80%, 90%, 95%).
- Can overlay multiple forecast scenarios on the same chart for comparison.

### 2.7 Alerts
- Same notification system as CEO.
- Additionally, Analyst can configure custom alerts (V2): "Alert me if weekly churn rate exceeds 5%."

### 2.8 Recommendations
- Same as CEO but with additional detail. Analyst sees the data supporting each recommendation and can drill into it.

### 2.9 Export
- **CSV:** Raw data table behind any chart.
- **JSON:** Structured data for programmatic use.
- **PNG:** Chart image for presentations.
- **SQL:** Copy the generated SQL query.

### 2.10 Logout
- Same as CEO.

---

## 3. Data Analyst / Engineer User Journey

### 3.1 Login
- Same SSO flow. JWT role: `DATA_ENGINEER`.
- **Screen:** Landing page shows the Schema Manager and recent metadata sync status alongside AI Chat.

### 3.2 Navigation
- **Left Sidebar:** Dashboard, AI Chat, Schema Manager, Glossary Editor, Audit Logs, Sync Status, Settings.
- **Unique features:** Schema Manager, Glossary Editor, and Audit Logs are only visible to this role and Admin.

### 3.3 AI Chat
- Data Analyst uses AI Chat the same way as Business Analyst.
- **Additional capability:** Every AI Chat response shows a "Debug" panel with:
  - The full system prompt sent to the LLM
  - The schemas retrieved from the vector store
  - The generated SQL (editable — Data Analyst can correct and re-execute)
  - The Snowflake execution plan and query duration
  - Token count and estimated cost for the LLM call

### 3.4 Dashboard
- Same capabilities as Business Analyst.

### 3.5 Schema Manager
1. **Screen:** Table listing all synced databases, schemas, and tables with columns: Name, Row Count, Last Sync, Status (Active/Disabled), Description Quality Score.
2. Data Analyst clicks on a table (e.g., `fct_orders`).
3. **Detail view:** Lists all columns with: Name, Data Type, Nullable, Description, PII Flag, Tags.
4. Data Analyst edits the description for `net_revenue`: Changes from "Revenue column" to "The final revenue amount after all discounts, returns, and taxes have been applied. Used as the canonical revenue metric for executive reporting."
5. The updated description is re-embedded into the vector store on save.

### 3.6 Glossary Editor
1. **Screen:** Searchable list of business term definitions.
2. Data Analyst adds a new glossary entry:
   - **Term:** "Active Customer"
   - **Definition:** "A customer who has placed at least one order in the last 90 days."
   - **SQL Fragment:** `customer_id IN (SELECT customer_id FROM fct_orders WHERE order_date >= DATEADD('day', -90, CURRENT_DATE()))`
3. This definition is embedded into the vector store and injected into SQL generation prompts when the term "active customer" appears in a user query.

### 3.7 Audit Logs
1. **Screen:** Paginated table of all AI Chat queries across all users.
2. Columns: Timestamp, User, Query Text, Generated SQL, Execution Time, Token Cost, Status (Success/Failed/Self-Healed).
3. Data Analyst can filter by: user, date range, status, cost threshold.
4. Clicking a row shows the full debug trace: prompt, LLM response, SQL, execution plan, result row count.

### 3.8 Sync Status
1. **Screen:** Shows the last metadata sync timestamp, number of tables synced, number of changed schemas detected, and any sync errors.
2. Data Analyst can trigger a manual re-sync by clicking "Sync Now."
3. Shows a diff of what changed since the last sync (new tables, dropped columns, modified descriptions).

### 3.9 Export
- Same as Business Analyst, plus ability to export audit logs as CSV.

### 3.10 Logout
- Same as CEO.

---

## 4. Operations Manager User Journey

### 4.1 Login
- Same SSO flow. JWT role: `MANAGER`. JWT contains additional claim: `department: "operations"`.
- **Screen:** Landing page shows the Operations Dashboard with supply chain KPIs.

### 4.2 Navigation
- **Left Sidebar:** Dashboard, AI Chat, Favorites, Shared With Me, Alerts.
- Similar to CEO but with department-specific default dashboard.

### 4.3 AI Chat
1. Manager types: "What's our delivery SLA compliance this week by carrier?"
2. System generates SQL against `fct_shipments` and `dim_carriers`.
3. **Important:** The Manager's Snowflake role (`OPS_MANAGER_ROLE`) automatically filters data to only their region/department. They cannot see finance or HR data.
4. **Response:** Bar chart showing SLA compliance by carrier. Carrier B is highlighted in red (below 90% threshold).
5. Manager follows up: "Show me Carrier B's late deliveries broken down by reason."

### 4.4 Dashboard
- Pre-configured Operations Dashboard with pinned KPIs: Delivery SLA, Order Fulfillment Time, Warehouse Utilization, Inventory Turnover.
- Manager can pin additional charts from AI Chat sessions.
- Cannot create dashboards visible to other departments (can share within Operations team).

### 4.5 Alerts
- Manager receives anomaly alerts specific to Operations KPIs.
- Example notification: "Warehouse utilization in Dallas exceeded 90% threshold (currently 93.2%)."
- Manager can click the alert to view the anomaly chart and AI-generated recommendations.

### 4.6 Forecast
- Manager can forecast operational metrics: "Forecast warehouse utilization for the next 3 months."
- System validates time-series requirements and returns forecast with confidence bands.
- Interpretation text: "Dallas warehouse is projected to reach 97% utilization by September, creating fulfillment bottlenecks. Consider redistributing inventory to Chicago (currently at 58% utilization)."

### 4.7 Recommendations
- Operations-specific recommendations are generated based on the data context.
- Example: "1. Shift 15% of Dallas inventory to Chicago warehouse. 2. Renegotiate SLA terms with Carrier B or evaluate Carrier D as alternative. 3. Add evening shift staffing to reduce post-4pm fulfillment delays."

### 4.8 Export
- Same as Business Analyst (CSV, JSON, PNG).

### 4.9 Logout
- Same as CEO.

---

## 5. System Administrator User Journey

### 5.1 Login
- Same SSO flow. JWT role: `ADMIN`.
- **Screen:** Landing page shows the Admin Control Panel with system health metrics.

### 5.2 Navigation
- **Left Sidebar:** Admin Panel (home), User Management, Datasource Config, Schema Manager, Glossary Editor, Audit Logs, Cost Monitor, Sync Manager, System Health, AI Chat.
- Admin has access to ALL features across all roles.

### 5.3 User Management
1. **Screen:** Table of all users with: Name, Email, Role, Department, Last Login, Status (Active/Disabled).
2. Admin can: invite new users, assign roles, disable accounts, map users to Snowflake roles.
3. Admin clicks "Add User" → enters email, selects role (CEO/Analyst/Manager/Data Analyst), assigns department, maps Snowflake role.
4. User receives an email invitation to join via SSO.

### 5.4 Datasource Configuration
1. **Screen:** Form for configuring Snowflake connection parameters.
2. Fields: Account URL, Warehouse Name, Database, Default Schema, Authentication Method (Key-Pair), Key Upload.
3. Admin uploads the Snowflake RSA private key (stored encrypted in Vault/PostgreSQL encrypted column).
4. "Test Connection" button validates connectivity and displays the Snowflake version, available roles, and accessible databases.

### 5.5 Cost Monitor
1. **Screen:** Dashboard showing:
   - **LLM Costs:** Daily/weekly/monthly token usage and cost breakdown by model (Claude 3.5 Sonnet, Haiku, embeddings).
   - **Snowflake Costs:** Credits consumed by NexusBI-generated queries, broken down by warehouse size and user.
   - **Per-User Cost:** Average cost per user per day (target: under $0.50).
2. Admin can set cost alerts: "Notify me if daily LLM costs exceed $100."
3. Admin can set per-user query limits to control runaway costs.

### 5.6 System Health
1. **Screen:** Real-time system health indicators:
   - API response times (p50, p95, p99)
   - Database connection pool utilization
   - Redis memory usage
   - LLM API error rates
   - Metadata sync status (last successful sync timestamp)
2. Health checks: Green/Yellow/Red indicators for each subsystem.

### 5.7 Schema Manager & Glossary Editor
- Same interface as Data Analyst, with additional capability to enable/disable entire databases or schemas from the search index.

### 5.8 Audit Logs
- Same interface as Data Analyst, with additional capability to export compliance reports and filter by security events (permission denials, PII access attempts).

### 5.9 AI Chat
- Admin has full AI Chat access with debug panels visible.
- Admin's Snowflake role typically has broader access for testing purposes.

### 5.10 Logout
- Same as CEO. Admin sessions have a shorter idle timeout (30 minutes vs. 8 hours for other roles) as a security measure.
