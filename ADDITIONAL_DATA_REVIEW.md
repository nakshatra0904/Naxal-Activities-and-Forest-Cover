# Additional data sources reviewed, 30 September 2026

This review separates data incorporated into the district analysis from sources that could support a later extension. A promising source is not evidence that its variables can be merged without a geographic or outcome-definition audit.

## Incorporated now: USGS GMTED2010 terrain

The [USGS GMTED2010](https://www.usgs.gov/centers/eros/science/usgs-eros-archive-digital-elevation-global-multi-resolution-terrain-elevation) public-domain 30-arc-second **mean-elevation** grid supplies approximately 2.12 million raster cells within the mapped study polygons. The analysis computes area-weighted district mean elevation and within-district elevation standard deviation. The second variable is a district-scale relief proxy, not local slope. The [official global grid download](https://topotools.cr.usgs.gov/gmted_viewer/gmted2010_global_grids.php) is reproducible through `work/fetch_terrain_grid.py` and `work/compute_terrain_controls.py`. The original 277 MB archive is not committed to GitHub; its verified district summaries are.

## High-priority next sources

1. **[University of Maryland Global Forest Change v1.13](https://storage.googleapis.com/earthenginepartners-hansen/GFC-2025-v1.13/download.html)** provides 2000 tree-canopy cover at about 30 m and annual tree-cover loss through 2025. It could independently test whether the FSI 2001 forest result depends on the forest definition, and support carefully framed descriptive change analysis. Canopy cover is a different construct from FSI forest cover. The producer warns that sensor and algorithm changes impair naive comparisons of annual loss across the whole period.
2. **[Ministry of Home Affairs annual reports](https://www.mha.gov.in/en/documents/annual-reports)** contain official left-wing-extremism incidents and deaths. They are valuable for checking the national and state time-series pattern against UCDP. MHA's incident definition covers a broader set of activity than the UCDP CPI-Maoist actor-ID selection; counts must be kept separate or explicitly reconciled. Older reports, including [2010–11](https://mha.gov.in/sites/default/files/AnnualReport_10_11.pdf), publish state-level series. These do not directly replace the harmonized district outcome.
3. **[Global Human Settlement Layer GHS-BUILT-S R2023A](https://human-settlement.emergency.copernicus.eu/ghs_buS2023.php)** offers a 2000 built-up-surface grid. It could improve the pre-period settlement and accessibility proxy beyond population density. It needs raster-to-2001-district aggregation and a check against the World Bank 2001 baseline.

## Later-period robustness source

**[ACLED India](https://acleddata.com/methodology/countrytime-period-coverage)** begins in January 2016 according to its country coverage page and includes a wider set of conflict and protest event types. It could test whether results are similar in 2016–2025 after careful actor and event-type selection. It cannot replace the full 2005–2025 UCDP outcome. [ACLED access](https://acleddata.com/faq/how-can-i-access-and-use-acled-data) requires registration, and its data have not been downloaded or merged here.

WorldClim's SRTM-derived elevation surface was also reviewed, but its [data licence](https://worldclim.org/about.html) restricts redistribution. Public-domain USGS terrain was chosen for the uploadable project.
