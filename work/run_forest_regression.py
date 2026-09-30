"""Descriptive 2001 forest-cover / 2005-2025 Maoist event regression.

Reproduce with the bundled Python runtime after extract_fsi_2001.py and
analyze_ged.py. All analytic choices and exclusions are written to outputs/.
"""
from pathlib import Path
import math
import re
from statistics import NormalDist

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
FSI = pd.read_csv(OUT / "fsi_2001_district_forest.csv")
EV = pd.read_csv(OUT / "maoist_ged_event_extract_2005_2025.csv")

def norm(s):
    return re.sub(r"[^a-z0-9]+", "", str(s).lower())

# Explicit label corrections where geography is unchanged. These are spelling,
# transliteration and district naming changes, not statistical fuzzy matches.
ALIASES = {
    "Andhra Pradesh": {
        "Visakhapatnam": "Vishakapatnam", "Prakasam": "Prakasham",
        "Mahbubnagar": "Mahboobnagar", "East Godavari": "East Godawari",
        "West Godavari": "West Godawari", "Hyderabad": "Hyderabad + Rangareddy",
        "Komaram Bheem": "Adilabad", "Kumarambhem": "Adilabad",
        "Bhadradri Kothagudem": "Khammam",
    },
    "Bihar": {
        "East Champaran": "Purbi Champaran",
        "West Champaran (Bettiah)": "Paschimi Champaran",
        "Kaimur (Bhabhua)": "Bhabua", "Rohtas (Sasaram)": "Rohtas",
    },
    "Chhattisgarh": {
        "Dantewada": "Dantewara", "Bijapur": "Dantewara",
        "Sukma": "Dantewara", "Narayanpur": "Bastar",
        "Kondagaon": "Bastar", "Gariaband": "Raipur + Dhamtari",
        "Dhamtari": "Raipur + Dhamtari", "Raipur": "Raipur + Dhamtari",
        "Mahasamund": "Mahasamud", "Kabirdham": "Kawardha",
        "Balrampur": "Surguja",
        "Mohla-Manpur-Ambagarh Chowki": "Rajnandgaon",
    },
    "Jharkhand": {
        "West Singhbhum": "Paschimi Singhbhum",
        "East Singhbhum": "Purbi Singhbhum",
        "Latehar": "Palamu", "Khunti": "Ranchi", "Simdega": "Gumla",
        "Seraikela-Kharsawan": "Paschimi Singhbhum",
        "Koderma": "Kodarma", "Pakur": "Pakaur", "Jamtara": "Dumka",
        "Ramgarh": "Hazaribagh",
    },
    "Maharashtra": {"Gondia": "Gondiya"},
    "Odisha": {
        "Kandhamal": "Khandamal", "Nuapada": "Nawapara",
        "Sundergarh": "Sundargarh", "Nabarangpur": "Nawrangpur",
        "Bargarh": "Baragarh", "Khordha": "Khurda",
        "Gajapati": "Gajpati",
    },
    "West Bengal": {
        "West Midnapore": "Medinipur", "East Midnapore": "Medinipur",
        "South 24 Parganas": "24 Pargana South",
        "Bardhaman": "Bardhman",
    },
}

SPLIT_LABELS = {
    ("Andhra Pradesh", "Komaram Bheem"),
    ("Andhra Pradesh", "Kumarambhem"),
    ("Andhra Pradesh", "Bhadradri Kothagudem"),
    ("Chhattisgarh", "Bijapur"), ("Chhattisgarh", "Sukma"),
    ("Chhattisgarh", "Narayanpur"), ("Chhattisgarh", "Kondagaon"),
    ("Chhattisgarh", "Gariaband"), ("Chhattisgarh", "Balrampur"),
    ("Chhattisgarh", "Mohla-Manpur-Ambagarh Chowki"),
    ("Jharkhand", "Latehar"), ("Jharkhand", "Khunti"),
    ("Jharkhand", "Simdega"), ("Jharkhand", "Seraikela-Kharsawan"),
    ("Jharkhand", "Jamtara"), ("Jharkhand", "Ramgarh"),
    ("West Bengal", "West Midnapore"), ("West Bengal", "East Midnapore"),
}

def old_state(s):
    return "Andhra Pradesh" if s == "Telangana" else s

lookup = {(r.state, norm(r.fsi_2001_unit)): r.fsi_2001_unit
          for r in FSI.itertuples()}
manual = {(s, norm(label)): target for s, d in ALIASES.items()
          for label, target in d.items()}
split_keys = {(a, norm(b)) for a, b in SPLIT_LABELS}
fsi_states = set(FSI.state)

def match(row):
    s = old_state(row.state)
    label = row.district_label
    if label == "Unspecified" or s not in fsi_states:
        return pd.Series([s, "", "excluded: no district/state"])
    key = (s, norm(label))
    # Known erroneous AP "Saran" labels are not assigned to Bihar by guess.
    if row.state == "Andhra Pradesh" and label == "Saran":
        return pd.Series([s, "", "excluded: inconsistent state/district"])
    if key in manual:
        status = "historical split" if key in split_keys else "name alias"
        return pd.Series([s, manual[key], status])
    if key in lookup:
        return pd.Series([s, lookup[key], "direct label"])
    return pd.Series([s, "", "excluded: unresolved boundary/label"])

EV[["fsi_state", "fsi_2001_unit", "match_status"]] = EV.apply(match, axis=1)
EV["victim_deaths"] = EV.deaths_civilians + EV.government_side_deaths
EV["fatal_events"] = EV.best.gt(0).astype(int)
matched = EV.fsi_2001_unit.ne("")

audit = (EV.groupby(["state", "district_label", "fsi_state", "fsi_2001_unit", "match_status"],
                    dropna=False)
         .agg(events=("id", "size"), victim_deaths=("victim_deaths", "sum"))
         .reset_index().sort_values(["events", "victim_deaths"], ascending=False))
audit.to_csv(OUT / "district_2001_crosswalk_audit.csv", index=False)

counts = (EV.loc[matched].groupby(["fsi_state", "fsi_2001_unit"])
          .agg(events=("id", "size"), fatal_events=("fatal_events", "sum"),
               victim_deaths=("victim_deaths", "sum"),
               civilian_deaths=("deaths_civilians", "sum"))
          .reset_index().rename(columns={"fsi_state": "state"}))
panel = FSI.merge(counts, on=["state", "fsi_2001_unit"], how="left", validate="one_to_one")
for col in ["events", "fatal_events", "victim_deaths", "civilian_deaths"]:
    panel[col] = panel[col].fillna(0).astype(int)
panel["events_per_1000km2_year"] = panel.events / panel.area_km2 * 1000 / 21
panel["victim_deaths_per_1000km2_year"] = panel.victim_deaths / panel.area_km2 * 1000 / 21
panel.to_csv(OUT / "forest_violence_2001_district_panel.csv", index=False)

def model(data, outcome="events"):
    """Poisson pseudo-ML with state fixed effects and log area-year offset.

    Sandwich HC0 covariance treats district as the independent observation.
    """
    states = sorted(data.state.unique())
    x = np.column_stack([
        np.ones(len(data)), data.forest_pct.to_numpy(float) / 10,
        *[(data.state == state).to_numpy(float) for state in states[1:]],
    ])
    y = data[outcome].to_numpy(float)
    offset = np.log(data.area_km2.to_numpy(float) * 21 / 1000)
    coef = np.zeros(x.shape[1])
    for _ in range(200):
        eta = np.clip(x @ coef + offset, -30, 30)
        mu = np.exp(eta)
        h = x.T @ (x * mu[:, None])
        step = np.linalg.lstsq(h, x.T @ (y - mu), rcond=None)[0]
        # Damping for severe overdispersion / large-count districts.
        scale = 1.0
        old = float(np.sum(y * eta - mu))
        while scale > 1e-7:
            candidate = coef + scale * step
            eta2 = np.clip(x @ candidate + offset, -30, 30)
            if float(np.sum(y * eta2 - np.exp(eta2))) >= old - 1e-8:
                break
            scale *= 0.5
        coef = coef + scale * step
        if np.max(abs(scale * step)) < 1e-9:
            break
    eta = np.clip(x @ coef + offset, -30, 30)
    mu = np.exp(eta)
    bread = np.linalg.pinv(x.T @ (x * mu[:, None]))
    score = x * (y - mu)[:, None]
    cov = bread @ (score.T @ score) @ bread
    se = math.sqrt(max(cov[1, 1], 0))
    residual_df = len(y) - x.shape[1]
    pearson_dispersion = float(np.sum((y - mu)**2 / mu) / residual_df)
    return {"beta": float(coef[1]), "irr": float(np.exp(coef[1])),
            "se_hc0": se, "ci95_low": float(np.exp(coef[1] - 1.96 * se)),
            "ci95_high": float(np.exp(coef[1] + 1.96 * se)),
            "p_normal_hc0": float(2 * (1 - NormalDist().cdf(abs(coef[1] / se)))),
            "dispersion": pearson_dispersion, "n": len(data),
            "sum_outcome": int(y.sum()), "iterations": _ + 1}

results = []
for outcome in ("events", "fatal_events", "victim_deaths"):
    full = model(panel, outcome)
    results.append({"sample": "all harmonized units", "outcome": outcome, **full})
    # Robustness: run only on historical units whose 2005-2025 events need no
    # split-district crosswalk, and on a sample excluding the top event unit.
    split_units = set(map(tuple, EV.loc[
        matched & EV.match_status.eq("historical split"),
        ["fsi_state", "fsi_2001_unit"]].drop_duplicates().to_numpy()))
    no_split = panel.loc[~panel.apply(lambda r: (r.state, r.fsi_2001_unit) in split_units, axis=1)]
    results.append({"sample": "exclude split-mapped units", "outcome": outcome,
                    **model(no_split, outcome)})
    top = panel.sort_values(outcome, ascending=False).iloc[0]
    drop_top = panel.loc[~((panel.state == top.state) &
                           (panel.fsi_2001_unit == top.fsi_2001_unit))]
    results.append({"sample": f"exclude top unit ({top.state}: {top.fsi_2001_unit})",
                    "outcome": outcome, **model(drop_top, outcome)})
    for state in sorted(panel.state.unique()):
        results.append({"sample": f"exclude state ({state})", "outcome": outcome,
                        **model(panel.loc[panel.state.ne(state)], outcome)})

result = pd.DataFrame(results)
result.to_csv(OUT / "forest_violence_regression_results.csv", index=False)
print(result[["sample", "outcome", "n", "sum_outcome", "irr",
              "ci95_low", "ci95_high", "p_normal_hc0", "dispersion"]].to_string(index=False))
print("Events matched", matched.sum(), "of", len(EV),
      "victim deaths matched", EV.loc[matched, "victim_deaths"].sum(),
      "of", EV.victim_deaths.sum())
print("Unmatched:")
print(audit.loc[audit.fsi_2001_unit.eq(""), ["state", "district_label", "events", "match_status"]].head(25).to_string(index=False))

# Quartile rates are descriptive pooled rates (area-year weighted), rather
# than a substitute for the within-state regression coefficient.
panel["forest_quartile"] = pd.qcut(panel.forest_pct, 4, labels=["Q1", "Q2", "Q3", "Q4"])
quartiles = (panel.groupby("forest_quartile", observed=True)
             .agg(n=("events", "size"), forest_min=("forest_pct", "min"),
                  forest_max=("forest_pct", "max"), area_km2=("area_km2", "sum"),
                  events=("events", "sum"), victim_deaths=("victim_deaths", "sum"))
             .reset_index())
quartiles["event_rate_per_1000km2_year"] = quartiles.events / quartiles.area_km2 * 1000 / 21
quartiles.to_csv(OUT / "forest_cover_quartile_rates.csv", index=False)
print(quartiles.to_string(index=False))

# Resample whole districts within each state; this captures sensitivity to the
# skewed count distribution. The permutation check shuffles forest values
# inside states while keeping areas and event counts fixed. Neither addresses
# spatial dependence or confounding, so both are exploratory checks.
rng = np.random.default_rng(20260930)
boot_irr = []
perm_beta = []
for b in range(500):
    boot = pd.concat([
        group.iloc[rng.integers(0, len(group), len(group))]
        for _, group in panel.groupby("state", sort=True)
    ], ignore_index=True)
    boot_irr.append(model(boot)["irr"])
    perm = panel.copy()
    perm["forest_pct"] = (perm.groupby("state", sort=True)["forest_pct"]
                          .transform(lambda x: rng.permutation(x.to_numpy())))
    perm_beta.append(model(perm)["beta"])
primary_beta = float(result.loc[
    result["sample"].eq("all harmonized units") & result.outcome.eq("events"),
    "beta"].iloc[0])
uncertainty = pd.DataFrame([{
    "outcome": "events", "bootstrap_repetitions": 500,
    "bootstrap_irr_p2_5": float(np.quantile(boot_irr, .025)),
    "bootstrap_irr_p97_5": float(np.quantile(boot_irr, .975)),
    "permutation_repetitions": 500,
    "permutation_two_sided_p": (1 + sum(abs(b) >= abs(primary_beta) for b in perm_beta)) / 501,
    "random_seed": 20260930,
}])
uncertainty.to_csv(OUT / "forest_violence_uncertainty_checks.csv", index=False)
print(uncertainty.to_string(index=False))
