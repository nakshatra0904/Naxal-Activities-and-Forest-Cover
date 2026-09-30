"""Rebuild the CPI-Maoist India event extract from UCDP GED 26.1."""
from pathlib import Path
import re
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)
ged = pd.read_csv(WORK / "ucdp_ged261_india.csv", low_memory=False)
actors = pd.read_csv(WORK / "ucdp_actor_v26_1.csv", encoding="cp1252", low_memory=False)
assert actors.loc[actors.ActorId.eq(195), "NameOrigFullEng"].iloc[0] == "Communist Party of India-Maoist"
assert ged.id.is_unique and ged.country.eq("India").all()
events = ged.loc[ged.year.between(2005, 2025) &
                 (ged.side_a_new_id.eq(195) | ged.side_b_new_id.eq(195))].copy()
assert len(events) == 3913
assert set(events.groupby("type_of_violence")["side_a"].unique().explode()) == {
    "Government of India", "CPI-Maoist"}
events["government_side_deaths"] = np.where(events.type_of_violence.eq(1), events.deaths_a, 0)
events["maoist_side_deaths"] = np.where(events.type_of_violence.eq(1), events.deaths_b, 0)
events["state"] = events.adm_1.fillna("Unspecified").str.replace(
    r"\s+state$", "", regex=True, flags=re.I).replace({"Orissa": "Odisha"})
events["district_label"] = events.adm_2.fillna("Unspecified").str.replace(
    r"\s+district$", "", regex=True, flags=re.I)
cols = ["id", "year", "date_start", "date_end", "type_of_violence",
        "state", "district_label", "where_prec", "date_prec", "event_clarity",
        "code_status", "best", "high", "low", "deaths_civilians",
        "government_side_deaths", "maoist_side_deaths", "deaths_unknown"]
extract = events[cols].sort_values(["year", "id"])
extract.to_csv(OUT / "maoist_ged_event_extract_2005_2025.csv", index=False)
print("Events", len(extract), "zero-best", int(extract.best.eq(0).sum()))
