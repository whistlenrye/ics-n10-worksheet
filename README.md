# ics-n10-worksheet

Turn DocFlow extraction JSON into an **Australian Import Declaration (N10) review worksheet**.

This does **not** lodge to the Integrated Cargo System, calculate duty or GST, or classify goods. A licensed broker still has to do those things. What it does is stop the rekey: the figures that are already on the invoice, packing list, and bill of lading are lined up against the public N10 captions, and the fields that are *not* on those documents are listed as gaps.

Item numbers cited here (59, 60, 68, 69, 70, 71) are the public captions on [Form 71L, Import Declaration (N10)](https://www.abf.gov.au/help-and-support-subsite/files/71l-import-declaration-n10.pdf). This is not an EDI message and it is not a Message Implementation Guideline.

## Pipeline

```text
docflow-extractor     read one document
shipment-crosscheck   do the documents agree?   https://github.com/whistlenrye/shipment-crosscheck
ics-n10-worksheet     this repo
```

Run the cross-check first. This worksheet will happily copy a quantity that the packing list disagrees with.

## Run

```bash
python3 -m ics_n10_worksheet samples/shipment.json --json
python3 -m ics_n10_worksheet samples/invoice.json samples/packing_list.json samples/bill_of_lading.json --csv lines.csv
```

The JSON worksheet has:

- `lodges_to_ics: false` — always
- `header` — importer (from the consignee, which may be wrong), supplier, invoice figures, ocean bill, house bill, packages, gross weight
- `lines` — description, quantity, printed HS code, and `tariff_classification: null`
- `gaps` — client id / ABN, 8-digit tariff, customs value, Lloyd's vessel id, cargo type, delivery address, biosecurity packing questions
- `sources` — which document each header fact came from

`--csv` writes one row per goods line with the header facts repeated. The tariff column is blank on purpose.

## Honest limits

- Consignee is not always the importer of record.
- A 6-digit HS code on an invoice is not an Australian working tariff.
- FOB invoice totals are not customs value. The worksheet says so when the Incoterm is FOB, FCA, FAS, or EXW.
- DocFlow's current parser stores a bare bill-of-lading number in `invoice_number`. If the warnings say `stored the bill of lading number`, this tool reads that as the ocean bill.

## Test

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Samples are synthetic. They are not a real shipment and not a filing.

## License

MIT.
