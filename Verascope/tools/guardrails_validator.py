import argparse
import csv
import json
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple


def load_csv_rows(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def summarize_nulls(rows: List[Dict[str, Any]], columns: List[str]) -> Dict[str, Any]:
    details = {}
    for column in columns:
        null_count = 0
        for row in rows:
            value = row.get(column)
            if value is None or str(value).strip() == "":
                null_count += 1
        details[column] = {
            "null_count": null_count,
            "null_rate": round(null_count / len(rows), 4) if rows else 0.0,
        }
    return details


def check_ranges(rows: List[Dict[str, Any]], checks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = []
    for check in checks:
        column = check["column"]
        minimum = check.get("min")
        maximum = check.get("max")
        failures = []
        for index, row in enumerate(rows, start=1):
            value = row.get(column)
            if value is None or str(value).strip() == "":
                continue
            try:
                numeric_value = float(value)
            except (TypeError, ValueError):
                failures.append({"row": index, "value": value, "reason": "non-numeric"})
                continue
            if minimum is not None and numeric_value < minimum:
                failures.append({"row": index, "value": value, "reason": "below_min"})
            if maximum is not None and numeric_value > maximum:
                failures.append({"row": index, "value": value, "reason": "above_max"})
        results.append({
            "column": column,
            "passed": len(failures) == 0,
            "failure_count": len(failures),
            "sample_failures": failures[:5],
        })
    return results


def validate_logic(rows: List[Dict[str, Any]], expected_row_count: int, required_columns: List[str], checks: List[Dict[str, Any]]) -> Dict[str, Any]:
    issues = []
    if expected_row_count <= 0:
        issues.append("expected_row_count must be positive")
    for column in required_columns:
        if not any(column in row for row in rows):
            issues.append(f"required column missing: {column}")
    for check in checks:
        column = check["column"]
        if column not in rows[0].keys() if rows else False:
            issues.append(f"range check references unknown column: {column}")
    return {"issues": issues, "passed": len(issues) == 0}


def write_report(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run automated guardrails checks on a CSV file")
    parser.add_argument("--input", required=True, help="Path to input CSV")
    parser.add_argument("--output", required=True, help="Path to output JSON report")
    parser.add_argument("--expected-row-count", type=int, default=0, help="Expected minimum row count")
    parser.add_argument("--required-columns", nargs="*", default=[], help="Columns that must exist")
    parser.add_argument("--range-check", action="append", default=[], help="Column check in form column:min:max")
    parser.add_argument("--null-columns", nargs="*", default=[], help="Columns to evaluate for nulls")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    rows = load_csv_rows(input_path)
    checks = []
    for entry in args.range_check:
        parts = entry.split(":")
        if len(parts) != 3:
            raise ValueError(f"Invalid range check: {entry}")
        column, minimum, maximum = parts
        checks.append({"column": column, "min": float(minimum), "max": float(maximum)})

    null_summary = summarize_nulls(rows, args.null_columns or [])
    range_results = check_ranges(rows, checks)
    logic_validation = validate_logic(rows, args.expected_row_count, args.required_columns, checks)

    row_count_ok = len(rows) >= args.expected_row_count if args.expected_row_count > 0 else True

    payload = {
        "input_file": str(input_path),
        "row_count": len(rows),
        "expected_row_count": args.expected_row_count,
        "row_count_ok": row_count_ok,
        "null_summary": null_summary,
        "range_results": range_results,
        "logic_validation": logic_validation,
        "overall_passed": row_count_ok and logic_validation["passed"] and all(item["passed"] for item in range_results),
    }

    write_report(output_path, payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
