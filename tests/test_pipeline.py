"""Automated checks for the educational processing logic (no Snakemake needed)."""
import csv
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import pipeline


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "data").mkdir()
        self.input = self.root / "data/reports.csv"
        self.output = self.root / "output"
        self.original_input = pipeline.INPUT
        self.original_output = pipeline.OUTPUT
        pipeline.INPUT = self.input
        pipeline.OUTPUT = self.output

    def tearDown(self):
        pipeline.INPUT = self.original_input
        pipeline.OUTPUT = self.original_output
        self.temp.cleanup()

    def write_input(self, rows):
        with self.input.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=pipeline.FIELDS)
            w.writeheader()
            w.writerows(rows)

    def base_rows(self):
        return [
            {"hospital": "A", "test_id": "101", "result": "Positive"},
            {"hospital": "A", "test_id": "102", "result": "Negative"},
            {"hospital": "B", "test_id": "103", "result": "Positive"},
            {"hospital": "B", "test_id": "103", "result": "Positive"},
        ]

    def test_happy_path(self):
        self.write_input(self.base_rows())
        pipeline.validate()
        pipeline.deduplicate()
        pipeline.aggregate()
        with (self.output / "summary.csv").open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(rows[0]["count"], "2")
        self.assertEqual(len(pipeline.read_rows(self.output / "unique.csv")), 3)

    def test_invalid_result_stops_before_output(self):
        rows = self.base_rows()
        rows[2]["result"] = "Unknown"
        self.write_input(rows)
        with self.assertRaisesRegex(ValueError, "invalid result"):
            pipeline.validate()
        self.assertFalse((self.output / "validated.csv").exists())

    def test_conflicting_duplicate_rejected(self):
        rows = self.base_rows()
        rows[3]["result"] = "Negative"
        self.write_input(rows)
        pipeline.validate()
        with self.assertRaisesRegex(ValueError, "Conflicting reports"):
            pipeline.deduplicate()
        self.assertFalse((self.output / "unique.csv").exists())

    def test_missing_id_rejected(self):
        rows = self.base_rows()
        rows[0]["test_id"] = ""
        self.write_input(rows)
        with self.assertRaisesRegex(ValueError, "required"):
            pipeline.validate()


if __name__ == "__main__":
    unittest.main()
