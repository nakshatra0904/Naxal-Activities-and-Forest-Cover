"""Join FSI 2001 forest units to Census-2001 shapes and 2001 WB covariates.

All nontrivial names/splits are explicit. Unresolved records fail rather than
silently fuzzy matching. The World Bank '2001' file uses later district units;
population-weighted aggregation returns them to the FSI 2001 reporting units.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "work" / "pydeps"))
import pandas as pd
import shapefile

OUT = ROOT / "outputs"
WORK = ROOT / "work"
FSI = pd.read_csv(OUT / "fsi_2001_district_forest.csv")

def norm(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())

ALIASES = {
    "Andhra Pradesh": {
        "Hyderabad": "Hyderabad + Rangareddy", "Rangareddi": "Hyderabad + Rangareddy",
        "Rangareddy": "Hyderabad + Rangareddy",
        "Mahbubnagar": "Mahboobnagar", "Visakhapatnam": "Vishakapatnam",
        "East Godavari": "East Godawari", "West Godavari": "West Godawari",
        "Prakasam": "Prakasham", "Sri Potti Sriramulu Nellore": "Nellore",
        "Y.S.R.": "Cuddapah",
    },
    "Bihar": {
        "Gopalganj": "Goplaganj", "Purba Champaran": "Purbi Champaran",
        "Pashchim Champaran": "Paschimi Champaran", "Kaimur (Bhabua)": "Bhabua",
        "Supaul": "Sapaul", "Arwal": "Jehanabad",
    },
    "Chhattisgarh": {
        "Dantewada": "Dantewara", "Dakshin Bastar Dantewada": "Dantewara",
        "Bijapur": "Dantewara", "Narayanpur": "Bastar",
        "Mahasamund": "Mahasamud", "Kabeerdham": "Kawardha",
        "Raipur": "Raipur + Dhamtari", "Dhamtari": "Raipur + Dhamtari",
        "Uttar Bastar Kanker": "Kanker",
        "Janjgir - Champa": "Janjgir-Champa",
    },
    "Jharkhand": {
        "Pashchimi Singhbhum": "Paschimi Singhbhum",
        "Saraikela-Kharsawan": "Paschimi Singhbhum",
        "Latehar": "Palamu", "Khunti": "Ranchi", "Simdega": "Gumla",
        "Jamtara": "Dumka", "Ramgarh": "Hazaribagh", "Pakur": "Pakaur",
    },
    "Madhya Pradesh": {
        "East Nimar": "Nimar East", "Khandwa (East Nimar)": "Nimar East",
        "Burhanpur": "Nimar East", "West Nimar": "Nimar West",
        "Khargone (West Nimar)": "Nimar West", "Gwalior": "Gwaliar",
        "Narsimhapur": "Narshimhapur", "Ashoknagar": "Guna",
        "Anuppur": "Shahdol", "Singrauli": "Sidhi", "Alirajpur": "Jhabua",
    },
    "Maharashtra": {
        "Mumbai": "Mumbai City", "Mumbai (Suburban)": "Mumbai Suburb",
        "Mumbai Suburban": "Mumbai Suburb", "Solapur": "Sholapur",
    },
    "Odisha": {
        "Anugul": "Angul", "Bargarh": "Baragarh", "Balangir": "Bolangir",
        "Baudh": "Boudh", "Debagarh": "Deogarh", "Gajapati": "Gajpati",
        "Jagatsinghapur": "Jagatsinghpur", "Jajapur": "Jajpur",
        "Kendrapara": "Kendarpara", "Kendujhar": "Keonjhar",
        "Kandhamal": "Khandamal", "Khordha": "Khurda",
        "Nuapada": "Nawapara", "Nabarangapur": "Nawrangpur",
        "Subarnapur": "Sonepur", "Sonapur": "Sonepur",
    },
    "Uttar Pradesh": {
        "Auraiya": "Orraiya", "Baghpat": "Bagpat",
        "Bulandshahr": "Bulandshahar", "Chitrakoot": "Chitrkoot",
        "Gautam Buddha Nagar": "Gautam Buddh Nagar",
        "Maharajganj": "Maharaj Ganj", "Mahrajganj": "Maharaj Ganj",
        "Muzaffarnagar": "Muzzaffarnagar", "Rae Bareli": "Raibareli",
        "Sant Ravidas Nagar Bhadohi": "Sant Ravidas Nagar",
        "Sant Ravidas Nagar (Bhadohi)": "Sant Ravidas Nagar",
        "Shrawasti": "Bahraich", "Mahamaya Nagar": "Hathras",
        "Kanshiram Nagar": "Etah",
    },
    "West Bengal": {
        "Barddhaman": "Bardhman", "Darjiling": "Darjeeling",
        "Haora": "Howrah", "Hugli": "Hoogli", "Koch Bihar": "Coochbehar",
        "Puruliya": "Purulia", "Kolkata": "Calcutta",
        "North Twenty Four Parganas": "24 Pargana North",
        "South Twenty Four Parganas": "24 Pargana South",
        "Paschim Medinipur": "Medinipur", "Purba Medinipur": "Medinipur",
    },
}
base = {(r.state, norm(r.fsi_2001_unit)): r.fsi_2001_unit
        for r in FSI.itertuples()}
aliases = {(state, norm(label)): target for state, entries in ALIASES.items()
           for label, target in entries.items()}

def match(state, label):
    state = "Odisha" if state == "Orissa" else state
    key = state, norm(label)
    if key in aliases:
        target = aliases[key]
        assert (state, norm(target)) in base, (state, label, target)
        return state, target, "explicit alias or historical parent"
    if key in base:
        return state, base[key], "direct normalized name"
    return state, "", "unmatched"

# Geometry. Shape count is 594 for all India; selected states have 292
# polygons and FSI has 289 units because three pairs are combined.
reader = shapefile.Reader(str(WORK / "geo2001" / "2001_Dist.shp"))
geometry_records = []
for i, rec in enumerate(reader.records()):
    if rec.ST_NM not in set(FSI.state) | {"Orissa"}:
        continue
    state, unit, status = match(rec.ST_NM, rec.DISTRICT)
    geometry_records.append({"shape_index": i, "shape_state": rec.ST_NM,
                             "shape_district": rec.DISTRICT, "state": state,
                             "fsi_2001_unit": unit, "match_status": status})
geo = pd.DataFrame(geometry_records)
assert len(geo) == 292, len(geo)
assert geo.fsi_2001_unit.ne("").all(), geo.loc[geo.fsi_2001_unit.eq("")]
assert set(map(tuple, geo[["state", "fsi_2001_unit"]].to_numpy())) == set(
    map(tuple, FSI[["state", "fsi_2001_unit"]].to_numpy()))
geo.to_csv(OUT / "geometry_to_fsi_2001_crosswalk.csv", index=False)

# Baseline 2001 population and demographics. They are on a mixed/later
# district geography in WB's 2001 indicator file, so aggregate exactly to
# FSI units; percentage indicators are population weighted.
wb = pd.read_csv(WORK / "worldbank_2001_ind_l2.csv", encoding="cp1252", low_memory=False)
wb = wb.loc[wb["Total/Rural/Urban Division"].eq("Total")].copy()
wb = wb.loc[wb["Level 1 name"].isin(FSI.state.unique())].copy()
assign = [match(s, d) for s, d in zip(wb["Level 1 name"], wb["Level 2 name"])]
wb[["state", "fsi_2001_unit", "match_status"]] = pd.DataFrame(assign, index=wb.index)
assert wb.fsi_2001_unit.ne("").all(), wb.loc[wb.fsi_2001_unit.eq(""), ["Level 1 name", "Level 2 name"]]
assert set(map(tuple, wb[["state", "fsi_2001_unit"]].to_numpy())) == set(
    map(tuple, FSI[["state", "fsi_2001_unit"]].to_numpy()))

cols = {
    "Population (thousands)": "population_thousands",
    "Area (sq. km.)": "wb_area_km2",
    "Scheduled Tribe (ST) population (percent)": "st_pct",
    "Scheduled Caste (SC) population (percent)": "sc_pct",
    "Literacy rate,7+ years,total(percent of population group)": "literacy_pct",
    "Working-age population, 7+ years, Total(percent)": "age7plus_pct",
}
for src, target in cols.items():
    wb[target] = pd.to_numeric(wb[src], errors="coerce")
wb[["Level 1 name", "Level 2 name", "state", "fsi_2001_unit", "match_status",
    *cols.values()]].to_csv(OUT / "worldbank_to_fsi_2001_crosswalk.csv", index=False)

def aggregate(g):
    total_pop = g.population_thousands.sum()
    out = {"population_thousands": total_pop, "wb_area_km2": g.wb_area_km2.sum(),
           "wb_input_units": len(g)}
    for col in ("st_pct", "sc_pct", "literacy_pct"):
        valid = g[col].notna() & g.population_thousands.notna()
        weights = g.loc[valid, "population_thousands"].copy()
        if col == "literacy_pct":
            valid &= g.age7plus_pct.notna()
            weights = g.loc[valid, "population_thousands"] * g.loc[valid, "age7plus_pct"] / 100
        out[col] = ((g.loc[valid, col] * weights).sum() / weights.sum()
                    if valid.any() else float("nan"))
    return pd.Series(out)

cov = wb.groupby(["state", "fsi_2001_unit"], sort=True).apply(
    aggregate, include_groups=False).reset_index()
cov = FSI[["state", "fsi_2001_unit", "area_km2"]].merge(
    cov, on=["state", "fsi_2001_unit"], validate="one_to_one")
cov["population_density_2001"] = cov.population_thousands * 1000 / cov.area_km2
cov["area_gap_pct"] = 100 * (cov.wb_area_km2 / cov.area_km2 - 1)
assert len(cov) == len(FSI) == 289
assert abs(cov.population_thousands.sum() - wb.population_thousands.sum()) < 1e-6
cov.to_csv(OUT / "baseline_2001_demographics_harmonized.csv", index=False)
print("Geometry polygons", len(geo), "FSI units", len(FSI), "WB rows", len(wb))
print("Missing baseline fields:\n", cov.isna().sum().to_string())
print("Population total (thousands):", cov.population_thousands.sum())
