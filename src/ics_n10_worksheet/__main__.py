"""CLI: ics-n10-worksheet invoice.json packing.json bol.json --json"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ics_n10_worksheet.csv_export import worksheet_to_csv
from ics_n10_worksheet.worksheet import build_worksheet


def load_documents(paths: list[str]) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    for raw_path in paths:
        payload = json.loads(Path(raw_path).read_text(encoding="utf-8"))
        if isinstance(payload, list):
            documents.extend(payload)
        elif isinstance(payload, dict) and isinstance(payload.get("documents"), list):
            documents.extend(payload["documents"])
        elif isinstance(payload, dict):
            documents.append(payload)
        else:
            raise SystemExit(f"{raw_path} must be a document object or a list of them.")
    return documents


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build an N10 review worksheet from DocFlow extraction JSON. Does not lodge to ICS.",
    )
    parser.add_argument("documents", nargs="+")
    parser.add_argument("--json", action="store_true", help="Print the worksheet as JSON (default).")
    parser.add_argument("--csv", metavar="PATH", help="Also write a line-level CSV to this path. Use - for stdout.")
    args = parser.parse_args(argv)
    try:
        worksheet = build_worksheet(load_documents(args.documents))
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.csv:
        rendered = worksheet_to_csv(worksheet)
        if args.csv == "-":
            print(rendered, end="")
        else:
            Path(args.csv).write_text(rendered, encoding="utf-8")
    if args.json or not args.csv:
        print(json.dumps(worksheet, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
