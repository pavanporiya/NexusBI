# Database Semantic Mapping Specification: dbt Project

This directory contains the dbt (data build tool) transformations and semantic definitions used to map Snowflake raw data into clean, business-conforming structures.

## 🗺️ Semantic Layer Ingest Architecture

Rather than pointing the LLM SQL generator directly at raw database tables, NexusBI utilizes dbt semantic models to maintain business rules (e.g., how `"active_revenue"` is defined).

```
┌──────────────────────────────────────┐
│         Snowflake Raw Tables         │
│      (stg_orders, stg_customers)     │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│           dbt Clean Models           │
│     (fct_orders, dim_customers)      │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│         dbt Semantic Models          │
│   (Dimensions, Metrics, Joins Specs) │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│       NexusBI Ingestion Engine       │
│  (Crawl schemas & upsert embeddings) │
└──────────────────────────────────────┘
```

## ⚙️ Catalog Synchronization Workflow
1. **Metadata Compilation:** When dbt compiles models, it outputs a `manifest.json` file containing full definitions of columns, descriptions, primary keys, relationships, and business metrics.
2. **Sync Service Crawl:** The NexusBI Ingestion Service reads this compiled file and maps it against the live Snowflake catalog `INFORMATION_SCHEMA`.
3. **Vector Vectorization:** Changed schema models are converted into text chunks:
   ```text
   Model Name: fct_orders
   Columns:
     - order_id (Primary Key)
     - customer_id (Foreign Key to dim_customers)
     - gross_revenue (Metric: Sum of price * quantity)
   Description: The fact table tracking customer checkouts and transaction volumes.
   ```
4. **Qdrant Index Sync:** The text chunks are vectorized using an embedding model and upserted to the Qdrant database to allow RAG-based context retrieval during Text-to-SQL compile.

## 🚦 Best Practices for Data Engineers
* **Always document columns in dbt `schema.yml`:** The SQL generator relies heavily on descriptions in order to map user questions to target columns.
* **Define join relationships explicitly:** Maintain foreign and primary key constraints in dbt config blocks so the query builder can write valid join paths automatically.
