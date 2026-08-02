# Adventure Works Table Relationships

## Overview
This file documents the main table relationships for the Adventure Works dataset.

## Key Tables
- customers
- sales_orders
- sales_order_details
- products
- salespeople
- territories
- dates

## Relationship Summary
- customers -> sales_orders: one customer can place many orders
- sales_orders -> sales_order_details: one order can contain many line items
- sales_order_details -> products: each line item references a product
- sales_orders -> salespeople: sales activity is associated with a salesperson
- sales_orders -> territories: sales activity is tied to a territory
- dates -> sales_orders: date dimensions support time-based analysis

## Join Guidance
- Use sales_orders or sales_order_details as the main grain depending on the question
- Use sales_order_details for quantity and line-item analysis
- Use products, customers, and territories for segmentation
- Ensure time-based analysis uses a consistent date dimension
