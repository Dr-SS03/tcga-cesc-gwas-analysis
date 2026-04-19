"""Regenerate Figures 4 (upregulated) and 5 (downregulated) FIGO-stage
heatmaps. Previous versions placed ↑*/↓* markers directly on top of the
gene labels. This version uses the same inline-suffix style as the fixed
Figure 3: append a black ' *' to any Spearman-significant gene label and
note ' * = Spearman p<0.05' in the title/legend.
"""
import os
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import Normalize

OUT = "/sessions/vibrant-wizardly-thompson/mnt/outputs"

# -------- load --------
with open("/tmp/tpm.pkl", "rb") as f:
    tpm = pickle.load(f)
with open("/tmp/top25.pkl", "rb") as f:
    top25 = pickle.load(f)

clinical = pd.read_csv(os.path.join(OUT, "clinical_metadata.csv"))
stage_df = pd.read_csv(os.path.join(OUT, "stage_expression.csv"))

# Map symbol → ensembl using top25
sym_to_ens = dict(zip(top25["gene_symbol"], top25["ensembl_id"]))
sym_to_dir = dict(zip(top25["gene_symbol"], top25["direction"]))

# Tumour samples with FIGO stage
t = clinical[clinical["sample_type"].str.lower().str.startswith("tum")].copy()
STAGE_ORDER = ["I", "II", "III", "IV"]
t = t[t["stage"].isin(STAGE_ORDER)].copy()

samples = [s for s in t["sample_id"] if s in tpm.columns]
t = t[t["sample_id"].isin(samples)].reset_index(drop=True)
stage_by_sample = dict(zip(t["sample_id"], t["stage"]))

# -------- compute mean per stage per gene --------
def build_matrix(gene_order):
    means = pd.DataFrame(index=gene_order, columns=STAGE_ORDER, dtype=float)
    for g in gene_order:
        ens = sym_to_ens.get(g)
        if ens is None or ens not in tpm.index:
            continue
        series = tpm.loc[ens, samples]
        for stage in STAGE_ORDER:
            stage_samples = [s for s in samples if stage_by_sample.get(s) == stage]
            means.loc[g, stage] = series[stage_samples].mean()
    return means

# Split panels
up_genes   = list(top25[top25["direction"] == "up"]["gene_symbol"])
down_genes = list(top25[top25["direction"] == "down"]["gene_symbol"])

# Spearman significance by gene (from stage_expression.csv)
sig = dict(zip(stage_df["gene"], stage_df["spearman_p"] < 0.05))

# -------- plotting helper --------
mpl.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "#f8f9fa",
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

def draw_heatmap(genes, title, outname):
    means = build_matrix(genes)
    # Row-Z
    row_mean = means.mean(axis=1)
    row_std  = means.std(axis=1).replace(0, np.nan)
    z = means.sub(row_mean, axis=0).div(row_std, axis=0).fillna(0)

    n = len(genes)
    fig, ax = plt.subplots(figsize=(6.5, max(5.5, 0.42 * n)), dpi=150)
    fig.patch.set_facecolor("white")
    im = ax.imshow(z.values, aspect="auto", cmap=plt.get_cmap("RdBu_r"),
                   norm=Normalize(vmin=-2, vmax=2))

    # Cell text
    for i in range(n):
        for j in range(len(STAGE_ORDER)):
            v = means.iloc[i, j]
            col = "white" if abs(z.iloc[i, j]) > 1.2 else "#222222"
            ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                    fontsize=9, color=col)

    # Inline '*' suffix for Spearman-significant genes
    y_labels = [f"{g} *" if sig.get(g, False) else g for g in genes]
    ax.set_xticks(range(len(STAGE_ORDER)))
    ax.set_xticklabels(STAGE_ORDER, fontsize=10)
    ax.set_yticks(range(n))
    ax.set_yticklabels(y_labels, fontsize=10)
    ax.set_xlabel("FIGO stage", fontsize=11)
    ax.tick_params(axis="both", length=0)
    ax.set_xlim(-0.5, len(STAGE_ORDER) - 0.5)

    cbar = fig.colorbar(im, ax=ax, shrink=0.7, pad=0.1)
    cbar.set_label("Row Z-score of log₂(TPM+1)", fontsize=10)

    ax.set_title(title + "\n* = Spearman p<0.05",
                 fontsize=12, pad=10)
    fig.text(0.995, 0.005, "* Spearman p<0.05",
             ha="right", va="bottom", fontsize=9,
             color="#000000", fontweight="bold")

    plt.tight_layout()
    png = os.path.join(OUT, f"{outname}.png")
    pdf = os.path.join(OUT, f"{outname}.pdf")
    plt.savefig(png, dpi=150, bbox_inches="tight", facecolor="white")
    plt.savefig(pdf, bbox_inches="tight", facecolor="white")
    plt.close()
    sig_genes = [g for g in genes if sig.get(g, False)]
    print(f"Wrote {png}  (sig: {sig_genes})")

# Build & save
draw_heatmap(up_genes,
             "Figure 4 — Upregulated DEGs across FIGO stage",
             "Fig4_stage_up_heatmap")
draw_heatmap(down_genes,
             "Figure 5 — Downregulated DEGs across FIGO stage",
             "Fig5_stage_down_heatmap")
