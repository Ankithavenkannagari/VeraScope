# Olist Table Relationships

## Overview
This file documents the main table relationships for the Olist ecommerce dataset.

## Key Tables
- customers
- orders
- order_items
- products
- sellers
- payments
- reviews

## Relationship Summary
- customers -> orders: one customer can place many orders
- orders -> order_items: one order can contain many line items
- order_items -> products: each order item references a product
- order_items -> sellers: each order item is associated with a seller
- orders -> payments: one order can have multiple payment records
- orders -> reviews: one order can have one review record

## Join Guidance
- Use orders as the main grain for order-level analysis
- Use order_items for product-level and revenue-level analysis
- Use customers and sellers for segmentation and customer behavior analysis
- Be careful not to double-count revenue when aggregating from order_items
