# NexusBI Phase 2 — Task 4: AI Decision Pipeline Specification

**Document Version:** 2.0.0  
**Date:** July 1, 2026

---

## Pipeline Overview

The NexusBI AI Decision Pipeline is a 19-stage sequential processing chain that transforms a natural language business question into a validated visualization, statistical forecast, and executive-grade business recommendation. Every stage has defined inputs, outputs, failure modes, and recovery strategies.

```
User Question → Intent → Context → Schema → Metadata → Prompt → LLM →
SQL → Validate → Security → Execute → Result Check → Chart → Insights →
Recommendations → Summary → Memory → Render → User
```

---

## Stage 1: Natural Language Question Ingestion

- **Purpose:** Capture the user's raw text input and attach session metadata (user identity, conversation ID, timestamp, active filters from prior turns).
- **Input:** Raw text string from WebSocket message. User JWT claims (role, department, Snowflake role mapping). Conversation ID (UUID).
- **Output:** `QueryContext` object containing: `raw_text`, `user_id`, `user_role`, `snowflake_role`, `conversation_id`, `timestamp`, `prior_filters` (from memory), `session_language`.
- **Failure Cases:** Empty input string; input exceeding 2,000 characters; non-UTF-8 encoding; WebSocket connection dropped mid-transmission.
- **Recovery Strategy:** Reject empty/oversized inputs with immediate user-facing error (NBI-1008). For encoding issues, attempt UTF-8 normalization. For dropped connections, discard the incomplete message (client-side retry handles reconnection).

---

## Stage 2: Intent Detection & Classification

- **Purpose:** Classify the user's intent into one of the defined action categories to route processing to the correct downstream pipeline branch.
- **Input:** `QueryContext.raw_text` and `prior_filters`.
- **Output:** `IntentResult` containing: `intent_type` (enum: `DATA_QUERY`, `FORECAST_REQUEST`, `ANOMALY_CHECK`, `DASHBOARD_ACTION`, `CLARIFICATION_RESPONSE`, `GENERAL_CHAT`, `EXPORT_REQUEST`), `confidence_score` (0.0-1.0), `extracted_entities` (dates, metrics, dimensions mentioned).
- **Classification Method:** Use a lightweight LLM call (Claude 3 Haiku or GPT-4o-mini) with a structured output schema. The prompt includes the 7 intent categories with 3 examples each. Response is parsed as JSON.
- **Failure Cases:** Confidence score below 0.6 (ambiguous intent); LLM returns malformed JSON; LLM API timeout.
- **Recovery Strategy:** If confidence < 0.6, trigger Stage 3 (Clarification). If JSON parsing fails, retry with explicit format instructions (1 retry). If API timeout, failover to secondary LLM provider.

---

## Stage 3: Business Context Identification & Clarification

- **Purpose:** Resolve ambiguities in the user's question by checking for multiple possible interpretations and, if necessary, asking the user for clarification.
- **Input:** `IntentResult`, `QueryContext`, KPI Catalog definitions (from vector store).
- **Output:** `ResolvedContext` containing: `confirmed_metrics` (list of specific KPI names), `confirmed_dimensions` (list of grouping/filtering fields), `time_range` (start_date, end_date, granularity), `disambiguation_needed` (boolean).
- **Ambiguity Detection Rules:**
  - "Sales" → Could mean `gross_sales`, `net_revenue`, or `order_count`. Check KPI catalog for matches.
  - "Last quarter" → Resolve to exact dates based on server timestamp and fiscal calendar configuration.
  - "Performance" → Too vague without a metric. Trigger clarification.
- **Failure Cases:** User's question contains no identifiable metric or dimension; KPI catalog returns zero matches; user abandons clarification dialog.
- **Recovery Strategy:** If no metric detected, present top 5 suggested KPIs based on the user's department and past query history. If user abandons clarification, persist the partial context and prompt "Would you like to continue where we left off?" on next interaction.

---

## Stage 4: Schema Discovery

- **Purpose:** Identify which database schemas, tables, and columns are relevant to the resolved business context.
- **Input:** `ResolvedContext.confirmed_metrics`, `ResolvedContext.confirmed_dimensions`, KPI-to-schema mapping from the KPI catalog.
- **Output:** `SchemaDiscoveryResult` containing: `candidate_tables` (list of table names with relevance scores), `candidate_columns` (list of columns with data types), `required_joins` (list of join relationships between candidate tables).
- **Discovery Method:** Embed the resolved metric names and dimension names. Execute a vector similarity search against the schema metadata index (pgvector in V1). Return top 15 results ranked by cosine similarity. Cross-reference with the KPI catalog's `required_data_sources` field for validation.
- **Failure Cases:** Vector search returns zero results (schema not indexed or metric not in catalog); vector search returns too many irrelevant results (noisy embeddings); required tables exist but user's Snowflake role lacks access.
- **Recovery Strategy:** Zero results → check for typos using edit distance, suggest corrections. Noisy results → apply metadata filters (restrict to user's authorized schemas). Access denied → inform user which role is needed and suggest contacting Admin.

---

## Stage 5: Semantic Layer Selection

- **Purpose:** Select the semantic layer definitions (business logic, pre-defined calculations, and glossary terms) that are relevant to the query.
- **Input:** `SchemaDiscoveryResult.candidate_tables`, Business Glossary entries from PostgreSQL.
- **Output:** `SemanticContext` containing: `glossary_terms` (list of term definitions with SQL fragments), `kpi_formulas` (list of canonical KPI calculation formulas), `business_rules` (list of filtering rules like "Active Customer = ordered in last 90 days").
- **Selection Method:** For each candidate table, retrieve all glossary terms that reference it. For each confirmed metric, retrieve the canonical KPI formula from the catalog.
- **Failure Cases:** Glossary is empty (no definitions configured); KPI formula references a column that doesn't exist in the customer's schema; conflicting definitions (two glossary entries define "revenue" differently).
- **Recovery Strategy:** Empty glossary → proceed without semantic enrichment (LLM uses raw schema descriptions only, with a warning logged). Missing columns → flag to admin in audit log. Conflicts → use the most recently updated definition and log the conflict for Data Analyst review.

---

## Stage 6: Metadata Retrieval & Context Assembly

- **Purpose:** Assemble the complete metadata context package that will be injected into the LLM prompt.
- **Input:** `SchemaDiscoveryResult`, `SemanticContext`, few-shot example library.
- **Output:** `MetadataPackage` containing: `schema_definitions` (Markdown-formatted table/column descriptions), `join_graph` (list of join paths), `business_rules` (semantic layer definitions), `few_shot_examples` (3-5 similar Text-to-SQL examples), `constraints` (max result size, read-only enforcement, Snowflake syntax rules).
- **Assembly Rules:** Total context must not exceed 8,000 tokens. If it exceeds this limit, progressively remove: (1) least-relevant tables, (2) column descriptions for non-critical columns, (3) reduce few-shot examples from 5 to 3.
- **Failure Cases:** Context exceeds token limit even after pruning; few-shot example library is empty; join graph contains cycles.
- **Recovery Strategy:** Token overflow → escalate to a model with larger context window (only if available). Empty few-shot library → proceed without examples (lower accuracy expected, log warning). Join cycles → use shortest path (Dijkstra) and log the cycle for Data Analyst review.

---

## Stage 7: Prompt Construction

- **Purpose:** Build the complete LLM prompt combining system instructions, metadata context, conversation history, and the user's question.
- **Input:** `MetadataPackage`, `QueryContext`, conversation memory (last 5 turns, compressed).
- **Output:** `PromptPayload` containing: `system_prompt` (static instructions + Snowflake SQL rules + security constraints), `context_block` (metadata package), `conversation_history` (compressed prior turns), `user_message` (current question), `output_format_instructions` (JSON schema for structured SQL output).
- **Prompt Structure:**
  1. System instructions (role definition, output format, security rules)
  2. Schema context (tables, columns, joins, business rules)
  3. Few-shot examples
  4. Conversation history (compressed)
  5. Current user question
  6. Output format specification (return SQL in a JSON wrapper with explanation)
- **Failure Cases:** Prompt exceeds model's maximum context window; system prompt template is corrupted or missing.
- **Recovery Strategy:** Context overflow → trigger aggressive pruning (reduce history to last 2 turns, reduce few-shots to 2). Missing template → fall back to a hardcoded minimal system prompt and alert Admin.

---

## Stage 8: LLM Reasoning & SQL Generation

- **Purpose:** Send the assembled prompt to the primary LLM and receive a structured response containing the generated SQL query and natural language explanation.
- **Input:** `PromptPayload`.
- **Output:** `LLMResponse` containing: `generated_sql` (Snowflake SQL string), `explanation` (natural language description of what the SQL does), `confidence` (self-assessed confidence 0.0-1.0), `suggested_chart_type` (optional hint from LLM).
- **Model Selection:** Primary: Claude 3.5 Sonnet. Fallback: GPT-4o. Emergency fallback: self-hosted Llama-3-70B.
- **Failure Cases:** LLM API returns HTTP 500/503 (provider outage); LLM returns SQL for wrong database dialect (PostgreSQL instead of Snowflake); LLM returns empty SQL; LLM returns multiple SQL statements; response latency exceeds 10 seconds.
- **Recovery Strategy:** API error → retry once, then failover to secondary provider. Wrong dialect → append "IMPORTANT: Use Snowflake SQL syntax only" and retry. Empty SQL → re-prompt with "You must return a SQL query." Multiple statements → reject, re-prompt with "Return exactly one SELECT statement." Timeout → cancel request, failover to secondary provider.

---

## Stage 9: SQL Validation (AST Parsing)

- **Purpose:** Parse the generated SQL into an Abstract Syntax Tree to verify structural correctness and enforce security rules before any database execution.
- **Input:** `LLMResponse.generated_sql`.
- **Output:** `ValidationResult` containing: `is_valid` (boolean), `statement_type` (SELECT/INSERT/UPDATE/DELETE/DDL), `referenced_tables` (list), `referenced_columns` (list), `has_subqueries` (boolean), `errors` (list of syntax errors if any).
- **Validation Rules:**
  1. Statement type MUST be `SELECT`. Any other type → immediate rejection.
  2. No semicolons (prevents statement chaining/injection).
  3. No `INFORMATION_SCHEMA` references (prevents metadata exfiltration).
  4. No `SYSTEM$` function calls.
  5. Must include `LIMIT` clause (inject `LIMIT 50000` if missing).
  6. No `INTO` clause (prevents `SELECT INTO` data export).
- **Parser Library:** `sqlglot` (Python) with Snowflake dialect.
- **Failure Cases:** SQL has syntax errors that sqlglot cannot parse; SQL uses proprietary Snowflake functions not recognized by sqlglot; SQL passes validation but is semantically wrong (correct syntax, wrong tables).
- **Recovery Strategy:** Parse errors → trigger self-healing (Stage 9b). Unrecognized functions → maintain an allowlist of known Snowflake functions; unknown functions are flagged for manual review but allowed through. Semantic errors → caught at execution stage (Stage 11).

### Stage 9b: Self-Healing Loop

- **Purpose:** Automatically correct SQL errors by feeding the error message back to the LLM.
- **Input:** Original `PromptPayload`, `LLMResponse.generated_sql`, error message from parser or Snowflake.
- **Output:** Corrected `LLMResponse` with new SQL.
- **Rules:** Maximum 2 self-healing attempts. If the third attempt still fails, return a user-facing error (NBI-1002) and log the full trace for Data Analyst review.
- **Failure Cases:** LLM repeats the same error; LLM generates a completely different query that doesn't match the user's intent.
- **Recovery Strategy:** Same error repeated → append "Your previous SQL had this error: [error]. Do NOT repeat this mistake." Different query → compare column references with original intent; if >50% divergence, reject and surface error to user.

---

## Stage 10: Security Validation

- **Purpose:** Verify that the generated SQL only accesses tables and columns the user is authorized to query, based on their Snowflake role mapping.
- **Input:** `ValidationResult.referenced_tables`, `ValidationResult.referenced_columns`, `QueryContext.snowflake_role`, authorization policy cache.
- **Output:** `SecurityResult` containing: `authorized` (boolean), `denied_tables` (list of unauthorized tables), `pii_columns` (list of PII columns that require masking), `applied_masks` (list of masking functions applied).
- **Validation Rules:**
  1. Cross-reference all referenced tables against the user's Snowflake role permissions (cached from metadata sync).
  2. Check all referenced columns against the PII column registry.
  3. If PII columns are detected and the user's role lacks PII access, apply masking functions in the SQL or remove the columns.
- **Failure Cases:** Authorization cache is stale (user permissions changed since last sync); PII column not flagged in metadata (classification gap); SQL uses wildcard `SELECT *` which may include PII columns.
- **Recovery Strategy:** Stale cache → execute a real-time permissions check against Snowflake (slower but accurate). Unclassified PII → log a warning for Data Analyst review. Wildcard SELECT → rewrite to explicit column list excluding PII columns, or allow Snowflake's native masking policies to handle it.

---

## Stage 11: Query Execution

- **Purpose:** Execute the validated, security-checked SQL against the Snowflake Data Warehouse.
- **Input:** Validated SQL string, `QueryContext.snowflake_role`, connection pool reference.
- **Output:** `ExecutionResult` containing: `data_frame` (tabular result set), `row_count`, `column_names`, `column_types`, `execution_time_ms`, `snowflake_query_id`, `warehouse_size`, `estimated_credits`.
- **Execution Rules:** Set `USE ROLE <snowflake_role>` before executing. Set query timeout to 30 seconds. Set `LIMIT 50000` if not already present.
- **Failure Cases:** Snowflake warehouse is suspended (cold start delay); query timeout exceeded (complex query on large tables); Snowflake returns an error (table dropped since last sync, permission denied at Snowflake layer); result set is empty.
- **Recovery Strategy:** Warehouse suspended → wait up to 15 seconds for resume, update UI with "Resuming compute warehouse..." status. Timeout → suggest the user add date filters or aggregations to reduce scope. Snowflake error → capture error, trigger metadata re-sync for affected tables, return user-facing error (NBI-1003). Empty result → inform user "No data matches your criteria" with suggestions to broaden filters.

---

## Stage 12: Result Validation

- **Purpose:** Verify that the returned data makes business sense before presenting it to the user.
- **Input:** `ExecutionResult.data_frame`, `ResolvedContext.confirmed_metrics`.
- **Output:** `ValidatedResult` containing: `data_frame` (cleaned), `quality_flags` (list of warnings), `row_count_warning` (if result set is suspiciously small or large).
- **Validation Checks:**
  1. **Null check:** If >50% of the primary metric column is NULL, flag a data quality warning.
  2. **Cardinality check:** If a dimension column has only 1 unique value, the grouping may be wrong.
  3. **Range check:** If numeric values are negative where they shouldn't be (e.g., negative revenue), flag.
  4. **Row count check:** If only 1 row returned for a time-series query, the date filter may be too narrow.
- **Failure Cases:** All values are NULL (schema mismatch); values are orders of magnitude off (wrong aggregation level); result contains future dates (date logic error).
- **Recovery Strategy:** All NULLs → re-check column names against schema, trigger self-healing if mismatch detected. Magnitude errors → log for Data Analyst review, present data with a warning banner. Future dates → sanitize output, log the date logic issue.

---

## Stage 13: Chart Recommendation

- **Purpose:** Determine the optimal visualization type based on the data structure and user's intent.
- **Input:** `ValidatedResult.data_frame` (column names, types, cardinality), `IntentResult.intent_type`.
- **Output:** `ChartSpec` containing: `chart_type` (line, bar, grouped_bar, scatter, pie, heatmap, gauge, kpi_card), `x_axis`, `y_axis`, `color_dimension`, `tooltip_fields`, `title`, `subtitle`.
- **Heuristic Rules:**
  - 1 datetime + 1 numeric → Line Chart
  - 1 categorical (≤10 unique) + 1 numeric → Bar Chart
  - 1 categorical (>10 unique) + 1 numeric → Horizontal Bar Chart (top 10)
  - 2 categorical + 1 numeric → Grouped Bar or Heatmap
  - 2 numeric → Scatter Plot
  - 1 numeric only (single value) → KPI Scorecard
  - Cohort data (date × date) → Cohort Heatmap
  - Percentage/ratio (0-100) → Gauge Chart
- **Failure Cases:** Data structure doesn't match any heuristic rule; multiple equally valid chart types; user previously expressed a chart preference that conflicts.
- **Recovery Strategy:** No match → default to a data table view with a suggestion: "I wasn't sure how to visualize this. Here's the data table — would you prefer a bar chart or line chart?" Multiple matches → choose the first matching rule (rules are ordered by priority). User preference conflict → honor user's stated preference.

---

## Stage 14: Insight Generation

- **Purpose:** Automatically identify statistical patterns, anomalies, and notable data points in the result set.
- **Input:** `ValidatedResult.data_frame`, `ResolvedContext`.
- **Output:** `InsightsList` containing 2-5 structured insights, each with: `type` (trend, anomaly, comparison, ranking), `description` (plain English), `supporting_value` (the specific number), `severity` (info, warning, critical).
- **Detection Methods:**
  - **Trend:** Linear regression on time-series. If slope is significantly positive/negative, report.
  - **Anomaly:** Z-score analysis. Values >2 standard deviations from mean are flagged.
  - **Comparison:** YoY or MoM percentage changes. Flag changes >10%.
  - **Ranking:** Identify top/bottom performers in grouped data.
- **Failure Cases:** Dataset too small for statistical analysis (<5 data points); all values are identical (no variance); anomaly detection produces false positives on seasonal data.
- **Recovery Strategy:** Too small → skip statistical analysis, provide only descriptive insights ("Revenue was $X in the selected period"). No variance → report stability as an insight. False positives → apply seasonal decomposition before anomaly detection (V2 enhancement; V1 uses simple z-score with a warning that seasonal patterns may affect results).

---

## Stage 15: Business Recommendation Generation

- **Purpose:** Generate actionable business recommendations grounded in the data insights.
- **Input:** `InsightsList`, `ValidatedResult.data_frame` (condensed JSON), `QueryContext.user_role`, original user question.
- **Output:** `RecommendationsList` containing 3 structured recommendations, each with: `action` (what to do), `rationale` (why, citing specific data points), `expected_impact` (quantified if possible), `priority` (high/medium/low).
- **LLM Call:** Uses Claude 3.5 Sonnet with a system prompt optimized for business advisory. The prompt instructs the model to be specific, cite numbers from the data, and avoid generic advice.
- **Failure Cases:** LLM generates generic advice not grounded in data; LLM hallucinates numbers not present in the dataset; LLM recommendations contradict each other.
- **Recovery Strategy:** Generic advice → re-prompt with "Your recommendations MUST reference specific numbers from the dataset." Hallucinated numbers → cross-reference all numbers in recommendations against the actual data frame; strip any number not found. Contradictions → present only the highest-confidence recommendation and note that additional analysis is needed.

---

## Stage 16: Executive Summary Compilation

- **Purpose:** Compile a concise, plain-English summary of the entire analysis suitable for an executive audience.
- **Input:** `ChartSpec`, `InsightsList`, `RecommendationsList`, original user question.
- **Output:** `ExecutiveSummary` containing: `headline` (one sentence), `key_findings` (2-3 bullet points), `recommendation_highlight` (top recommendation).
- **Failure Cases:** Summary is too long (>200 words); summary uses technical jargon inappropriate for the user's role.
- **Recovery Strategy:** Too long → truncate to 150 words and append "See full analysis below." Technical jargon → role-aware language filter: for CEO role, replace technical terms with business equivalents.

---

## Stage 17: Conversation Memory Update

- **Purpose:** Persist the current turn's context into conversation memory for multi-turn continuity.
- **Input:** `QueryContext`, `ResolvedContext`, `ValidatedResult` (metadata only — not raw data), `ChartSpec`.
- **Output:** Updated `ConversationMemory` containing: last 10 turns (compressed), active filters, selected metrics, selected dimensions, last chart type.
- **Compression Strategy:** Store only: user question, intent, resolved metrics/dimensions, filters applied, chart type rendered. Discard: raw data frames, full SQL, full LLM prompts. This keeps memory under 2,000 tokens per conversation.
- **Storage:** Redis with TTL of 24 hours. Persistent backup to PostgreSQL for conversations the user explicitly "saves."
- **Failure Cases:** Redis is unavailable; memory exceeds token budget; conversation context becomes incoherent after many turns.
- **Recovery Strategy:** Redis unavailable → degrade gracefully to stateless mode (no multi-turn context, each question treated independently). Token overflow → apply aggressive summarization (keep only last 3 turns). Incoherence → detect via intent classifier confidence drop; suggest user start a new conversation.

---

## Stage 18: Response Rendering & Delivery

- **Purpose:** Package all outputs into a structured WebSocket response payload and deliver it to the client browser.
- **Input:** `ChartSpec`, `ValidatedResult.data_frame`, `ExecutiveSummary`, `InsightsList`, `RecommendationsList`, `LLMResponse.generated_sql`.
- **Output:** WebSocket JSON message containing: `chart_spec` (ECharts JSON), `data` (serialized result set), `summary` (executive summary text), `insights` (structured insight list), `recommendations` (structured recommendation list), `sql` (generated SQL for debug panel), `metadata` (execution time, token cost, query ID).
- **Serialization:** Data frame serialized as Apache Arrow (binary) for large datasets (>1,000 rows) or JSON for small datasets (<1,000 rows).
- **Failure Cases:** WebSocket connection dropped during transmission; payload exceeds WebSocket frame size limit; client-side rendering error.
- **Recovery Strategy:** Connection dropped → buffer response in Redis for 60 seconds; if client reconnects, deliver buffered response. Frame size → chunk large payloads into multiple WebSocket frames with sequence numbers. Client error → include a fallback data table view that works even if chart rendering fails.

---

## Stage 19: Client-Side Rendering

- **Purpose:** The React frontend receives the response payload and renders the interactive visualization, insights panel, and recommendation cards.
- **Input:** WebSocket JSON message from Stage 18.
- **Output:** Rendered UI containing: interactive ECharts visualization, executive summary text, insight highlights, recommendation cards, expandable debug panel (for Data Analyst/Admin roles only).
- **Rendering Pipeline:** Parse ECharts JSON spec → initialize chart canvas → bind data → apply theme (light/dark mode) → enable interactivity (tooltips, zoom, brush selection) → render text panels.
- **Failure Cases:** ECharts spec contains invalid configuration; dataset exceeds browser memory for client-side rendering; user's browser doesn't support required canvas features.
- **Recovery Strategy:** Invalid spec → fall back to data table view. Memory overflow → paginate data (show first 1,000 rows with a "Load More" button). Browser incompatibility → display a "Please use a modern browser" message (minimum: Chrome 90+, Firefox 88+, Safari 15+, Edge 90+).
