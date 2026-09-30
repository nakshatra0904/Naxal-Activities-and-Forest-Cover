"""Publication-style descriptive and model-comparison figures."""
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

OUT = ROOT / "outputs"
models = pd.read_csv(OUT / "alternative_model_results.csv")
selected = [
    ("Poisson, state + area", "Poisson: area offset, state FE"),
    ("Poisson, + population density", "Poisson: area + population density"),
    ("Poisson, + ST/SC + literacy", "Poisson: full baseline controls"),
    ("Poisson, + elevation + relief", "Poisson: full controls + terrain"),
    ("Poisson, terrain; all areas agree", "Poisson: full controls + terrain, all areas consistent"),
    ("Poisson, terrain; exclude Jharkhand", "Poisson: full controls + terrain, exclude Jharkhand"),
    ("Negative binomial, terrain controls", "NB2: full controls + terrain"),
]
fig, ax = plt.subplots(figsize=(9.4, 6.0), layout="constrained")
for i, (label, key) in enumerate(selected):
    r = models.loc[models.model.eq(key)].iloc[0]
    y = len(selected) - i
    color = "#a35b25" if "Negative" in label else ("#31735b" if "terrain" in label or "relief" in label else "#265d83")
    ax.errorbar(r.ratio, y,
                xerr=np.array([[r.ratio-r.ci_low], [r.ci_high-r.ratio]]),
                fmt="o", color=color, ecolor=color, capsize=3, markersize=6,
                elinewidth=1.8)
    ax.text(3.28, y, f"{r.ratio:.2f}  [{r.ci_low:.2f}, {r.ci_high:.2f}]",
            va="center", ha="left", fontsize=9)
ax.axvline(1, color="#777e88", ls="--", lw=1)
ax.set_xlim(.75, 4.8)
ax.set_yticks(range(1, len(selected)+1), [x[0] for x in selected[::-1]])
ax.set_xlabel("Event-rate ratio per +10 percentage points 2001 forest cover")
ax.set_title("Forest coefficient across count-model specifications", loc="left", fontsize=15)
ax.text(0, -.21, "Intervals use district-robust standard errors. Models vary in assumptions and conditioning set; none identifies a causal forest effect.",
        transform=ax.transAxes, fontsize=8.5, color="#55616e")
ax.spines[["top", "right", "left"]].set_visible(False)
ax.tick_params(axis="y", length=0)
fig.savefig(OUT / "model_comparison.png", dpi=220, bbox_inches="tight")
fig.savefig(OUT / "model_comparison.pdf", bbox_inches="tight")
plt.close(fig)

events = pd.read_csv(OUT / "maoist_ged_event_extract_2005_2025.csv")
events["fatal_event"] = events.best.gt(0).astype(int)
events["victim_deaths"] = events.deaths_civilians + events.government_side_deaths
annual = (events.groupby("year")
          .agg(recorded_events=("id", "size"), fatal_events=("fatal_event", "sum"),
               victim_deaths=("victim_deaths", "sum"),
               maoist_side_deaths=("maoist_side_deaths", "sum"))
          .reset_index())
annual.to_csv(OUT / "annual_activity_descriptives.csv", index=False)
fig, axes = plt.subplots(2, 1, figsize=(8.6, 6.1), sharex=True, layout="constrained")
axes[0].plot(annual.year, annual.recorded_events, color="#265d83", lw=2.2,
             marker="o", ms=3.5, label="Recorded events")
axes[0].plot(annual.year, annual.fatal_events, color="#638a9b", lw=1.5,
             label="Events with ≥1 best-estimate death")
axes[0].set_ylabel("Events per year")
axes[0].legend(frameon=False, loc="upper right", fontsize=8.5)
axes[1].plot(annual.year, annual.victim_deaths, color="#a35b25", lw=2.2,
             marker="o", ms=3.5, label="Civilian + government-side deaths")
axes[1].plot(annual.year, annual.maoist_side_deaths, color="#7f7b76", lw=1.5,
             label="CPI-Maoist-side deaths")
axes[1].set_ylabel("Best-estimate deaths per year")
axes[1].set_xlabel("Calendar year")
axes[1].legend(frameon=False, loc="upper right", fontsize=8.5)
for ax in axes:
    ax.grid(axis="y", color="#e8ebef", lw=.8)
    ax.spines[["top", "right"]].set_visible(False)
axes[1].set_xticks([2005, 2010, 2015, 2020, 2025])
fig.suptitle("CPI-Maoist events and deaths recorded by UCDP, 2005–2025",
             fontsize=15, fontweight="bold")
fig.savefig(OUT / "annual_activity_2005_2025.png", dpi=220, bbox_inches="tight")
fig.savefig(OUT / "annual_activity_2005_2025.pdf", bbox_inches="tight")
plt.close(fig)
