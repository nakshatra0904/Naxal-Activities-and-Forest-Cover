"""Exploratory baseline-only PCA and K-means; violence is never a feature."""
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
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

OUT = ROOT / "outputs"
df = pd.read_csv(OUT / "extended_district_analysis_panel.csv")
features = ["forest_pct", "st_pct", "sc_pct", "literacy_pct", "log_density"]
names = ["Forest cover", "Scheduled Tribe share", "Scheduled Caste share",
         "Literacy", "Log population density"]
x = StandardScaler().fit_transform(df[features])
pca = PCA().fit(x)
scores = pca.transform(x)
loadings = pd.DataFrame(pca.components_.T, index=names,
                        columns=[f"PC{i+1}" for i in range(len(features))])
loadings.insert(0, "variable", names)
loadings.to_csv(OUT / "pca_loadings.csv", index=False)
pd.DataFrame({"component": [f"PC{i+1}" for i in range(len(features))],
              "variance_share": pca.explained_variance_ratio_,
              "cumulative_variance": np.cumsum(pca.explained_variance_ratio_)
             }).to_csv(OUT / "pca_explained_variance.csv", index=False)

scores_by_k = []
labels_by_k = {}
for k in range(2, 7):
    fit = KMeans(n_clusters=k, n_init=50, random_state=20260930).fit(x)
    labels_by_k[k] = fit.labels_
    scores_by_k.append({"k": k, "silhouette": silhouette_score(x, fit.labels_),
                        "inertia": fit.inertia_})
selection = pd.DataFrame(scores_by_k)
selection.to_csv(OUT / "cluster_selection.csv", index=False)
k = int(selection.sort_values(["silhouette", "k"], ascending=[False, True]).iloc[0].k)
raw_labels = labels_by_k[k]
order = (df.assign(raw_cluster=raw_labels).groupby("raw_cluster").forest_pct.mean()
         .sort_values().index.tolist())
remap = {old: i+1 for i, old in enumerate(order)}
df["cluster"] = [remap[x] for x in raw_labels]
df["PC1"] = scores[:, 0]
df["PC2"] = scores[:, 1]
df[["state", "fsi_2001_unit", "cluster", "PC1", "PC2", "forest_pct",
    "events"]].to_csv(OUT / "pca_cluster_district_scores.csv", index=False)

profiles = (df.groupby("cluster")
            .agg(n=("events", "size"), forest_pct=("forest_pct", "mean"),
                 st_pct=("st_pct", "mean"), sc_pct=("sc_pct", "mean"),
                 literacy_pct=("literacy_pct", "mean"),
                 population_density=("population_density_2001", "median"),
                 area_km2=("area_km2", "sum"), events=("events", "sum"),
                 victim_deaths=("victim_deaths", "sum"))
            .reset_index())
profiles["event_rate_per_1000km2_year"] = profiles.events / profiles.area_km2 * 1000 / 21
profiles.to_csv(OUT / "baseline_cluster_profiles.csv", index=False)

palette = ["#507c85", "#b88455", "#566b9e", "#8c689a", "#7c8850", "#9b5d67"]
fig, ax = plt.subplots(figsize=(8.5, 5.5), layout="constrained")
for group, part in df.groupby("cluster"):
    ax.scatter(part.PC1, part.PC2, s=28, alpha=.72,
               color=palette[int(group)-1], label=f"Cluster {group} (n={len(part)})")
ax.axhline(0, lw=.7, color="#bbc2ca")
ax.axvline(0, lw=.7, color="#bbc2ca")
ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% of baseline-feature variance)")
ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}% of baseline-feature variance)")
ax.set_title("District baseline profiles (2001): exploratory PCA and K-means")
ax.legend(frameon=False, loc="best", fontsize=9)
ax.text(.01, -.16, "Features: forest, ST/SC shares, literacy, log density. Violence was excluded from clustering.",
        transform=ax.transAxes, fontsize=8.5, color="#596574")
fig.savefig(OUT / "pca_clusters.png", dpi=220, bbox_inches="tight")
fig.savefig(OUT / "pca_clusters.pdf", bbox_inches="tight")
plt.close(fig)
print("Chosen K", k)
print(selection.to_string(index=False))
print(profiles.to_string(index=False))
print("PC variance", pca.explained_variance_ratio_[:2])
print(loadings[["variable", "PC1", "PC2"]].to_string(index=False))
