# AI Analyst

An AI-driven data analyst built on Claude Code, backed by Snowflake. It answers business and data questions by routing requests through a set of specialized agents (EDA, data quality, insight generation, forecasting, anomaly detection, data dictionary, report scheduling), following documented data models and metric definitions instead of ad-hoc queries.

## How it works

`CLAUDE.md` defines the orchestration workflow: clarify intent → identify the target database → route to the right agent → apply reporting standards → automatically run guardrails validation → save outputs to a database-specific folder. See `.claude/agents/` for each agent's role and `.claude/skills/` for the data model, metrics glossary, reporting style, and guardrails guidance it follows.

## Databases

Two Snowflake databases are supported out of the box:

| | Database | Schema |
|---|---|---|
| Database 1 | `OLIST_ECOMMERCE` | `RAW_DATA` |
| Database 2 | `ADVENTURE_WORKS` | `DATA` |

## Setup

1. Install the Snowflake MCP server (`mcp_snowflake_server`).
2. Copy `.claude/mcp.json.example` to `.claude/mcp.json` and fill in your Snowflake account, username, and password. **`.claude/mcp.json` is gitignored — never commit real credentials.**
3. Open the project in Claude Code. Ask a data question; the orchestrator will pick the right agent and Snowflake connection automatically.

## Project structure

```
.claude/agents/     Agent definitions (EDA, quality, insights, forecasting, anomaly detection, data dictionary, scheduling, guardrails)
.claude/skills/      Data model, metrics glossary, reporting style, and guardrails references
metadata/            Business rules, metric extensions, and table relationships per database
outputs/<db>/reports/       Generated reports (eda_, quality_, insights_, guardrails_ prefixes)
outputs/<db>/charts/        Generated charts
outputs/<db>/cleaned_data/  Cleaned data exports (gitignored — regenerate from Snowflake as needed)
```

## Output conventions

Reports and charts follow a fixed naming scheme (`eda_<table>.md`, `quality_<table>.md`, `insights_<topic>.md`, `chart_<analysis>.png`) and are always written to the database-specific `outputs/` subfolder. See `CLAUDE.md` for full reporting standards and the "Data Analysis Lessons Learned" section for dataset-specific quirks (customer identity keys, review deduplication, join fan-out traps, etc.).
