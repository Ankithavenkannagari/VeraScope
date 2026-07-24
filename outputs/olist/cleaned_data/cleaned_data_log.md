# Cleaned Data Log — Olist E-Commerce (OLIST_ECOMMERCE.RAW_DATA)

**Date:** 2026-07-22
**Based on:** `eda_olist_ecommerce.md` and `quality_olist_ecommerce.md` (both dated 2026-07-22)
**Connection:** Snowflake MCP (snowflake_OR)

## Scope

Only tables with an actual row-level or value-level defect were cleaned. Tables that were internally consistent — even if a *usage* rule was needed (e.g., "join on the right column") — were left untouched, per the Data Quality Agent's "prefer minimally invasive fixes" guidance. See **Tables Not Cleaned** below for what was intentionally skipped and why.

## 1. cleaned_reviews.csv

**Issue:** REVIEWS.REVIEW_ID is not unique (789 duplicate-ID groups) and 547 orders carry more than one review row. A full-column comparison in the quality report confirmed the duplicate rows are **not** copy-paste duplicates — each row has genuinely different content sharing a REVIEW_ID string — so the fix could not be a simple `SELECT DISTINCT`.

**Method:** Re-graded REVIEWS to one row per ORDER_ID, keeping the row with the latest `REVIEW_ANSWER_TIMESTAMP` per order (tie-break: latest `REVIEW_CREATION_DATE`, then `REVIEW_ID` ascending, for determinism), per the quality report's recommended remediation. Implemented via `ROW_NUMBER() OVER (PARTITION BY ORDER_ID ORDER BY REVIEW_ANSWER_TIMESTAMP DESC NULLS LAST, REVIEW_CREATION_DATE DESC NULLS LAST, REVIEW_ID) = 1`.

Export: queried in 7 batches (OFFSET 0/15000/30000/45000/60000/75000/90000, batch sizes 15000×6 + 8673) because a single unbatched query exceeded the MCP tool's response size limit (large free-text comment fields). Batches were concatenated in ORDER_ID order.

**Before:** 99,224 rows, 789 duplicate REVIEW_IDs, 547 orders with >1 review row.

**After:** 98,673 rows — exactly one row per distinct ORDER_ID (verified: 98,673 rows = 98,673 distinct ORDER_ID values, 0 remaining duplicates at the order grain).

**Output:**
- File: `outputs/olist/cleaned_data/cleaned_reviews.csv`
- Columns: REVIEW_ID, ORDER_ID, REVIEW_SCORE, REVIEW_COMMENT_TITLE, REVIEW_COMMENT_MESSAGE, REVIEW_CREATION_DATE, REVIEW_ANSWER_TIMESTAMP
- Row count: 98,673 (+ header)
- Note: REVIEW_ID itself may still repeat across rows in this cleaned file if two different orders' latest reviews happen to share an ID — the grain guarantee is ONE ROW PER ORDER_ID, not a unique REVIEW_ID. Do not join or dedupe on REVIEW_ID alone.

## 2. cleaned_products.csv

**Issue 1:** 610 products (1.85%) have NULL `PRODUCT_CATEGORY_NAME`. **Issue 2:** 13 products reference a category name (`pc_gamer`: 3 products; `portateis_cozinha_e_preparadores_de_alimentos`: 10 products) with no match in CATEGORY_TRANSLATION. **Issue 3:** 4 products have `PRODUCT_WEIGHT_G` ≤ 0.

**Method:**
- Added `PRODUCT_CATEGORY_NAME_CLEAN`: recodes NULL and the 2 unmatched category names to `'unknown_category'`; all other values pass through unchanged. The original `PRODUCT_CATEGORY_NAME` column is preserved as-is for traceability.
- Added `CATEGORY_QUALITY_FLAG`: `'missing_category'` (610 rows), `'unmatched_translation'` (13 rows), or `'ok'` (32,328 rows).
- Added `WEIGHT_QUALITY_FLAG`: `'invalid_weight'` (4 rows where PRODUCT_WEIGHT_G ≤ 0) or `'ok'` (32,947 rows). **No weight values were altered or imputed** — per the quality report's low-severity, minimally-invasive recommendation, these 4 rows are flagged for exclusion from weight-based analysis (freight-per-kg, density) rather than having a fabricated replacement value written in.
- All other PRODUCTS columns passed through unchanged.

Export: queried in 3 batches (OFFSET 0/12000/24000, batch sizes 12000/12000/8951).

**Before:** 32,951 rows, 610 with null category, 13 with unmatched category translation, 4 with zero/negative weight.

**After:** 32,951 rows (no rows dropped — verified via flag counts: `CATEGORY_QUALITY_FLAG` = ok 32,328 / missing_category 610 / unmatched_translation 13; `WEIGHT_QUALITY_FLAG` = ok 32,947 / invalid_weight 4 — both match the quality report exactly).

**Output:**
- File: `outputs/olist/cleaned_data/cleaned_products.csv`
- Columns: PRODUCT_ID, PRODUCT_CATEGORY_NAME, PRODUCT_CATEGORY_NAME_CLEAN, CATEGORY_QUALITY_FLAG, PRODUCT_NAME_LENGTH, PRODUCT_DESCRIPTION_LENGTH, PRODUCT_PHOTOS_QTY, PRODUCT_WEIGHT_G, WEIGHT_QUALITY_FLAG, PRODUCT_LENGTH_CM, PRODUCT_HEIGHT_CM, PRODUCT_WIDTH_CM
- Row count: 32,951 (+ header)

## 3. cleaned_geolocation.csv

**Issue:** GEOLOCATION is a raw geocoding lookup with many rows per zip-code prefix (1,000,163 rows across only 19,015 distinct zips) — flagged in the EDA as a fan-out risk if joined to CUSTOMERS/SELLERS on zip prefix without first aggregating to one row per zip.

**Method:** Aggregated to exactly one row per `GEOLOCATION_ZIP_CODE_PREFIX`:
- `GEOLOCATION_LAT` / `GEOLOCATION_LNG`: average of all recorded coordinates for that zip, rounded to 6 decimal places (~0.1m precision).
- `GEOLOCATION_CITY` / `GEOLOCATION_STATE`: the most frequently occurring (city, state) pair for that zip (mode), tie-broken alphabetically by city name for determinism — since a small number of zips have inconsistent city/state spellings across source rows.

Export: queried in 2 batches (OFFSET 0/12000, batch sizes 12000/7015).

**Before:** 1,000,163 rows, 19,015 distinct zip prefixes (many-to-one).

**After:** 19,015 rows — exactly one row per distinct zip prefix (verified: 19,015 rows = 19,015 distinct GEOLOCATION_ZIP_CODE_PREFIX values).

**Output:**
- File: `outputs/olist/cleaned_data/cleaned_geolocation.csv`
- Columns: GEOLOCATION_ZIP_CODE_PREFIX, GEOLOCATION_LAT, GEOLOCATION_LNG, GEOLOCATION_CITY, GEOLOCATION_STATE
- Row count: 19,015 (+ header)

## Tables Not Cleaned (Intentional)

| Table | Reason |
|---|---|
| CUSTOMERS | No row-level defect. CUSTOMER_ID is internally unique and CUSTOMER_UNIQUE_ID is internally consistent — the issue is purely "use CUSTOMER_UNIQUE_ID, not CUSTOMER_ID, for customer-count metrics," which is a query-time rule, not a data fix. Documented in the quality report and should be enforced in the Metrics Glossary, not by altering the table. |
| ORDERS | No integrity or business-rule violations found (0 orphaned FKs, delivery-date sequencing valid, 0 nulls in ORDER_ESTIMATED_DELIVERY_DATE). Lifecycle-date nulls (approved/delivered) are consistent with non-"delivered" order statuses, not a data error. |
| ORDER_ITEMS | No zero/negative PRICE or FREIGHT_VALUE, no orphaned FKs, no duplicate (ORDER_ID, ORDER_ITEM_ID) keys. Fully clean. |
| SELLERS | No duplicate SELLER_ID, no orphaned references from ORDER_ITEMS. Fully clean. |
| PAYMENTS | 9 rows with PAYMENT_VALUE = 0 were reviewed and assessed as plausible ($0 voucher/not_defined rows alongside other payment rows on the same order), not erroneous — they contribute correctly as $0 in any SUM-based metric. No fix needed; flagged in the quality report for awareness only if per-row averages are ever computed. |
| CATEGORY_TRANSLATION | No duplicate PRODUCT_CATEGORY_NAME keys. The 2 missing translations are a PRODUCTS-side gap (see cleaned_products.csv), not a defect in this table itself. |

## Date and Author
- Date: 2026-07-22
- Author: AI Analyst — Data Quality Agent workflow
