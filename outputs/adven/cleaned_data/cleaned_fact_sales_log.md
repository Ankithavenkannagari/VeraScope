# Cleaned Data Log — cleaned_fact_sales.csv

## Source
- ADVENTURE_WORKS.DATA.FACT_SALES_2020 (56,046 rows)
- ADVENTURE_WORKS.DATA.FACT_SALES_2021 (18,758 rows)
- ADVENTURE_WORKS.DATA.FACT_SALES_2022 (9,906 rows)
- Connection: Snowflake MCP (snowflake_AW)

## Issue
FACT_SALES_2021 and FACT_SALES_2022 are fully-redundant subsets of FACT_SALES_2020. Verified by:
- Key containment: every row in FACT_SALES_2021 and FACT_SALES_2022 (keyed on ORDER_NUMBER + ORDER_LINE_ITEM) also exists in FACT_SALES_2020, with 0 rows in either table missing from FACT_SALES_2020.
- Full column-value comparison (IS DISTINCT FROM semantics) across all matched keys: only 1 of 56,046 keys had any column-level difference across the three tables (see note below). No net-new data is contributed by FACT_SALES_2021 or FACT_SALES_2022.

## Method
The cleaned output is FACT_SALES_2020 taken in full, since it is confirmed to be the complete and most-complete (no extra NULLs relative to the other two tables, on any matched row, in either direction) version of every row spanning the 2020–2022 range.

Naively unioning all three source tables would have double/triple-counted roughly 28,664 order lines with zero net new data gained.

Export method: queried FACT_SALES_2020 in full (all 8 columns, with ORDER_DATE and STOCK_DATE cast to text via TO_VARCHAR to avoid MCP DATE-serialization errors), ordered by ORDER_NUMBER, ORDER_LINE_ITEM, and paged through in 4 batches (OFFSET 0/15000/30000/45000, batch sizes 15000/15000/15000/11046) because a single unbatched query exceeded the MCP tool's response size limit. Batches were concatenated and de-duplication was verified by confirming 56,046 unique (ORDER_NUMBER, ORDER_LINE_ITEM) keys across the combined output with no overlap or gap at batch boundaries.

## Before
56,046 + 18,758 + 9,906 = 84,710 total raw rows across the three source tables if naively unioned (with heavy duplication of ~28,664 order lines).

## After
56,046 rows in the cleaned output (0 duplicates, 0 orphaned FK risk — already verified clean in the prior EDA/quality pass).

## Notes / Minor Data Points
- One-row STOCK_DATE completeness difference: order SO59728, line 4 — FACT_SALES_2020 has STOCK_DATE = '2021-08-15' while FACT_SALES_2021's copy of the same row has STOCK_DATE = NULL. Resolved by using FACT_SALES_2020's value (the non-null, more complete one), which is what this export does automatically since it is sourced solely from FACT_SALES_2020.
- ORDER_DATE in the cleaned output spans 2020-01-01 through 2022-06-30 (confirmed via CSV min/max), consistent with the known distribution of 2,630 rows dated 2020, 23,935 dated 2021, and 29,481 dated 2022.

## Output
- File: outputs/adven/cleaned_data/cleaned_fact_sales.csv
- Columns: ORDER_DATE, STOCK_DATE, ORDER_NUMBER, PRODUCT_KEY, CUSTOMER_KEY, TERRITORY_KEY, ORDER_LINE_ITEM, ORDER_QUANTITY
- Row count: 56,046 (header row + 56,046 data rows)

## Date and Author
- Date: 2026-07-22
- Author: AI Analyst — Data Quality Agent workflow
