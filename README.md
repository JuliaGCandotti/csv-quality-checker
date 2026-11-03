# csv-quality-checker

A small Python command-line tool that checks a CSV file against a set of rules and reports every problem it finds, with the exact line number.

I built it because catching bad data before it is published or imported is tedious to do by hand. Missing values, duplicate IDs, malformed emails, impossible dates, and unexpected categories all show up in real files. The rules live in a JSON file, so the same tool can check different kinds of CSV files without changing any code.

It uses only the Python standard library, so there is nothing to install to run it.

## Example

Sample data with deliberate mistakes is included in `sample_data/`.

```console
$ python -m csv_quality_checker sample_data/members.csv --rules sample_data/rules.json
Checked 10 rows, found 6 issue(s).
  [patterns] line 4, column 'email': 'carla.souza@example' does not match the expected format
  [not_empty] line 5, column 'name': Value is empty
  [dates] line 6, column 'signup_date': '2025-13-45' is not a valid date (%Y-%m-%d)
  [unique] line 7, column 'email': 'ana.silva@example.com' already appears on line 2
  [unique] line 8, column 'id': '6' already appears on line 7
  [allowed_values] line 8, column 'plan': 'gold' is not one of: free, basic, premium
```

## Usage

Requires Python 3.9 or newer.

```console
python -m csv_quality_checker FILE.csv --rules RULES.json [--format text|markdown|json] [--output REPORT]
```

| Option | Meaning |
|---|---|
| `--rules` | JSON file describing the checks (required) |
| `--format` | `text` (default), `markdown`, or `json` |
| `--output` | Save the report to a file instead of printing it |

The exit code makes it easy to use in scripts: `0` means no issues, `1` means issues were found, and `2` means the check could not run (for example, a file was not found).

## Rules

| Rule | What it checks |
|---|---|
| `required_columns` | These columns must exist in the file |
| `not_empty` | These columns cannot have empty values |
| `unique` | Values in these columns cannot repeat |
| `patterns` | Values must fully match a regular expression |
| `dates` | Values must be valid dates in the given format |
| `allowed_values` | Values must come from a fixed list |

See `sample_data/rules.json` for an example of every rule.

## Project layout

```
csv_quality_checker/
  checker.py   # reads the CSV and runs each rule (the core logic)
  report.py    # formats the issues as text, Markdown, or JSON
  cli.py       # command-line arguments and exit codes
tests/         # pytest tests for every rule and the CLI
sample_data/   # example CSV and rules
```

## Running the tests

```console
pip install -r requirements-dev.txt
pytest
```

The tests also run automatically on every push through GitHub Actions.

## Design notes

- **One small function per rule.** Each rule is a separate function that returns a list of issues, so adding a new rule means adding one function and one line in `run_checks`.
- **Rules as data.** Keeping the rules in JSON means people who do not write Python can adjust the checks.
- **Clear error locations.** Every issue includes the line number in the file (the header is line 1), so problems are easy to find in Excel or a text editor.
- **Duplicates point to the first occurrence.** A duplicate message says where the value first appeared.

## Ideas for next steps

- Number-range rules (for example, price must be between 0 and 1000)
- A `--fix` mode for simple cleanups such as trimming spaces
- Support for Excel files

## Author

Julia Candotti, Calgary, AB. [LinkedIn](https://www.linkedin.com/in/juliacandotti)
