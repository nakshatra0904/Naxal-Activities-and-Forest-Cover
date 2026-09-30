"""Independent statsmodels replication and alternative descriptive models."""
from pathlib import Path
import sys
import warnings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "work" / "pydeps"))
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

OUT = ROOT / "outputs"
p = pd.read_csv(OUT / "forest_violence_2001_district_panel.csv")
c = pd.read_csv(OUT / "baseline_2001_demographics_harmonized.csv")
t = pd.read_csv(OUT / "terrain_2001_district_controls.csv")
df = p.merge(c.drop(columns="area_km2"), on=["state", "fsi_2001_unit"], validate="one_to_one")
df = df.merge(t, on=["state", "fsi_2001_unit"], validate="one_to_one")
assert len(df) == 289 and df.notna().all().all()
df["forest10"] = df.forest_pct / 10
df["forest10_sq"] = df.forest10 ** 2
df["st10"] = df.st_pct / 10
df["sc10"] = df.sc_pct / 10
df["literacy10"] = df.literacy_pct / 10
df["log_density"] = np.log(df.population_density_2001)
df["log_area"] = np.log(df.area_km2)
df["terrain_elev100"] = df.terrain_mean_elevation_m / 100
df["terrain_relief100"] = df.terrain_relief_sd_m / 100
df["any_event"] = df.events.gt(0).astype(int)
df["area_consistent"] = df.area_gap_pct.abs().le(10)
df["terrain_area_gap_pct"] = 100 * (df.terrain_sampled_area_km2 / df.area_km2 - 1)
df["all_areas_consistent"] = df.area_consistent & df.terrain_area_gap_pct.abs().le(10)
df.to_csv(OUT / "extended_district_analysis_panel.csv", index=False)

offset_area = lambda d: np.log(d.area_km2 * 21 / 1000)
offset_pop = lambda d: np.log(d.population_thousands * 1000 * 21 / 100000)

baseline = "events ~ forest10 + C(state)"
adjusted = "events ~ forest10 + log_density + st10 + sc10 + literacy10 + C(state)"
terrain = "events ~ forest10 + terrain_elev100 + terrain_relief100 + C(state)"
adjusted_terrain = adjusted.replace(" + C(state)",
    " + terrain_elev100 + terrain_relief100 + C(state)")
results = []

def collect(name, outcome, scale, fit, data, formula):
    beta = float(fit.params["forest10"])
    se = float(fit.bse["forest10"])
    ci = fit.conf_int().loc["forest10"].to_numpy(float)
    results.append({
        "model": name, "outcome": outcome, "scale": scale,
        "formula": formula, "n": len(data), "events_sum": int(data.events.sum()),
        "beta": beta, "se": se, "ratio": float(np.exp(beta)),
        "ci_low": float(np.exp(ci[0])), "ci_high": float(np.exp(ci[1])),
        "p_value": float(fit.pvalues["forest10"]),
        "aic": float(fit.aic),
        "converged": bool(getattr(fit, "converged", getattr(fit, "mle_retvals", {}).get("converged", True))),
        "alpha_nb2": float(fit.params.get("alpha", np.nan)),
    })

def poisson(name, data, formula, outcome="events", offset=None):
    fit = smf.glm(formula, data=data, family=sm.families.Poisson(),
                  offset=offset).fit(cov_type="HC3")
    collect(name, outcome, "incidence rate ratio", fit, data, formula)
    return fit

primary = poisson("Poisson: area offset, state FE", df, baseline, offset=offset_area(df))
old = pd.read_csv(OUT / "forest_violence_regression_results.csv")
old_beta = old.loc[old["sample"].eq("all harmonized units") & old.outcome.eq("events"), "beta"].iloc[0]
assert abs(primary.params["forest10"] - old_beta) < 1e-8, (primary.params["forest10"], old_beta)
poisson("Poisson: area + population density", df,
        "events ~ forest10 + log_density + C(state)", offset=offset_area(df))
adj = poisson("Poisson: full baseline controls", df, adjusted, offset=offset_area(df))
poisson("Poisson: area + terrain controls", df, terrain, offset=offset_area(df))
adj_terrain = poisson("Poisson: full controls + terrain", df,
                      adjusted_terrain, offset=offset_area(df))
coef_ci = adj_terrain.conf_int()
pd.DataFrame({
    "term": adj_terrain.params.index,
    "beta": adj_terrain.params.to_numpy(),
    "robust_se": adj_terrain.bse.to_numpy(),
    "rate_ratio": np.exp(adj_terrain.params.to_numpy()),
    "ci_low": np.exp(coef_ci.iloc[:, 0].to_numpy()),
    "ci_high": np.exp(coef_ci.iloc[:, 1].to_numpy()),
    "p_value": adj_terrain.pvalues.to_numpy(),
}).to_csv(OUT / "terrain_adjusted_coefficients.csv", index=False)
poisson("Poisson: full controls + terrain, area-consistent units",
        df.loc[df.area_consistent], adjusted_terrain,
        offset=offset_area(df.loc[df.area_consistent]))
poisson("Poisson: full controls + terrain, all areas consistent",
        df.loc[df.all_areas_consistent], adjusted_terrain,
        offset=offset_area(df.loc[df.all_areas_consistent]))
poisson("Poisson: full controls, area-consistent units", df.loc[df.area_consistent],
        adjusted, offset=offset_area(df.loc[df.area_consistent]))
top_key = df.sort_values("events", ascending=False).iloc[0][["state", "fsi_2001_unit"]].tolist()
without_top = df.loc[~(df.state.eq(top_key[0]) & df.fsi_2001_unit.eq(top_key[1]))]
poisson("Poisson: full controls, exclude top unit", without_top,
        adjusted, offset=offset_area(without_top))
poisson("Poisson: full controls + terrain, exclude top unit", without_top,
        adjusted_terrain, offset=offset_area(without_top))
for state in sorted(df.state.unique()):
    sample = df.loc[df.state.ne(state)]
    poisson(f"Poisson: full controls, exclude {state}", sample,
            adjusted, offset=offset_area(sample))
    poisson(f"Poisson: full controls + terrain, exclude {state}", sample,
            adjusted_terrain, offset=offset_area(sample))
poisson("Poisson: population offset", df, baseline, offset=offset_pop(df))
poisson("Poisson: deaths, full controls", df,
        adjusted.replace("events ~", "victim_deaths ~"), "victim_deaths",
        offset_area(df))
poisson("Poisson: deaths, full controls + terrain", df,
        adjusted_terrain.replace("events ~", "victim_deaths ~"), "victim_deaths",
        offset_area(df))

for name, formula in [
    ("NB2: area offset, state FE", baseline),
    ("NB2: full baseline controls", adjusted),
    ("NB2: full controls + terrain", adjusted_terrain),
]:
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        fit = smf.negativebinomial(formula, data=df, offset=offset_area(df)).fit(
            method="bfgs", maxiter=1000, disp=False, cov_type="HC0")
    collect(name, "events", "incidence rate ratio", fit, df, formula)
    print(name, "converged", fit.mle_retvals.get("converged"),
          "warnings", [str(x.message) for x in w])

for name, formula in [
    ("Logit: any event, state FE", "any_event ~ forest10 + log_area + C(state)"),
    ("Logit: any event, full controls",
     "any_event ~ forest10 + log_area + log_density + st10 + sc10 + literacy10 + C(state)"),
    ("Logit: any event, full controls + terrain",
     "any_event ~ forest10 + log_area + log_density + st10 + sc10 + literacy10 + terrain_elev100 + terrain_relief100 + C(state)"),
]:
    fit = smf.logit(formula, data=df).fit(method="bfgs", maxiter=1000,
                                            disp=False, cov_type="HC3")
    collect(name, "any_event", "odds ratio", fit, df, formula)

# An optional curvature check; report beta1/beta2 separately because no
# single constant IRR represents a quadratic forest association.
quad_formula = adjusted_terrain.replace("forest10 +", "forest10 + forest10_sq +")
quad = smf.glm(quad_formula, data=df, family=sm.families.Poisson(),
               offset=offset_area(df)).fit(cov_type="HC3")
pd.DataFrame([{
    "model": "Poisson quadratic: full controls + terrain", "n": len(df),
    "forest10_beta": float(quad.params["forest10"]),
    "forest10_sq_beta": float(quad.params["forest10_sq"]),
    "forest10_sq_p": float(quad.pvalues["forest10_sq"]),
    "aic_quadratic": float(quad.aic), "aic_linear": float(adj_terrain.aic),
}]).to_csv(OUT / "forest_nonlinearity_check.csv", index=False)

res = pd.DataFrame(results)
res.to_csv(OUT / "alternative_model_results.csv", index=False)

def desc(series):
    return {"n": int(series.count()), "mean": float(series.mean()),
            "sd": float(series.std()), "min": float(series.min()),
            "p25": float(series.quantile(.25)), "median": float(series.median()),
            "p75": float(series.quantile(.75)), "max": float(series.max())}

variables = {
    "forest cover (%)": "forest_pct", "dense forest (%)": None,
    "recorded events (21 years)": "events", "events with >=1 death": "fatal_events",
    "civilian + government-side deaths": "victim_deaths",
    "annual events per 1,000 km2": "events_per_1000km2_year",
    "area (km2)": "area_km2", "population (thousands)": "population_thousands",
    "population density (per km2)": "population_density_2001",
    "Scheduled Tribe share (%)": "st_pct", "Scheduled Caste share (%)": "sc_pct",
    "literacy (%)": "literacy_pct",
    "mean elevation (m)": "terrain_mean_elevation_m",
    "within-district elevation SD (m)": "terrain_relief_sd_m",
}
summary = []
for label, col in variables.items():
    series = df.dense_forest_km2 / df.area_km2 * 100 if col is None else df[col]
    summary.append({"variable": label, **desc(series)})
pd.DataFrame(summary).to_csv(OUT / "descriptive_statistics.csv", index=False)

states = df.groupby("state", sort=True).agg(
    units=("events", "size"), area_km2=("area_km2", "sum"),
    forest_km2=("forest_km2", "sum"), events=("events", "sum"),
    fatal_events=("fatal_events", "sum"), victim_deaths=("victim_deaths", "sum"),
    population_thousands=("population_thousands", "sum"),
).reset_index()
states["forest_pct"] = 100 * states.forest_km2 / states.area_km2
states["events_per_1000km2_year"] = states.events / states.area_km2 * 1000 / 21
states.to_csv(OUT / "state_descriptive_statistics.csv", index=False)

print(res[["model", "n", "ratio", "ci_low", "ci_high", "p_value", "alpha_nb2", "converged"]].to_string(index=False))
print("Area-consistent units", df.area_consistent.sum(), "events",
      df.loc[df.area_consistent, "events"].sum())
print("All-areas-consistent units", df.all_areas_consistent.sum(), "events",
      df.loc[df.all_areas_consistent, "events"].sum())
print("Forest-ST correlation", df[["forest_pct", "st_pct"]].corr().iloc[0, 1])
