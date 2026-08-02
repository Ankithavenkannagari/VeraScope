---
name: data-model
description: Use this skill whenever an agent needs to understand the schema, validate joins, or write correct SQL for the Olist (OLIST_ECOMMERCE) or Adventure Works (ADVENTURE_WORKS) databases.
---

# Data Model Skill

## Purpose
Use this skill whenever an agent needs to understand the schema, validate joins, and write correct SQL for the AI Analyst project.

This skill applies to both databases used by the project:
- OLIST_ECOMMERCE / RAW_DATA
- ADVENTURE_WORKS / DATA

## Core Rules
- Always confirm the target database and schema before writing SQL.
- Use the correct grain for the question being answered.
- Never join tables at different levels of detail without aggregating first.
- Prefer the primary key / foreign key relationship that matches the business logic.
- If a relationship is unclear, state the assumption instead of guessing.

## General Data Modeling Guidance
- Fact tables generally contain events or transactions.
- Dimension tables generally describe entities such as customers, products, sellers, or dates.
- Bridge or mapping tables should be used only when the relationship is many-to-many.
- Date tables should be used for time-based analysis whenever available.
- Use filters consistently so that measures are calculated on the intended population.

## Database 1: OLIST_ECOMMERCE / RAW_DATA

### Typical model structure
The Olist dataset is usually organized around an e-commerce transaction model:
- Customers describe buyers.
- Orders capture purchase events.
- Order items represent the line-level products within each order.
- Products describe the items sold.
- Sellers describe the merchants fulfilling orders.
- Payments and reviews provide additional transaction-level context.

### Expected relationship patterns
- Customer -> Orders: one customer can place many orders.
- Orders -> Order Items: one order can contain many line items.
- Order Items -> Products: each line item references a product.
- Order Items -> Sellers: each line item is associated with a seller.
- Orders -> Payments: one order can have one or more payment records depending on the dataset.
- Orders -> Reviews: one order may have one review record.

### SQL guidance for Olist
- Use orders as the central fact for order-level analysis.
- Use order_items for product-level or revenue-level analysis.
- Use customers and sellers for segmentation.
- When calculating revenue, ensure the metric is based on the correct grain.
- If analyzing product performance, aggregate from order_items to avoid double-counting.

## Database 2: ADVENTURE_WORKS / DATA

### Typical model structure
The Adventure Works dataset is usually organized around sales and product data:
- Customers represent buyers.
- Sales orders capture transactions.
- Sales order details capture line-level products per order.
- Products describe the catalog items.
- Salespeople and territories provide sales organization context.
- Dates support time-based reporting.

### Expected relationship patterns
- Customer -> Sales Orders: one customer can place many orders.
- Sales Orders -> Sales Order Details: one order can have many line items.
- Sales Order Details -> Products: each line item references a product.
- Sales Orders -> Salespeople / Territories: sales activity is associated with sales organization entities.
- Products -> Product Categories / Subcategories: product hierarchies are typically modeled through category tables.

### SQL guidance for Adventure Works
- Use sales orders or sales order details as the main transaction grain depending on the question.
- Use sales order details for line-item and quantity analysis.
- Use product, customer, and territory dimensions for segmentation.
- For trend analysis, use a date dimension consistently.
- When summarizing by product or customer, make sure the aggregation matches the underlying grain.

## Agent Instructions
When an agent uses this skill, it should:
1. Identify the correct table grain before writing SQL.
2. Select the relevant join path based on the business question.
3. Avoid mixing transaction-level and aggregated data without explicit aggregation.
4. Document any assumptions about missing or ambiguous relationships.
5. Validate that the resulting query is consistent with the data model.

## Common Mistakes to Avoid
- Joining a fact table directly to a dimension table without understanding the cardinality.
- Calculating totals from a line-item table without grouping correctly.
- Using the wrong date field for time-based analysis.
- Treating one-to-many relationships as one-to-one.
- Ignoring duplicate or incomplete keys.

## Output Expectation
Agents should be able to explain:
- the main tables involved,
- the join logic used,
- the grain of the query,
- and any assumptions made.
