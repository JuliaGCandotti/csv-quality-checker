import json

from csv_quality_checker.checker import load_rules, read_rows, run_checks
from csv_quality_checker.cli import main

RULES = {
    "required_columns": ["id", "email"],
    "not_empty": ["id"],
    "unique": ["id"],
    "patterns": {"email": "[^@\\s]+@[^@\\s]+\\.[^@\\s]+"},
    "dates": {"signup_date": "%Y-%m-%d"},
    "allowed_values": {"plan": ["free", "basic"]},
}


def check(columns, rows, rules=RULES):
    return run_checks(columns, rows, rules)


def rules_of(issues):
    return [issue.rule for issue in issues]


def test_clean_file_has_no_issues():
    rows = [{"id": "1", "email": "a@b.com", "signup_date": "2025-01-31", "plan": "free"}]
    assert check(["id", "email", "signup_date", "plan"], rows) == []


def test_missing_required_column_is_reported_once():
    issues = check(["id"], [{"id": "1"}])
    assert rules_of(issues) == ["required_columns"]
    assert issues[0].column == "email"


def test_empty_value_is_reported_with_line_number():
    rows = [{"id": "1", "email": "a@b.com"}, {"id": "", "email": "c@d.com"}]
    issues = check(["id", "email"], rows)
    assert [(i.row, i.rule) for i in issues] == [(3, "not_empty")]


def test_duplicate_points_to_first_occurrence():
    rows = [{"id": "7", "email": "a@b.com"}, {"id": "7", "email": "c@d.com"}]
    issues = check(["id", "email"], rows)
    assert len(issues) == 1
    assert issues[0].rule == "unique"
    assert issues[0].row == 3
    assert "line 2" in issues[0].message


def test_bad_email_pattern():
    issues = check(["id", "email"], [{"id": "1", "email": "not-an-email"}])
    assert rules_of(issues) == ["patterns"]


def test_invalid_date_is_caught():
    rows = [{"id": "1", "email": "a@b.com", "signup_date": "2025-13-45"}]
    issues = check(["id", "email", "signup_date"], rows)
    assert rules_of(issues) == ["dates"]


def test_value_not_in_allowed_list():
    rows = [{"id": "1", "email": "a@b.com", "plan": "gold"}]
    issues = check(["id", "email", "plan"], rows)
    assert rules_of(issues) == ["allowed_values"]


def test_spaces_around_values_are_ignored():
    rows = [{"id": " 1 ", "email": " a@b.com "}]
    assert check(["id", "email"], rows) == []


def test_read_rows_and_load_rules(tmp_path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("id,email\n1,a@b.com\n", encoding="utf-8")
    rules_file = tmp_path / "rules.json"
    rules_file.write_text(json.dumps({"required_columns": ["id"]}), encoding="utf-8")

    columns, rows = read_rows(csv_file)
    assert columns == ["id", "email"]
    assert rows == [{"id": "1", "email": "a@b.com"}]
    assert load_rules(rules_file) == {"required_columns": ["id"]}


def test_cli_exit_codes(tmp_path):
    rules_file = tmp_path / "rules.json"
    rules_file.write_text(json.dumps({"not_empty": ["id"]}), encoding="utf-8")

    good = tmp_path / "good.csv"
    good.write_text("id,name\n1,Ana\n", encoding="utf-8")
    bad = tmp_path / "bad.csv"
    bad.write_text("id,name\n,Ana\n", encoding="utf-8")

    assert main([str(good), "--rules", str(rules_file)]) == 0
    assert main([str(bad), "--rules", str(rules_file)]) == 1
    assert main([str(tmp_path / "missing.csv"), "--rules", str(rules_file)]) == 2


def test_cli_writes_json_report_to_file(tmp_path):
    rules_file = tmp_path / "rules.json"
    rules_file.write_text(json.dumps({"not_empty": ["id"]}), encoding="utf-8")
    data = tmp_path / "data.csv"
    data.write_text("id,name\n,Ana\n", encoding="utf-8")
    out = tmp_path / "report.json"

    main([str(data), "--rules", str(rules_file), "--format", "json", "--output", str(out)])

    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["issue_count"] == 1
    assert report["issues"][0]["rule"] == "not_empty"
