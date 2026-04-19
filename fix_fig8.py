"""Regenerate Figure 8 with two fixes:

Left panel (Fig 8a — lollipop of GWAS p-values):
  * Gene labels previously ran off the left edge into the grey plot area.
  * Fix: move the combined "GENE  rsID (chr:pos)" text completely OUT of
    the plot into the white margin on the left, use a wider figure and
    explicit subplot spacing so the label column has room, and add padding
    between the y-tick labels and the y-axis spine.

Right panel (Fig 8b — DE profile of the 25 genes):
  * Triangle markers bunched up and labels piled on top of each other.
  * Fix: adopt the Fig 10a pattern — use adjustText to spread the gene
    labels out, connecting each label back to its triangle with a thin
    grey leader line.
"""
import os
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.lines import Line2D
from adjustText import adjust_text

OUT = "/sessions/vibrant-wizardly-thompson/mnt/outputs"

# -------- load --------
# Prefer /tmp pickles if present; otherwise reconstruct from CSVs.
try:
    with open("/tmp/gwas_annotation.pkl", "rb") as f:
        gwas = pickle.load(f)
    with open("/tmp/top25.pkl", "rb") as f:
        top25 = pickle.load(f)
except FileNotFoundError:
    gwas = pd.read_csv(os.path.join(OUT, "gwas_annotation.csv"))
    up_df_csv = pd.read_csv(os.path.join(OUT, "top15_upregulated.csv"))
    dn_df_csv = pd.read_csv(os.path.join(OUT, "top10_downregulated.csv"))
    top25 = pd.concat([up_df_csv, dn_df_csv], ignore_index=True)
    # top25 in CSV uses 'gene' as symbol — add gene_symbol alias
    top25["gene_symbol"] = top25["gene"]

# -------- shared styling --------
TIER_COLOR = {
    "STRONG":   "#2e7d32",
    "MODERATE": "#f9a825",
    "LIMITED":  "#1f6fb4",
    "NONE":     "#9e9e9e",
}

CATEGORY_COLOR = {
    "Alarmin/S100 Cluster":       "#d62728",
    "Cell Adhesion":              "#1f77b4",
    "Cell Cycle":                 "#ff9f1c",
    "Cytoskeleton":               "#7f3fcc",
    "Extracellular Matrix":       "#8c564b",
    "Growth Factor Signalling":   "#17becf",
    "Hormone Signalling":         "#e377c2",
    "Ion Channel":                "#bcbd22",
    "Transcription Factor":       "#2ca02c",
}

# MR-confirmed set (copied from build_report.py — these are called out in the
# report narrative as having mendelian-randomization evidence).
MR_CONFIRMED = {"S100A9", "CDKN2A"}

mpl.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor":   "#f8f9fa",
    "font.family":      "DejaVu Sans",
    "font.size":        11,
    "axes.spines.top":   False,
    "axes.spines.right": False,
})

# -------- prep data --------
def neglog10(p):
    if pd.isna(p) or p <= 0:
        return 300.0
    return -np.log10(p)

g = gwas.copy()
g["neglog10p"] = g["gwas_min_p"].apply(neglog10)
# Preserve top25 rank for display ordering
rank_map = dict(zip(top25["gene_symbol"], top25["rank"]))
g["plot_rank"] = g["gene"].map(rank_map)

# Sort for lollipop: descending p-value (strongest at top)
g = g.sort_values("neglog10p", ascending=False).reset_index(drop=True)

# Build the left-panel label: "GENE   rsID (chr:pos)"
def make_locus_label(row):
    rsid = row.get("rsid", "")
    locus = row.get("locus", "")
    if pd.isna(rsid) or rsid == "":
        return f"{row['gene']}"
    locus_str = f" ({locus})" if (pd.notna(locus) and locus != "") else ""
    return f"{row['gene']}   {rsid}{locus_str}"

g["lollipop_label"] = g.apply(make_locus_label, axis=1)

# DE profile (right panel): merge top25 with category
t = top25.copy()
t["bio_category"] = t["bio_category"].fillna("Other")
t["neglog10_de"]  = -np.log10(t["p_value"].replace(0, 1e-300))

GW_LINE = -np.log10(5e-8)

# -------- figure --------
# Wider figure + explicit width ratios so left panel has room for long labels.
fig = plt.figure(figsize=(18, 11), dpi=150)
fig.patch.set_facecolor("white")
gs = fig.add_gridspec(1, 2, width_ratios=[1.15, 1.0], wspace=0.08,
                       left=0.20, right=0.98, top=0.93, bottom=0.08)
ax_a = fig.add_subplot(gs[0, 0])
ax_b = fig.add_subplot(gs[0, 1])

# ========== Left: 8a lollipop ==========
n = len(g)
y = np.arange(n)[::-1]     # top to bottom in display order
values = g["neglog10p"].values
colours = [TIER_COLOR.get(t, "#9e9e9e") for t in g["evidence_level"]]

# Stem (line) and head (dot)
for yi, v, c in zip(y, values, colours):
    ax_a.hlines(yi, 0, v, colors=c, linewidth=2.2, alpha=0.9, zorder=2)
ax_a.scatter(values, y, c=colours, s=95, edgecolors="white", linewidths=1.4,
             zorder=3)

# MR-confirmed gold stars, plotted just past the lollipop head
star_x = values.max() * 1.03
for yi, row in zip(y, g.itertuples()):
    if row.gene in MR_CONFIRMED:
        ax_a.scatter([star_x], [yi], marker="*", s=180,
                     color="#e0a800", edgecolors="#7a5c00",
                     linewidths=0.8, zorder=4)

# Genome-wide significance cutoff
ax_a.axvline(GW_LINE, color="#c0392b", linestyle="--", linewidth=1, alpha=0.7,
             zorder=1)

# Y-ticks with the long composite label — moved fully into the white margin
ax_a.set_yticks(y)
ax_a.set_yticklabels(g["lollipop_label"].tolist(), fontsize=9)
ax_a.tick_params(axis="y", length=0, pad=8)

ax_a.set_xlim(0, values.max() * 1.08)
ax_a.set_ylim(-0.5, n - 0.5)
ax_a.set_xlabel("-Log$_{10}$(GWAS p-value)", fontsize=11)
ax_a.set_title("Figure 8a — GWAS loci for top-25 DEGs\n★ = MR-confirmed causal gene",
               fontsize=12, fontweight="bold", pad=10)
ax_a.grid(axis="x", linestyle=":", color="#cccccc", alpha=0.6, zorder=0)

# ========== Right: 8b DE profile — clean triangles only ==========
# Only the 25 highlight genes are drawn (no volcano background dots) so the
# triangles read cleanly. Bold gene labels with thin grey leader lines are
# placed by adjustText — same labeling style as Fig 10a.

# Reference lines
ax_b.axvline(0,       color="#888888", linewidth=0.8, alpha=0.5, zorder=1)
ax_b.axhline(GW_LINE, color="#888888", linewidth=0.8, alpha=0.5,
             linestyle="--", zorder=1)

up_df   = t[t["direction"] == "up"].copy()
down_df = t[t["direction"] == "down"].copy()

for df, marker in [(up_df, "^"), (down_df, "v")]:
    for cat, sub in df.groupby("bio_category"):
        ax_b.scatter(sub["log2fc"], sub["neglog10_de"],
                     s=160, c=CATEGORY_COLOR.get(cat, "#888888"),
                     marker=marker, edgecolors="#222222", linewidths=0.9,
                     alpha=0.95, zorder=3)

# Axis limits — focus on the region where the top-25 triangles live so they
# are not squashed by distant background outliers.
xlim_pad = max(abs(t["log2fc"].min()), abs(t["log2fc"].max())) * 0.12
ax_b.set_xlim(t["log2fc"].min() - xlim_pad, t["log2fc"].max() + xlim_pad)
y25_min = float(t["neglog10_de"].min())
y25_max = float(t["neglog10_de"].max())
pad_y   = (y25_max - y25_min) * 0.55 + 1.0
ax_b.set_ylim(max(0, y25_min - pad_y * 0.35), y25_max + pad_y)

# Gene labels: bold black text, NO bounding box, leader line to triangle
texts = []
for row in t.itertuples():
    texts.append(ax_b.text(row.log2fc, row.neglog10_de, row.gene_symbol,
                           fontsize=10, fontweight="bold", color="#111111",
                           ha="center", va="center", zorder=5))

adjust_text(
    texts, ax=ax_b,
    expand_text=(1.3, 1.6),
    expand_points=(1.5, 1.8),
    force_text=(0.8, 1.5),
    force_points=(0.6, 1.2),
    lim=3000,
    arrowprops=dict(arrowstyle="-", color="#666666", lw=0.6, alpha=0.85,
                    shrinkA=3, shrinkB=6),
)

ax_b.set_xlabel("Log$_{2}$ Fold Change", fontsize=11)
ax_b.set_ylabel("-Log$_{10}$(DE p-value)", fontsize=11)
ax_b.set_title("Figure 8b — DE profile of the 25 genes by functional category",
               fontsize=12, fontweight="bold", pad=10)
ax_b.grid(linestyle=":", color="#cccccc", alpha=0.6, zorder=0)

# Category legend (inside ax_b, upper-right)
cat_handles = [Line2D([0],[0], marker="o", linestyle="",
                      markerfacecolor=c, markeredgecolor="#333333",
                      markersize=8, label=cat)
               for cat, c in CATEGORY_COLOR.items()]
ax_b.legend(handles=cat_handles, loc="upper right", fontsize=8, frameon=True,
            framealpha=0.9, title=None, ncol=1,
            bbox_to_anchor=(1.0, 1.0))

# Save
png = os.path.join(OUT, "Fig8_gwas_loci_lollipop.png")
pdf = os.path.join(OUT, "Fig8_gwas_loci_lollipop.pdf")
plt.savefig(png, dpi=150, bbox_inches="tight", facecolor="white")
plt.savefig(pdf,         bbox_inches="tight", facecolor="white")
plt.close()
print("Wrote:", png)
print("Wrote:", pdf)
