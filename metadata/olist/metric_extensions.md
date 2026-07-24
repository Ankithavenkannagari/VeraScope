# Olist Metric Extensions

## Purpose
This file defines business metrics that can be derived from the Olist data model.

## Core Metrics
- Total Revenue
- Order Count
- Average Order Value
- Number of Customers
- Average Review Score
- Cancellation Rate

## Metric Notes
- Revenue should be computed from the appropriate order or line-item level
- Order count should use distinct order identifiers
- Average order value should be calculated as revenue divided by order count
- Review metrics should use the relevant review records only
