# Data Quality Report: Olist E-Commerce (OLIST_ECOMMERCE.RAW_DATA)

**Date:** 2026-07-22
**Database:** OLIST_ECOMMERCE | **Schema:** RAW_DATA | **Warehouse:** COMPUTE_WH
**Based on:** `eda_olist_ecommerce.md` (2026-07-22)

## Executive Summary

Following up on the EDA snapshot, six issues were validated and severity-ranked: two **high-severity** issues that will silently distort standard metrics if not corrected (a non-unique REVIEW_ID in the REVIEWS table, and a CUSTOMER_ID that does not represent a real customer), and four **medium/low-severity** product- and payment-level cleanliness issues. Core referential integrity across the transactional chain (orders, order_items, payments, reviews, customers) remains fully clean — no FK repair is required. The two high-severity issues are both "silent" in nature: neither breaks a query, but each will quietly overstate a commonly-requested metric (review volume and customer count, respectively) unless explicitly handled.

## Issues Found, Severity, and Evidence

### 1. REVIEWS.REVIEW_ID is not unique — Severity: HIGH

**What's broken:** 789 distinct REVIEW_ID values each appear on more than one row, totaling 1,603 rows (814 rows in excess of what a unique key would produce).

**Evidence:**
- `GROUP BY REVIEW_ID HAVING COUNT(*) > 1` returns 789 groups; summed row count in those groups is 1,603 (789 groups + 814 excess rows).
- A full-column comparison within the 1,603 affected rows (REVIEW_ID, ORDER_ID, REVIEW_SCORE, REVIEW_COMMENT_MESSAGE, REVIEW_CREATION_DATE) found **1,603 distinct combinations for 1,603 rows** — meaning these are **not** copy-paste duplicate rows. Each row carries genuinely different content (often a different ORDER_ID and/or score) while sharing the same REVIEW_ID string. This points to an ID collision or ID-reuse pattern in the source system, not a load-time duplication bug.
- The 1,603 affected rows touch 1,412 distinct ORDER_IDs, and separately, 547 individual orders have more than one REVIEWS row regardless of REVIEW_ID overlap (814 excess rows at the order grain too — a related but distinct symptom).
- Sampling confirmed both patterns exist side by side: some multi-row orders carry different review scores (genuine repeat feedback, e.g., order `c88b1d1b157a9999ce368f218a407141` has 3 rows / 2 distinct scores), others carry identical scores across all rows (looks like true duplication, e.g., order `df56136b8031ecd28e200bb18e6ddb2e` has 3 rows / 1 distinct score).

**Why it matters:** Any query that treats REVIEW_ID as a primary key (e.g., `COUNT(DISTINCT REVIEW_ID)` as "review count," or a join keyed on REVIEW_ID alone) will undercount reviews and can produce incorrect one-to-many fan-out if REVIEWS is joined to anything else by REVIEW_ID. Because the duplicate rows are **not** identical, a naive `SELECT DISTINCT *` will not fix this — it will keep all 1,603 rows.

**Recommended remediation:** Treat REVIEWS as a table with grain (ORDER_ID, REVIEW_ID) rather than REVIEW_ID alone. For any "one review per order" metric (e.g., average review score by order), pick a single deterministic row per ORDER_ID — recommended rule: keep the row with the latest REVIEW_ANSWER_TIMESTAMP per ORDER_ID, since that represents Olist's most recent recorded response. Flag the underlying ID-collision pattern to the data owner; it suggests a possible ID-generation defect in the source review system.

### 2. CUSTOMER_ID does not represent a unique customer — Severity: HIGH

**What's broken:** CUSTOMERS has 99,441 rows, each with a unique CUSTOMER_ID, but only 96,096 distinct CUSTOMER_UNIQUE_ID values — i.e., 96,096 real people placed orders using 99,441 order-scoped customer records.

**Evidence:**
- `COUNT(DISTINCT CUSTOMER_ID)` = 99,441 (0 duplicates — CUSTOMER_ID itself is a clean key), but `COUNT(DISTINCT CUSTOMER_UNIQUE_ID)` = 96,096.
- Breakdown of CUSTOMER_UNIQUE_ID by number of associated CUSTOMER_ID rows: 93,099 customers ordered once (1 customer_id), 2,745 ordered twice, 203 three times, 30 four times, 8 five times, 6 six times, 3 seven times, 1 nine times, and 1 customer has 17 separate customer_id rows (17 orders). In total, **2,997 real customers (3.1% of the 96,096 unique customers) are "repeat" customers who would each be double- (or up to 17x-) counted if CUSTOMER_ID were used as the customer key.**
- This matches Olist's documented dataset design: CUSTOMER_ID is generated fresh per order, while CUSTOMER_UNIQUE_ID is the stable person-level identifier.

**Why it matters:** Any "number of customers" metric, new-vs-repeat customer split, or customer-level segmentation that groups by CUSTOMER_ID instead of CUSTOMER_UNIQUE_ID will overstate the customer base by ~3.5% (99,441 vs. 96,096) and will report 0% repeat-purchase rate, which is factually wrong — the dataset does contain repeat purchasers, just hidden behind per-order customer_id values.

**Recommended remediation:** Standardize — every customer-count, retention, or repeat-purchase metric must use `COUNT(DISTINCT CUSTOMER_UNIQUE_ID)`, never `COUNT(DISTINCT CUSTOMER_ID)`. Document this explicitly in the Metrics Glossary so it isn't re-derived incorrectly in future analyses. No row-level fix is needed — CUSTOMERS itself is internally consistent; this is purely a "use the right column" issue.

### 3. 610 products have no category name — Severity: MEDIUM

**What's broken:** 610 of 32,951 products (1.85%) have NULL PRODUCT_CATEGORY_NAME, and the same 610 rows also have NULL PRODUCT_NAME_LENGTH.

**Evidence:** `WHERE PRODUCT_CATEGORY_NAME IS NULL` returns exactly 610 rows; `WHERE PRODUCT_NAME_LENGTH IS NULL` also returns exactly 610 rows — the exact count match indicates a single incomplete-capture batch, not scattered corruption.

**Why it matters:** Any category-level sales or product-mix report will need an explicit "Unknown category" bucket for these products, or they will silently disappear from an INNER JOIN-based category rollup.

**Recommended remediation:** Recode NULL category to an explicit 'Unknown' label in category-level reporting views. Do not drop these 610 products — their PRODUCT_ID, dimensions, and order_items linkage remain usable for non-category analysis.

### 4. 13 products reference a category name missing from CATEGORY_TRANSLATION — Severity: LOW/MEDIUM

**What's broken:** Two category names appear in PRODUCTS but have no corresponding row in CATEGORY_TRANSLATION: `pc_gamer` (3 products) and `portateis_cozinha_e_preparadores_de_alimentos` (10 products).

**Evidence:** LEFT JOIN from PRODUCTS to CATEGORY_TRANSLATION on PRODUCT_CATEGORY_NAME, filtered to non-null category names with no match, returns exactly these 13 rows across the 2 category names above.

**Combined business impact of Issues #3 and #4:** Products with either a NULL category or one of these 2 unmatched categories account for **1,627 order-line items and $185,049.76 in revenue** (1.2% of ORDER_ITEMS rows, 1.4% of the $13,591,643.70 total revenue in ORDER_ITEMS) — a small but non-trivial slice that will fall out of any category-level revenue report unless explicitly bucketed.

**Recommended remediation:** Confirm with the data owner whether `pc_gamer` and `portateis_cozinha_e_preparadores_de_alimentos` are simply missing translation rows (add them to CATEGORY_TRANSLATION) or represent a category taxonomy that predates/postdates the current translation table. Until confirmed, bucket these 13 products under "Unknown category" alongside the 610 NULL-category products rather than excluding them from revenue totals.

### 5. 4 products have zero PRODUCT_WEIGHT_G — Severity: LOW

**What's broken:** Products `81781c0fed9fe1ad6e8c81fca1e1cb08`, `8038040ee2a71048d4bdbbdc985b69ab`, `36ba42dd187055e1fbe943b2d11430ca`, and `e673e90efa65a5409ff4196c038bb5af` all have PRODUCT_WEIGHT_G = 0.

**Evidence:** `WHERE PRODUCT_WEIGHT_G <= 0` returns exactly these 4 rows (all exactly 0, none negative).

**Why it matters:** A weight of 0 is physically implausible for a shippable product and would produce a divide-by-zero or misleading result in any "freight cost per kg" or shipping-efficiency metric.

**Recommended remediation:** Exclude these 4 products from weight-based logistics calculations (freight-per-kg, density metrics) until the source system provides a corrected weight; they represent 0.01% of the product catalog, so exclusion has negligible impact on aggregate analysis.

### 6. 9 payment rows have PAYMENT_VALUE = 0 — Severity: LOW

**What's broken:** 9 of 103,886 PAYMENTS rows have PAYMENT_VALUE = 0.00 (6 rows of PAYMENT_TYPE = 'voucher', 3 rows of PAYMENT_TYPE = 'not_defined').

**Evidence:** `WHERE PAYMENT_VALUE <= 0` returns 9 rows; no negative values were found, only exact zeros.

**Why it matters:** Plausible as a $0 voucher applied alongside another payment row on the same order (common in multi-payment-row orders), rather than a data error — but if a report sums PAYMENT_VALUE per order to reconstruct "amount paid," these rows contribute correctly as $0 and are not a distortion risk on their own.

**Recommended remediation:** No action required for aggregate reporting (they correctly contribute $0). If per-payment-row analysis is ever done (e.g., "average voucher value"), exclude these 9 zero-value rows from the average so they don't pull it down artificially.

## Business Rule Validation Summary (checks that passed clean)

- No duplicate primary keys in CUSTOMER_ID, ORDER_ID, PRODUCT_ID, SELLER_ID, (ORDER_ID, ORDER_ITEM_ID), or CATEGORY_TRANSLATION.PRODUCT_CATEGORY_NAME — 0 duplicates each.
- No orphaned foreign keys anywhere in the core transactional chain: ORDERS → CUSTOMERS, ORDER_ITEMS → ORDERS/PRODUCTS/SELLERS, PAYMENTS → ORDERS, REVIEWS → ORDERS. All checks returned 0 orphans.
- No negative or zero PRICE in ORDER_ITEMS (range $0.85–$6,735.00).
- No negative FREIGHT_VALUE in ORDER_ITEMS.
- No negative PAYMENT_VALUE in PAYMENTS (only the 9 zero-value rows noted above).
- REVIEW_SCORE fully within valid 1–5 range, average 4.09, no nulls.
- ORDER_ESTIMATED_DELIVERY_DATE has 0 nulls across all 99,441 orders.
- 0 rows where ORDER_DELIVERED_CUSTOMER_DATE precedes ORDER_PURCHASE_TIMESTAMP — delivery sequencing is logically consistent.
- Lifecycle-timestamp nulls in ORDERS (160 approved, 1,783 delivered-to-carrier, 2,965 delivered-to-customer) track consistently with the ~2,000-2,600 orders in non-"delivered" statuses (canceled/shipped/processing/etc.), not unexplained gaps.

## Recommended Next Steps (prioritized)

1. **(High)** Before any review-volume or review-score-by-order metric is built, decide and document a REVIEWS de-duplication rule (recommended: keep the row with the latest REVIEW_ANSWER_TIMESTAMP per ORDER_ID). Escalate the underlying REVIEW_ID collision pattern to the data owner for root-cause investigation.
2. **(High)** Update the Metrics Glossary (if not already reflecting this) to mandate `COUNT(DISTINCT CUSTOMER_UNIQUE_ID)` for all customer-count and repeat-purchase metrics — never `CUSTOMER_ID`.
3. **(Medium)** Build a cleaned product-category view that recodes NULL and the 2 unmatched category names (`pc_gamer`, `portateis_cozinha_e_preparadores_de_alimentos`) to an explicit "Unknown category" bucket, so the $185,049.76 (1.4%) of revenue tied to these products isn't silently dropped from category reports.
4. **(Low)** Exclude the 4 zero-weight products from any shipping/logistics weight-based calculation.
5. **(Low)** Exclude the 9 zero-value payment rows from per-row payment-value averages (no action needed for order-level or aggregate sums).

## Key Takeaways

- Core data integrity is strong across the transactional backbone: zero orphaned foreign keys and zero duplicate primary keys on CUSTOMER_ID, ORDER_ID, PRODUCT_ID, SELLER_ID, and the ORDER_ITEMS composite key.
- The two issues that actually threaten reporting accuracy are both HIGH severity and both "silent": **REVIEW_ID is not unique** (789 duplicate-ID groups, 1,603 affected rows that are genuinely different content, not copy-duplicates) and **CUSTOMER_ID is not a real customer** (99,441 order-scoped IDs represent only 96,096 actual people, with 2,997 of them — 3.1% — being repeat customers hidden behind fresh per-order IDs).
- Product catalog issues (610 null-category products, 13 products with unmatched category names, 4 zero-weight products) are small in scale (combined ~1.4% of revenue, 0.01%-1.85% of the product catalog) and easily bucketed/filtered rather than table-wide corruption.
- No business-rule violations were found on prices, freight, payment values (aside from the 9 legitimate-looking $0 rows), or review scores.
