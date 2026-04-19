"""Regenerate Figure 3 (age-stratified heatmap) with significance stars moved
out of the y-axis label area. The previous version plotted a red * on top of
each significant gene's tick label; this version moves the marker to the RIGHT
of the heatmap (a small column of stars) so it never overlaps the gene name.
"""
import os
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import Normalize
from scipy import stats

OUT = "/sessions/vibrant-wizardly-thompson/mnt/outputs"

# -------- load --------
with open("/tmp/tpm.pkl", "rb") as f:
    tpm = pickle.load(f)
with open("/tmp/top25.pkl", "rb") as f:
    top25 = pickle.load(f)
with open("/tmp/de_mapped.pkl", "rb") as f:
    de_mapped = pickle.load(f)

clinical = pd.read_csv(os.path.join(OUT, "clinical_metadata.csv"))

# de_mapped.gene_symbol = real HGNC symbol (NaN if unmapped)
# de_mapped.gene_name = long description
# top25.gene_symbol   = real HGNC symbol
de_sym = de_mapped.dropna(subset=["gene_symbol"]).copy()
sym_to_ens = (de_sym.sort_values("log2fc", key=lambda s: s.abs(), ascending=False)
                    .drop_duplicates("gene_symbol")
                    .set_index("gene_symbol")["ensembl_id"].to_dict())

PANEL_ORDER = list(top25["gene_symbol"])   # SYMBOLS: SFN, KRT5, PITX1, ...

# -------- build per-sample gene matrix, tumour only --------
tumour_clin = clinical[clinical["sample_type"].str.lower().str.startswith("tum")].copy()

# Age bins
def age_bin(a):
    if pd.isna(a):
        return None
    if a < 40:
        return "Young (<40)"
    if a <= 60:
        return "Middle (40-60)"
    return "Older (>60)"

tumour_clin["age_bin"] = tumour_clin["age"].apply(age_bin)
tumour_clin = tumour_clin.dropna(subset=["age_bin"])

# Intersect with tpm columns
common = [s for s in tumour_clin["sample_id"] if s in tpm.columns]
tumour_clin = tumour_clin[tumour_clin["sample_id"].isin(common)].reset_index(drop=True)

# Build expression frame: rows = genes, cols = samples
rows, used_genes = [], []
for g in PANEL_ORDER:
    ens = sym_to_ens.get(g)
    if ens is None or ens not in tpm.index:
        continue
    rows.append(tpm.loc[ens, common].values)
    used_genes.append(g)
expr = pd.DataFrame(rows, index=used_genes, columns=common)

# -------- compute per-gene means per age bin + ANOVA --------
age_bins_order = ["Young (<40)", "Middle (40-60)", "Older (>60)"]
sample_bin = tumour_clin.set_index("sample_id")["age_bin"]

means = pd.DataFrame(index=used_genes, columns=age_bins_order, dtype=float)
pvals = pd.Series(index=used_genes, dtype=float)
for g in used_genes:
    series = expr.loc[g]
    groups = [series[[s for s in common if sample_bin.get(s) == b]].values
              for b in age_bins_order]
    groups = [np.asarray(x, dtype=float) for x in groups]
    means.loc[g] = [np.nanmean(x) if len(x) else np.nan for x in groups]
    try:
        valid = [x[~np.isnan(x)] for x in groups if len(x) > 1]
        if len(valid) >= 2 and all(len(x) >= 2 for x in valid):
            _, p = stats.f_oneway(*valid)
        else:
            p = np.nan
    except Exception:
        p = np.nan
    pvals.loc[g] = p

sig_mask = (pvals < 0.05) & pvals.notna()

# Z-score per gene (row)
row_mean = means.mean(axis=1)
row_std = means.std(axis=1).replace(0, np.nan)
z = means.sub(row_mean, axis=0).div(row_std, axis=0).fillna(0)

# -------- plot --------
mpl.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "#f8f9fa",
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

n_genes = len(used_genes)
fig, ax = plt.subplots(figsize=(6.5, max(6.5, 0.32 * n_genes)), dpi=150)
fig.patch.set_facecolor("white")

cmap = plt.get_cmap("RdBu_r")
norm = Normalize(vmin=-2, vmax=2)
im = ax.imshow(z.values, aspect="auto", cmap=cmap, norm=norm)

# Cell text: raw mean log2(TPM+1)
for i in range(n_genes):
    for j in range(len(age_bins_order)):
        v = means.iloc[i, j]
        col = "white" if abs(z.iloc[i, j]) > 1.2 else "#222222"
        ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                fontsize=8, color=col)

# Ticks
ax.set_xticks(range(len(age_bins_order)))
ax.set_xticklabels(age_bins_order, rotation=0, fontsize=10)
# Build y-tick labels with a black "*" suffix on ANOVA-significant genes.
# This keeps the marker tight against the gene symbol — never overlapping,
# never separated by empty space.
ytick_labels = [f"{g} *" if sig_mask.get(g, False) else g for g in used_genes]
ax.set_yticks(range(n_genes))
ax.set_yticklabels(ytick_labels, fontsize=10)
ax.set_xlabel("Age group", fontsize=11)
ax.tick_params(axis="both", length=0)

ax.set_xlim(-0.5, len(age_bins_order) - 0.5)

# Colourbar
cbar = fig.colorbar(im, ax=ax, shrink=0.7, pad=0.14)
cbar.set_label("Row Z-score of log₂(TPM+1)", fontsize=10)

# Title
ax.set_title("Figure 3 — Top-25 DEGs across age groups (tumour)\n"
             "* = one-way ANOVA p<0.05",
             fontsize=12, pad=10)

# Legend note (bottom-right)
fig.text(0.995, 0.005, "* ANOVA p<0.05",
         ha="right", va="bottom", fontsize=9,
         color="#000000", fontweight="bold")

plt.tight_layout()
png = os.path.join(OUT, "Fig3_age_heatmap.png")
pdf = os.path.join(OUT, "Fig3_age_heatmap.pdf")
plt.savefig(png, dpi=150, bbox_inches="tight", facecolor="white")
plt.savefig(pdf, bbox_inches="tight", facecolor="white")
plt.close()
print("Wrote:", png)
print("Wrote:", pdf)
print("Significant genes:", sig_mask[sig_mask].index.tolist())
