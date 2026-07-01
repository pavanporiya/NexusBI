# NexusBI Phase 2 — Task 2: Enterprise Business KPI Catalog

**Document Version:** 2.0.0  
**Date:** July 1, 2026

---

## 1. KPI Catalog Purpose

This catalog defines every standard business KPI that NexusBI must understand, calculate, and visualize out of the box. Each KPI entry provides the semantic definition that will be embedded into the vector store and referenced by the Text-to-SQL compiler. When a user asks "Show me our profit margin," the system must resolve to the exact formula defined here — not the LLM's generic understanding.

---

## 2. Financial KPIs

### 2.1 Revenue (Total Revenue)
- **Business Definition:** The total income generated from the sale of goods or services before any deductions.
- **Formula:** `SUM(order_line_items.unit_price * order_line_items.quantity)`
- **Business Importance:** The top-line indicator of business scale and growth trajectory. Every executive dashboard starts here.
- **Owner:** CFO / VP Finance
- **Visualization Type:** Line Chart (time-series trend), KPI Scorecard (current period total)
- **Update Frequency:** Daily
- **Required Data Sources:** `fct_orders`, `fct_order_line_items`, `dim_date`
- **Example Interpretation:** "Total revenue for Q2 2026 was $14.2M, representing a 12% increase over Q2 2025."

### 2.2 Gross Profit
- **Business Definition:** Revenue remaining after deducting the direct cost of goods sold (COGS). Measures production and sourcing efficiency.
- **Formula:** `SUM(revenue) - SUM(cost_of_goods_sold)`
- **Business Importance:** Indicates whether core operations are profitable before overhead. A declining gross profit with stable revenue signals rising input costs.
- **Owner:** CFO / VP Finance
- **Visualization Type:** Line Chart (trend), Stacked Bar (revenue vs. COGS breakdown)
- **Update Frequency:** Daily
- **Required Data Sources:** `fct_orders`, `fct_order_line_items`, `dim_products` (for COGS mapping)
- **Example Interpretation:** "Gross profit was $8.5M on $14.2M revenue (59.9% margin). COGS increased 3% due to raw material price increases in APAC suppliers."

### 2.3 Net Profit
- **Business Definition:** The final profit after all expenses — COGS, operating expenses, taxes, interest, and depreciation.
- **Formula:** `SUM(revenue) - SUM(cogs) - SUM(operating_expenses) - SUM(taxes) - SUM(interest)`
- **Business Importance:** The definitive measure of business profitability. Drives investor confidence and valuation.
- **Owner:** CFO
- **Visualization Type:** Line Chart (trend), KPI Scorecard
- **Update Frequency:** Monthly
- **Required Data Sources:** `fct_orders`, `fct_expenses`, `fct_tax_records`
- **Example Interpretation:** "Net profit for June 2026 was $1.8M (12.7% net margin), down from $2.1M in May due to one-time legal settlement costs."

### 2.4 Profit Margin (Gross & Net)
- **Business Definition:** Profitability expressed as a percentage of revenue. Gross margin measures production efficiency; net margin measures total operational efficiency.
- **Formula (Gross):** `(SUM(revenue) - SUM(cogs)) / SUM(revenue) * 100`
- **Formula (Net):** `SUM(net_profit) / SUM(revenue) * 100`
- **Business Importance:** Enables comparison across time periods, product lines, and competitors regardless of absolute revenue scale.
- **Owner:** CFO / VP Finance
- **Visualization Type:** Line Chart (trend over time), Grouped Bar (by product category or region)
- **Update Frequency:** Monthly
- **Required Data Sources:** `fct_orders`, `fct_expenses`, `dim_products`, `dim_regions`
- **Example Interpretation:** "Gross margin improved from 57% to 60% after renegotiating supplier contracts. Net margin held steady at 12.5%."

### 2.5 Average Order Value (AOV)
- **Business Definition:** The average monetary value of each customer order.
- **Formula:** `SUM(order_total_amount) / COUNT(DISTINCT order_id)`
- **Business Importance:** Indicates whether upselling and cross-selling strategies are effective. A rising AOV with stable order counts means more revenue per transaction.
- **Owner:** VP Sales / VP Marketing
- **Visualization Type:** Line Chart (trend), Bar Chart (by customer segment or channel)
- **Update Frequency:** Daily
- **Required Data Sources:** `fct_orders`, `dim_customers`, `dim_channels`
- **Example Interpretation:** "AOV increased from $127 to $142 after introducing the premium bundle option in March."

### 2.6 Customer Lifetime Value (CLV / CLTV)
- **Business Definition:** The predicted total revenue a business expects from a single customer account over their entire relationship.
- **Formula:** `AVG(order_value) * AVG(purchase_frequency_per_year) * AVG(customer_lifespan_years)`
- **Business Importance:** Determines how much the company can afford to spend on acquiring a customer while remaining profitable. If CLV < CAC, the business model is unsustainable.
- **Owner:** VP Marketing / VP Sales
- **Visualization Type:** Bar Chart (by customer segment), KPI Scorecard
- **Update Frequency:** Monthly
- **Required Data Sources:** `fct_orders`, `dim_customers`, `fct_customer_events`
- **Example Interpretation:** "Enterprise segment CLV is $24,500 (3.2x the SMB segment CLV of $7,600), validating the decision to expand enterprise sales headcount."

### 2.7 Customer Acquisition Cost (CAC)
- **Business Definition:** The total cost of acquiring a new customer, including marketing spend, sales team costs, and onboarding expenses.
- **Formula:** `SUM(marketing_spend + sales_costs) / COUNT(new_customers_acquired)` over a period
- **Business Importance:** Must be evaluated against CLV. A healthy business maintains CLV:CAC ratio of at least 3:1.
- **Owner:** VP Marketing / CMO
- **Visualization Type:** Line Chart (trend), Grouped Bar (by acquisition channel)
- **Update Frequency:** Monthly
- **Required Data Sources:** `fct_marketing_spend`, `fct_sales_costs`, `dim_customers` (first_order_date for new customer identification)
- **Example Interpretation:** "CAC dropped from $380 to $290 after shifting 30% of paid search budget to organic content marketing. CLV:CAC ratio improved from 2.8:1 to 3.6:1."

---

## 3. Customer & Retention KPIs

### 3.1 Customer Retention Rate
- **Business Definition:** The percentage of existing customers who remain active over a defined period.
- **Formula:** `((customers_at_end - new_customers_acquired) / customers_at_start) * 100`
- **Business Importance:** Retention is 5-25x cheaper than acquisition. A 5% increase in retention can increase profits by 25-95%.
- **Owner:** VP Customer Success
- **Visualization Type:** Line Chart (monthly trend), Cohort Heatmap
- **Update Frequency:** Monthly
- **Required Data Sources:** `dim_customers`, `fct_orders`, `fct_subscriptions`
- **Example Interpretation:** "Monthly retention rate is 94.2%, up from 91.8% after launching the loyalty rewards program in Q1."

### 3.2 Repeat Purchase Rate
- **Business Definition:** The percentage of customers who make more than one purchase within a defined period.
- **Formula:** `COUNT(customers_with_orders > 1) / COUNT(DISTINCT customers_with_orders) * 100`
- **Business Importance:** Measures customer loyalty and product-market fit. High repeat rates indicate strong satisfaction.
- **Owner:** VP Sales / VP Marketing
- **Visualization Type:** Bar Chart (by product category), Line Chart (trend)
- **Update Frequency:** Monthly
- **Required Data Sources:** `fct_orders`, `dim_customers`
- **Example Interpretation:** "Repeat purchase rate for the Electronics category is 67%, compared to 41% for Home & Garden, suggesting stronger brand loyalty in electronics."

### 3.3 Conversion Rate
- **Business Definition:** The percentage of visitors or leads who complete a desired action (purchase, signup, demo request).
- **Formula:** `COUNT(conversions) / COUNT(total_visitors_or_leads) * 100`
- **Business Importance:** The core metric for marketing and sales funnel efficiency. Small improvements in conversion rate compound into significant revenue gains.
- **Owner:** VP Marketing / VP Sales
- **Visualization Type:** Funnel Chart, Line Chart (trend by channel)
- **Update Frequency:** Daily
- **Required Data Sources:** `fct_web_sessions`, `fct_orders`, `dim_channels`, `dim_campaigns`
- **Example Interpretation:** "Website conversion rate improved from 2.1% to 2.8% after redesigning the checkout flow, generating an estimated $420K in additional monthly revenue."

### 3.4 Churn Rate
- **Business Definition:** The percentage of customers who stop using the product or cancel their subscription within a defined period.
- **Formula:** `COUNT(churned_customers) / COUNT(customers_at_start_of_period) * 100`
- **Business Importance:** The inverse of retention. High churn signals product dissatisfaction, competitive displacement, or pricing misalignment.
- **Owner:** VP Customer Success / CEO
- **Visualization Type:** Line Chart (trend), Cohort Heatmap, Bar Chart (by churn reason)
- **Update Frequency:** Monthly
- **Required Data Sources:** `dim_customers`, `fct_subscriptions`, `fct_churn_events`
- **Example Interpretation:** "Monthly churn rate spiked to 6.2% in April (from baseline 3.8%) following the 15% price increase. Customers citing 'pricing' as the cancellation reason increased by 180%."

### 3.5 Customer Satisfaction Score (CSAT)
- **Business Definition:** A direct measure of customer satisfaction, typically collected via post-interaction surveys on a 1-5 or 1-10 scale.
- **Formula:** `COUNT(satisfied_responses) / COUNT(total_survey_responses) * 100` (where satisfied = rating >= 4 on a 5-point scale)
- **Business Importance:** Leading indicator of retention and word-of-mouth growth. CSAT below 75% signals systemic product or service issues.
- **Owner:** VP Customer Success / VP Support
- **Visualization Type:** Gauge Chart, Line Chart (trend), Bar Chart (by support category)
- **Update Frequency:** Weekly
- **Required Data Sources:** `fct_survey_responses`, `dim_customers`, `dim_support_tickets`
- **Example Interpretation:** "CSAT score is 82%, with the lowest scores concentrated in the 'Billing & Payments' category (68%), indicating a need for billing UX improvements."

### 3.6 Net Promoter Score (NPS)
- **Business Definition:** Measures customer loyalty by asking "How likely are you to recommend us?" on a 0-10 scale. Respondents are categorized as Promoters (9-10), Passives (7-8), or Detractors (0-6).
- **Formula:** `(% Promoters) - (% Detractors)`
- **Business Importance:** Industry-standard benchmark for brand loyalty. NPS > 50 is considered excellent; > 70 is world-class.
- **Owner:** CEO / VP Customer Success
- **Visualization Type:** Gauge Chart, Stacked Bar (Promoters/Passives/Detractors), Line Chart (trend)
- **Update Frequency:** Quarterly
- **Required Data Sources:** `fct_nps_surveys`, `dim_customers`
- **Example Interpretation:** "NPS improved from +38 to +47 following the launch of the new mobile app. Promoters increased by 12% while Detractors decreased by 6%."

---

## 4. Operations & Supply Chain KPIs

### 4.1 Refund Rate
- **Business Definition:** The percentage of orders that result in a full or partial refund.
- **Formula:** `COUNT(refunded_orders) / COUNT(total_orders) * 100`
- **Business Importance:** High refund rates erode margins and signal product quality, fulfillment accuracy, or marketing expectation mismatches.
- **Owner:** VP Operations / VP Product
- **Visualization Type:** Line Chart (trend), Bar Chart (by product category or refund reason)
- **Update Frequency:** Weekly
- **Required Data Sources:** `fct_orders`, `fct_refunds`, `dim_products`
- **Example Interpretation:** "Refund rate for the Apparel category is 14.2% (vs. 3.1% company average), driven by sizing inconsistencies. Recommend standardizing size charts."

### 4.2 Inventory Turnover
- **Business Definition:** The number of times inventory is sold and replaced over a period. Measures how efficiently inventory is managed.
- **Formula:** `SUM(cost_of_goods_sold) / AVG(inventory_value)`
- **Business Importance:** High turnover means efficient inventory management. Low turnover means capital is tied up in unsold stock, increasing storage costs and obsolescence risk.
- **Owner:** VP Supply Chain / VP Operations
- **Visualization Type:** Bar Chart (by product category), Line Chart (trend)
- **Update Frequency:** Monthly
- **Required Data Sources:** `fct_inventory_snapshots`, `fct_order_line_items`, `dim_products`, `dim_warehouses`
- **Example Interpretation:** "Inventory turnover for Electronics is 8.2x (healthy), but Home Décor is 2.1x (slow-moving). Recommend markdown strategy for Home Décor items older than 120 days."

### 4.3 Delivery SLA Compliance
- **Business Definition:** The percentage of orders delivered within the promised delivery window.
- **Formula:** `COUNT(orders_delivered_on_time) / COUNT(total_orders_shipped) * 100`
- **Business Importance:** Directly impacts customer satisfaction and repeat purchase behavior. Amazon has trained customers to expect 1-2 day delivery; SLA failures drive churn.
- **Owner:** VP Logistics / VP Operations
- **Visualization Type:** Line Chart (trend), Heatmap (by region and carrier), Bar Chart (by carrier)
- **Update Frequency:** Daily
- **Required Data Sources:** `fct_shipments`, `fct_orders`, `dim_carriers`, `dim_regions`
- **Example Interpretation:** "Overall SLA compliance is 94.7%, but West Coast deliveries via Carrier B dropped to 87.3% due to the port delays in Long Beach. Recommend shifting 20% of West Coast volume to Carrier A."

### 4.4 Warehouse Utilization
- **Business Definition:** The percentage of available warehouse storage capacity currently occupied.
- **Formula:** `SUM(occupied_storage_units) / SUM(total_storage_capacity) * 100`
- **Business Importance:** Utilization below 60% means over-investment in warehouse space; above 90% creates bottlenecks and increases pick/pack errors.
- **Owner:** VP Supply Chain / VP Operations
- **Visualization Type:** Gauge Chart, Bar Chart (by warehouse location)
- **Update Frequency:** Weekly
- **Required Data Sources:** `fct_inventory_snapshots`, `dim_warehouses`
- **Example Interpretation:** "Dallas warehouse utilization hit 93%, creating pick/pack bottlenecks. Chicago warehouse is at 58%. Recommend redistributing 15% of Dallas inventory to Chicago."

### 4.5 Order Fulfillment Time
- **Business Definition:** The average time from order placement to shipment dispatch.
- **Formula:** `AVG(DATEDIFF('hour', order_placed_at, order_shipped_at))`
- **Business Importance:** Faster fulfillment enables shorter delivery windows and improves customer satisfaction. Increasing fulfillment times signal operational capacity issues.
- **Owner:** VP Operations
- **Visualization Type:** Line Chart (trend), Histogram (distribution), Bar Chart (by warehouse)
- **Update Frequency:** Daily
- **Required Data Sources:** `fct_orders`, `fct_shipments`, `dim_warehouses`
- **Example Interpretation:** "Average fulfillment time is 4.2 hours, meeting the 6-hour SLA. However, orders placed after 4pm have a 9.1-hour average, suggesting insufficient evening shift staffing."

---

## 5. Marketing & Campaign KPIs

### 5.1 Marketing ROI (ROMI)
- **Business Definition:** The return on investment for marketing spend, measuring revenue generated per marketing dollar spent.
- **Formula:** `(SUM(attributed_revenue) - SUM(marketing_spend)) / SUM(marketing_spend) * 100`
- **Business Importance:** Determines which marketing channels and campaigns generate profitable returns. Guides budget allocation decisions.
- **Owner:** CMO / VP Marketing
- **Visualization Type:** Bar Chart (by channel), Line Chart (trend), Waterfall Chart
- **Update Frequency:** Monthly
- **Required Data Sources:** `fct_marketing_spend`, `fct_orders`, `dim_campaigns`, `dim_channels`, `fct_attribution`
- **Example Interpretation:** "Email marketing ROI is 4,200% ($42 revenue per $1 spent), while paid social ROI is 180%. Recommend reallocating 15% of paid social budget to email automation."

### 5.2 Campaign Performance (Click-Through Rate)
- **Business Definition:** The percentage of recipients or viewers who click on a campaign link or call-to-action.
- **Formula:** `COUNT(clicks) / COUNT(impressions_or_sends) * 100`
- **Business Importance:** Measures creative effectiveness and audience relevance. Low CTR indicates poor targeting or messaging.
- **Owner:** VP Marketing / Marketing Manager
- **Visualization Type:** Bar Chart (by campaign), Line Chart (trend), Table (campaign comparison)
- **Update Frequency:** Daily (for active campaigns)
- **Required Data Sources:** `fct_campaign_events`, `dim_campaigns`, `dim_channels`
- **Example Interpretation:** "The 'Summer Sale' email campaign achieved a 4.8% CTR (vs. 2.1% benchmark), while the LinkedIn ad campaign underperformed at 0.6% CTR."

---

## 6. Workforce & Productivity KPIs

### 6.1 Employee Productivity (Revenue per Employee)
- **Business Definition:** Total revenue divided by the number of full-time equivalent employees.
- **Formula:** `SUM(total_revenue) / COUNT(active_fte_employees)`
- **Business Importance:** Measures organizational efficiency. Declining revenue per employee during growth may indicate hiring outpacing revenue generation.
- **Owner:** CHRO / CFO
- **Visualization Type:** Line Chart (trend), Bar Chart (by department)
- **Update Frequency:** Quarterly
- **Required Data Sources:** `fct_orders`, `dim_employees`, `fct_hr_headcount`
- **Example Interpretation:** "Revenue per employee is $285K, up from $260K last quarter, indicating that the recent automation investments are improving productivity."

### 6.2 Support Ticket Resolution Time
- **Business Definition:** The average time from when a customer support ticket is opened to when it is resolved.
- **Formula:** `AVG(DATEDIFF('hour', ticket_created_at, ticket_resolved_at))`
- **Business Importance:** Directly impacts CSAT. Customers expect resolution within 24 hours for standard issues and 4 hours for critical issues.
- **Owner:** VP Customer Support
- **Visualization Type:** Line Chart (trend), Histogram (distribution), Bar Chart (by priority level)
- **Update Frequency:** Daily
- **Required Data Sources:** `fct_support_tickets`, `dim_support_agents`, `dim_ticket_categories`
- **Example Interpretation:** "Average resolution time is 6.2 hours (within SLA), but P1 tickets are averaging 5.8 hours (exceeding the 4-hour P1 SLA). Escalation process review recommended."

---

## 7. Forecasting & Planning KPIs

### 7.1 Forecast Accuracy
- **Business Definition:** How closely actual results match the predicted forecast values.
- **Formula:** `(1 - ABS(actual_value - forecasted_value) / actual_value) * 100`
- **Business Importance:** Measures the reliability of the forecasting engine. Inaccurate forecasts lead to over/under-stocking, missed revenue targets, and poor resource planning.
- **Owner:** VP Finance / VP Operations
- **Visualization Type:** Line Chart (actual vs. forecast overlay), Bar Chart (accuracy by metric)
- **Update Frequency:** Monthly (retrospective evaluation)
- **Required Data Sources:** `fct_forecasts`, `fct_orders`, `fct_actuals`
- **Example Interpretation:** "Revenue forecast accuracy for Q2 was 94.3% (within the 90% target). Inventory forecast accuracy was 81.2% (below target), driven by unexpected demand spikes in the Electronics category."

### 7.2 Budget Variance
- **Business Definition:** The difference between budgeted and actual spending, expressed as a percentage of the budget.
- **Formula:** `(SUM(actual_spend) - SUM(budgeted_amount)) / SUM(budgeted_amount) * 100`
- **Business Importance:** Negative variance (under-budget) may indicate under-investment; positive variance (over-budget) signals cost control failures.
- **Owner:** CFO / Department Heads
- **Visualization Type:** Waterfall Chart, Bar Chart (by department), KPI Scorecard
- **Update Frequency:** Monthly
- **Required Data Sources:** `fct_budgets`, `fct_expenses`, `dim_departments`, `dim_cost_centers`
- **Example Interpretation:** "Engineering department is 8% over budget ($2.4M actual vs. $2.2M budget), driven by unplanned cloud infrastructure scaling costs. Marketing is 5% under budget."

### 7.3 Days Sales Outstanding (DSO)
- **Business Definition:** The average number of days it takes to collect payment after a sale is made.
- **Formula:** `(SUM(accounts_receivable) / SUM(total_credit_sales)) * number_of_days_in_period`
- **Business Importance:** High DSO indicates cash flow problems. If DSO exceeds payment terms (e.g., Net 30), it signals collection process failures.
- **Owner:** CFO / VP Finance
- **Visualization Type:** Line Chart (trend), Bar Chart (by customer segment)
- **Update Frequency:** Monthly
- **Required Data Sources:** `fct_invoices`, `fct_payments`, `dim_customers`
- **Example Interpretation:** "DSO is 38 days (above our Net 30 terms). Enterprise accounts average 45 days. Recommend automated payment reminders at Day 25 and escalation at Day 35."

### 7.4 Working Capital Ratio
- **Business Definition:** Measures the company's ability to meet short-term financial obligations.
- **Formula:** `SUM(current_assets) / SUM(current_liabilities)`
- **Business Importance:** A ratio below 1.0 indicates potential liquidity risk. Between 1.2 and 2.0 is considered healthy.
- **Owner:** CFO
- **Visualization Type:** Gauge Chart, Line Chart (trend)
- **Update Frequency:** Monthly
- **Required Data Sources:** `fct_balance_sheet`, `dim_accounts`
- **Example Interpretation:** "Working capital ratio is 1.65, indicating healthy liquidity. However, the ratio declined from 1.82 last quarter due to increased short-term borrowing for inventory buildup."

---

## 8. KPI Catalog Integration with NexusBI

### 8.1 Semantic Embedding Strategy
Each KPI definition above must be embedded into the vector store as a structured text chunk. When a user asks "What's our profit margin?", the RAG pipeline retrieves the KPI definition, formula, and required data sources — ensuring the SQL generator uses the correct calculation, not a hallucinated formula.

### 8.2 KPI-to-Schema Mapping
Every KPI links to specific fact and dimension tables. The metadata sync engine must validate that these tables exist in the customer's Snowflake instance during onboarding. Missing tables trigger a setup wizard recommending the required data transformations.

### 8.3 KPI Ownership & Alerting
Each KPI has a designated business owner role. The alerting system (V2) will automatically route anomaly notifications to the appropriate owner based on this catalog mapping.
