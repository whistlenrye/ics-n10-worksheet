import csv
import io
import json
import unittest
from pathlib import Path

from ics_n10_worksheet.__main__ import main
from ics_n10_worksheet.csv_export import worksheet_to_csv
from ics_n10_worksheet.worksheet import build_worksheet

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


def load_shipment():
    payload = json.loads((SAMPLES / "shipment.json").read_text(encoding="utf-8"))
    return payload["documents"]


class WorksheetTests(unittest.TestCase):
    def test_maps_invoice_and_bill_without_lodging(self):
        sheet = build_worksheet(load_shipment())
        self.assertFalse(sheet["lodges_to_ics"])
        self.assertIn("does not lodge", sheet["disclaimer"].lower())
        self.assertEqual(sheet["header"]["importer_name"], "Southbank Industrial Supplies Pty Ltd")
        self.assertEqual(sheet["header"]["invoice_number"], "INV-2026-1187")
        self.assertEqual(sheet["header"]["ocean_bill_of_lading"], "HLCU8877665")
        self.assertEqual(sheet["header"]["house_bill_of_lading"], "HBL-2026-1187")
        self.assertEqual(sheet["header"]["packages"], 18)
        self.assertEqual(sheet["header"]["gross_weight_kg"], 842.4)
        self.assertEqual(len(sheet["lines"]), 2)
        self.assertIsNone(sheet["lines"][0]["tariff_classification"])
        self.assertIn("FOB", sheet["header"]["valuation_note"])
        gap_fields = {gap["field"] for gap in sheet["gaps"]}
        self.assertIn("Tariff classification", gap_fields)
        self.assertIn("Importer client / ABN", gap_fields)

    def test_parser_style_bill_number(self):
        docs = load_shipment()
        bol = docs[2]
        bol.pop("transport")
        bol["invoice_number"] = "HLCU8877665"
        bol["warnings"] = ["No invoice number; stored the bill of lading number."]
        sheet = build_worksheet(docs)
        self.assertEqual(sheet["header"]["ocean_bill_of_lading"], "HLCU8877665")
        self.assertIsNone(sheet["header"]["house_bill_of_lading"])

    def test_csv_has_one_row_per_line(self):
        rendered = worksheet_to_csv(build_worksheet(load_shipment()))
        rows = list(csv.DictReader(io.StringIO(rendered)))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["invoice_number"], "INV-2026-1187")
        self.assertEqual(rows[0]["ocean_bill_of_lading"], "HLCU8877665")
        self.assertEqual(rows[1]["goods_description"], "Brass ball valves, 25mm")
        self.assertEqual(rows[0]["tariff_classification"], "")

    def test_cli(self):
        self.assertEqual(main([str(SAMPLES / "shipment.json"), "--json"]), 0)


if __name__ == "__main__":
    unittest.main()
