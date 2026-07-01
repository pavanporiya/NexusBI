# NexusBI Phase 2.2: Enterprise Data Warehouse Blueprint

**Document Version:** 1.0.0  
**Status:** Approved for Implementation  
**Author:** Principal Data Architect & Snowflake Data Architect  
**Target Platform:** Snowflake Enterprise Data Cloud  

---

## 1. Business Domains

The NexusBI Enterprise Data Warehouse (EDW) is structured around bounded business domains. This ensures a clean modular topology that prevents inter-domain spaghetti dependencies.

```text
                                  ┌───────────────┐
                                  │   Metadata    │
                                  └───────┬───────┘
                                          │ monitors
                                          ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                                FINANCE                                    │
│   ┌───────────────┐        ┌───────────────┐        ┌───────────────┐     │
│   │   Payments    ├───────>│     Sales     │<───────┤    Returns    │     │
│   └───────────────┘        └───────┬───────┘        └───────────────┘     │
└────────────────────────────────────┼──────────────────────────────────────┘
                                     │ logs events
                                     ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                              OPERATIONS                                   │
│   ┌───────────────┐        ┌───────────────┐        ┌───────────────┐     │
│   │   Inventory   │<───────┤   Shipping    ├───────>│  Warehouses   │     │
│   └───────────────┘        └───────────────┘        └───────────────┘     │
└───────────────────────────────────────────────────────────────────────────┘
                                     ▲
                                     │ references dimensions
┌────────────────────────────────────┴──────────────────────────────────────┐
│                               ENTITIES                                    │
│   ┌───────────────┐        ┌───────────────┐        ┌───────────────┐     │
│   │   Customers   │        │   Products    │        │   Employees   │     │
│   └───────────────┘        └───────────────┘        └───────────────┘     │
└───────────────────────────────────────────────────────────────────────────┘
```

### 1.1 Sales Domain
* **Business Meaning:** Captures all commercial revenue-generating transactions.
* **Boundaries:** Begins when an order is finalized by a customer; ends when the transaction is cleared or marked as failed/cancelled.
* **Ownership:** Global Sales & E-commerce Operations.
* **Justification:** The primary driver of business analysis. It acts as the core fact generation point for revenue, average order value (AOV), and customer order frequency.

### 1.2 Customer Domain
* **Business Meaning:** Tracks the identity, demographics, behavioral cohorts, and lifetime profiles of company buyers.
* **Boundaries:** Begins at customer account registration; updates with profile edits, purchases, and marketing touches.
* **Ownership:** Customer Success & Marketing Operations.
* **Justification:** Essential for calculating Customer Lifetime Value (CLV), churn rates, retention trends, and cohort-specific trends.

### 1.3 Product Domain
* **Business Meaning:** Stores the corporate catalog containing items, categories, pricing tiers, and bundles.
* **Boundaries:** Governs product metadata from product release configuration to product deprecation.
* **Ownership:** Product Management & Merchandising.
* **Justification:** Forms the dimension backbone for sales categorizations, inventory stock codes, and product recommendation engines.

### 1.4 Inventory Domain
* **Business Meaning:** Tracks the real-time stock levels, replenishment orders, safety margins, and cost of goods sold (COGS) in warehouses.
* **Boundaries:** Records stock receipts, allocations, stock adjustments, and stock write-offs.
* **Ownership:** Supply Chain & Logistics.
* **Justification:** Critical for monitoring inventory turn ratios, out-of-stock rates, and forecasting warehousing capacity constraints.

### 1.5 Marketing Domain
* **Business Meaning:** Records customer acquisition campaigns, ad spend, marketing attribution, and click-through rates.
* **Boundaries:** Begins at campaign creation; tracks campaign touches, conversions, and campaign spend allocations.
* **Ownership:** Growth Marketing Team.
* **Justification:** Provides the baseline attribution data to calculate Customer Acquisition Cost (CAC) and Return on Ad Spend (ROAS).

### 1.6 Finance & Payments Domain
* **Business Meaning:** Tracks ledger accounts, invoices, payment transaction states (successful, settled, refunded), payment methods, and transaction costs.
* **Boundaries:** Links sales transactions to underlying cash reconciliations and payment gateway fees.
* **Ownership:** Corporate Finance.
* **Justification:** Drives gross margin calculations, cash flow statements, and DSO (Days Sales Outstanding) tracking.

### 1.7 Returns & Support Domain
* **Business Meaning:** Governs returned merchandise processing, credit notes, refunds, support tickets, and customer satisfaction metrics (CSAT).
* **Boundaries:** Processes order returns from request through warehouse receipt, refund issuance, and support ticket closure.
* **Ownership:** Customer Experience & Logistics operations.
* **Justification:** Feeds return rate calculations, product defect alerts, and customer support volume monitors.

### 1.8 Shipping & Fulfillment Domain
* **Business Meaning:** Tracks fulfillment operations, carrier tracking events, delivery time stamps, and shipping carrier fees.
* **Boundaries:** Starts at order pick-pack completion; ends when carrier confirms delivery to the customer.
* **Ownership:** Logistics & Shipping Partners.
* **Justification:** Computes delivery SLA compliance rates, average fulfillment times, and shipping margin leakages.

### 1.9 Warehouses Domain
* **Business Meaning:** Represents physical and logical storage facilities, locations, capacity limits, and operating overheads.
* **Boundaries:** Manages warehouse physical layout mapping, operating cost parameters, and site availability.
* **Ownership:** Facilities & Global Supply Chain.
* **Justification:** Essential dimension for calculating shipping zones, warehousing efficiencies, and geographical sales mapping.

### 1.10 Employees & Workforce Domain
* **Business Meaning:** Stores internal organizational charts, department budgets, headcounts, roles, and resource costs.
* **Boundaries:** Governs employee records from hire to termination.
* **Ownership:** HR & Corporate Planning.
* **Justification:** Backs administrative RLS controls (who can view what data) and provides workforce cost baselines for operational efficiency metrics.

---

## 2. Conceptual Data Model

The conceptual model defines how domains interact. Relationships are governed by business event links:

* **Customer** *places* **Sales Transactions** (1 to Many relationship).
* **Sales Transactions** *contain* **Products** (Many to Many relationship, resolved by line-item fact details).
* **Sales Transactions** *trigger* **Payments** (1 to 1 or 1 to Many for split payments).
* **Products** *are stored in* **Warehouses** (Many to Many relationship, monitored by inventory snapshot states).
* **Shipping Carriers** *fulfill* **Sales Transactions** (Many to 1 relationship).
* **Returns** *reference* original **Sales Transactions** and **Products** (1 to 1 or Many to 1).
* **Marketing Campaigns** *attract* **Customers** (Many to Many relationship, resolved by attribution tables).
* **Employees** *manage* **Warehouses** and *own* **Metadata Catalog** boundaries.

---

## 3. Logical Data Model

Below are the definitions of the major logical entities within the EDW:

### 3.1 Order Entity
* **Purpose:** Represents the core purchase contract between the company and customer.
* **Business Description:** Captures the timestamp, status, tax, discount, shipping fees, currency, and total amount of a transaction.
* **Relationships:** Belongs to a Customer; contains multiple Order Items; links to a Payment; references a Shipping Address.
* **Ownership:** Sales Domain.
* **Lifecycle:** Starts as "Pending", transitions to "Paid", then "Fulfilled", and terminates at "Completed" or "Returned/Refunded".
* **Dependencies:** Requires Customer and Product definitions to exist.

### 3.2 Product Entity
* **Purpose:** Defines a sellable SKU within the corporate catalog.
* **Business Description:** Includes item name, SKU code, category, brand, supplier cost, baseline price, dimension metrics, and active status.
* **Relationships:** Links to Order Items; maps to Inventory levels; associates with Suppliers.
* **Ownership:** Product Domain.
* **Lifecycle:** Active during catalog availability; archived upon deprecation.
* **Dependencies:** Category hierarchy structures.

### 3.3 Customer Profile Entity
* **Purpose:** Houses the single point of truth for customer identities and metrics.
* **Business Description:** Stores name, email, billing country, registration date, tier (Free/Premium), acquisition channel, and cohort month.
* **Relationships:** Links to Orders; links to Support Tickets; maps to Attribution events.
* **Ownership:** Customer Domain.
* **Lifecycle:** Extends from registration until account deletion (compliant with GDPR right to erasure).
* **Dependencies:** None.

### 3.4 Payment Transaction Entity
* **Purpose:** Tracks currency exchange validation for sales completion.
* **Business Description:** Stores transaction ID, gateway name (Stripe, Adyen), fee amount, status, and settlement time.
* **Relationships:** Links 1:1 to an Order; links to a Finance ledger account.
* **Ownership:** Finance Domain.
* **Lifecycle:** Immutable once payment status reaches "Settled" or "Refunded".
* **Dependencies:** Order entity.

### 3.5 Inventory Stock State Entity
* **Purpose:** Monitors physical supply levels in real time.
* **Business Description:** Tracks SKU, Warehouse ID, units on hand, units allocated to orders, safety stock limit, and unit cost.
* **Relationships:** Links to Product SKU; links to Warehouse facility.
* **Ownership:** Inventory Domain.
* **Lifecycle:** Updated continuously by logistics transactions.
* **Dependencies:** Product and Warehouse entities.

---

## 4. Physical Warehouse Strategy

To optimize analytical query performance, storage, and retrieval within Snowflake, tables are physically categorized:

```text
┌────────────────────────────────────────────────────────┐
│                        DIMENSIONS                      │
│   ┌───────────────┐  ┌───────────────┐  ┌───────────┐  │
│   │ dim_customers │  │  dim_products  │  │ dim_dates │  │
│   └───────┬───────┘  └───────┬───────┘  └─────┬─────┘  │
└───────────┼──────────────────┼────────────────┼────────┘
            │                  │                │
            ▼                  ▼                ▼
┌────────────────────────────────────────────────────────┐
│                          FACTS                         │
│   ┌────────────────────────────────────────────────┐   │
│   │                fct_order_items                 │   │
│   │               (Grain: Line Item)               │   │
│   └────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────┘
```

### 4.1 Fact Tables
* **Role:** Store numerical measures and foreign keys pointing to dimensions. Represent business events.
* **Examples:** `fct_order_items`, `fct_payment_transactions`, `fct_shipping_events`, `fct_support_tickets`.
* **Justification:** Designed for high-volume append operations. Star schema join layouts enable Snowflake to leverage micro-partition pruning efficiently.

### 4.2 Dimension Tables
* **Role:** Store descriptive attributes used to filter and group fact measures.
* **Examples:** `dim_customers`, `dim_products`, `dim_warehouses`, `dim_dates`, `dim_campaigns`.
* **Justification:** Contain denormalized, high-cardinality descriptive data. Query tools (and the AI generator) join facts to dimensions to create readable dashboards.

### 4.3 Bridge Tables
* **Role:** Resolve many-to-many relationships between dimensions.
* **Examples:** `bridge_customer_segments` (a customer can have multiple segments; a segment has multiple customers).
* **Justification:** Prevents double-counting of metrics when joining across multi-valued dimensions.

### 4.4 Reference Tables
* **Role:** Store static codes, standard conversion factors, currency rates, and parameters.
* **Examples:** `ref_currency_rates`, `ref_postal_codes`, `ref_status_codes`.
* **Justification:** Keeps lookup values consistent across different fact and dimension models.

### 4.5 Metadata & Audit Tables
* **Role:** Track ELT sync dates, row counts, pipeline audit stats, and data quality check results.
* **Examples:** `audit_elt_runs`, `meta_schema_catalog`, `audit_data_quality_log`.
* **Justification:** Provides the monitoring layer for pipeline health. The AI system reads the catalog to check for column name updates.

### 4.6 Snapshot Tables
* **Role:** Capture state balances at regular intervals (e.g., daily, monthly).
* **Examples:** `snap_daily_inventory_levels`, `snap_monthly_customer_balances`.
* **Justification:** Avoids recalculating transaction histories to find historical balances (e.g., "what was our stock level on June 1st?").

### 4.7 Aggregate Tables
* **Role:** Store pre-summarized data to speed up high-level dashboard queries.
* **Examples:** `agg_daily_revenue_by_category`, `agg_monthly_cohort_retention`.
* **Justification:** Speeds up response times for high-level executive queries, saving Snowflake compute credits by avoiding full fact table scans.

---

## 5. Star Schema Strategy

The core transactional engine of the EDW uses a dimensional star schema design.

### 5.1 Sales Star Schema Example

```text
               ┌───────────────────────┐
               │     dim_customers     │
               │   Surrogate Key: id   │
               └───────────┬───────────┘
                           │ 1:N
                           ▼
┌───────────────┐ 1:N ┌───────────────────────┐ N:1 ┌───────────────┐
│   dim_dates   ├────>│    fct_order_items    │<────┤ dim_products  │
│ Surrogate Key │     │ Grain: One line item  │     │ Surrogate Key │
└───────────────┘     │  Measures: quantity,  │     └───────────────┘
                      │  price, discount, net │
                      └───────────▲───────────┘
                           │ 1:N
                           │
                       ┌───┴───────────┐
                       │ dim_campaigns │
                       │ Surrogate Key │
                       └───────────────┘
```

* **Facts:** `fct_order_items`
* **Dimensions:** `dim_customers`, `dim_products`, `dim_dates`, `dim_campaigns`
* **Grain:** One row per individual item line in a sales order.
* **Measures:** `quantity_ordered`, `unit_price`, `discount_applied`, `tax_amount`, `shipping_amount`, `gross_revenue`, `net_revenue`, `cogs`.
* **Business Events:** The completion of a customer checkout.
* **Surrogate Keys:** Autogenerated hash values (e.g., `md5(customer_natural_id)`) used as join keys. This shields the warehouse from source system key changes.
* **Natural Keys:** Source IDs (e.g., `customer_id` from the production database, `sku` from the ERP).
* **Slowly Changing Dimensions (SCD):**
  * **SCD Type 1 (Overwrite):** Applied to `dim_products.price` overrides and category adjustments where only current states matter.
  * **SCD Type 2 (History Retention):** Applied to `dim_customers.billing_country` and `dim_customers.tier`. Uses `valid_from`, `valid_to`, and `is_current` columns to track historical changes.
  * **Justification:** If a customer moves from the US to the UK, older orders must remain associated with the US for regional tax reporting, while new orders are attributed to the UK.

---

## 6. KPI Mapping

This section defines how the core KPIs from Task 2 map to the physical warehouse tables:

| KPI | Source Fact | Required Dimensions | Calculation Flow | Business Meaning |
|:---|:---|:---|:---|:---|
| **Gross Revenue** | `fct_order_items` | `dim_dates`, `dim_products` | `sum(quantity * unit_price)` | Total sales volume before discounts, tax, and returns. |
| **CLV (Customer Lifetime Value)** | `fct_order_items` | `dim_customers` | `sum(net_revenue)` grouped by `customer_surrogate_key` | Total net profit generated by a single customer account over its lifetime. |
| **Return Rate** | `fct_order_items`, `fct_returns` | `dim_products`, `dim_dates` | `sum(returned_quantity) / sum(ordered_quantity)` | Percentage of ordered products that are returned by customers. |
| **Inventory Turn Ratio** | `snap_daily_inventory_levels`, `fct_order_items` | `dim_products`, `dim_dates` | `sum(cogs) / average(inventory_valuation)` | Measures how fast stock is sold and replaced over a period. |
| **CAC (Customer Acquisition Cost)** | `fct_marketing_spend`, `dim_customers` | `dim_dates`, `dim_campaigns` | `sum(marketing_spend) / count(new_customers)` | Average marketing cost required to acquire one new customer. |

---

## 7. Data Flow Topology

```
[ Source Systems ] (ERP, CRM, Stripe, GA)
       │
       ▼ (Staged ingest via Fivetran/Snowpipe)
[ Raw Schema (DB_RAW) ] (Landing tables, transient objects)
       │
       ▼ (dbt compilation & cleaning)
[ Staging Schema (DB_STG) ] (Deduplicated, cast types, column renaming)
       │
       ▼ (dbt dimensional modeling)
[ Warehouse Schema (DB_ANALYTICS) ] (fct_*, dim_*, snapshots, aggregates)
       │
       ▼ (dbt Semantic Layer configurations)
[ Semantic Model Spec ] (Metrics, metrics boundaries, dimensions)
       │
       ▼ (LLM schema mapping via pgvector)
[ NexusBI AI Engine ] (NL-to-SQL compile, self-healing validation)
       │
       ▼ (Snowflake warehouse run execution)
[ React Client UI ] (ECharts interactive dashboard delivery)
```

1. **Source Systems:** Raw transaction systems, CRM databases, payment gateways, and ad network trackers.
2. **Raw Layer:** Landed tables in Snowflake (`DB_RAW` database). No transformations are applied. Data is stored in raw JSON/Variant or structural tables.
3. **Staging:** `dbt` reads from the raw layer, cleans up null values, casts data types, and renames fields to match standard conventions (`stg_` prefix models).
4. **Transformation:** Staging tables are joined and transformed into fact and dimension models, snapshots, and aggregates.
5. **Warehouse:** The final analytics-ready schema (`dim_`, `fct_` tables). This is the only database layer exposed to the BI semantic layer.
6. **Semantic Layer:** Translates the database structure into business terms. It maps physical columns to KPIs (e.g., mapping `fct_order_items.price` to the "Revenue" metric).
7. **AI Layer:** The NexusBI engine reads the semantic layer. The LLM translates user queries into SQL using these verified paths.
8. **Dashboard:** The compiled SQL runs on Snowflake, returning JSON rows that render as interactive charts in the UI.

---

## 8. Snowflake Platform Optimization

This section defines the performance optimization and cost management configurations for Snowflake:

```text
                    [ Ad-hoc User Query ]
                              │
                              ▼
                ┌───────────────────────────┐
                │   Result Cache Lookup     │ ─── (Hit: Return immediately)
                └─────────────┬─────────────┘
                              │ Miss
                              ▼
                ┌───────────────────────────┐
                │   Metadata Cache Scan     │ ─── (Partitions pruned here)
                └─────────────┬─────────────┘
                              │
                              ▼
                ┌───────────────────────────┐
                │  Warehouse Compute Run    │ ─── (Reads local SSD cache)
                └───────────────────────────┘
```

### 8.1 Micro-Partitioning & Pruning
* **Mechanism:** Snowflake automatically stores table rows in compressed micro-partitions (50MB to 500MB). It uses metadata pointers (min/max values per column) to skip irrelevant partitions during queries.
* **Optimization Rule:** Fact tables are ordered by event date (`ordered_at`) during ELT loads.
* **Justification:** This aligns the physical data storage with time-range query filters (e.g., `WHERE ordered_at >= '2026-06-01'`). Queries prune up to 95% of partitions without needing indexing overhead.

### 8.2 Clustering Keys
* **Rule:** Table clustering keys are defined on high-volume fact tables (e.g., clustering `fct_order_items` on `(ordered_date, product_category)`).
* **Justification:** Prevents performance degradation over time as tables grow. Snowflake automatically reclusters data in the background, keeping queries fast.

### 8.3 Caching Layers
* **Result Cache:** Retains query results for 24 hours. Identical queries return instantly without starting a compute warehouse.
* **Local Disk Cache:** Compute warehouses store queried data on local SSDs. Subsequent queries scanning the same data read from SSD rather than remote storage.
* **Metadata Cache:** Snowflake stores table statistics in a metadata layer, allowing queries like `COUNT(*)` to return instantly without scanning data.

### 8.4 Warehouse Sizing & Auto-Scaling
* **Routing Rules:**
  * Metadata crawling & sync: **XS Single Warehouse** (low resource needs).
  * Ad-hoc user queries: **S Multi-Cluster Warehouse** (scaled to 1-5 clusters to handle concurrency spikes).
  * Heavy nightly ELT runs: **L Single Warehouse** (optimized for deep batch transformations).
* **Auto-Suspend:** Set to 60 seconds across all warehouses to prevent idle compute costs.

---

## 9. Data Governance

### 9.1 Data Quality Rules (Great Expectations / dbt-expectations)

```text
                       [ Sync Triggered ]
                               │
                               ▼
                   ┌───────────────────────┐
                   │    Null & Type Checks │ ── (Fail: Stop sync, alert SRE)
                   └───────────┬───────────┘
                               │ Pass
                               ▼
                   ┌───────────────────────┐
                   │ Cardinality & Limits  │ ── (Fail: Flag anomalies)
                   └───────────┬───────────┘
                               │ Pass
                               ▼
                   ┌───────────────────────┐
                   │ Update Vector Index   │
                   └───────────────────────┘
```

* **Null Checks:** Columns marked as primary keys (e.g., `customer_id`, `product_id`) must have 0% null values.
* **Cardinality Checks:** Junction tables must pass referential integrity checks (every foreign key must match an active dimension record).
* **Range Checks:** Financial metrics must fall within logical boundaries (e.g., `unit_price >= 0`, `discount_applied <= unit_price`).
* **PII Redaction:** Columns marked as PII (emails, names) are masked at the database level. Only authorized roles (e.g., HR/Admin) see unmasked values.

### 9.2 Lineage Tracking
* **Tooling:** `dbt` auto-generates lineage graphs tracking data transformations from raw source tables down to final dimension and fact tables.
* **Ownership:** Analytics Engineering Lead.
* **Justification:** Ensures that any change to a source table can be traced downstream to find which KPI metrics and dashboards are affected.

---

## 10. Final Data Architecture Review

### 10.1 Strengths
* **Symmetrical Star Schemas:** Simplifies the database structure for the AI query generator. The LLM only needs to understand standard fact-to-dimension joins.
* **Snowflake Caching:** Minimizes compute costs. Over 30% of repeated business dashboard queries can be served directly from Snowflake's result cache.
* **dbt-Backed Transformations:** Keeps data transformations testable, version-controlled, and documented.

### 10.2 Weaknesses & Risks
* **Metadata Crawl Latency:** If the metadata crawler fails to sync schema updates, the AI agent will generate queries using outdated column structures, leading to SQL execution errors.
* **Compute Cost Spikes:** Poorly phrased natural language queries (e.g., running massive joins without date filters) can trigger full table scans, consuming compute credits quickly.

### 10.3 Recommendations
* **Enforce Date Filters:** The AI compiler must automatically inject a default date filter (e.g., `ordered_at >= CURRENT_DATE - 365`) into any query that doesn't specify a time range.
* **Query Cost Limits:** Enable Snowflake query timeout limits (e.g., aborting queries that run longer than 45 seconds) to prevent run-away credit consumption.
