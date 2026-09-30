"""Two-panel India district map on DataMeet's Census-2001 geometry."""
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
from matplotlib.collections import PatchCollection
from matplotlib.colors import LogNorm, Normalize
from matplotlib.patches import Polygon, Patch
from matplotlib.cm import ScalarMappable
import numpy as np
import pandas as pd
import shapefile

OUT = ROOT / "outputs"
reader = shapefile.Reader(str(ROOT / "work" / "geo2001" / "2001_Dist.shp"))
cross = pd.read_csv(OUT / "geometry_to_fsi_2001_crosswalk.csv")
panel = pd.read_csv(OUT / "extended_district_analysis_panel.csv")
cross = cross.merge(panel[["state", "fsi_2001_unit", "forest_pct",
                           "events_per_1000km2_year", "area_gap_pct"]],
                    on=["state", "fsi_2001_unit"], validate="many_to_one")
by_index = cross.set_index("shape_index")

def parts(shape):
    starts = list(shape.parts) + [len(shape.points)]
    return [np.asarray(shape.points[starts[i]:starts[i+1]])
            for i in range(len(starts)-1) if starts[i+1] - starts[i] >= 3]

fig, axes = plt.subplots(1, 2, figsize=(15.6, 8.3), layout="constrained")
background = []
select = {"forest": [], "events": []}
color_vals = {"forest": [], "events": []}
zeros = []
for i, shape in enumerate(reader.shapes()):
    polygons = [Polygon(part, closed=True) for part in parts(shape)]
    if i not in by_index.index:
        background.extend(polygons)
        continue
    row = by_index.loc[i]
    select["forest"].extend(polygons)
    color_vals["forest"].extend([row.forest_pct] * len(polygons))
    rate = float(row.events_per_1000km2_year)
    if rate > 0:
        select["events"].extend(polygons)
        color_vals["events"].extend([rate] * len(polygons))
    else:
        zeros.extend(polygons)

forest_norm = Normalize(vmin=0, vmax=70)
event_norm = LogNorm(vmin=.004, vmax=3.0)
for ax, mode in zip(axes, ["forest", "events"]):
    ax.add_collection(PatchCollection(background, facecolor="#e7ebef",
                                      edgecolor="#f8f9fa", linewidth=.16, zorder=1))
    if mode == "events":
        ax.add_collection(PatchCollection(zeros, facecolor="#f4f2ee",
                                          edgecolor="#c9cbd0", linewidth=.20, zorder=2))
    ax.add_collection(PatchCollection(select[mode],
                                      cmap="YlGn" if mode == "forest" else "YlOrRd",
                                      norm=forest_norm if mode == "forest" else event_norm,
                                      array=np.asarray(color_vals[mode]),
                                      edgecolor="#6e7379", linewidth=.24, zorder=3))
    ax.set_xlim(67.2, 98.0)
    ax.set_ylim(6.0, 37.8)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    ax.set_title("A  Forest cover in 2001 (%)" if mode == "forest"
                 else "B  CPI-Maoist recorded events, 2005–2025", loc="left",
                 fontsize=15, fontweight="bold", pad=11)

forest_cbar = fig.colorbar(ScalarMappable(norm=forest_norm, cmap="YlGn"),
                           ax=axes[0], fraction=.035, pad=.01, shrink=.72)
forest_cbar.set_label("Forest cover (% of district area)")
forest_cbar.set_ticks([0, 10, 20, 30, 40, 50, 60, 70])
event_cbar = fig.colorbar(ScalarMappable(norm=event_norm, cmap="YlOrRd"),
                          ax=axes[1], fraction=.035, pad=.01, shrink=.72)
event_cbar.set_label("Recorded events / 1,000 km² / year (log scale)")
event_cbar.set_ticks([.005, .01, .05, .1, .5, 1, 3])
event_cbar.set_ticklabels(["0.005", "0.01", "0.05", "0.1", "0.5", "1", "3"])
axes[1].legend(handles=[Patch(facecolor="#f4f2ee", edgecolor="#c9cbd0",
                              label="No matched recorded event"),
                        Patch(facecolor="#e7ebef", edgecolor="#e7ebef",
                              label="Outside nine-state analysis")],
               loc="lower left", bbox_to_anchor=(.1, .02), frameon=False, fontsize=8)
fig.suptitle("Forest cover and recorded Maoist activity across India",
             fontsize=20, fontweight="bold", y=.995)
fig.text(.5, .025,
         "Sources: Forest Survey of India 2001; UCDP GED 26.1; DataMeet Census-2001 district polygons. "
         "FSI/census district areas differ >10% for 23 of 289 units; boundaries are approximate for those units.",
         ha="center", fontsize=8.5, color="#475467")
fig.savefig(OUT / "india_forest_activity_maps.png", dpi=250, bbox_inches="tight")
fig.savefig(OUT / "india_forest_activity_maps.pdf", bbox_inches="tight")
plt.close(fig)
print("Mapped", len(cross), "polygons onto", len(panel), "FSI units;")
print("Area discrepancies >10%:", int(panel.area_gap_pct.abs().gt(10).sum()))
