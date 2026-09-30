# Forest cover and recorded CPI-Maoist activity in India

A reproducible district-level analysis linking Forest Survey of India (FSI) 2001 forest cover to UCDP GED 26.1 events involving CPI-Maoist actor ID 195 during 2005–2025. The analysis covers 289 historical FSI reporting units in nine states and now controls for elevation and district-scale relief from USGS GMTED2010. It is descriptive, not a causal estimate or a census of all Naxal activity.

**Read the [ten-page LaTeX report](report/report.pdf) first.** It contains the India forest, activity and terrain maps, observed event rates and fitted regression curves, alternative model results, descriptive tables, PCA and clustering, and limitations. The editable source is [report/report.tex](report/report.tex).

## Main result

The state-adjusted Poisson count model, with district area-years as an offset, estimates a recorded-event rate ratio of **1.79** (95% district-robust interval **1.42–2.26**) for 10 percentage points more 2001 forest cover. With 2001 population density, Scheduled Tribe share, Scheduled Caste share, and literacy added, the ratio is **1.31** (**1.03–1.65**). Adding mean elevation and within-district elevation standard deviation gives **1.37** (**1.06–1.76**). The terrain-adjusted result is **1.31** (**1.02–1.68**) in the 266-unit subset with no more than a 10% FSI versus World Bank area discrepancy. It is **1.31** (**1.00–1.70**, unrounded lower bound 1.0028) in the 256-unit subset whose FSI, census and terrain polygon areas all agree within 10%, and **1.12** (**0.81–1.55**) if Jharkhand is omitted. A terrain-adjusted negative-binomial model gives **2.33** (**1.84–2.93**). These differences limit confidence in a single effect size.

The outcome counts 3,763 district-assigned UCDP records from 3,913 selected India records. It includes 185 records with a zero best-estimate death count; the project also computes a stricter fatal-event outcome. The nine states are Andhra Pradesh (including present-day Telangana), Bihar, Chhattisgarh, Jharkhand, Madhya Pradesh, Maharashtra, Odisha, Uttar Pradesh, and West Bengal.

## Reproduce

Python 3.12 was used for this release. From the repository root:

```bash
python -m venv .venv
# Activate the virtual environment using your operating system's instructions.
python -m pip install -r requirements.txt
python reproduce.py
```

`reproduce.py` rebuilds the event extract, district panel, geographic crosswalks, terrain-adjusted models, descriptive data, PCA, clusters, figures, and verification checks from the checked-in source snapshots and terrain summary. It may take several minutes. The FSI district table is checked in as a derived CSV because the original FSI report PDF is not redistributed here. To re-extract it from the official source:

```bash
python work/fetch_fsi_report.py
python work/extract_fsi_2001.py
python reproduce.py
```

The fetch step checks the PDF's SHA-256 hash and stops if FSI changes the file. If it changes, inspect the new source and extraction rather than bypassing the check.

The 277 MB public-domain terrain archive is also omitted from the GitHub project; its 289-row derived district table is included. To regenerate the terrain controls directly from USGS:

```bash
python work/fetch_terrain_grid.py
python work/compute_terrain_controls.py
python reproduce.py
```

The terrain fetch checks the original ZIP's SHA-256. The relief measure is elevation standard deviation within a district, not local slope.

To rebuild the PDF report after figures are generated, install [Tectonic](https://tectonic-typesetting.github.io/) and run from `report/`:

```bash
tectonic report.tex
```

The report includes a prebuilt PDF so a LaTeX installation is not required to read the results.

## Files

- `work/`: versioned source snapshots, 2001 district boundaries, and analysis scripts; optional hash-checked FSI and USGS downloads.
- `outputs/`: derived panels, explicit crosswalks and audits, model tables, plotted curve data, and figure PDF/PNG pairs.
- `report/`: editable LaTeX source and compiled PDF.
- `DATA_SOURCES.md`: provenance, licences, hashes, and important geographic limits.
- `ADDITIONAL_DATA_REVIEW.md`: promising forest, incident, and settlement sources, with limits and current integration status.
- `work/verify_results.py`: integrity checks for source files, join coverage, principal estimates, curve ratios, and figures.

## Interpretation

The plotted lines are standardized predictions from log-link count regressions, not a causal response to changing forest cover. Forest cover correlates with tribal population share, settlement density, terrain, access, and other factors. The report includes measured elevation and relief controls but does not estimate effects of roads or rainfall. Twenty-three of 289 units have more than a 10% area difference between FSI and World Bank/Census geographies; 23 also exceed 10% for the terrain polygons, with 33 distinct units failing at least one check. Map polygons for those units are approximate representations. District-level robust intervals also do not correct spatial correlation.

This repository is ready to upload to GitHub as a new repository. No GitHub remote or public repository is created by this archive.
