# EDA Report: Olist E-Commerce (OLIST_ECOMMERCE.RAW_DATA)

**Date:** 2026-07-22
**Database:** OLIST_ECOMMERCE | **Schema:** RAW_DATA | **Warehouse:** COMPUTE_WH

## Executive Summary

Olist is a 9-table Brazilian e-commerce transaction model (customers, orders, order line items, products, sellers, payments, reviews, geolocation, and a category-name translation table) covering orders from 2016-09-04 through 2018-10-17. Referential integrity between the core transactional tables (orders, order items, payments, reviews) is fully clean — zero orphaned foreign keys anywhere in that chain. However, three data quality issues need attention before reporting: **REVIEWS has 789 duplicate REVIEW_ID values (814 excess rows) and 547 orders with more than one review row**, **CUSTOMER_ID is not a real customer identifier** (99,441 customer_id rows collapse to only 96,096 distinct CUSTOMER_UNIQUE_ID — a 3,345-row gap that will overstate customer counts unless CUSTOMER_UNIQUE_ID is used), and **13 products carry a category name not present in the category-translation table** (610 more have no category at all).

## Key Findings

**Row counts (verified against live data):**

| Table | Rows |
|---|---|
| CATEGORY_TRANSLATION | 71 |
| CUSTOMERS | 99,441 |
| GEOLOCATION | 1,000,163 |
| ORDERS | 99,441 |
| ORDER_ITEMS | 112,650 |
| PAYMENTS | 103,886 |
| PRODUCTS | 32,951 |
| REVIEWS | 99,224 |
| SELLERS | 3,095 |

**Schema shape:**
- CUSTOMERS (5 cols): CUSTOMER_ID (PK, order-scoped), CUSTOMER_UNIQUE_ID (the true customer identifier), CUSTOMER_ZIP_CODE_PREFIX, CUSTOMER_CITY, CUSTOMER_STATE.
- ORDERS (8 cols): ORDER_ID (PK), CUSTOMER_ID (FK), ORDER_STATUS, ORDER_PURCHASE_TIMESTAMP + 4 lifecycle timestamps (approved/delivered-to-carrier/delivered-to-customer/estimated-delivery).
- ORDER_ITEMS (7 cols): (ORDER_ID, ORDER_ITEM_ID) composite PK, PRODUCT_ID (FK), SELLER_ID (FK), SHIPPING_LIMIT_DATE, PRICE, FREIGHT_VALUE.
- PAYMENTS (5 cols): ORDER_ID (FK, not unique — orders can have multiple payment rows), PAYMENT_SEQUENTIAL, PAYMENT_TYPE, PAYMENT_INSTALLMENTS, PAYMENT_VALUE.
- PRODUCTS (9 cols): PRODUCT_ID (PK), PRODUCT_CATEGORY_NAME (FK to CATEGORY_TRANSLATION), name/description length, photo count, weight/dimensions.
- SELLERS (4 cols): SELLER_ID (PK), SELLER_ZIP_CODE_PREFIX, SELLER_CITY, SELLER_STATE.
- REVIEWS (7 cols): REVIEW_ID (intended PK, **not actually unique**), ORDER_ID (FK), REVIEW_SCORE (1-5), comment title/message, creation/answer timestamps.
- GEOLOCATION (5 cols): GEOLOCATION_ZIP_CODE_PREFIX, LAT, LNG, CITY, STATE — a many-rows-per-zip lookup table (1,000,163 rows across only 19,015 distinct zip prefixes and 27 states), not a table with a single-row-per-zip grain.
- CATEGORY_TRANSLATION (2 cols): PRODUCT_CATEGORY_NAME (Portuguese, PK) → PRODUCT_CATEGORY_NAME_ENGLISH.

**Referential integrity (checked by anti-join, zero tolerance except where noted):**
- ORDERS → CUSTOMERS: **0 orphaned rows**.
- ORDER_ITEMS → ORDERS, PRODUCTS, SELLERS: **0 orphaned rows** in all three.
- PAYMENTS → ORDERS: **0 orphaned rows**.
- REVIEWS → ORDERS: **0 orphaned rows**.
- PRODUCTS → CATEGORY_TRANSLATION: **13 orphaned rows** — 2 category names (`pc_gamer`, 3 products; `portateis_cozinha_e_preparadores_de_alimentos`, 10 products) exist in PRODUCTS but have no matching row in CATEGORY_TRANSLATION, so these 13 products cannot get an English category label via this join.
- Primary-key duplicate checks: CUSTOMER_ID (0 dup), ORDER_ID (0 dup), PRODUCT_ID (0 dup), SELLER_ID (0 dup), (ORDER_ID, ORDER_ITEM_ID) (0 dup), CATEGORY_TRANSLATION.PRODUCT_CATEGORY_NAME (0 dup) — all clean.
- **REVIEW_ID: 789 duplicate-ID groups, 814 excess rows** (99,224 total rows but fewer distinct REVIEW_ID values than that). Sampled duplicate groups show the same REVIEW_ID repeated 3x on different rows.
- **REVIEWS.ORDER_ID: 547 orders have more than one review row** (814 excess rows total, of which 551 rows are attributable to the order-level grouping). Spot-checking 5 multi-review orders found some with 2 distinct review scores on the same order (e.g., order `c88b1d1b157a9999ce368f218a407141`: 3 review rows, 2 distinct scores) and some with all-identical scores (e.g., order `df56136b8031ecd28e200bb18e6ddb2e`: 3 rows, 1 distinct score) — i.e., this is a mix of genuine repeat-review activity and likely straight duplication, not one single cause.

**CUSTOMERS — CUSTOMER_ID vs. CUSTOMER_UNIQUE_ID:**
- 99,441 CUSTOMER_ID values (0 duplicates — each is unique), but only **96,096 distinct CUSTOMER_UNIQUE_ID values** — a gap of 3,345. This is the well-known Olist design where CUSTOMER_ID is generated per-order (so a repeat shopper gets a new CUSTOMER_ID on every order) while CUSTOMER_UNIQUE_ID is the stable person-level identifier. **Any "number of customers" metric must use COUNT(DISTINCT CUSTOMER_UNIQUE_ID), not CUSTOMER_ID**, or repeat customers will be overcounted as new ones.

**ORDERS:**
- Date range: 2016-09-04 21:15:19 to 2018-10-17 17:30:18 (ORDER_PURCHASE_TIMESTAMP).
- ORDER_STATUS distribution: delivered 96,478 (97.0%), shipped 1,107, canceled 625, unavailable 609, invoiced 314, processing 301, created 5, approved 2.
- Lifecycle timestamp nulls: ORDER_APPROVED_AT 160 nulls (0.16%), ORDER_DELIVERED_CARRIER_DATE 1,783 nulls (1.79%), ORDER_DELIVERED_CUSTOMER_DATE 2,965 nulls (2.98%), ORDER_ESTIMATED_DELIVERY_DATE 0 nulls. The delivered-date nulls track closely with non-"delivered" order statuses (625+609+314+301+107+5+2 ≈ 1,963 to 2,653 non-delivered/partially-delivered orders), consistent with orders that were canceled, are still in transit, or never shipped.
- **0 rows** where ORDER_DELIVERED_CUSTOMER_DATE is earlier than ORDER_PURCHASE_TIMESTAMP — logically consistent.

**ORDER_ITEMS:**
- PRICE: $0.85–$6,735.00, average $120.65, **0 zero/negative prices**.
- FREIGHT_VALUE: $0.00–$409.68, **0 negative values** (some legitimately $0, plausible for free-shipping promotions or pickup orders — not separately verified).

**PAYMENTS:**
- PAYMENT_VALUE: $0.00–$13,664.08, average $154.10. **9 rows have PAYMENT_VALUE = 0** — 6 are `voucher` type and 3 are `not_defined` type, which is plausible (a $0 voucher applied as one of several payment rows on an order) rather than a clear data error.
- PAYMENT_TYPE: credit_card 76,795 (73.9%), boleto 19,784 (19.0%), voucher 5,775 (5.6%), debit_card 1,529 (1.5%), not_defined 3 rows.
- 103,886 payment rows against 99,441 orders (99,440 distinct order_ids referenced) confirms orders can have multiple payment rows, consistent with the documented one-to-many relationship.

**REVIEWS:**
- REVIEW_SCORE: range 1-5, average 4.09 (skewed positive, typical for e-commerce review data).
- REVIEW_COMMENT_TITLE: 87,658 of 99,224 rows null (88.3% — most reviewers don't title their review).
- REVIEW_COMMENT_MESSAGE: 58,256 of 99,224 rows null (58.7% — most reviewers leave a score with no written comment).

**PRODUCTS:**
- 610 of 32,951 products (1.85%) have NULL PRODUCT_CATEGORY_NAME, and the same 610 rows have NULL PRODUCT_NAME_LENGTH — indicating these are likely a single batch of incompletely-captured product records, not scattered corruption.
- PRODUCT_WEIGHT_G / PRODUCT_LENGTH_CM: only 2 nulls each (rounding error / negligible).
- **4 products have PRODUCT_WEIGHT_G ≤ 0** — physically implausible for a shippable product; worth flagging before using weight in shipping-cost or logistics analysis.

**GEOLOCATION:**
- 1,000,163 rows across 19,015 distinct zip-code prefixes and 27 states — many rows per zip (multiple lat/lng samples per prefix), so this table is a raw geocoding lookup, not a clean one-row-per-location dimension. Any join to CUSTOMERS/SELLERS on zip prefix will fan out unless first aggregated (e.g., to a single representative lat/lng per zip).

## Data Quality Issues

1. **REVIEWS has 789 duplicate REVIEW_ID values (814 excess rows) and 547 orders with more than one review row.** REVIEW_ID is not a reliable primary key as-is. Some multi-review orders carry genuinely different scores (repeat feedback), others carry identical scores on every row (likely straight duplication) — the cause is mixed and needs a de-duplication rule (e.g., keep the latest REVIEW_ANSWER_TIMESTAMP per order) before REVIEWS is used in any per-order or per-review-id join, or review counts/averages will be inflated.
2. **CUSTOMER_ID is not a stable customer identifier** — 99,441 CUSTOMER_ID rows represent only 96,096 unique people (CUSTOMER_UNIQUE_ID). Any "customer count" or repeat-purchase analysis built on CUSTOMER_ID instead of CUSTOMER_UNIQUE_ID will overstate the customer base by ~3.4%.
3. **13 products reference a PRODUCT_CATEGORY_NAME with no match in CATEGORY_TRANSLATION** (`pc_gamer`: 3 products; `portateis_cozinha_e_preparadores_de_alimentos`: 10 products), so these products will silently drop out of any INNER JOIN to get an English category label, or show as blank/null in a LEFT JOIN — worth flagging to whoever maintains the translation table.
4. **610 products (1.85%) have no category name and no name-length value** — likely one incomplete data-capture batch; these products can still be used for revenue/quantity analysis via ORDER_ITEMS but will fall into an "Unknown category" bucket in any category-level rollup.
5. **4 products have zero or negative PRODUCT_WEIGHT_G**, which is physically invalid and would corrupt shipping-cost-per-kg or logistics analysis if not filtered.
6. **9 payment rows have PAYMENT_VALUE = 0** (6 voucher, 3 not_defined) — plausible in context (partial voucher payments) but should be confirmed before being treated as a data error or excluded from spend totals.

## Suggested Next Steps

- Route this database to the Data Quality Agent to size, severity-rank, and propose a de-duplication rule for the REVIEWS table (789 duplicate REVIEW_IDs, 547 multi-review orders) before any review-score reporting is built.
- Standardize on CUSTOMER_UNIQUE_ID (not CUSTOMER_ID) for every "number of customers" or repeat-purchase metric going forward — document this in the Metrics Glossary if not already assumed there.
- Confirm with the data owner whether the 2 unmatched category names and 610 null-category products should be recoded to "Unknown"/mapped manually, or left as-is with category-level reports simply excluding them.
- Decide a filtering rule for the 4 zero/negative-weight products before any logistics or freight-efficiency analysis.
- Before joining GEOLOCATION to CUSTOMERS or SELLERS on zip-code prefix, aggregate GEOLOCATION down to one representative row per zip (e.g., average lat/lng) to avoid fan-out.

## Assumptions and Limitations

- Row counts and all figures above were captured live via Snowflake queries against OLIST_ECOMMERCE.RAW_DATA on 2026-07-22; if the underlying tables are refreshed, these numbers should be re-verified.
- "Orphaned foreign key" checks were performed via LEFT JOIN / anti-join on the key columns implied by the data model skill (CUSTOMER_ID, ORDER_ID, PRODUCT_ID, SELLER_ID, PRODUCT_CATEGORY_NAME); no formal foreign-key constraints were inspected in the schema metadata, so this assumes those are the intended join columns.
- The cause of REVIEWS duplication was only spot-checked on 5 sample orders, not exhaustively classified across all 547 — the "mixed cause" conclusion is based on that small sample and should be treated as a hypothesis, not a confirmed root cause.
- Only SELECT queries were run; no data was modified.

## Key Takeaways

- All 9 tables were profiled; the core transactional chain (orders → order_items → products/sellers, orders → payments, orders → reviews, orders → customers) has **zero orphaned foreign keys**, so joins along that chain are safe.
- The most consequential issue is in REVIEWS: **789 duplicate REVIEW_ID values and 547 orders with multiple review rows** — treat REVIEW_ID as non-unique and de-duplicate before per-review or per-order review analysis.
- **CUSTOMER_ID ≠ customer.** 99,441 customer_id values collapse to 96,096 real customers via CUSTOMER_UNIQUE_ID — always use CUSTOMER_UNIQUE_ID for customer-count or retention metrics.
- Products are largely clean, with a small (1.85%) batch of null-category records and 13 products whose category name isn't recognized by the translation table — both easily filtered/bucketed rather than table-wide corruption.
- GEOLOCATION is a raw many-row-per-zip geocoding table, not a clean dimension — must be aggregated before joining to avoid fan-out.
