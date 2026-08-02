# Verascope

**A governed multi-agent AI analyst that turns raw warehouse data into trustworthy, business-ready answers.**

Verascope is an agentic data-analyst platform built on Claude Code and Snowflake. Instead of one model guessing at a query, it routes every business question through a deterministic pipeline of specialized agents — each with a narrow job, a shared source of truth, and a mandatory quality gate — so the answer that comes back is explainable, reproducible, and safe to put in front of stakeholders.

---

## What this is

A framework of eight cooperating agents, orchestrated by a single set of rules (`CLAUDE.md`), that sit in front of one or more Snowflake databases and answer natural-language business questions.

## What it does

- Explores and profiles new tables before anyone analyzes them (EDA).
- Validates data trustworthiness — nulls, duplicates, broken keys, out-of-range values — before it's reported on.
- Generates business insights (trends, drivers, comparisons) using **approved metric definitions**, never ad-hoc math.
- Forecasts near-term metrics like revenue from historical trend and seasonality.
- Detects anomalies and unusual patterns before they contaminate a report or forecast.
- Documents the data model itself, so table and column meaning don't live only in someone's head.
- Runs an automated guardrails check — row counts, null rates, ranges, duplicates — as the last gate before any report is finalized.
- Sends recurring reports on a schedule, without manual re-running.

## Purpose — what problem this solves

Most "chat with your data" tools produce a plausible-sounding answer with no visibility into how it was derived, whether the underlying data was clean, or whether the same question asked twice gives the same answer. Verascope solves that by making every step of the analysis pipeline **explicit, ordered, and auditable**:

- **Consistency** — every agent uses the same data model and metrics glossary, so two people (or two databases) never get silently different definitions of "revenue" or "active customer."
- **Trust** — nothing is reported as final until it passes an automated guardrails gate.
- **Reuse** — prior EDA, quality, and insight artifacts are checked first, so the same analysis isn't redone (or redefined) every time someone asks.
- **Multi-tenancy** — designed to run against multiple independent Snowflake databases (currently e-commerce and enterprise-sales domains) without cross-contaminating outputs.

---

## Quick start

1. Install the Snowflake MCP server (`mcp_snowflake_server`).
2. Copy `.claude/mcp.json.example` to `.claude/mcp.json` and fill in your Snowflake account, username, and password.
   `.claude/mcp.json` is gitignored — **never commit real credentials.**
3. Create a virtual environment and install Python dependencies: `pip install -r requirements.txt` (used for the guardrails test suite and chart generation).
4. Open the project in Claude Code.
5. Ask a data question in plain English. The orchestrator identifies the target database, picks the right agent(s), and applies the reporting and guardrails standards automatically.

```
"What's driving the drop in reviews this quarter?"
"Give me an EDA on the products table."
"Forecast next month's revenue."
"Is the sales_log data trustworthy enough to report on?"
```

## Commands

Verascope has no custom CLI — everything runs through natural-language requests inside Claude Code, which routes to the right agent per the workflow below. Useful things to say:

| Ask for... | Routes to |
|---|---|
| "Give me an overview / EDA of `<table>`" | EDA Agent |
| "Check / clean / validate `<dataset>`" | Data Quality Agent |
| "What's driving `<metric>`?" / "Give me insights on `<topic>`" | Insight Generator Agent |
| "Forecast `<metric>` for next month" | Forecasting Agent |
| "Are there any unusual patterns in `<metric>`?" | Anomaly Detection Agent |
| "What does column/table `<x>` mean?" | Data Dictionary Agent |
| "Validate this report/dataset before we ship it" | Guardrails Agent |
| "Send me the weekly report" | Report Scheduler Agent |
| Simple factual lookups | Snowflake MCP directly |

## Workflow

Every request follows the same deterministic path, defined in `CLAUDE.md`:

1. **Clarify intent** — ask a short question if the request is ambiguous.
2. **Identify the target database** — infer from context or ask.
3. **Confirm the Snowflake MCP connection** for that database.
4. **Reuse prior work** — check existing EDA/quality/insight artifacts before starting fresh.
5. **Route deterministically** to the right agent (EDA → Data Quality → Guardrails → Insights → Forecasting → Anomaly Detection → Data Dictionary → Report Scheduler, as applicable).
6. **Apply the handoff contract** — each agent reads the prior agent's artifact and states its own assumptions, evidence, and open issues.
7. **Apply reporting standards** and automatically run the guardrails gate on any generated report.
8. **Save outputs** to the correct database-specific folder.

## Repo structure

```
CLAUDE.md                    Orchestration rules — routing, standards, database config
.claude/agents/               8 agent definitions (EDA, quality, insights, forecasting,
                               anomaly detection, data dictionary, scheduling, guardrails)
.claude/skills/                Shared references every agent must follow:
                               data model, metrics glossary, reporting style, guardrails
metadata/<db>/                Business rules, metric extensions, table relationships per database
outputs/<db>/reports/          Generated reports (eda_, quality_, insights_, guardrails_ prefixes)
outputs/<db>/charts/           Generated charts
outputs/<db>/cleaned_data/     Cleaned data exports (gitignored — regenerate from Snowflake)
```

## Databases

Verascope currently supports two independent Snowflake databases out of the box; outputs are always kept in separate, database-specific folders and are never cross-combined unless explicitly requested.

| | Database | Schema |
|---|---|---|
| Database 1 | `OLIST_ECOMMERCE` | `RAW_DATA` |
| Database 2 | `ADVENTURE_WORKS` | `DATA` |

## Output conventions

Reports and charts follow a fixed naming scheme (`eda_<table>.md`, `quality_<table>.md`, `insights_<topic>.md`, `forecast_<topic>.md`, `anomaly_<topic>.md`, `guardrails_<table>.md`, `chart_<analysis>.png`) and are always written to the database-specific `outputs/` subfolder. See `CLAUDE.md` for full reporting standards and the "Data Analysis Lessons Learned" section for dataset-specific quirks (customer identity keys, review deduplication, join fan-out traps, etc.).
