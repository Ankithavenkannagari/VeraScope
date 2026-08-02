# Adventure Works Metric Extensions

## Purpose
This file defines business metrics that can be derived from the Adventure Works data model.

## Core Metrics
- Total Sales
- Order Count
- Average Order Value
- Units Sold
- Customer Count
- Return Rate

## Metric Notes
- Sales should be computed from the appropriate order or line-item level
- Order count should use distinct sales order identifiers
- Average order value should be calculated as sales divided by order count
- Return metrics should use the relevant return or cancellation flags when available
