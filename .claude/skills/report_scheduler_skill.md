# Report Scheduler Skill

Use this skill when the task is to generate and send weekly reports automatically.

## When to Use
- The request is to create a recurring weekly report.
- The report should be distributed by email.
- The goal is to summarize recent performance, changes, or risks in a concise weekly update.

## Workflow
1. Gather the latest relevant data and prior report context.
2. Select the main weekly metrics and updates.
3. Draft a concise report with an executive summary and key findings.
4. Format the content for email delivery.
5. Send the report through the project Gmail SMTP configuration using environment variables.
6. Prefer the provided mail script over manual email sending.

## Output Style
- Keep the report short and structured.
- Use clear headings such as Summary, Key Findings, Risks, and Recommendations.
- Mention any data limitations or missing information.
- Make the content suitable for a business audience.

## Notes
- Use the latest verified data rather than stale snapshots.
- If the emailing workflow is not configured, note the missing setup clearly.
- Avoid overloading the recipient with excessive detail.
