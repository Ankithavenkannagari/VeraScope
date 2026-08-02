---
name: guardrails-skill
description: Use this skill when adding automated validation gates for datasets, reports, or cleaned-data outputs.
---

# Guardrails Skill

Use this skill to add a final validation step before a report or cleaned dataset is accepted.

## Recommended checks
- Row count sanity: ensure the data has at least the expected minimum number of rows.
- Null checks: flag columns with unexpectedly high missing rates.
- Range sanity checks: ensure numeric fields remain within plausible bounds.
- Duplicate checks: verify that primary-key-like fields are not unexpectedly duplicated.
- Logic self-checks: confirm the validation rule references valid columns and coherent thresholds.

## Suggested workflow
1. Define expected row count and required columns.
2. Add sanity checks for numeric ranges or accepted categories.
3. Run the validator script against the cleaned data or analysis output.
4. If any check fails, block the report and request remediation.

## Expected output
- A machine-readable JSON report.
- A short human-readable guardrail note attached to the downstream report.
