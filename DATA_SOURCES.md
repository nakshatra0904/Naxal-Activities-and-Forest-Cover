# Data provenance and reuse

Source snapshots were acquired for this analysis on 30 September 2026. The SHA-256 values below identify the exact files in `work/`; `work/verify_results.py` checks them. The editable report and derived CSV files document the transformations.

## Forest Survey of India

- Source: Forest Survey of India, *State of Forest Report 2001*, [official PDF](https://fsi.nic.in/documents/sfr_2001_hindi.pdf).
- Use: nine state district tables of geographic area, dense forest and open forest; dense plus open is the forest-cover numerator.
- PDF SHA-256: `4fe576566d1561f37b420a38e9229678ccb183c43b5be29aaae580ce2b6b00f1`.
- The source PDF is not included in this repository. `work/fetch_fsi_report.py` downloads and verifies it; `work/extract_fsi_2001.py` extracts and validates the tables. The derived `outputs/fsi_2001_district_forest.csv` is included.
- Two published combined district rows remain combined. Nine state area and forest totals were checked against their published totals.

## Uppsala Conflict Data Program

- Source: [UCDP download centre](https://ucdp.uu.se/downloads/), GED global 26.1 and Actor Dataset 26.1. UCDP makes these datasets available under [CC BY 4.0](https://ucdp.uu.se/downloads/).
- Snapshot files: `work/ucdp_ged261_india.csv` (only India records from the global GED CSV) and `work/ucdp_actor_v26_1.csv`.
- India GED SHA-256: `1e3ca049cda22fa11e4c233c59d1c95dbe5a43a0b9001e72af80807629adce06`.
- Actor CSV SHA-256: `766a1ab8a0ed5831dbfe99e0e4ada21dd6114deb8dcaa743290bb988d43f9a92`.
- Selection: actor ID 195, Communist Party of India-Maoist, on either side; event years 2005–2025. The subset contains 3,913 records. The source does not cover every possible form of Naxal activity. The selection includes 185 events whose `best` death estimate is zero; the analysis calls them *recorded events*, not *lethal events*.
- Requested UCDP citations: Davies, Pettersson, and Öberg (2026), “Organized violence 1989–2025, and violent political protests,” *Journal of Peace Research*, [doi:10.1093/jopres/xjag046](https://doi.org/10.1093/jopres/xjag046); Sundberg and Melander (2013), “Introducing the UCDP Georeferenced Event Dataset,” *Journal of Peace Research* 50(4). Identify the dataset as GED **26.1**.

## World Bank India Spatial Database

- Source: [India Spatial Database, Level 2, 2001](https://datacatalog.worldbank.org/search/dataset/0062657/india-spatial-database), World Bank, [CC BY 4.0](https://datacatalog.worldbank.org/search/dataset/0062657/india-spatial-database).
- Snapshot: `work/worldbank_2001_ind_l2.csv`; SHA-256 `83cea287ff065b43b6dfc509c80bf92e4a512ac6843dece1cde36166c8d50e86`.
- Use: 2001 population, Scheduled Tribe/Caste shares, literacy, and a geographic-area comparison. The database contains some later district subdivisions even for 2001 indicators. The explicit crosswalk aggregates 308 selected rows into 289 FSI reporting units.
- Its forest percentage is **not** substituted for FSI forest cover, because the constructs disagree substantially in some states.

## Census 2001 district geometry

- Source: [DataMeet's Census 2001 district boundaries](https://github.com/yashveeeeeeer/india-geodata/tree/main/data/administrative/districts/census-2001), via the India Geodata mirror. The underlying DataMeet project describes its datasets as [CC BY 4.0](https://github.com/datameet/maps).
- Snapshot: `work/geo2001/2001_Dist.{shp,shx,dbf,prj}`. SHP SHA-256: `2de4a9e21553c193ff2936f7a8412402e74dcc5d45d8100cd556b356d8aee623`.
- Use: whole-India outline and 292 mapped polygons in the nine-state region, associated with 289 FSI units. This source is an approximate spatial presentation where administrative boundaries or source areas disagree; 23 units differ by over 10% from the FSI area.

## USGS/NGA GMTED2010 terrain

- Source: [USGS GMTED2010](https://www.usgs.gov/centers/eros/science/usgs-eros-archive-digital-elevation-global-multi-resolution-terrain-elevation), [official global-grid page](https://topotools.cr.usgs.gov/gmted_viewer/gmted2010_global_grids.php), `mn30_grd.zip` mean-elevation grid at 30 arc-seconds. USGS identifies the dataset as public domain.
- Source archive SHA-256: `dfd0d6c6486f4da22109be6107c93a70ef9917a5b6f954cd82d87cf8b920149d`. The original archive is 277,229,566 bytes and is not included in GitHub. `work/fetch_terrain_grid.py` downloads, checks, and extracts it; `work/compute_terrain_controls.py` generates the included `outputs/terrain_2001_district_controls.csv`.
- Use: about 2.12 million valid 30-arc-second cells within the 292 study polygons. Cell-centre assignment and cosine-latitude area weighting produce mean district elevation and within-district elevation standard deviation. The latter is a district-scale relief proxy. Both are scaled per 100 m in regressions.
- Limitation: the raster source is compiled as GMTED2010 and its source elevations include data collected at different times. Terrain is treated as approximately time-invariant. The measures share the district-boundary caveats above and do not capture local road slope or every aspect of accessibility.

## Derived data and geographic matching

The source-to-FSI mappings are `outputs/district_2001_crosswalk_audit.csv`, `outputs/worldbank_to_fsi_2001_crosswalk.csv`, and `outputs/geometry_to_fsi_2001_crosswalk.csv`. `outputs/extended_district_analysis_panel.csv` contains one row per historical FSI unit, including terrain controls. Of 3,913 selected UCDP events, 3,763 are assigned to those units. Excluded events and ambiguous names are documented in the audit and report. The India maps show district aggregates; no event points are plotted.

The MIT licence in `LICENSE` applies to original project code and text only. Source and derived data retain their respective source licences and attribution requirements.
