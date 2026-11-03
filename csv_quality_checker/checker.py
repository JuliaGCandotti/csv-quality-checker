"""Core validation logic: read a CSV file and check it against a set of rules."""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class Issue:
    """One problem found in the file."""

    row: int  # line number in the file (the header is line 1); 0 = whole file
    column: str
    rule: str
    message: str


def load_rules(path: str | Path) -> dict:
    """Read the rules from a JSON file."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def read_rows(path: str | Path) -> tuple[list[str], list[dict[str, str]]]:
    """Return (column names, list of rows). Each row is a dict: column -> value."""
    # utf-8-sig quietly removes the invisible marker Excel adds to CSV files
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames or []
        rows = list(reader)
    return columns, rows


def _line_number(index: int) -> int:
    """Row 0 of the data is line 2 of the file, because line 1 is the header."""
    return index + 2


def _value(row: dict[str, str], column: str) -> str:
    """Get a cell as clean text. Missing cells become an empty string."""
    return (row.get(column) or "").strip()


def check_required_columns(columns: list[str], rules: dict) -> list[Issue]:
    issues = []
    for name in rules.get("required_columns", []):
        if name not in columns:
            issues.append(Issue(0, name, "required_columns", f"Column '{name}' is missing"))
    return issues


def check_not_empty(columns, rows, rules) -> list[Issue]:
    issues = []
    for name in rules.get("not_empty", []):
        if name not in columns:
            continue  # already reported by check_required_columns
        for i, row in enumerate(rows):
            if _value(row, name) == "":
                issues.append(Issue(_line_number(i), name, "not_empty", "Value is empty"))
    return issues


def check_unique(columns, rows, rules) -> list[Issue]:
    issues = []
    for name in rules.get("unique", []):
        if name not in columns:
            continue
        first_seen: dict[str, int] = {}
        for i, row in enumerate(rows):
            value = _value(row, name)
            if value == "":
                continue  # empty values are the job of "not_empty"
            line = _line_number(i)
            if value in first_seen:
                issues.append(
                    Issue(line, name, "unique", f"'{value}' already appears on line {first_seen[value]}")
                )
            else:
                first_seen[value] = line
    return issues


def check_patterns(columns, rows, rules) -> list[Issue]:
    issues = []
    for name, pattern in rules.get("patterns", {}).items():
        if name not in columns:
            continue
        regex = re.compile(pattern)
        for i, row in enumerate(rows):
            value = _value(row, name)
            if value and not regex.fullmatch(value):
                issues.append(Issue(_line_number(i), name, "patterns", f"'{value}' does not match the expected format"))
    return issues


def check_dates(columns, rows, rules) -> list[Issue]:
    issues = []
    for name, date_format in rules.get("dates", {}).items():
        if name not in columns:
            continue
        for i, row in enumerate(rows):
            value = _value(row, name)
            if not value:
                continue
            try:
                datetime.strptime(value, date_format)
            except ValueError:
                issues.append(
                    Issue(_line_number(i), name, "dates", f"'{value}' is not a valid date ({date_format})")
                )
    return issues


def check_allowed_values(columns, rows, rules) -> list[Issue]:
    issues = []
    for name, allowed in rules.get("allowed_values", {}).items():
        if name not in columns:
            continue
        for i, row in enumerate(rows):
            value = _value(row, name)
            if value and value not in allowed:
                issues.append(
                    Issue(_line_number(i), name, "allowed_values", f"'{value}' is not one of: {', '.join(allowed)}")
                )
    return issues


def run_checks(columns: list[str], rows: list[dict[str, str]], rules: dict) -> list[Issue]:
    """Run every rule and return the issues sorted by line number."""
    issues: list[Issue] = []
    issues += check_required_columns(columns, rules)
    issues += check_not_empty(columns, rows, rules)
    issues += check_unique(columns, rows, rules)
    issues += check_patterns(columns, rows, rules)
    issues += check_dates(columns, rows, rules)
    issues += check_allowed_values(columns, rows, rules)
    return sorted(issues, key=lambda issue: (issue.row, issue.column))
