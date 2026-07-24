# Forecasting Skill

Use this skill when the task is to forecast the next month of revenue or another time-based metric from historical data.

## When to Use
- The user asks for a next-month forecast.
- The request is about revenue, demand, sales, or other trend-based predictions.
- The analysis should be based on historical patterns rather than a one-off descriptive summary.

## Workflow
1. Identify the target metric and the relevant time series.
2. Review historical values and note trend direction, seasonality, and anomalies.
3. Choose a simple, defensible method such as:
   - linear trend projection,
   - moving average,
   - exponential smoothing,
   - or time-based regression.
4. Produce a forecast for the next period and explain the assumptions.
5. Highlight uncertainty and practical business interpretation.

## Output Style
- Clearly separate historical observations from forecast values.
- State the chosen method.
- Mention confidence limits or caution if the series is volatile.
- Keep the tone business-friendly and concise.

## Notes
- Prefer simple methods when the dataset is limited.
- If the pattern is unstable or sparse, report that explicitly.
- Do not overstate certainty.
