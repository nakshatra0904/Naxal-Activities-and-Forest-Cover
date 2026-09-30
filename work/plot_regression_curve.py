"""Plot observed event rates and two explicit Poisson fitted curves."""
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "work" / "mplconfig"))
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "work" / "pydeps"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import patsy
import statsmodels.api as sm
import statsmodels.formula.api as smf

OUT = ROOT / "outputs"
df = pd.read_csv(OUT / "extended_district_analysis_panel.csv")
offset = np.log(df.area_km2 * 21 / 1000)
specs = [
    ("State + area", "events ~ forest10 + C(state)", "#256186"),
    ("+ 2001 demographics", "events ~ forest10 + log_density + st10 + sc10 + literacy10 + C(state)", "#a35b25"),
    ("+ demographics + terrain", "events ~ forest10 + log_density + st10 + sc10 + literacy10 + terrain_elev100 + terrain_relief100 + C(state)", "#31735b"),
]

grid = np.linspace(0, 70, 141)
predictions = []
fig, ax = plt.subplots(figsize=(9.0, 5.9), layout="constrained")
ax.scatter(df.forest_pct, df.events_per_1000km2_year, s=15,
           facecolors="#64717f", edgecolors="none", alpha=.30,
           label="Observed 2001 district unit")
for label, formula, color in specs:
    fit = smf.glm(formula, data=df, family=sm.families.Poisson(),
                  offset=offset).fit(cov_type="HC3")
    for forest in grid:
        new = df.copy()
        new["forest10"] = forest / 10
        design = patsy.dmatrix(formula.split("~", 1)[1], new,
                               return_type="dataframe")
        design = design.reindex(columns=fit.params.index)
        if design.isna().any().any():
            raise ValueError("Prediction design matrix differs from fitted model")
        x = design.to_numpy()
        rates = np.exp(x @ fit.params.to_numpy())
        mean = rates.mean()
        grad = np.mean(rates[:, None] * x, axis=0)
        se_log = np.sqrt(max(grad @ fit.cov_params().to_numpy() @ grad, 0)) / mean
        predictions.append({"model": label, "forest_pct": forest,
                            "predicted_events_per_1000km2_year": mean,
                            "ci_low": mean * np.exp(-1.96 * se_log),
                            "ci_high": mean * np.exp(1.96 * se_log)})
    part = pd.DataFrame([r for r in predictions if r["model"] == label])
    ax.plot(part.forest_pct, part.predicted_events_per_1000km2_year,
            lw=2.5, color=color, label=f"Poisson fitted: {label}")
    ax.fill_between(part.forest_pct, part.ci_low, part.ci_high,
                    color=color, alpha=.12, linewidth=0)

ax.set_xlim(0, 70)
ax.set_ylim(0, 3.8)
ax.set_yscale("symlog", linthresh=.012, linscale=1)
ax.set_yticks([0, .01, .03, .1, .3, 1, 3])
ax.set_yticklabels(["0", "0.01", "0.03", "0.1", "0.3", "1", "3"])
ax.set_xlabel("FSI 2001 forest cover (% of historical district area)")
ax.set_ylabel("UCDP recorded events / 1,000 km² / year, 2005–2025\n(symmetric log scale)")
ax.set_title("Forest cover and recorded CPI-Maoist events: observed rates and fitted curves",
             loc="left", fontsize=14)
ax.grid(axis="y", color="#e6eaee", linewidth=.7)
ax.spines[["top", "right"]].set_visible(False)
ax.legend(frameon=False, loc="upper left", fontsize=9)
ax.text(0, -.22,
        "Lines average model predictions across the observed state/covariate distribution at each forest value; bands are 95% coefficient intervals. "
        "They are associations, not causal effects.",
        transform=ax.transAxes, fontsize=8.2, color="#55616e", wrap=True)
fig.savefig(OUT / "forest_regression_fitted_curves.png", dpi=220, bbox_inches="tight")
fig.savefig(OUT / "forest_regression_fitted_curves.pdf", bbox_inches="tight")
plt.close(fig)
pd.DataFrame(predictions).to_csv(OUT / "forest_regression_curve_data.csv", index=False)
print("Saved fitted curves. Predicted rates at 10% and 40% forest:")
pred = pd.DataFrame(predictions)
print(pred.loc[pred.forest_pct.isin([10, 40]), ["model", "forest_pct", "predicted_events_per_1000km2_year"]].to_string(index=False))
