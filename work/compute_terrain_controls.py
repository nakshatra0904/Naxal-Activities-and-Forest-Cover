"""Aggregate public-domain USGS GMTED2010 elevation to FSI 2001 units.

The primary terrain measure is the within-district standard deviation of
elevation, a district-scale relief proxy. Values are raster-cell-area weighted
using cosine(latitude). The source is the 30 arc-second mean-elevation grid.
"""
from pathlib import Path
import sys
import warnings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "work" / "pydeps"))
import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask
import shapefile

WORK, OUT = ROOT / "work", ROOT / "outputs"
cross = pd.read_csv(OUT / "geometry_to_fsi_2001_crosswalk.csv")
reader = shapefile.Reader(str(WORK / "geo2001" / "2001_Dist.shp"))
grid = WORK / "terrain" / "mn30_grd"
if not grid.exists():
    raise FileNotFoundError("Download/extract GMTED2010 via fetch_terrain_grid.py first")

records = []
with rasterio.open(grid) as dem:
    assert dem.crs.to_epsg() == 4326 and abs(dem.res[0] - 1 / 120) < 1e-6
    for row in cross.itertuples(index=False):
        polygon = reader.shape(int(row.shape_index)).__geo_interface__
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            cells, transform = mask(dem, [polygon], crop=True,
                                    filled=False, all_touched=False)
        elevations = cells[0]
        rows, cols = np.nonzero(~np.ma.getmaskarray(elevations))
        if len(rows) == 0:
            raise ValueError(f"No DEM pixels in polygon {row.shape_index}")
        z = np.asarray(elevations[rows, cols], dtype=np.float64)
        latitude = transform.f + (rows + 0.5) * transform.e
        w = np.cos(np.deg2rad(latitude))
        if not (np.isfinite(z).all() and np.all(w > 0)):
            raise ValueError(f"Invalid terrain pixels in polygon {row.shape_index}")
        records.append({"state": row.state, "fsi_2001_unit": row.fsi_2001_unit,
                        "shape_index": int(row.shape_index), "terrain_cells": len(z),
                        "w_sum": w.sum(), "w_z": np.dot(w, z),
                        "w_z2": np.dot(w, z*z),
                        "min_elevation_m": z.min(), "max_elevation_m": z.max()})

p = pd.DataFrame(records)
g = (p.groupby(["state", "fsi_2001_unit"], as_index=False)
     .agg(terrain_cells=("terrain_cells", "sum"),
          terrain_polygon_count=("shape_index", "size"),
          w_sum=("w_sum", "sum"), w_z=("w_z", "sum"),
          w_z2=("w_z2", "sum"),
          min_elevation_m=("min_elevation_m", "min"),
          max_elevation_m=("max_elevation_m", "max")))
g["terrain_mean_elevation_m"] = g.w_z / g.w_sum
g["terrain_relief_sd_m"] = np.sqrt(np.maximum(
    g.w_z2 / g.w_sum - g.terrain_mean_elevation_m ** 2, 0))
g["terrain_elevation_range_m"] = g.max_elevation_m - g.min_elevation_m
g["terrain_sampled_area_km2"] = (g.w_sum * (111.32 / 120) ** 2)
g = g.drop(columns=["w_sum", "w_z", "w_z2"])
assert len(p) == 292 and len(g) == 289
assert g.terrain_cells.min() > 5
assert g.terrain_relief_sd_m.notna().all()
g.to_csv(OUT / "terrain_2001_district_controls.csv", index=False)
print("Terrain units", len(g), "pixels", int(g.terrain_cells.sum()))
print(g[["terrain_mean_elevation_m", "terrain_relief_sd_m",
         "terrain_elevation_range_m", "terrain_cells"]].describe().to_string())
print(g.nlargest(8, "terrain_relief_sd_m")[["state", "fsi_2001_unit",
          "terrain_mean_elevation_m", "terrain_relief_sd_m"]].to_string(index=False))
