"""Map district elevation and relief from public-domain USGS GMTED2010."""
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
from matplotlib.colors import Normalize, PowerNorm
from matplotlib.patches import Polygon
from matplotlib.cm import ScalarMappable
import numpy as np
import pandas as pd
import shapefile

OUT = ROOT / "outputs"
reader = shapefile.Reader(str(ROOT / "work" / "geo2001" / "2001_Dist.shp"))
cross = pd.read_csv(OUT / "geometry_to_fsi_2001_crosswalk.csv")
terrain = pd.read_csv(OUT / "terrain_2001_district_controls.csv")
cross = cross.merge(terrain, on=["state", "fsi_2001_unit"],
                    validate="many_to_one").set_index("shape_index")

def parts(shape):
    starts = list(shape.parts) + [len(shape.points)]
    return [np.asarray(shape.points[starts[i]:starts[i+1]])
            for i in range(len(starts)-1) if starts[i+1]-starts[i] >= 3]

background, selected, mean_values, relief_values = [], [], [], []
for i, shape in enumerate(reader.shapes()):
    polygons = [Polygon(part, closed=True) for part in parts(shape)]
    if i not in cross.index:
        background.extend(polygons)
    else:
        selected.extend(polygons)
        mean_values.extend([cross.loc[i, "terrain_mean_elevation_m"]] * len(polygons))
        relief_values.extend([cross.loc[i, "terrain_relief_sd_m"]] * len(polygons))

fig, axes = plt.subplots(1, 2, figsize=(15.6, 8.3), layout="constrained")
settings = [
    ("A  Mean elevation", mean_values, "terrain", Normalize(0, 950),
     "Mean elevation (m)"),
    ("B  Within-district elevation variation", relief_values, "YlOrBr",
     PowerNorm(gamma=.52, vmin=0, vmax=800), "Elevation SD within district (m)"),
]
for ax, (title, values, cmap, norm, bar_label) in zip(axes, settings):
    ax.add_collection(PatchCollection(background, facecolor="#e7ebef",
                                      edgecolor="#f8f9fa", linewidth=.16))
    ax.add_collection(PatchCollection(selected, cmap=cmap, norm=norm,
                                      array=np.asarray(values),
                                      edgecolor="#6e7379", linewidth=.24))
    ax.set_xlim(67.2, 98.0)
    ax.set_ylim(6.0, 37.8)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    ax.set_title(title, loc="left", fontsize=15, fontweight="bold", pad=11)
    cb = fig.colorbar(ScalarMappable(norm=norm, cmap=cmap), ax=ax,
                      fraction=.035, pad=.01, shrink=.72)
    cb.set_label(bar_label)
fig.suptitle("Terrain in the nine-state study region", fontsize=20,
             fontweight="bold", y=.995)
fig.text(.5, .025,
         "Source: USGS GMTED2010 mean-elevation grid (30 arc-seconds); district summaries on DataMeet Census-2001 polygons. "
         "Pale gray areas are outside the analysis. Relief is the area-weighted standard deviation of elevation.",
         ha="center", fontsize=8.5, color="#475467")
fig.savefig(OUT / "india_terrain_maps.png", dpi=250, bbox_inches="tight")
fig.savefig(OUT / "india_terrain_maps.pdf", bbox_inches="tight")
plt.close(fig)
