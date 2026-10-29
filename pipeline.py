"""Educational CSV pipeline. Standard-library Python; no patient data.

Stages are run separately so Snakemake can track their file dependencies.
Assumption: test_id uniquely identifies a test event across all hospitals.
"""
import argparse  # Read the stage name from the terminal.
import csv  # Read and write comma-separated files.
from pathlib import Path  # Build paths consistently across platforms.

INPUT = Path("data/reports.csv")  # Raw reports: do not edit during a production run.
OUTPUT = Path("output")  # Intermediate and final files are written here.
FIELDS = ["hospital", "test_id", "result"]  # Required input data contract.
ALLOWED_RESULTS = {"Positive", "Negative"}  # Simplified demo-only coding rule.


def read_rows(path):
    """Load a CSV as dictionaries; one dictionary represents one report."""
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)  # Use the header row as dictionary keys.
        if reader.fieldnames is None:
            raise ValueError(f"{path}: CSV is empty or missing its header")
        if len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError(f"{path}: duplicate column names")
        if not set(FIELDS).issubset(reader.fieldnames):
            missing = sorted(set(FIELDS) - set(reader.fieldnames))
            raise ValueError(f"{path}: missing required columns: {missing}")
        rows = list(reader)  # Load all reports; appropriate only for a tiny demo.
    return rows


def write_rows(path, fields, rows):
    """Write a completed stage's results for the next stage to consume."""
    path.parent.mkdir(parents=True, exist_ok=True)  # Create output/ if needed.
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()  # Preserve explicit column names.
        writer.writerows(rows)  # Write one row per processed record.


def validate():
    """Stage 1: enforce schema, nonmissing values, and allowed result codes."""
    rows = read_rows(INPUT)  # Read raw reports; check required columns.
    for number, row in enumerate(rows, start=2):  # CSV line 1 is the header.
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f"Line {number}: malformed row or missing field")
        if not row["hospital"].strip() or not row["test_id"].strip():
            raise ValueError(f"Line {number}: hospital and test_id are required")
        if row["result"] not in ALLOWED_RESULTS:
            raise ValueError(
                f"Line {number}: invalid result {row['result']!r}; "
                "expected Positive or Negative"
            )
    write_rows(OUTPUT / "validated.csv", FIELDS, rows)
    print(f"VALIDATE: {len(rows)} records passed the checks.")


def deduplicate():
    """Stage 2: keep one report per test event; reject conflicting duplicates."""
    rows = read_rows(OUTPUT / "validated.csv")  # Consume Stage 1 output.
    seen = {}  # test_id -> (hospital, result) of first occurrence.
    unique = []  # Keep the first copy of each test event.
    for row in rows:
        test_id = row["test_id"]  # Demo assumes globally unique test IDs.
        signature = (row["hospital"], row["result"])
        if test_id in seen:
            if seen[test_id] != signature:
                raise ValueError(f"Conflicting reports for test_id={test_id}")
            continue  # Same test event, same details: ignore repeated report.
        seen[test_id] = signature  # Remember this event for later comparisons.
        unique.append(row)  # Add the first occurrence to the cleaned dataset.
    write_rows(OUTPUT / "unique.csv", FIELDS, unique)
    print(f"DEDUPLICATE: {len(rows)} reports -> {len(unique)} unique tests.")


def aggregate():
    """Stage 3: count positive TEST EVENTS, not clinical COVID-19 cases."""
    rows = read_rows(OUTPUT / "unique.csv")  # Consume Stage 2 output.
    positives = sum(row["result"] == "Positive" for row in rows)
    write_rows(OUTPUT / "summary.csv", ["metric", "count"], [
        {"metric": "distinct_positive_tests", "count": positives}
    ])
    print(f"AGGREGATE: {positives} distinct positive tests.")


def main():
    parser = argparse.ArgumentParser(description="Run one CSV processing stage")
    parser.add_argument("stage", choices=["validate", "deduplicate", "aggregate"])
    stage = parser.parse_args().stage
    {"validate": validate, "deduplicate": deduplicate,
     "aggregate": aggregate}[stage]()  # Execute the selected stage.


if __name__ == "__main__":
    main()  # Only run when invoked as a script, not when imported by tests.
