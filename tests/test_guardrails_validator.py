import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "guardrails_validator.py"
WRAPPER = ROOT / "tools" / "guardrails_report_wrapper.py"


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "value"])
        writer.writeheader()
        writer.writerows(rows)


def test_validator_reports_expected_pass_and_fail(tmp_path: Path) -> None:
    sample = tmp_path / "sample.csv"
    write_csv(sample, [{"id": "1", "value": "10"}, {"id": "2", "value": "20"}])
    output = tmp_path / "report.json"

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--input",
            str(sample),
            "--output",
            str(output),
            "--expected-row-count",
            "2",
            "--required-columns",
            "id",
            "value",
            "--null-columns",
            "id",
            "value",
            "--range-check",
            "value:0:30",
        ],
        check=True,
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["row_count_ok"] is True
    assert payload["overall_passed"] is True

    failing = tmp_path / "failing.csv"
    write_csv(failing, [{"id": "", "value": "31"}])
    output2 = tmp_path / "report2.json"

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--input",
            str(failing),
            "--output",
            str(output2),
            "--expected-row-count",
            "2",
            "--required-columns",
            "id",
            "value",
            "--null-columns",
            "id",
            "value",
            "--range-check",
            "value:0:30",
        ],
        check=True,
    )

    payload2 = json.loads(output2.read_text(encoding="utf-8"))
    assert payload2["row_count_ok"] is False
    assert payload2["null_summary"]["id"]["null_count"] == 1
    assert payload2["range_results"][0]["passed"] is False


def test_report_wrapper_generates_guardrail_artifacts(tmp_path: Path) -> None:
    sample = tmp_path / "sample.csv"
    write_csv(sample, [{"id": "1", "value": "10"}, {"id": "2", "value": "20"}])
    report_path = tmp_path / "report.md"
    report_path.write_text("# Sample Report\n", encoding="utf-8")
    output_dir = tmp_path / "guardrails"

    subprocess.run(
        [
            sys.executable,
            str(WRAPPER),
            "--input",
            str(sample),
            "--report-path",
            str(report_path),
            "--output-dir",
            str(output_dir),
            "--expected-row-count",
            "2",
            "--required-columns",
            "id",
            "value",
            "--null-columns",
            "id",
            "value",
            "--range-check",
            "value:0:30",
        ],
        check=True,
    )

    json_path = output_dir / "guardrails_report.json"
    markdown_path = output_dir / "guardrails_report.md"
    assert json_path.exists()
    assert markdown_path.exists()
