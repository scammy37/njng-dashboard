#!/usr/bin/env python3
"""
process_bill.py — Parse a downloaded NJNG bill PDF and add it to data.json

Usage:
    python scripts/process_bill.py path/to/bill.pdf

With no argument, looks for a single PDF in incoming/ and processes that one.
On success, deletes the source PDF if it came from incoming/.

Note: this parser was written against NJNG's visual bill layout (screenshots),
not a live-extracted PDF text dump. The first real bill processed should be
checked carefully — if the regex below doesn't match, it prints the raw PDF
text so the pattern can be adjusted.
"""

import re
import json
import sys
from pathlib import Path
import pdfplumber

ROOT = Path(__file__).parent.parent
DATA_PATH = ROOT / "data.json"
INCOMING_DIR = ROOT / "incoming"

MONTHS = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,
          "Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}


def parse_pdf(pdf_path: Path) -> dict:
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join(p.extract_text() or "" for p in pdf.pages)

    # Service period + meter reading + therms + this-period gas charge, e.g.:
    # "May 07 Jun 08 00833337 6242 - 6207 = 35 x 1.0584 = 37.04 76.38"
    m = re.search(
        r"(\w{3} \d{2})\s+(\w{3} \d{2})\s+\S+\s+[\d,]+\s*-\s*[\d,]+\s*=\s*([\d,]+)\s*x\s*([\d.]+)\s*=\s*([\d.]+)\s+([\d.]+)",
        text,
    )
    if not m:
        print(f"--- PDF text (first 2000 chars) ---\n{text[:2000]}\n---")
        raise ValueError("Could not find service period / meter reading row in PDF — check the PDF format above.")

    start_str, end_str = m.group(1), m.group(2)
    ccf    = int(m.group(3).replace(",", ""))
    therms = float(m.group(5))
    cost   = float(m.group(6))

    # Due date gives us the year context
    ym = re.search(r"DUE DATE\s+\w+ \d{1,2},\s*(\d{4})", text)
    if not ym:
        print(f"--- PDF text (first 2000 chars) ---\n{text[:2000]}\n---")
        raise ValueError("Could not find due date (for year) in PDF — check the PDF format above.")
    due_year = int(ym.group(1))

    end_month  = MONTHS[end_str.split()[0]]
    start_month = MONTHS[start_str.split()[0]]
    # Due date is usually ~3 weeks after the period end, in the same year as the end date
    # unless the bill spans a Dec->Jan boundary.
    end_year = due_year
    start_year = end_year - 1 if start_month == 12 and end_month == 1 else end_year

    label  = f"{start_str.split()[0]} {str(start_year)[2:]}"
    period = f"{start_str}–{end_str}, {end_year}"

    from datetime import date
    days = (date(end_year, end_month, int(end_str.split()[1])) -
            date(start_year, start_month, int(start_str.split()[1]))).days

    # Bill calculation breakdown: BGS (supply) + one or more DEL (delivery) lines + customer charge
    m = re.search(r"[\d.]+ Therms X ([\d.]+) BGS\s*=\s*([\d.]+)", text)
    supply_cost = float(m.group(2)) if m else None

    delivery_cost = sum(float(v) for v in re.findall(r"[\d.]+ Therms X [\d.]+ DEL\s*=\s*([\d.]+)", text))
    delivery_cost = round(delivery_cost, 2) if delivery_cost else None

    m = re.search(r"Customer Charge\s*=\s*([\d.]+)", text)
    customer_charge = float(m.group(1)) if m else None

    # Avg temp — NJNG shows "*-" or similar when not available for the current month
    temp = None
    m = re.search(r"Avg Temp This Month:\s*(-?\d+)\s*°", text)
    if m:
        temp = int(m.group(1))

    return {
        "label":          label,
        "period":         period,
        "days":           days,
        "ccf":            ccf,
        "therms":         therms,
        "cost":           cost,
        "supplyCost":     supply_cost,
        "deliveryCost":   delivery_cost,
        "customerCharge": customer_charge,
        "temp":           temp,
    }


def update_data_json(entry: dict) -> bool:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        bills = json.load(f)

    if any(b["label"] == entry["label"] for b in bills):
        print(f"Entry for {entry['label']} already exists — skipping.")
        return False

    new_line = "  " + json.dumps(entry, separators=(",", ":"), ensure_ascii=False)
    raw = DATA_PATH.read_text(encoding="utf-8").rstrip()
    assert raw.endswith("]"), "Unexpected data.json format"
    updated = raw[:-1].rstrip() + ",\n" + new_line + "\n]\n"
    DATA_PATH.write_text(updated, encoding="utf-8")

    print(f"Added {entry['label']} to data.json")
    return True


def find_incoming_pdf() -> Path:
    pdfs = sorted(INCOMING_DIR.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(
            f"No PDF found in {INCOMING_DIR}/ — drop the bill PDF there, or pass a path directly."
        )
    if len(pdfs) > 1:
        raise ValueError(
            f"Multiple PDFs found in {INCOMING_DIR}/ — pass the one to process as an argument: "
            f"{[p.name for p in pdfs]}"
        )
    return pdfs[0]


def main():
    pdf_path = Path(sys.argv[1]) if len(sys.argv) >= 2 else find_incoming_pdf()

    entry = parse_pdf(pdf_path)
    print(f"\nParsed entry:\n{json.dumps(entry, indent=2)}")
    added = update_data_json(entry)

    if added and pdf_path.resolve().is_relative_to(INCOMING_DIR.resolve()):
        pdf_path.unlink()
        print(f"Removed processed PDF: {pdf_path}")

    if added:
        print(f"\n✓ NEW bill added: {entry['label']} | {entry['therms']} Therms | ${entry['cost']:.2f}")
    else:
        print(f"\nNo update: {entry['label']} already in dashboard")


if __name__ == "__main__":
    main()
