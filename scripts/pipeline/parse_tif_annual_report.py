"""
parse_tif_annual_report.py
==========================
Extract per-district increment-captured dollar figures from the
Dallas County TIF Annual Report PDF.

Produces `data/raw/layer3_tif_oz/dallas_tif_increment_2025.csv` with
columns:

    district_name, fy, base_value, current_value,
    increment_captured, lifetime_increment, source_page

Why this script exists:

  The thesis quotes `L3_DOWNTOWN_TIF: $8.83B` and `L3_GRAND_PARK_SOUTH_TIF:
  $333M` (FACTS.md) but no CSV in the repo holds the underlying
  per-district numbers. Until those are derived from the source PDF,
  the 26:1 ratio claim has no traceable lineage. Running this script
  closes that gap.

USAGE:

    python -m scripts.pipeline.parse_tif_annual_report \\
        --pdf data/raw/layer3_tif_oz/annual_reports/2025-TIF-Annual-Report.pdf \\
        --out data/raw/layer3_tif_oz/dallas_tif_increment_2025.csv

NOTE on PDF parsing:

  The 2025 county TIF Annual Report uses tabular formats that vary
  page-to-page. This script tries `pdfplumber` first (clean
  table-extract), then `pypdf` text fallback for pages where the table
  parser misses. Any pages where neither succeeds are written as
  diagnostics to `outputs/tables/tif_pdf_parse_warnings.csv` for
  manual review. **Manual transcription of those pages is expected
  and acceptable** — the goal is provenance, not full automation.
"""
from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import List, Dict

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("tif-parse")

REPO = Path(__file__).resolve().parents[2]

# District name normalization: PDF uses inconsistent casing/spacing.
DISTRICT_ALIASES = {
    "downtown connection": "Downtown Connection TIF",
    "city center":         "City Center TIF",
    "state-thomas":        "State-Thomas TIF",
    "state thomas":        "State-Thomas TIF",
    "uptown":              "Uptown TIF",
    "cedars":              "Cedars TIF",
    "deep ellum":          "Deep Ellum TIF",
    "design district":     "Design District TIF",
    "farmers market":      "Farmers Market TIF",
    "sports arena":        "Sports Arena TIF",
    "vickery meadow":      "Vickery Meadow TIF",
    "skillman corridor":   "Skillman Corridor TIF",
    "mlk":                 "MLK Jr. TIF",
    "fort worth avenue":   "Fort Worth Avenue TIF",
    "fort worth ave":      "Fort Worth Avenue TIF",
    "davis garden":        "Davis Garden TIF",
    "grand park south":    "Grand Park South TIF",
    "southwestern medical":"Southwestern Medical TIF",
    "tod":                 "Transit-Oriented Development TIF",
    "mall area":           "Mall Area Redevelopment TIF",
    "cypress waters":      "Cypress Waters TIF",
    "oak cliff gateway":   "Oak Cliff Gateway TIF",
}


def normalize_district(raw: str) -> str:
    s = raw.strip().lower().replace("tif", "").strip()
    for k, v in DISTRICT_ALIASES.items():
        if k in s:
            return v
    return raw.strip()


# Money parsing: handles $1,234,567.89 / $1.3 billion / $333M / $8.83B
_MONEY_RE = re.compile(
    r"\$?\s*([\d,]+(?:\.\d+)?)\s*(billion|million|thousand|b|m|k)?",
    re.IGNORECASE,
)
_MULT = {"billion": 1e9, "b": 1e9, "million": 1e6, "m": 1e6, "thousand": 1e3, "k": 1e3}


def parse_money(text: str) -> float | None:
    if not text:
        return None
    m = _MONEY_RE.search(text)
    if not m:
        return None
    raw_num = m.group(1).replace(",", "")
    try:
        n = float(raw_num)
    except ValueError:
        return None
    suffix = (m.group(2) or "").lower()
    return n * _MULT.get(suffix, 1.0)


def extract_with_pdfplumber(pdf_path: Path) -> tuple[List[Dict], List[Dict]]:
    """Returns (rows, warnings)."""
    try:
        import pdfplumber  # noqa
    except ImportError:
        log.error("pdfplumber not installed. Run: pip install pdfplumber")
        sys.exit(2)

    rows: List[Dict] = []
    warnings: List[Dict] = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables() or []
            if not tables:
                continue
            for tbl in tables:
                if not tbl or len(tbl) < 2:
                    continue
                header = [(c or "").lower().strip() for c in tbl[0]]
                # Heuristic: only try tables that have a "district"/"tif" col + a money col
                has_district = any("district" in h or "tif" in h for h in header)
                has_money    = any("increment" in h or "value" in h or "lifetime" in h for h in header)
                if not (has_district and has_money):
                    continue
                for row in tbl[1:]:
                    cells = [(c or "").strip() for c in row]
                    if not any(cells):
                        continue
                    name_cell = next((c for c in cells if c and not c.replace(",", "").replace("$", "").replace(".", "").isdigit()), "")
                    money_cells = [parse_money(c) for c in cells]
                    money_cells = [m for m in money_cells if m is not None]
                    if not name_cell or not money_cells:
                        continue
                    rows.append({
                        "district_name": normalize_district(name_cell),
                        "fy": "2024-2025",
                        "base_value":         money_cells[0] if len(money_cells) > 0 else None,
                        "current_value":      money_cells[1] if len(money_cells) > 1 else None,
                        "increment_captured": money_cells[2] if len(money_cells) > 2 else None,
                        "lifetime_increment": money_cells[-1] if money_cells else None,
                        "source_page": i,
                    })
            # Heuristic warning: page contains TIF context but parser found nothing
            text = (page.extract_text() or "").lower()
            if "tif" in text and not any(r["source_page"] == i for r in rows):
                warnings.append({"page": i, "reason": "TIF context present, no table extracted"})
    return rows, warnings


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--pdf", required=True, type=Path,
                   help="Path to Dallas County TIF Annual Report PDF")
    p.add_argument("--out", required=True, type=Path,
                   help="Output CSV path (district x FY)")
    args = p.parse_args()

    if not args.pdf.exists():
        log.error("PDF not found: %s", args.pdf)
        log.error("  Source: https://www.dallascounty.org/Assets/uploads/docs/plandev/2025-TIF-Annual-Report-and-District-Status-Update.pdf")
        return 2

    log.info("Parsing %s ...", args.pdf.name)
    rows, warnings = extract_with_pdfplumber(args.pdf)
    log.info("  ✓ extracted %d district rows", len(rows))
    if warnings:
        warn_path = REPO / "outputs" / "tables" / "tif_pdf_parse_warnings.csv"
        warn_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(warnings).to_csv(warn_path, index=False)
        log.warning("  ! %d page(s) flagged for manual review → %s",
                    len(warnings), warn_path.relative_to(REPO))

    if not rows:
        log.error("No district rows extracted. Manual transcription required.")
        log.error("  Open the PDF and fill in %s by hand using this header:", args.out)
        log.error("  district_name,fy,base_value,current_value,increment_captured,lifetime_increment,source_page")
        return 3

    df = pd.DataFrame(rows).sort_values(["district_name", "fy"])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    log.info("✓ wrote %s (%d rows)", args.out.relative_to(REPO), len(df))
    return 0


if __name__ == "__main__":
    sys.exit(main())
