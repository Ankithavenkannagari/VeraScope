# Data Quality Report: Adventure Works (ADVENTURE_WORKS.DATA)

**Date:** 2026-07-22
**Database:** ADVENTURE_WORKS | **Schema:** DATA | **Warehouse:** COMPUTE_WH
**Based on:** `eda_adventure_works.md` (2026-07-22)

## Executive Summary

Following up on the EDA snapshot, five issues were validated and severity-ranked: one **high-severity** structural overlap between the three yearly sales fact tables that will silently inflate any "3-year" revenue rollup, one **high-severity** disconnect in the category/region pivot table that blocks reconciliation, and three **medium/low-severity** customer-data cleanliness issues. Core referential integrity (foreign keys, primary keys) is fully clean across all 11 tables — no dedupe or FK-repair work is required there. The main risk is analytical, not structural: someone unaware of the FACT_SALES_2020 overlap could easily triple-count 2021/2022 revenue.

## Issues Found, Severity, and Evidence

### 1. FACT_SALES_2020 fully overlaps FACT_SALES_2021 and FACT_SALES_2022 — Severity: HIGH

**What's broken:** FACT_SALES_2020 (56,046 rows) is not a "2020 only" table. Its ORDER_DATE spans 2020-01-01 to 2022-06-30. Breaking it down by order year: 2,630 rows dated 2020, 23,935 rows dated 2021, 29,481 rows dated 2022.

**Evidence:**
- Joining FACT_SALES_2020 to FACT_SALES_2021 on (ORDER_NUMBER, ORDER_LINE_ITEM) returns 18,758 matched rows — exactly 100% of FACT_SALES_2021's total row count (18,758), and a check confirmed 0 rows of FACT_SALES_2021 are missing from that match.
- The same test against FACT_SALES_2022 returns 9,906 matches — exactly 100% of FACT_SALES_2022's total row count (9,906), again with 0 unmatched FACT_SALES_2022 rows.
- A full-column comparison on the matched pairs (PRODUCT_KEY, CUSTOMER_KEY, ORDER_QUANTITY, ORDER_DATE) found 0 mismatches — the overlapping rows are byte-for-byte duplicates across tables, not coincidental key collisions.
- FACT_SALES_2020 additionally contains roughly 24,752 rows dated 2021/2022 that have no matching key in FACT_SALES_2021/2022 at all (53,416 rows dated 2021/2022 in FACT_SALES_2020 vs. 28,664 matched by key), meaning FACT_SALES_2020 is a broader/more complete extract, not a strict superset built by simple concatenation.

**Why it matters:** Any query that does `SELECT * FROM FACT_SALES_2020 UNION ALL SELECT * FROM FACT_SALES_2021 UNION ALL SELECT * FROM FACT_SALES_2022` to build a "3-year sales" view will count 18,758 + 9,906 = 28,664 order lines twice, and will still be missing an unknown amount of 2021/2022 activity that exists only in FACT_SALES_2020's non-matching rows. This directly inflates revenue, order counts, and quantity totals for 2021 and 2022 if the tables are combined naively.

**Recommended remediation:** Exclude — do not union the three fact tables as-is. Treat FACT_SALES_2020 as the authoritative, most-complete sales table for the full 2020–mid-2022 window and use it alone for historical trend analysis, OR, if per-year tables must be combined, first de-duplicate on (ORDER_NUMBER, ORDER_LINE_ITEM) keeping one instance of each combination. Flag this to the data owner — the naming convention ("FACT_SALES_2020/2021/2022") is actively misleading given the actual contents, and the source ETL process should be reviewed.

### 2. DIM_PRODUCT_CATEGORY_SALES_PIVOT is disconnected from the core model — Severity: HIGH

**What's broken:** The table has only 20 rows, covering exactly 5 calendar days (2022-07-01 through 2022-07-05) across 4 product categories, with 3 region columns (NORTH_REGION, CENTRAL_REGION, SOUTH_REGION).

**Evidence:**
- Its date range starts the day after DIM_CALENDAR's maximum date (2022-06-30) and the maximum date across all three FACT_SALES tables (also 2022-06-30) — there is zero date overlap with the rest of the model, so it cannot be validated or reconciled against fact sales for consistency.
- Its three region columns (North/Central/South) do not match any of DIM_TERRITORY's 10 REGION values (Australia, Canada, Central, France, Germany, Northeast, Northwest, Southeast, Southwest, United Kingdom) — there's no direct mapping from "NORTH_REGION" to a DIM_TERRITORY row, so the aggregation grain and source of these numbers is unverifiable from the data alone.

**Why it matters:** Any report that tries to blend this pivot table with FACT_SALES-derived numbers ("category sales by region") will either silently produce a disjoint, non-additive result or require an undocumented, guessed mapping between its 3 region buckets and DIM_TERRITORY's 10 regions.

**Recommended remediation:** Exclude this table from any sales trend or regional analysis until the data owner confirms (a) what "NORTH/CENTRAL/SOUTH_REGION" map to in DIM_TERRITORY terms, and (b) why its date range sits entirely outside the calendar/fact coverage. Document it as a standalone/derived artifact in the data model, not a joinable fact table, until clarified.

### 3. GENDER contains a literal "NA" string instead of NULL or a valid code — Severity: MEDIUM

**What's broken:** 130 of 18,148 DIM_CUSTOMER rows (0.72%) have GENDER = the text string "NA", rather than "M", "F", or a proper NULL.

**Evidence:** `GROUP BY GENDER` on DIM_CUSTOMER returns three buckets: F = 8,892, M = 9,126, "NA" = 130. The same 130-row count exactly matches the count of NULL PREFIX values (130 of 18,148), strongly suggesting these are the same subset of customers with incomplete demographic capture, not a data corruption scattered across the table.

**Why it matters:** Because "NA" is a real string value (not SQL NULL), it will not be excluded by `WHERE GENDER IS NOT NULL` filters and will appear as a spurious third gender category in any customer segmentation, pie chart, or cross-tab unless explicitly handled.

**Recommended remediation:** Standardize — recode GENDER = 'NA' to NULL (or an explicit 'Unknown' label, per reporting convention) in a cleaned/derived customer view. Do not drop these 130 customers; their other attributes (income, occupation, etc.) are fully populated and usable.

### 4. 38 customers have implausible birth dates (100+ years old) — Severity: MEDIUM

**What's broken:** DIM_CUSTOMER.BIRTH_DATE ranges from 1910-08-13 to 1980-12-26. Using today's date (2026-07-22), 38 customers would be 100 years old or older.

**Evidence:** `DATEDIFF('year', BIRTH_DATE, CURRENT_DATE) > 100` returns 38 rows out of 18,148 (0.21%). No future-dated birth dates were found (0 rows), and no birth dates implying an age under 10 were found (0 rows), so this is an isolated tail issue rather than a systemic date problem.

**Why it matters:** Age-based segmentation (e.g., "customers over 65") will slightly overstate the oldest bracket if these 38 records are taken at face value; the effect on aggregate income/occupation analysis is negligible given the small count.

**Recommended remediation:** Filter/flag — exclude or cap these 38 records in age-banded analysis, or flag them for source-system review, but do not delete the underlying customer rows since their other fields are intact and usable for non-age-based analysis.

### 5. FACT_RETURNS and FACT_SALES have structural gaps for cross-analysis — Severity: LOW

**What's broken:** FACT_RETURNS has no CUSTOMER_KEY or ORDER_NUMBER column (only RETURN_DATE, TERRITORY_KEY, PRODUCT_KEY, RETURN_QUANTITY). None of the three FACT_SALES tables carries a revenue/dollar-amount column.

**Evidence:** Confirmed via INFORMATION_SCHEMA.COLUMNS — FACT_RETURNS has exactly 4 columns, none of which reference DIM_CUSTOMER or an order number; FACT_SALES_2020/2021/2022 each have exactly 8 columns, none of which is a dollar amount.

**Why it matters:** This is a schema design limitation rather than a defect — return rate can only be computed at the product/territory/date grain (not per customer or per order), and all dollar-based sales analysis requires joining ORDER_QUANTITY to DIM_PRODUCT.PRODUCT_PRICE (a current, non-effective-dated price), introducing a documented approximation for any historical revenue figure.

**Recommended remediation:** No data change possible without new source columns; document the limitation in any report that touches return rates or dollar sales, and note that revenue figures are approximate (based on current list price, not point-of-sale price).

## Business Rule Validation Summary (checks that passed clean)

- No duplicate primary keys in any of the 6 dimension tables (CUSTOMER_KEY, PRODUCT_KEY, PRODUCT_SUBCATEGORY_KEY, PRODUCT_CATEGORY_KEY, SALES_TERRITORY_KEY, DATE_KEY) — 0 duplicates each.
- No duplicate (ORDER_NUMBER, ORDER_LINE_ITEM) combinations within any single FACT_SALES table.
- No orphaned foreign keys anywhere: FACT_SALES_2020/2021/2022 → DIM_CUSTOMER/DIM_PRODUCT/DIM_TERRITORY/DIM_CALENDAR, FACT_RETURNS → DIM_PRODUCT/DIM_TERRITORY, DIM_PRODUCT → DIM_PRODUCT_SUBCATEGORY → DIM_PRODUCT_CATEGORY. All checks returned 0 orphans.
- No negative or zero ORDER_QUANTITY (range 1–3) or RETURN_QUANTITY (range 1–4) anywhere.
- No negative PRODUCT_COST or PRODUCT_PRICE, and no product priced below its own cost (0 rows).
- No negative ANNUAL_INCOME (range $10,000–$170,000).
- MARITAL_STATUS (M/S) and HOME_OWNER (Y/N) are fully clean — no nulls, no stray values.
- EDUCATION_LEVEL and OCCUPATION are fully populated with 5 consistent categorical values each, no nulls.
- No duplicate customer emails across 18,148 customers.
- STOCK_DATE never occurs after ORDER_DATE in any FACT_SALES table.
- All fact and return dates fall within DIM_CALENDAR's covered range (2020-01-01 to 2022-06-30), except DIM_PRODUCT_CATEGORY_SALES_PIVOT (see Issue 2).

## Recommended Next Steps (prioritized)

1. **(High)** Escalate the FACT_SALES_2020/2021/2022 overlap to the data owner and agree on a single source table (or a documented de-dupe key) before any revenue/order-count reporting is built. Do not union the three tables as-is.
2. **(High)** Get clarification on DIM_PRODUCT_CATEGORY_SALES_PIVOT's region definitions and date range before using it in any regional or category report; treat it as out-of-scope for now.
3. **(Medium)** Build a cleaned customer view that recodes GENDER = 'NA' to NULL/'Unknown' for the 130 affected customers, keeping the customer rows intact.
4. **(Medium)** Flag the 38 customers with 100+ implied age for source-system review; exclude them from age-banded segmentation until confirmed.
5. **(Low)** Document, in any report using FACT_RETURNS or dollar-based FACT_SALES metrics, that returns cannot be tied to a customer/order and that revenue is derived from current list price, not historical transaction price.

## Key Takeaways

- Core data integrity is strong: zero duplicate primary keys and zero orphaned foreign keys across all 11 tables — no dedupe or FK-repair work needed at the join-key level.
- The one issue that actually threatens report accuracy is the FACT_SALES_2020/2021/2022 overlap (rated HIGH): FACT_SALES_2020 contains 100% of FACT_SALES_2021 (18,758/18,758 rows) and 100% of FACT_SALES_2022 (9,906/9,906 rows) as exact duplicates — do not union these tables without de-duplication.
- DIM_PRODUCT_CATEGORY_SALES_PIVOT (rated HIGH for usability) is disconnected in both date range and region taxonomy from the rest of the model and should be excluded from analysis until clarified.
- Customer demographic data is otherwise clean; the two flagged issues (130 GENDER="NA" rows, 38 implausible birth dates) affect under 1% of the 18,148-row customer base combined and are easily filterable, not table-wide corruption.
- No business-rule violations were found on quantities, prices, costs, or income (no negatives, no price-below-cost, no negative income) across any fact or dimension table.
