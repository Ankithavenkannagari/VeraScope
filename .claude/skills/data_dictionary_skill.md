# Data Dictionary Skill

Use this skill when the task is to document the structure of a warehouse, schema, or dataset.

## When to Use
- The request is to create or update a data dictionary.
- You need to describe tables, columns, keys, and business meaning.
- The goal is to make data easier to understand for analysts or downstream users.

## Workflow
1. Identify the target database or schema.
2. Inventory the tables and columns.
3. Describe each table by purpose and grain.
4. Describe each column by meaning, type, and role.
5. Highlight key identifiers, dates, measures, and dimensions.

## Output Style
- Use a clear table-by-table structure.
- Keep the format consistent and easy to scan.
- Note uncertainties when field meaning is not obvious.
- Favor practical descriptions over overly technical wording.

## Notes
- If the schema is large, prioritize core tables and high-value columns first.
- Distinguish between technical fields and business-facing fields.
- Do not invent meanings that are not supported by the data.
