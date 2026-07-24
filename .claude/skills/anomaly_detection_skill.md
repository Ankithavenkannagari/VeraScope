# Anomaly Detection Skill

Use this skill when the task is to detect unusual patterns in daily data.

## When to Use
- The request is about unusual spikes, drops, or irregular behavior in daily metrics.
- You need to flag data issues, sudden changes, or suspicious trends.
- The analysis should support investigation before reporting or forecasting.

## Workflow
1. Identify the metric and the daily time series to review.
2. Compare recent values to the recent baseline or trend.
3. Look for sudden changes, outliers, missing days, or unusual volatility.
4. Determine whether the pattern is likely a real business event or a data issue.
5. Summarize the anomaly clearly with the affected period and its likely impact.

## Output Style
- State what changed and when.
- Mention the magnitude of the deviation.
- Explain whether the anomaly is likely meaningful or likely data-related.
- Keep the explanation concise and business-friendly.

## Notes
- Prefer simple checks first when the series is limited.
- If the evidence is weak, say so explicitly.
- Do not overstate certainty.
