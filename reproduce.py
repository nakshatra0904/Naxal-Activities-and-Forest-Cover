"""Rebuild data, analysis and figures from the checked-in source snapshots."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
SCRIPTS = [
    "prepare_event_extract.py",
    "run_forest_regression.py",
    "harmonize_2001_geography.py",
    "extended_models.py",
    "pca_clusters.py",
    "make_analytic_figures.py",
    "plot_regression_curve.py",
    "map_india_2001.py",
    "map_terrain_2001.py",
    "verify_results.py",
]
for script in SCRIPTS:
    print(f"Running {script}", flush=True)
    subprocess.run([sys.executable, str(ROOT / "work" / script)],
                   cwd=ROOT, check=True)
print("Analysis and figures reproduced. Compile report/report.tex separately with Tectonic.")
