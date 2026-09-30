"""Extract and validate 2001 FSI district forest-cover tables from official PDF.

The FSI report sometimes publishes two districts as one combined row. Those
rows are retained as combined units and explicitly flagged below.
"""
from pathlib import Path
import re
import pdfplumber
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "work" / "sfr_2001.pdf"
OUT = ROOT / "outputs" / "fsi_2001_district_forest.csv"

TABLES = {
    "Andhra Pradesh": (42, "6.01", 275069, 44637, 23),
    "Bihar": (48, "6.04", 94163, 5720, 37),
    "Chhattisgarh": (50, "6.05", 135191, 56448, 16),
    "Jharkhand": (64, "6.12", 79714, 22637, 18),
    "Madhya Pradesh": (70, "6.15", 308245, 77265, 45),
    "Maharashtra": (73, "6.16", 307713, 47482, 35),
    "Odisha": (82, "6.21", 155707, 48838, 30),
    "Uttar Pradesh": (95, "6.27", 240928, 13746, 70),
    "West Bengal": (101, "6.29", 88752, 10693, 18),
}

NUM = r"[0-9][0-9,]*(?:\.[0-9]+)?"
ROW = re.compile(
    rf"^(.+?)\s+({NUM})\s+({NUM})\s+({NUM})\s+({NUM})\s+({NUM})\s+({NUM})$"
)


def number(text):
    return float(text.replace(",", ""))


def clean_name(text):
    text = re.sub(r"\s*[TH]+$", "", text.strip())
    text = re.sub(r"\s+", " ", text)
    return text


rows = []
with pdfplumber.open(PDF) as pdf:
    for state, (start_page, table, state_area, state_forest, n_districts) in TABLES.items():
        began = False
        completed = False
        pending = ""
        parsed = []
        for page_no in range(start_page, min(start_page + 5, len(pdf.pages) + 1)):
            lines = (pdf.pages[page_no - 1].extract_text() or "").splitlines()
            if not began:
                marker = f"Table {table} District-wise Forest Cover"
                starts = [i for i, line in enumerate(lines) if marker in line]
                if not starts:
                    continue
                lines = lines[starts[0] + 1 :]
                began = True
            for line in lines:
                line = line.strip().replace("\u00ad", "")
                m = ROW.fullmatch(line)
                if not m and pending:
                    m = ROW.fullmatch(pending + " " + line)
                if m:
                    name = clean_name(m.group(1))
                    area, dense, open_, forest, pct, scrub = map(number, m.groups()[1:])
                    pending = ""
                    if name == "Total":
                        assert int(area) == state_area, (state, area)
                        assert int(forest) == state_forest, (state, forest)
                        completed = True
                        break
                    if abs(dense + open_ - forest) > 1.1:
                        continue
                    if abs(100 * forest / area - pct) > 1.1:
                        continue
                    parsed.append([state, name, area, dense, open_, forest, pct, scrub, page_no, table, "single"])
                elif line and not re.match(r"^(?:\(?Area in|Forest Cover|District|Dense forest|area$|\d+\s+STATE|Forest and Tree Cover|Table |Number of Districts:)", line):
                    # A split row has its district name on one line and six
                    # numbers on the next. Hold one candidate line only.
                    pending = line
            if completed:
                break
        if not completed:
            raise RuntimeError(f"Did not reach total row for {state}")

        if state == "Andhra Pradesh":
            parsed.append([state, "Hyderabad + Rangareddy", 7710, 46, 335, 381, 4.94, 235, 42, table, "combined"])
        elif state == "Chhattisgarh":
            parsed.append([state, "Raipur + Dhamtari", 16468, 3183, 2025, 5208, 31.62, 18, 51, table, "combined"])

        got_area = sum(r[2] for r in parsed)
        got_forest = sum(r[5] for r in parsed)
        print(state, "units", len(parsed), "area", got_area, "forest", got_forest,
              "expected", state_area, state_forest)
        if abs(got_area - state_area) > 1 or abs(got_forest - state_forest) > 1:
            print("UNMATCHED OR DUPLICATE ROWS:", [(r[1], r[2], r[5]) for r in parsed])
            raise RuntimeError(f"Failed table total for {state}")
        rows.extend(parsed)

frame = pd.DataFrame(rows, columns=[
    "state", "fsi_2001_unit", "area_km2", "dense_forest_km2",
    "open_forest_km2", "forest_km2", "forest_pct", "scrub_km2",
    "source_pdf_page", "source_table", "unit_type",
])
frame.to_csv(OUT, index=False)
print("Wrote", len(frame), "units to", OUT)
