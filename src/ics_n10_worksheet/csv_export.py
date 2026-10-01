"""One CSV row per goods line, with header facts repeated."""

from __future__ import annotations

import csv
import io
from typing import Any

_COLUMNS = [
    "line_number",
    "goods_description",
    "quantity",
    "quantity_unit",
    "unit_price",
    "invoice_line_amount",
    "hs_code_as_printed",
    "tariff_classification",
    "country_of_origin",
    "invoice_number",
    "currency",
    "incoterms",
    "supplier_name",
    "importer_name",
    "ocean_bill_of_lading",
    "house_bill_of_lading",
    "packages",
    "gross_weight_kg",
]


def worksheet_to_csv(worksheet: dict[str, Any]) -> str:
    header = worksheet.get("header") or {}
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=_COLUMNS, lineterminator="\n")
    writer.writeheader()
    lines = worksheet.get("lines") or []
    if not lines:
        lines = [{}]
    for line in lines:
        row = {column: line.get(column, "") for column in _COLUMNS}
        for key in (
            "invoice_number",
            "currency",
            "incoterms",
            "supplier_name",
            "importer_name",
            "ocean_bill_of_lading",
            "house_bill_of_lading",
            "packages",
            "gross_weight_kg",
        ):
            value = header.get(key)
            row[key] = "" if value is None else value
        writer.writerow(row)
    return buffer.getvalue()
