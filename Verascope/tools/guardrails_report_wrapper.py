import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import List


def build_markdown(report_path: Path, payload: dict) -> str:
    lines = [
        "# Guardrails Report",
        "",
        f"- Source report: {report_path.name}",
        f"- Rows checked: {payload['row_count']}",
        f"- Expected minimum rows: {payload['expected_row_count']}",
        f"- Overall status: {'PASS' if payload['overall_passed'] else 'FAIL'}",
        "",
        "## Checks",
    ]
    for item in payload.get("range_results", []):
        status = "PASS" if item["passed"] else "FAIL"
        lines.append(f"- {item['column']}: {status} ({item['failure_count']} failures)")
    lines.append("")
    lines.append("## Notes")
    if payload["logic_validation"]["issues"]:
        lines.extend(f"- {issue}" for issue in payload["logic_validation"]["issues"])
    else:
        lines.append("- Validation logic passed its internal checks.")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run guardrails after a report is generated")
    parser.add_argument("--input", required=True, help="Path to the input CSV")
    parser.add_argument("--report-path", required=True, help="Path to the generated report")
    parser.add_argument("--output-dir", required=True, help="Directory for guardrail artifacts")
    parser.add_argument("--expected-row-count", type=int, default=0, help="Expected minimum row count")
    parser.add_argument("--required-columns", nargs="*", default=[], help="Columns that must exist")
    parser.add_argument("--range-check", action="append", default=[], help="Column check in form column:min:max")
    parser.add_argument("--null-columns", nargs="*", default=[], help="Columns to evaluate for nulls")
    args = parser.parse_args()

    input_path = Path(args.input)
    report_path = Path(args.report_path)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    validator = Path(__file__).with_name("guardrails_validator.py")
    command = [
        sys.executable,
        str(validator),
        "--input",
        str(input_path),
        "--output",
        str(output_dir / "guardrails_report.json"),
        "--expected-row-count",
        str(args.expected_row_count),
        "--required-columns",
        *args.required_columns,
        "--null-columns",
        *args.null_columns,
    ]
    for entry in args.range_check:
        command.extend(["--range-check", entry])

    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    payload = json.loads((output_dir / "guardrails_report.json").read_text(encoding="utf-8"))
    markdown_path = output_dir / "guardrails_report.md"
    markdown_path.write_text(build_markdown(report_path, payload), encoding="utf-8")

    print(completed.stdout)
    print(f"Guardrail artifacts written to {output_dir}")


if __name__ == "__main__":
    main()
