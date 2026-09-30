"""Reproducibility gate for source snapshots, joins, estimates and figures."""
from pathlib import Path
import hashlib
import math
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
WORK, OUT = ROOT / "work", ROOT / "outputs"
EXPECTED_HASHES = {
    "ucdp_ged261_india.csv": "1e3ca049cda22fa11e4c233c59d1c95dbe5a43a0b9001e72af80807629adce06",
    "ucdp_actor_v26_1.csv": "766a1ab8a0ed5831dbfe99e0e4ada21dd6114deb8dcaa743290bb988d43f9a92",
    "worldbank_2001_ind_l2.csv": "83cea287ff065b43b6dfc509c80bf92e4a512ac6843dece1cde36166c8d50e86",
    "geo2001/2001_Dist.shp": "2de4a9e21553c193ff2936f7a8412402e74dcc5d45d8100cd556b356d8aee623",
}
for name, expected in EXPECTED_HASHES.items():
    actual = hashlib.sha256((WORK / name).read_bytes()).hexdigest()
    assert actual == expected, f"Source snapshot changed: {name}"

events = pd.read_csv(OUT / "maoist_ged_event_extract_2005_2025.csv")
panel = pd.read_csv(OUT / "extended_district_analysis_panel.csv")
models = pd.read_csv(OUT / "alternative_model_results.csv").set_index("model")
curves = pd.read_csv(OUT / "forest_regression_curve_data.csv")
terrain = pd.read_csv(OUT / "terrain_2001_district_controls.csv")
geo = pd.read_csv(OUT / "geometry_to_fsi_2001_crosswalk.csv")
wb = pd.read_csv(OUT / "worldbank_to_fsi_2001_crosswalk.csv")

assert len(events) == 3913 and events.id.is_unique
assert events.year.between(2005, 2025).all()
assert int(events.best.eq(0).sum()) == 185
assert len(panel) == 289 and not panel[["state", "fsi_2001_unit"]].duplicated().any()
assert panel.events.sum() == 3763 and int(panel.events.eq(0).sum()) == 177
assert len(geo) == 292 and len(wb) == 308
assert len(terrain) == 289 and int(terrain.terrain_cells.sum()) == 2120567
assert terrain.terrain_relief_sd_m.between(0, 1000).all()
assert panel.terrain_relief_sd_m.notna().all()
assert geo.fsi_2001_unit.notna().all() and wb.fsi_2001_unit.notna().all()
assert int(panel.area_gap_pct.abs().gt(10).sum()) == 23
assert int(panel.terrain_area_gap_pct.abs().gt(10).sum()) == 23
assert int(panel.all_areas_consistent.sum()) == 256

simple = models.loc["Poisson: area offset, state FE"]
full = models.loc["Poisson: full baseline controls"]
full_terrain = models.loc["Poisson: full controls + terrain"]
all_areas = models.loc["Poisson: full controls + terrain, all areas consistent"]
assert math.isclose(simple.ratio, 1.7947402714038498, rel_tol=1e-9)
assert math.isclose(full.ratio, 1.305907745547461, rel_tol=1e-9)
assert math.isclose(full_terrain.ratio, 1.3665031312924631, rel_tol=1e-9)
assert all_areas.n == 256 and math.isclose(all_areas.ratio, 1.307420, rel_tol=1e-5)
assert simple.ci_low < simple.ratio < simple.ci_high
assert full.ci_low < full.ratio < full.ci_high
assert full_terrain.ci_low < full_terrain.ratio < full_terrain.ci_high
for label, fit in [("State + area", simple), ("+ 2001 demographics", full),
                   ("+ demographics + terrain", full_terrain)]:
    c = curves.loc[curves.model.eq(label)].set_index("forest_pct")
    observed_ratio = c.loc[40., "predicted_events_per_1000km2_year"] / c.loc[10., "predicted_events_per_1000km2_year"]
    assert math.isclose(observed_ratio, fit.ratio ** 3, rel_tol=1e-9)
    assert (c.ci_low < c.predicted_events_per_1000km2_year).all()
    assert (c.predicted_events_per_1000km2_year < c.ci_high).all()

for figure in ["forest_regression_fitted_curves", "india_forest_activity_maps",
               "india_terrain_maps", "model_comparison",
               "annual_activity_2005_2025", "pca_clusters"]:
    assert (OUT / f"{figure}.png").stat().st_size > 10_000
    assert (OUT / f"{figure}.pdf").stat().st_size > 10_000

print("Verified four committed source hashes, 3,913 selected events, 289 districts,"
      " 2.12 million terrain cells, 3,763 matched events, join coverage,"
      " model estimates, fitted-curve ratios and six figure pairs.")
