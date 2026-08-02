---
name: metrics-glossary
description: Use this skill to define, compute, and report business metrics (revenue, order count, AOV, review score, cancellation/return rate, etc.) consistently for the Olist and Adventure Works databases. Never define a metric ad hoc — check here first.
---

# Metrics Guide for AI Analyst

## Purpose
Use this guide to define, compute, and report business metrics consistently for both databases used in this project.

Databases covered:
- OLIST_ECOMMERCE / RAW_DATA
- ADVENTURE_WORKS / DATA

## General Metric Rules
- Always define the metric before computing it.
- Use the correct grain of analysis.
- State the formula clearly.
- Specify the time period and population.
- Use consistent units and naming.
- Avoid mixing order-level and line-item-level metrics without explicit aggregation.

## Olist Metrics

### 1. Total Revenue
- Definition: Total value of completed orders.
- Typical formula: SUM(order_value) or SUM(price * quantity) depending on the available table.
- Best used when: evaluating sales performance or order value trends.
- Recommended grain: order level or line-item level depending on the question.

### 2. Order Count
- Definition: Number of orders placed.
- Typical formula: COUNT(DISTINCT order_id).
- Best used when: measuring business volume.
- Recommended grain: order level.

### 3. Average Order Value
- Definition: Average revenue per order.
- Typical formula: Total Revenue / Order Count.
- Best used when: comparing customer spending behavior or order size trends.

### 4. Number of Customers
- Definition: Count of unique customers.
- Typical formula: COUNT(DISTINCT customer_id).
- Best used when: measuring customer base growth or retention.

### 5. Average Review Score
- Definition: Mean customer review score.
- Typical formula: AVG(review_score).
- Best used when: evaluating customer satisfaction.
- Recommended grain: order or review level.

### 6. Cancellation Rate
- Definition: Share of orders canceled.
- Typical formula: canceled orders / total orders.
- Best used when: monitoring service reliability or fulfillment issues.

## Adventure Works Metrics

### 1. Total Sales
- Definition: Total sales value for the selected period.
- Typical formula: SUM(sales_amount) or SUM(line_total).
- Best used when: evaluating sales performance and revenue trends.
- Recommended grain: order or line-item depending on the question.

### 2. Order Count
- Definition: Number of sales orders.
- Typical formula: COUNT(DISTINCT sales_order_id).
- Best used when: measuring order volume.

### 3. Average Order Value
- Definition: Average sales value per order.
- Typical formula: Total Sales / Order Count.
- Best used when: comparing average basket size or customer spend.

### 4. Units Sold
- Definition: Total quantity sold.
- Typical formula: SUM(quantity).
- Best used when: evaluating product demand and volume trends.

### 5. Customer Count
- Definition: Number of unique customers.
- Typical formula: COUNT(DISTINCT customer_id).
- Best used when: analyzing customer reach or repeat purchase behavior.

### 6. Return Rate
- Definition: Share of orders or items returned.
- Typical formula: returned orders / total orders.
- Best used when: assessing product quality or fulfillment issues.

## Cross-Database Metric Guidance
Use the same reporting structure for both databases:
1. Metric Name
2. Business Definition
3. Formula
4. Grain / Table Used
5. Time Period
6. Notes or Assumptions

## Reporting Standard
When reporting any metric, include:
- the metric name,
- the value,
- the period measured,
- the population used,
- and any caveat or assumption.

## Common Mistakes to Avoid
- Mixing revenue with profit.
- Using the wrong denominator for rates.
- Counting line items as orders.
- Comparing metrics from different grains without transformation.
- Reporting totals without a clear time frame.
