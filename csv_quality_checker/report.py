"""Turn a list of issues into a report (plain text, Markdown, or JSON)."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict

from .checker import Issue


def _summary_line(issues: list[Issue], total_rows: int) -> str:
    if not issues:
        return f"OK - checked {total_rows} rows, no issues found."
    return f"Checked {total_rows} rows, found {len(issues)} issue(s)."


def format_text(issues: list[Issue], total_rows: int) -> str:
    lines = [_summary_line(issues, total_rows)]
    for issue in issues:
        where = "file" if issue.row == 0 else f"line {issue.row}"
        lines.append(f"  [{issue.rule}] {where}, column '{issue.column}': {issue.message}")
    return "\n".join(lines)


def format_markdown(issues: list[Issue], total_rows: int) -> str:
    lines = ["# CSV quality report", "", _summary_line(issues, total_rows), ""]
    if issues:
        by_rule = Counter(issue.rule for issue in issues)
        lines += ["## Issues by rule", "", "| Rule | Count |", "|---|---|"]
        lines += [f"| {rule} | {count} |" for rule, count in sorted(by_rule.items())]
        lines += ["", "## Details", "", "| Line | Column | Rule | Message |", "|---|---|---|---|"]
        for issue in issues:
            line = "-" if issue.row == 0 else issue.row
            lines.append(f"| {line} | {issue.column} | {issue.rule} | {issue.message} |")
    return "\n".join(lines)


def format_json(issues: list[Issue], total_rows: int) -> str:
    data = {
        "rows_checked": total_rows,
        "issue_count": len(issues),
        "issues": [asdict(issue) for issue in issues],
    }
    return json.dumps(data, indent=2)


FORMATTERS = {"text": format_text, "markdown": format_markdown, "json": format_json}
