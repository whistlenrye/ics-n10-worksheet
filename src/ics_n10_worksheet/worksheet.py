"""Map DocFlow extraction JSON onto an N10 review worksheet.

This does not lodge a declaration, calculate duty, or classify goods. It lines
commercial-document figures up against the public short titles on the
Australian Border Force Import Declaration (N10 / Form 71L) so a broker can
see what is already on the paperwork and what is still missing.

Item numbers below are the public N10 captions, not an EDI implementation.
"""

from __future__ import annotations

from typing import Any

INVOICE_TYPES = {"shipping.commercial_invoice", "generic.invoice"}
PACKING_TYPES = {"shipping.packing_list"}
BOL_TYPES = {"shipping.bill_of_lading"}

DISCLAIMER = (
    "Review worksheet only. It does not lodge to the Integrated Cargo System, "
    "calculate customs duty or GST, or replace a licensed customs broker."
)


def _first(documents: list[dict[str, Any]], types: set[str]) -> dict[str, Any] | None:
    for doc in documents:
        if doc.get("doc_type") in types:
            return doc
    return None


def _party(doc: dict[str, Any] | None, role: str) -> dict[str, Any]:
    if not doc:
        return {}
    party = doc.get(role)
    return party if isinstance(party, dict) else {}


def _transport(doc: dict[str, Any] | None) -> dict[str, Any]:
    if not doc:
        return {}
    raw = doc.get("transport")
    return raw if isinstance(raw, dict) else {}


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _lines(doc: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not doc:
        return []
    raw = doc.get("line_items") or []
    return [item for item in raw if isinstance(item, dict)]


def _bill_number(bol: dict[str, Any] | None, key: str) -> str | None:
    direct = _text(_transport(bol).get(key))
    if direct:
        return direct
    if key == "ocean_bill" and bol:
        warnings = " ".join(bol.get("warnings") or []).lower()
        stuffed = "bill of lading number" in warnings
        if stuffed or not _transport(bol):
            return _text(bol.get("invoice_number"))
    return None


def _incoterm_code(invoice: dict[str, Any] | None) -> str | None:
    raw = _text((invoice or {}).get("incoterms"))
    if not raw:
        return None
    return raw.split()[0].upper()


def _source(doc: dict[str, Any] | None, field: str) -> str | None:
    if not doc:
        return None
    return f"{doc.get('doc_type')}.{field}"


def build_worksheet(documents: list[dict[str, Any]]) -> dict[str, Any]:
    """Return an N10 review worksheet for one shipment."""
    if not documents:
        raise ValueError("At least one document is required.")
    for index, doc in enumerate(documents):
        if not isinstance(doc, dict):
            raise TypeError(f"Document {index} is not an object.")

    invoice = _first(documents, INVOICE_TYPES)
    packing = _first(documents, PACKING_TYPES)
    bol = _first(documents, BOL_TYPES)
    shipper = _party(invoice, "shipper") or _party(packing, "shipper") or _party(bol, "shipper")
    consignee = _party(invoice, "consignee") or _party(packing, "consignee") or _party(bol, "consignee")
    shipper_doc = invoice or packing or bol
    consignee_doc = invoice or packing or bol
    bol_transport = _transport(bol) or _transport(packing) or _transport(invoice)
    weight_doc = bol if _transport(bol).get("gross_weight_kg") is not None else packing
    package_doc = bol if _transport(bol).get("packages") is not None else packing

    mode = _text(bol_transport.get("mode"))
    if not mode and bol:
        mode = "sea"

    code = _incoterm_code(invoice)
    if code in {"FOB", "FCA", "FAS", "EXW"}:
        valuation_note = (
            f"Incoterm is {code}. The invoice total may exclude international freight "
            "and insurance to Australia. Do not copy it straight into customs value."
        )
    elif code in {"CIF", "CIP", "CFR", "CPT"}:
        valuation_note = (
            f"Incoterm is {code}. Confirm whether freight and insurance are already "
            "inside the invoice total before treating any figure as customs value."
        )
    else:
        valuation_note = (
            "No recognised Incoterm. Do not treat the invoice total as the customs value."
        )

    header = {
        "suggested_owner_reference": _text((invoice or {}).get("invoice_number")),
        "importer_name": _text(consignee.get("name")),
        "importer_address": _text(consignee.get("address")),
        "importer_country": _text(consignee.get("country")),
        "supplier_name": _text(shipper.get("name")),
        "supplier_address": _text(shipper.get("address")),
        "supplier_country": _text(shipper.get("country")),
        "supplier_tax_id": _text(shipper.get("tax_id")),
        "invoice_number": _text((invoice or {}).get("invoice_number")),
        "invoice_date": _text((invoice or {}).get("invoice_date")),
        "incoterms": _text((invoice or {}).get("incoterms")),
        "currency": _text((invoice or {}).get("currency")),
        "invoice_subtotal": (invoice or {}).get("subtotal"),
        "invoice_freight": (invoice or {}).get("freight"),
        "invoice_insurance": (invoice or {}).get("insurance"),
        "invoice_total": (invoice or {}).get("total"),
        "mode_of_transport": mode,
        "vessel_name": _text(bol_transport.get("vessel")),
        "voyage": _text(bol_transport.get("voyage")),
        "port_of_loading": _text(bol_transport.get("port_of_loading")),
        "port_of_discharge": _text(bol_transport.get("port_of_discharge")),
        "ocean_bill_of_lading": _bill_number(bol, "ocean_bill"),
        "house_bill_of_lading": _text(_transport(bol).get("house_bill")),
        "packages": (package_doc and _transport(package_doc).get("packages")),
        "gross_weight_kg": (weight_doc and _transport(weight_doc).get("gross_weight_kg")),
        "containers": bol_transport.get("containers") or [],
        "valuation_note": valuation_note,
    }
    sources = {
        "importer_name": _source(consignee_doc, "consignee.name"),
        "supplier_name": _source(shipper_doc, "shipper.name"),
        "invoice_number": _source(invoice, "invoice_number"),
        "ocean_bill_of_lading": _source(bol, "transport.ocean_bill"),
        "packages": _source(package_doc, "transport.packages"),
        "gross_weight_kg": _source(weight_doc, "transport.gross_weight_kg"),
    }

    invoice_lines = _lines(invoice) or _lines(packing)
    lines = []
    for offset, item in enumerate(invoice_lines, start=1):
        hs = _text(item.get("hs_code"))
        lines.append({
            "line_number": offset,
            "goods_description": _text(item.get("description")),
            "quantity": item.get("quantity"),
            "quantity_unit": _text(item.get("unit")),
            "unit_price": item.get("unit_price"),
            "invoice_line_amount": item.get("amount"),
            "hs_code_as_printed": hs,
            "tariff_classification": None,
            "country_of_origin": _text(item.get("country_of_origin")),
            "statistical_code": None,
        })

    gaps = [
        {
            "field": "Importer client / ABN",
            "why": "The ICS client identifier is not printed on a commercial invoice. The consignee name above may also be a notify party rather than the importer of record.",
        },
        {
            "field": "Tariff classification",
            "why": "An HS code printed on an invoice is usually 6 digits. An import declaration needs the Australian working tariff and statistical code. This worksheet leaves tariff_classification empty on purpose.",
        },
        {
            "field": "Customs value",
            "why": valuation_note,
        },
        {
            "field": "Vessel identifier (N10 item 68)",
            "why": "Item 68 wants the Lloyd's number (or the department's operator code), not the vessel name copied from the bill of lading.",
        },
        {
            "field": "Cargo type (N10 item 71)",
            "why": "FCL, FCX, LCL, break bulk, or bulk is an operational fact. Container numbers alone do not settle it.",
        },
        {
            "field": "Delivery address and phone (N10 items 59 and 60)",
            "why": "Final delivery is not the same field as the consignee address on the invoice.",
        },
        {
            "field": "Biosecurity packing questions",
            "why": "AQIS concern, packing, and premises fields are not on the commercial invoice. Answer them from the packing declaration, not from this worksheet.",
        },
    ]
    if not invoice:
        gaps.insert(0, {
            "field": "Commercial invoice",
            "why": "No invoice was supplied, so value, currency, and supplier lines are incomplete.",
        })
    if not header["ocean_bill_of_lading"] and mode == "sea":
        gaps.append({
            "field": "Ocean bill of lading (N10 item 69)",
            "why": "Sea cargo needs the ocean bill number. None was found on the bill of lading extraction.",
        })

    return {
        "form": "Import Declaration (N10)",
        "lodges_to_ics": False,
        "disclaimer": DISCLAIMER,
        "header": header,
        "sources": sources,
        "lines": lines,
        "gaps": gaps,
        "documents_read": [doc.get("doc_type") for doc in documents],
    }
