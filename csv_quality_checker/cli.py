"""Command-line interface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .checker import load_rules, read_rows, run_checks
from .report import FORMATTERS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="csv-quality-checker",
        description="Check a CSV file against a set of rules and report problems.",
    )
    parser.add_argument("csv_file", help="path to the CSV file to check")
    parser.add_argument("--rules", required=True, help="path to the JSON rules file")
    parser.add_argument("--format", choices=sorted(FORMATTERS), default="text", help="report format (default: text)")
    parser.add_argument("--output", help="write the report to this file instead of the screen")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Exit codes: 0 = no issues, 1 = issues found, 2 = could not run the check."""
    args = build_parser().parse_args(argv)

    try:
        rules = load_rules(args.rules)
        columns, rows = read_rows(args.csv_file)
    except FileNotFoundError as error:
        print(f"Error: file not found: {error.filename}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as error:
        print(f"Error: the rules file is not valid JSON ({error})", file=sys.stderr)
        return 2

    issues = run_checks(columns, rows, rules)
    report = FORMATTERS[args.format](issues, len(rows))

    if args.output:
        Path(args.output).write_text(report + "\n", encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(report)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
