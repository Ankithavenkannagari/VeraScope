# EDA Report: Adventure Works (ADVENTURE_WORKS.DATA)

**Date:** 2026-07-22
**Database:** ADVENTURE_WORKS | **Schema:** DATA | **Warehouse:** COMPUTE_WH

## Executive Summary

Adventure Works is a 11-table star schema (4 dimensions plus a category hierarchy, a territory dimension, a calendar dimension, three yearly sales fact tables, one returns fact table, and one derived pivot table) covering bike/accessory retail sales from 2020-01-01 through 2022-06-30. Referential integrity between fact and dimension tables is clean (zero orphaned foreign keys, zero duplicate primary keys anywhere), but there is one critical structural problem: **FACT_SALES_2020 is not limited to 2020 — it is a cumulative table that fully contains every row of FACT_SALES_2021 and FACT_SALES_2022**, so a naive UNION ALL across the three yearly fact tables would badly double- and triple-count revenue. A handful of secondary issues (customer demographic placeholders, implausible birth dates, a disconnected pivot table) are also documented below.

## Key Findings

**Row counts (verified against live data, all match the values supplied at kickoff):**

| Table | Rows |
|---|---|
| DIM_CALENDAR | 912 |
| DIM_CUSTOMER | 18,148 |
| DIM_PRODUCT | 293 |
| DIM_PRODUCT_CATEGORY | 4 |
| DIM_PRODUCT_CATEGORY_SALES_PIVOT | 20 |
| DIM_PRODUCT_SUBCATEGORY | 37 |
| DIM_TERRITORY | 10 |
| FACT_RETURNS | 1,809 |
| FACT_SALES_2020 | 56,046 |
| FACT_SALES_2021 | 18,758 |
| FACT_SALES_2022 | 9,906 |

**Schema shape:**
- DIM_CUSTOMER (13 cols): CUSTOMER_KEY (PK) + demographics (PREFIX, FIRST_NAME, LAST_NAME, BIRTH_DATE, MARITAL_STATUS, GENDER, EMAIL_ADDRESS, ANNUAL_INCOME, TOTAL_CHILDREN, EDUCATION_LEVEL, OCCUPATION, HOME_OWNER).
- DIM_PRODUCT (11 cols): PRODUCT_KEY (PK), PRODUCT_SUBCATEGORY_KEY (FK), SKU/name/model/description/color/size/style, PRODUCT_COST, PRODUCT_PRICE.
- DIM_PRODUCT_SUBCATEGORY (3 cols) rolls up to DIM_PRODUCT_CATEGORY (2 cols) via PRODUCT_CATEGORY_KEY.
- DIM_TERRITORY (4 cols): SALES_TERRITORY_KEY (PK), REGION, COUNTRY, CONTINENT.
- DIM_CALENDAR (1 col): DATE_KEY (PK) — a single-column date spine, 2020-01-01 through 2022-06-30, no gaps (912 distinct dates = 912 calendar days in range).
- FACT_SALES_2020 / 2021 / 2022 (8 cols each, **identical schema**): ORDER_DATE, STOCK_DATE, ORDER_NUMBER, PRODUCT_KEY, CUSTOMER_KEY, TERRITORY_KEY, ORDER_LINE_ITEM, ORDER_QUANTITY. **Note: none of the three fact tables has a sales-amount/revenue column** — dollar sales must be derived as `ORDER_QUANTITY × DIM_PRODUCT.PRODUCT_PRICE` (or PRODUCT_COST for margin), joined through PRODUCT_KEY.
- FACT_RETURNS (4 cols): RETURN_DATE, TERRITORY_KEY, PRODUCT_KEY, RETURN_QUANTITY — **no ORDER_NUMBER or CUSTOMER_KEY**, so returns cannot be tied back to a specific order or customer, only to a product/territory/date.
- DIM_PRODUCT_CATEGORY_SALES_PIVOT (5 cols): SALES_DATE, PRODUCT_CATEGORY, NORTH_REGION, CENTRAL_REGION, SOUTH_REGION — a pre-aggregated/derived table, not a base fact table (see Data Quality Issues).

**Referential integrity (all checked by anti-join, zero tolerance):**
- FACT_SALES_2020/2021/2022 → DIM_CUSTOMER, DIM_PRODUCT, DIM_TERRITORY, DIM_CALENDAR: **0 orphaned rows** in every combination checked.
- FACT_RETURNS → DIM_PRODUCT, DIM_TERRITORY: **0 orphaned rows**.
- DIM_PRODUCT → DIM_PRODUCT_SUBCATEGORY → DIM_PRODUCT_CATEGORY: **0 orphaned rows** at either level.
- Primary-key duplicate check on all 6 dimension tables (CUSTOMER_KEY, PRODUCT_KEY, PRODUCT_SUBCATEGORY_KEY, PRODUCT_CATEGORY_KEY, SALES_TERRITORY_KEY, DATE_KEY): **0 duplicates** in every table.
- DIM_CUSTOMER.EMAIL_ADDRESS: **0 duplicate emails** across 18,148 customers.
- FACT_SALES_2020/2021/2022: **0 duplicate (ORDER_NUMBER, ORDER_LINE_ITEM) combinations** within each table individually.

**FACT_SALES_2020/2021/2022 schema/date consistency check — the critical finding:**
- Column names, order, and data types are identical across all three tables, so a UNION would be syntactically valid.
- However, ORDER_DATE in FACT_SALES_2020 ranges from 2020-01-01 to **2022-06-30** — it is not restricted to calendar year 2020. Breaking FACT_SALES_2020 down by year of ORDER_DATE: 2,630 rows are dated 2020, 23,935 rows are dated 2021, and 29,481 rows are dated 2022.
- Joining FACT_SALES_2020 to FACT_SALES_2021 on (ORDER_NUMBER, ORDER_LINE_ITEM) returns exactly 18,758 matches — i.e., **100% of FACT_SALES_2021's rows** have an identical-key match in FACT_SALES_2020, and every FACT_SALES_2021 row matches (0 rows in FACT_SALES_2021 lack a match in FACT_SALES_2020). A full-column comparison (PRODUCT_KEY, CUSTOMER_KEY, ORDER_QUANTITY, ORDER_DATE) on those matched pairs found **0 mismatches** — they are exact duplicates, not just key collisions.
- The same test against FACT_SALES_2022 returns exactly 9,906 matches — again **100% of FACT_SALES_2022's rows**, with 0 rows in FACT_SALES_2022 unmatched.
- Conclusion: FACT_SALES_2020 is a **cumulative/superset sales table** (effectively "all sales through 2022-06-30"), while FACT_SALES_2021 and FACT_SALES_2022 are single-year extracts of the same underlying data. FACT_SALES_2020 also contains additional 2021/2022-dated rows that are *not* present in the FACT_SALES_2021/2022 tables (23,935 + 29,481 = 53,416 rows dated 2021/2022 in FACT_SALES_2020, vs. only 18,758 + 9,906 = 28,664 matched by key — leaving roughly 24,752 rows unique to FACT_SALES_2020 with 2021/2022 dates). This means FACT_SALES_2020 alone is likely the most complete source, not a table to be unioned with the other two.
- STOCK_DATE vs ORDER_DATE: 0 rows in any of the three tables where STOCK_DATE occurs after ORDER_DATE (logically consistent).
- ORDER_QUANTITY: no nulls, no zero/negative values, range 1–3 in all three fact tables.

**DIM_CALENDAR coverage:** 2020-01-01 to 2022-06-30, 912 rows = 912 calendar days in that span (no missing dates). This means the calendar dimension — and by extension any FACT_SALES_2022 or FACT_SALES_2020 rows dated after 2022-06-30, if any existed — is capped at mid-2022. All fact and returns dates observed fall within this range.

**DIM_PRODUCT_CATEGORY_SALES_PIVOT:** Only 20 rows total, covering exactly 5 calendar days (2022-07-01 through 2022-07-05) across 4 product categories (Accessories, Bikes, Clothing, Components) with 3 region columns (NORTH_REGION, CENTRAL_REGION, SOUTH_REGION). This date range falls entirely **outside** DIM_CALENDAR's coverage (max 2022-06-30) and outside all three FACT_SALES tables' date ranges — it cannot be joined against DIM_CALENDAR or reconciled against fact sales for the same period. Its three region columns (North/Central/South) also do not map cleanly to DIM_TERRITORY's REGION values (Northeast, Northwest, Southeast, Southwest, Central, Canada, Australia, France, Germany, United Kingdom), so the aggregation grain/source of this table is unclear from the data alone.

**DIM_TERRITORY:** 10 rows — Australia, Canada, Central (US), France, Germany, Northeast (US), Northwest (US), Southeast (US), Southwest (US), United Kingdom — spanning 4 continents (Pacific, North America, Europe). No data quality issues found.

**DIM_PRODUCT:** 293 products, 0 nulls in PRODUCT_SUBCATEGORY_KEY/PRODUCT_COST/PRODUCT_PRICE/PRODUCT_SKU/PRODUCT_NAME. PRODUCT_COST ranges $0.86–$2,171.29; PRODUCT_PRICE ranges $2.29–$3,578.27. 0 rows where price is negative or price < cost.

**DIM_CUSTOMER demographics:**
- ANNUAL_INCOME: $10,000–$170,000, average ~$57,269, 0 negative values, 0 nulls.
- BIRTH_DATE: 1910-08-13 to 1980-12-26, 0 nulls, 0 future dates. 38 customers would be over 100 years old as of today (2026-07-22) based on BIRTH_DATE — see Data Quality Issues.
- TOTAL_CHILDREN: range 0–5, 0 nulls.
- GENDER: M = 9,126, F = 8,892, and a literal text value **"NA" = 130** rows (not a NULL, an actual string).
- PREFIX: MR. = 9,126, MRS. = 6,422, MS. = 2,470, **NULL = 130** rows.
- MARITAL_STATUS: M = 9,817, S = 8,331 — clean, no nulls, no stray values.
- HOME_OWNER: Y = 12,260, N = 5,888 — clean.
- EDUCATION_LEVEL (5 values, all populated): Bachelors 5,261; Partial College 4,966; High School 3,241; Graduate Degree 3,125; Partial High School 1,555.
- OCCUPATION (5 values, all populated): Professional 5,424; Skilled Manual 4,501; Management 3,011; Clerical 2,859; Manual 2,353.
- The 130 rows with GENDER = "NA" and the 130 rows with PREFIX = NULL are very likely the same customer subset (counts match exactly) representing incomplete demographic capture, not a data corruption spread across the table.

**FACT_RETURNS:** 1,809 rows, 0 nulls in any column, RETURN_QUANTITY ranges 1–4 with 0 zero/negative values, RETURN_DATE ranges 2020-01-18 to 2022-06-30 (within DIM_CALENDAR coverage). No orphaned PRODUCT_KEY or TERRITORY_KEY.

## Data Quality Issues

1. **FACT_SALES_2020 overlaps FACT_SALES_2021 and FACT_SALES_2022 entirely** — unioning the three tables as "3 years of sales" would double/triple-count the overlapping rows. This is the most consequential issue found; see Supporting Evidence above and the companion quality report for severity and remediation.
2. **GENDER contains a literal "NA" string for 130 customers**, alongside 130 NULL PREFIX values — likely the same incomplete-profile customers, but GENDER "NA" is not machine-readable as a missing value the way NULL is, which will silently corrupt any GROUP BY GENDER analysis (a 3rd "gender" bucket appears) unless explicitly filtered/recoded.
3. **38 customers have implausible birth dates** (100+ years old as of 2026), which will distort age-based segmentation if used at face value.
4. **DIM_PRODUCT_CATEGORY_SALES_PIVOT is disconnected from the rest of the model** — its 5-day date range (2022-07-01 to 2022-07-05) falls outside DIM_CALENDAR's range and outside all FACT_SALES date coverage, and its North/Central/South region breakdown does not map 1:1 to DIM_TERRITORY's 10 regions. It cannot currently be joined or reconciled against the fact/dimension tables.
5. **FACT_RETURNS has no CUSTOMER_KEY or ORDER_NUMBER**, limiting return analysis to the product/territory/date grain — return rate cannot be computed per customer or tied to the specific order that generated the return.
6. **FACT_SALES fact tables carry no revenue/amount column** — all dollar-based analysis requires a join to DIM_PRODUCT for PRODUCT_PRICE (list price at time of query, not necessarily the price at time of sale — see Limitations).

## Suggested Next Steps

- Route this database to the Data Quality Agent (done — see `quality_adventure_works.md`) to size, severity-rank, and propose remediation for each issue above before any revenue/customer reporting is built on top of these tables.
- Before writing any query that aggregates "total sales" or "sales by year," explicitly decide and document which fact table(s) to use — recommended default is FACT_SALES_2020 alone (as the most complete cumulative table) rather than a UNION of all three, pending confirmation from the data owner on why the tables overlap this way.
- Confirm with the data owner whether DIM_PRODUCT_CATEGORY_SALES_PIVOT is intended to extend the fact sales beyond 2022-06-30, and what its NORTH/CENTRAL/SOUTH regions correspond to in DIM_TERRITORY.
- Decide a standard treatment for GENDER = "NA" (recode to NULL or a documented "Unknown" category) before it is used in any customer segmentation.

## Assumptions and Limitations

- Row counts and all figures above were captured live via Snowflake queries against ADVENTURE_WORKS.DATA on 2026-07-22; if the underlying tables are refreshed, these numbers should be re-verified.
- PRODUCT_PRICE/PRODUCT_COST in DIM_PRODUCT are current/point-in-time values with no history — if prices changed over 2020–2022, revenue derived by joining fact quantity to current price will not exactly match true historical revenue. No effective-dated pricing table was found.
- "Orphaned foreign key" checks were performed via NOT EXISTS anti-joins on the exact key columns named in each table; they assume DATE_KEY/CUSTOMER_KEY/PRODUCT_KEY/SALES_TERRITORY_KEY are the intended join columns (consistent with the star-schema data model provided).
- Only SELECT queries were run; no data was modified.

## Key Takeaways

- All 11 tables were profiled; row counts match the pre-supplied figures exactly, and dimension/fact foreign keys are 100% clean — no orphaned FKs and no duplicate primary keys anywhere in the model.
- The single biggest issue is structural, not cosmetic: **FACT_SALES_2020 fully contains every row of FACT_SALES_2021 (18,758/18,758 matched) and FACT_SALES_2022 (9,906/9,906 matched)** with identical data on every column checked — treat it as a cumulative table, not a "2020-only" extract.
- Customer demographics are largely clean (0 nulls on income, marital status, gender proper values, home ownership) but 130 customers (0.7%) have GENDER recorded as literal text "NA" and NULL prefix, and 38 customers have birth dates implying 100+ years of age.
- DIM_PRODUCT_CATEGORY_SALES_PIVOT is an isolated 20-row table covering only 2022-07-01 to 2022-07-05, outside the calendar and fact sales date range — treat it as a separate derived artifact, not part of the core star schema, until its source/grain is clarified.
- FACT_SALES tables have no dollar amount column and FACT_RETURNS has no customer/order linkage — both are structural limitations to plan around, not data errors.
