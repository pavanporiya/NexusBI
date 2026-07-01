# NexusBI Phase 2.4: AI Intelligence Blueprint

**Document Version:** 1.0.0  
**Status:** Approved for Implementation  
**Author:** Chief AI Architect & Principal AI Engineer  
**Target Platform:** Claude 3.5 Sonnet / Haiku & pgvector Semantic Index  

---

## SECTION 1: AI Vision

The NexusBI AI Intelligence Layer acts as the cognitive core of the platform. Its primary goal is to democratize complex data access by translating natural business questions into secure, optimized SQL executions and transforming raw query tables into actionable executive insights.

### 1.1 Business Problems Solved
* **SQL bottlenecks:** Eliminates the dependency on busy analytics teams to write basic or intermediate SQL queries.
* **Information silos:** Cross-references scattered corporate datasets to answer multi-dimensional business questions.
* **Complex data analysis:** Automatically identifies mathematical trends, statistical anomalies, and root causes without requiring manual Excel operations.
* **Actionable reporting:** Converts raw numbers into executive summaries and recommendations that directly support decision-making.

### 1.2 Justification for Large Language Models (LLMs)
* **Natural language flexibility:** Traditional keyword search engines fail when users ask conversational or ambiguous questions. LLMs understand user intent and business context natively.
* **Dynamic query writing:** Rules-based natural language systems break when schemas change. LLMs adapt dynamically by parsing schema metadata injected into prompts.
* **Advanced business reasoning:** Deep transformer models excel at summarizing complex data patterns and generating professional business recommendations.

### 1.3 AI Boundaries & Rejections
The AI layer must operate within strict security and functional boundaries:

* **Read-only execution:** The AI is strictly barred from drafting or executing any DML/DDL statements (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`).
* **No database writes:** The AI cannot modify database states, schemas, or store any production business data in its weights.
* **No code generation:** The AI cannot generate executable Python, JavaScript, or bash code for server runtimes.
* **No raw credential access:** The AI has no visibility into raw database credentials, connection strings, or system configuration keys.

---

## SECTION 2: AI Capability Matrix

This section catalogs the core cognitive capabilities of the NexusBI AI Intelligence Layer:

| Capability | Input | Reasoning Action | Output | Business Value |
|:---|:---|:---|:---|:---|
| **NL Analytics** | User question, schema metadata | Translates conversational requests into structured SQL blocks. | Executable SQL | Accelerates ad-hoc data access. |
| **Intent Detection** | User prompt | Classifies user request types (e.g., query, forecast, alert). | Intent Enum | Routes request to optimal processing branch. |
| **Business Context** | User prompt, KPI catalog | Resolves generic business terms (e.g., "sales") to concrete KPIs. | Target Metric & Filters | Ensures query calculations are mathematically accurate. |
| **Chart Recommendation** | Data columns, data sizes | Applies visual heuristics to select the best chart type. | ECharts configuration | Displays data in its most readable format. |
| **Executive Summary** | Query results, user question | Summarizes key findings in plain English for executives. | 150-word text summary | Saves executives time when reviewing reports. |
| **Insight Generation** | Data values, historical averages | Runs statistical calculations to spot trends and anomalies. | Structured Insight List | Surfaces critical business changes automatically. |
| **Recommendation Generation** | Selected insights, user business role | Generates actionable business steps to address data trends. | Actions & Expected Impacts | Moves dashboards from descriptive to prescriptive analytics. |
| **Root Cause Analysis** | Anomaly event data, relevant dimensions | Drills down into grouping metrics to identify drivers of anomalies. | Diagnostic explanation | Speeds up issue resolution times for operations. |
| **Conversation Memory** | Prior turn context, active filter states | Preserves context across multi-turn chats. | Active session context | Enables conversational follow-ups. |

---

## SECTION 3: Complete AI Decision Pipeline

This section defines the 14-stage reasoning workflow of the NexusBI AI Intelligence Layer:

```text
[ User Prompt ]
      │
      ▼
1. Authentication & RBAC ──────────> Validate User Claims & Snowflake Role
      │
      ▼
2. Intent Detection ───────────────> Route to Chat, Forecast, or Dashboard Branch
      │
      ▼
3. Business Context Resolution ────> Match prompt to KPI Catalog & dates
      │
      ▼
4. Metadata & Schema Discovery ────> Search pgvector for tables & columns
      │
      ▼
5. Semantic Layer Enrichment ──────> Retrieve business glossary & rules
      │
      ▼
6. Prompt Construction ────────────> Assemble prompt with context & few-shots
      │
      ▼
7. LLM SQL Generation ─────────────> Compile SQL (Claude 3.5 Sonnet)
      │
      ▼
8. AST Security Validation ────────> Block dangerous queries, inject row limits
      │
      ▼
9. Query Execution ────────────────> Run read-only query on Snowflake
      │
      ▼
10. Result Validation ─────────────> Verify row bounds, null levels, & data types
      │
      ▼
11. Chart Selection ───────────────> Map rows to optimal ECharts layout JSON
      │
      ▼
12. Insight & Recommendation Gen ──> Generate business metrics summaries
      │
      ▼
13. Executive Summary Compilation ─> Build plain-English summary of findings
      │
      ▼
[ Client Response ]
```

### 3.1 Pipeline Stage Details

#### Stage 1: Authentication & RBAC Validation
* **Purpose:** Ensure the user is authorized to execute commands before any AI resources are consumed.
* **Inputs:** Request JWT claims, user metadata.
* **Outputs:** Validated `SecurityContext` containing authorization roles and active Snowflake read-only parameters.
* **Dependencies:** Auth Service.
* **Failure Cases:** Expired token, unauthorized access request.
* **Recovery Strategy:** Immediately terminate request pipeline; return HTTP 401/403 with `NBI-1002` error envelope.

#### Stage 2: Intent Detection & Routing
* **Purpose:** Route the user's request to the correct downstream service engine.
* **Inputs:** Raw input string.
* **Outputs:** Intent category classification (e.g., ad-hoc query, forecast generation, dashboard layout updates).
* **Dependencies:** Lightweight classification prompt (Claude 3 Haiku).
* **Failure Cases:** Confusing query where intent classification confidence falls below 0.6.
* **Recovery Strategy:** Route to a clarification flow. Ask the user: "Did you want to view a chart of this data or run a forecast?"

#### Stage 3: Business Context Resolution
* **Purpose:** Resolve generic terms (e.g., "earnings") to canonical metric definitions (e.g., `net_revenue`).
* **Inputs:** User question, KPI catalog.
* **Outputs:** Confirmed KPI identities and resolved date dimensions.
* **Dependencies:** KPI Semantic Catalog.
* **Failure Cases:** The query mentions metrics that do not exist in the KPI catalog.
* **Recovery Strategy:** Search for closely matching terms in the catalog; present suggestions to the user for validation.

#### Stage 4: Metadata & Schema Discovery
* **Purpose:** Locate the exact physical tables and columns needed to write the SQL query.
* **Inputs:** Confirmed KPI metrics and dimensions.
* **Outputs:** Matching candidate tables, columns, and relationship maps.
* **Dependencies:** pgvector Metadata Index.
* **Failure Cases:** Vector search returns zero matching schemas.
* **Recovery Strategy:** Fall back to search for schemas using edit-distance text matching on table comments.

#### Stage 5: Semantic Layer Enrichment
* **Purpose:** Retrieve business calculation logic and glossary terms to ensure SQL queries align with corporate rules.
* **Inputs:** Candidate tables.
* **Outputs:** SQL calculation rules (e.g., "Active Customer = ordered in last 90 days").
* **Dependencies:** Business Glossary Database.
* **Failure Cases:** Conflicting rules exist for a single KPI name.
* **Recovery Strategy:** Retrieve the most recently updated rule; log a warning in the audit trail.

#### Stage 6: Prompt Construction
* **Purpose:** Assemble all metadata, rules, few-shot examples, and user input into a single LLM prompt.
* **Inputs:** User question, schema context, few-shots, conversation memory.
* **Outputs:** Final prompt payload.
* **Dependencies:** Dynamic Prompt Assembly Engine.
* **Failure Cases:** Assembled prompt size exceeds the model's context window.
* **Recovery Strategy:** Prune oldest conversation history first, then reduce the number of few-shot examples.

#### Stage 7: LLM SQL Generation
* **Purpose:** Generate the initial raw SQL query draft.
* **Inputs:** Prompt payload.
* **Outputs:** Raw Snowflake SQL query string.
* **Dependencies:** Claude 3.5 Sonnet API.
* **Failure Cases:** LLM API times out, or returns invalid SQL dialects.
* **Recovery Strategy:** Failover immediately to secondary LLM API provider; re-prompt with dialect rules on failure.

#### Stage 8: AST Security Validation
* **Purpose:** Verify query safety by parsing the SQL structure.
* **Inputs:** Raw SQL string.
* **Outputs:** Verified SQL string or validation error list.
* **Dependencies:** SQLGlot Parser.
* **Failure Cases:** Detects DML/DDL statements, database function calls, or missing limit parameters.
* **Recovery Strategy:** Block execution. Feed syntax errors back to LLM for one healing attempt; reject query if validation fails again.

#### Stage 9: Query Execution
* **Purpose:** Execute the validated SQL query against Snowflake.
* **Inputs:** Validated SQL string, Snowflake credentials mapping.
* **Outputs:** Tabular rows, column metadata, execution statistics.
* **Dependencies:** Snowflake connection pool.
* **Failure Cases:** Database query times out or returns SQL runtime errors.
* **Recovery Strategy:** Route execution error back to LLM self-healing pipeline (max 1 attempt); otherwise surface error message to user.

#### Stage 10: Result Validation
* **Purpose:** Check the query results for data anomalies before formatting the response.
* **Inputs:** Tabular rows, target KPIs list.
* **Outputs:** Cleaned tabular dataset.
* **Dependencies:** Basic statistics rules.
* **Failure Cases:** Query returns zero rows, or columns contain excessive null values.
* **Recovery Strategy:** Inform the user "No data matches your criteria," and suggest adjusting date or department filters.

#### Stage 11: Chart Selection
* **Purpose:** Determine the best chart style to represent the returned data.
* **Inputs:** Dataset shapes, dimensions, value distributions.
* **Outputs:** Optimal visualization type (e.g., Line, Stacked Bar) and ECharts configuration JSON.
* **Dependencies:** Visualization Heuristics rules.
* **Failure Cases:** No rules match the returned dataset layout.
* **Recovery Strategy:** Default to rendering a raw, searchable data table view.

#### Stage 12: Insight & Recommendation Generation
* **Purpose:** Translate raw data patterns into written business findings and actions.
* **Inputs:** Cleaned data values.
* **Outputs:** Bulleted lists of trends, anomalies, and recommendations.
* **Dependencies:** Claude 3.5 Sonnet.
* **Failure Cases:** Generates generic recommendations not supported by the data.
* **Recovery Strategy:** Force LLM to cite specific rows and column numbers for every recommendation generated.

#### Stage 13: Executive Summary Compilation
* **Purpose:** Package the analysis into a concise, plain-English summary.
* **Inputs:** Insights list, recommendations list, original question.
* **Outputs:** 150-word headline summary.
* **Dependencies:** Claude 3 Haiku.
* **Failure Cases:** Summary exceeds the 150-word limit or uses technical jargon.
* **Recovery Strategy:** Truncate output automatically and append a "Show More" link.

#### Stage 14: Response Delivery
* **Purpose:** Package all assets (summary, chart specs, raw data) and return them to the client.
* **Inputs:** Executive summary, ECharts JSON, data frame, debug SQL.
* **Outputs:** WebSocket response payload.
* **Dependencies:** API Gateway router.
* **Failure Cases:** WebSocket connection drops during transmission.
* **Recovery Strategy:** Cache response in Redis for 60 seconds, allowing client-side retry to fetch on reconnection.

---

## SECTION 4: Prompt Engineering Architecture

Prompt configurations are versioned and stored in the `ai/prompts/` directory to manage AI behavior changes systematically.

```text
ai/prompts/
├── system/
│   ├── sql_generator.md        # Structural SQL generation rules
│   └── insight_analyst.md      # McKinsey-style business summary rules
└── few_shot/
    ├── sql_examples.json       # Few-shot query examples
    └── insight_examples.json   # Few-shot summary examples
```

### 4.1 Dynamic Prompt Assembly Flow
Prompts are constructed dynamically at runtime using a five-block structural layout:

```
┌────────────────────────────────────────────────────────┐
│ Block 1: System Core (Dialect, limitations, constraints)│
├────────────────────────────────────────────────────────┤
│ Block 2: Context Block (Schemas, tables, columns)      │
├────────────────────────────────────────────────────────┤
│ Block 3: Semantic Logic (KPI calculations, glossary)  │
├────────────────────────────────────────────────────────┤
│ Block 4: Few-Shots (3-5 verified question-to-SQL pairs)│
├────────────────────────────────────────────────────────┤
│ Block 5: User Query (Current input & memory context)   │
└────────────────────────────────────────────────────────┘
```

### 4.2 Few-Shot Strategy
* **Dynamic Selection:** Few-shot examples are not static. The system vectorizes the user's question, queries the verified `few_shot/sql_examples.json` index, and retrieves the 3-5 most similar past queries to inject into the prompt.
* **Why it matters:** Injecting relevant examples prevents the LLM from hallucinating join paths or column aliases, improving query accuracy.

### 4.3 Prompt Security & Injection Mitigations
* **System Prompt Isolation:** System instructions are clearly separated from user input using XML tags (e.g., `<system_directives>...</system_directives>`).
* **Input Sanitization:** The pipeline scans user queries for injection attacks (e.g., "ignore previous instructions") and rejects the request if malicious patterns are detected.

---

## SECTION 5: Conversation Memory

NexusBI manages conversational state using a dual-memory approach to maintain query context across multi-turn chats:

```text
                    [ WebSocket Request ]
                              │
                              ▼
                ┌───────────────────────────┐
                │   Active Redis Session    │
                │    (Short-term cache)     │
                └─────────────┬─────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
        ┌───────────────────┐   ┌───────────────────┐
        │  Postgres Archive │   │ Context Summarizer│
        │ (Saved sessions)  │   │  (Sliding window) │
        └───────────────────┘   └───────────────────┘
```

### 5.1 Short-Term Memory
* **Storage:** In-memory Redis cache (keyed by `conversation_id`).
* **Content:** Stores the metric and date filter states of the last 5 turns.
* **Justification:** If a user asks "Show me sales in the US," and follows up with "What about the UK?", the system retains the metric selection and updates only the country filter.

### 5.2 Context Window Management (Sliding Window & Compression)
* When memory token sizes exceed 2,000 tokens, the system runs an asynchronous compression job.
* Claude 3 Haiku summarizes older turns (e.g., merging turns 1-4 into a brief summary of active filters) while keeping the most recent 2 turns verbatim. This preserves context without overloading the LLM's prompt token limit.

---

## SECTION 6: Business Reasoning Engine

This section defines the logic rules used by the AI to explain data patterns and anomalies:

```text
               [ Statistical Anomaly Detected ]
                              │
                              ▼
                ┌───────────────────────────┐
                │   Identify Driver Dimension│ ── (e.g., Region: "North")
                └─────────────┬─────────────┘
                              │
                              ▼
                ┌───────────────────────────┐
                │   Drill Down Subgroups    │ ── (e.g., Store A vs Store B)
                └─────────────┬─────────────┘
                              │
                              ▼
                ┌───────────────────────────┐
                │  Construct Root Cause Msg │ ── (e.g., "Out of stock on Item X")
                └───────────────────────────┘
```

### 6.1 Trend & Anomaly Explanations
* The system does not ask the LLM to guess why numbers changed. Instead, it computes statistical metrics first (e.g., rolling averages, standard deviations).
* When an anomaly is detected (e.g., a 35% revenue drop), the system queries sub-dimensions (such as region, product category, or store location) to find the primary driver of the change.
* The LLM is provided with this statistical drill-down data and summarizes it for the user (e.g., "Revenue dropped by 35% due to a 60% decrease in North region product sales").

### 6.2 Recommendation Heuristics
Recommendations must be actionable and follow a strict structural rule:
1. **Action:** What operational change is needed (e.g., "Increase safety stock levels").
2. **Rationale:** Citations from the query data (e.g., "Inventory levels fell below safety margins 4 times last month").
3. **Expected Impact:** Estimated outcome (e.g., "Reduces out-of-stock events by 15%").

---

## SECTION 7: SQL Intelligence

The SQL Intelligence layer acts as the compiler that translates business questions into database commands.

### 7.1 Schema Retrieval
* Rather than sending the entire database schema to the LLM, the system runs a vector search using pgvector to retrieve only the schema metadata and table structures relevant to the user's question.

### 7.2 AST Validation & Parsing
* The generated SQL string is parsed into an Abstract Syntax Tree (AST) using SQLGlot.
* **AST Validation Rules:**
  * Statement type must be `SELECT`. Any other statement type is blocked.
  * Semicolons are stripped to prevent query chaining.
  * Functions not in the system allowlist are flagged.
  * A `LIMIT 50000` clause is injected if not already present, protecting browser and server memory.

---

## SECTION 8: Visualization Intelligence

The system maps data patterns to visualization types using deterministic rules rather than relying on LLM choices. This keeps dashboard styling consistent:

| Data Structure | Optimal Chart | Business Value |
|:---|:---|:---|
| Single numeric value | **KPI Scorecard** | Provides immediate, high-level metric visibility. |
| Time series (1 date column + 1 metric) | **Line Chart** | Highlights trends and changes over time. |
| Low-cardinality comparisons (e.g., <10 categories) | **Bar Chart** | Simplifies comparative analysis between groups. |
| High-cardinality comparisons (e.g., >10 categories) | **Horizontal Bar Chart** | Keeps category names readable on the vertical axis. |
| Multi-dimensional metrics (e.g., date × region × sales) | **Stacked Bar / Heatmap** | Shows metric distributions across two dimensions. |
| Correlation analysis (2 numeric columns) | **Scatter Plot** | Reveals relationship strengths between metrics. |
| Geographic distributions | **Choropleth Map** | Simplifies regional performance evaluations. |

---

## SECTION 9: Hallucination Prevention

To ensure data accuracy, the system runs multiple verification checks before returning answers to the user:

```text
                    [ SQL Generated ]
                           │
                           ▼
             ┌───────────────────────────┐
             │    AST Security Check     │ ── (Fail: Auto-correct/Reject)
             └─────────────┬─────────────┘
                           │ Pass
                           ▼
             ┌───────────────────────────┐
             │    Snowflake Run Check    │ ── (Fail: Capture error, retry)
             └─────────────┬─────────────┘
                           │ Pass
                           ▼
             ┌───────────────────────────┐
             │   Fact Verification Check │ ── (Fail: Strip invalid metrics)
             └─────────────┬─────────────┘
                           │ Pass
                           ▼
                   [ Render Output ]
```

### 9.1 Verification Rules
* **SQL Parsing:** Every query must compile successfully under the SQLGlot Snowflake dialect parser.
* **Fact Verification:** The system matches all metrics in the final summary against the actual columns returned by the query. Any numbers generated by the LLM that do not exist in the source dataset are stripped out.
* **Confidence Scoring:** If the intent classifier confidence score falls below 0.6, or the generated SQL fails AST validation, the system returns a fallback response asking the user to clarify their request.

---

## SECTION 10: Model Strategy

The platform uses a multi-model architecture to balance processing speed, generation accuracy, and API costs:

```text
                             [ User Prompt ]
                                    │
                                    ▼
                      ┌───────────────────────────┐
                      │    Intent Classification  │ ── (Claude 3 Haiku)
                      └─────────────┬─────────────┘
                                    │
                       ┌────────────┴────────────┐
             Query/Data│                         │ Administrative
                       ▼                         ▼
         ┌───────────────────────────┐     ┌───────────────────────────┐
         │     SQL Generation        │     │      General Chat / Help  │
         │   (Claude 3.5 Sonnet)     │     │     (Claude 3 Haiku)      │
         └───────────────────────────┘     └───────────────────────────┘
```

* **Primary Model (Claude 3.5 Sonnet):** Handles SQL query construction and generating business recommendations.
* **Secondary Model (Claude 3 Haiku):** Handles intent routing, visual chart selection, and summarizing final results.
* **Embedding Model (`text-embedding-3-small`):** Vectorizes metadata comments and glossary terms.
* **Reranking (`cohere-rerank-v3`):** Reranks pgvector search results to ensure only the most relevant table contexts are injected into prompts.
* **Query Caching:** Pre-compiled SQL queries and execution results are cached in Redis. Matches return instantly, avoiding LLM generation latency and Snowflake compute costs.

---

## SECTION 11: Enterprise AI Review

### 11.1 Weaknesses & Risks
* **Prompt Drift:** Changes in Anthropic's model versions can affect how Claude interprets prompts, potentially leading to query syntax errors.
* **Cold Starts:** If the vector database return times increase, prompt assembly times can exceed latency targets.
* **Context Overload:** Complex schemas with hundreds of tables can overwhelm the LLM context window, resulting in dropped join paths.

### 11.2 Recommendations
* **Automated Prompt Validdation:** Run daily prompt regression tests against a golden dataset (Tasks 7) to catch syntax issues before they hit production.
* **Schema Pruning:** Implement strict metadata category scoping, limiting vector searches to tables matching the user's primary business unit.
