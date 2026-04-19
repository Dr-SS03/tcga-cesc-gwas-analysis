"""Regenerate Figure 9 (Gene × Functional Category network) with two fixes:

1. Header text was a jumble: title, 'Marker colour = GWAS tier', 'Shape ▲/▼
   = direction', 'Size = GWAS significance', 'UPREGULATED / DOWNREGULATED'
   and 'Label = GWAS p' all overlapped in the top strip.
   Fix: one clean title + one subtitle line + the UP/DOWN section banners
   placed INSIDE the plot (just above the first grid row) with no overlap.

2. The GWAS p-value numbers (e.g. 3e-182, 0e+0, 1e-58) were written INSIDE
   each triangle and were often invisible against dark fill.
   Fix: place the p-value text BELOW each triangle as a small grey label,
   with a white halo stroke for contrast so it is readable against both
   the plot background and the grid.
"""
import os
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D

OUT = "/sessions/vibrant-wizardly-thompson/mnt/outputs"

# -------- load --------
try:
    with open("/tmp/gwas_annotation.pkl", "rb") as f:
        gwas = pickle.load(f)
except FileNotFoundError:
    gwas = pd.read_csv(os.path.join(OUT, "gwas_annotation.csv"))

TIER_COLOR = {
    "STRONG":   "#2e7d32",
    "MODERATE": "#f9a825",
    "LIMITED":  "#1f6fb4",
    "NONE":     "#9e9e9e",
}

# Ordered gene axes, up block then down block
up   = gwas[gwas["direction"] == "up"].sort_values("rank").reset_index(drop=True)
down = gwas[gwas["direction"] == "down"].sort_values("rank").reset_index(drop=True)

gene_order = up["gene"].tolist() + down["gene"].tolist()
gene_to_x  = {g: i for i, g in enumerate(gene_order)}
divider_x  = len(up) - 0.5            # vertical dashed line separating up / down

# Category order: most frequent first, but keep a sensible fixed order.
CAT_ORDER = [
    "Alarmin/S100 Cluster",
    "Cytoskeleton",
    "Extracellular Matrix",
    "Cell Adhesion",
    "Cell Cycle",
    "Growth Factor Signalling",
    "Hormone Signalling",
    "Transcription Factor",
    "Ion Channel",
]
cat_to_y = {c: i for i, c in enumerate(CAT_ORDER[::-1])}  # top-down

# -------- sizing / formatting helpers --------
def neglog10(p):
    if pd.isna(p) or p <= 0:
        return 300.0
    return -np.log10(p)

def bubble_size(p):
    # Scale by -log10(p): 0 → 60, 300 → ~900
    val = neglog10(p)
    return float(60 + 2.6 * val)

def format_p(p):
    if pd.isna(p) or p == 0:
        return "0e+0"
    # Compact scientific: e.g. 3e-182, 1e-58
    exp = int(np.floor(np.log10(p)))
    mantissa = p / (10.0 ** exp)
    return f"{mantissa:.0f}e{exp:+d}"

# -------- style --------
mpl.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor":   "#f8f9fa",
    "font.family":      "DejaVu Sans",
    "font.size":        11,
    "axes.spines.top":   False,
    "axes.spines.right": False,
})

fig, ax = plt.subplots(figsize=(16, 8.5), dpi=150)
fig.patch.set_facecolor("white")

# Grid lines
for i in range(len(gene_order)):
    ax.axvline(i, color="#e0e0e0", linestyle=":", linewidth=0.8, zorder=1)
for i in range(len(CAT_ORDER)):
    ax.axhline(i, color="#e0e0e0", linestyle=":", linewidth=0.8, zorder=1)

# Dashed vertical divider between up and down
ax.axvline(divider_x, color="#333333", linestyle="--", linewidth=1.1, alpha=0.7,
           zorder=2)

# Plot each gene's triangle
for _, row in gwas.iterrows():
    g = row["gene"]
    cat = row["bio_category"]
    if g not in gene_to_x or cat not in cat_to_y:
        continue
    x = gene_to_x[g]
    y = cat_to_y[cat]
    tier = row["evidence_level"]
    colour = TIER_COLOR.get(tier, "#9e9e9e")
    marker = "^" if row["direction"] == "up" else "v"
    size = bubble_size(row["gwas_min_p"])
    ax.scatter([x], [y], marker=marker, s=size,
               facecolors=colour, edgecolors="#222222", linewidths=0.9,
               alpha=0.95, zorder=3)

    # p-value label — placed BELOW the triangle, with a white stroke halo so
    # it is readable even over the grid lines.
    radius_pts = np.sqrt(size) / 2.0
    ax.annotate(
        format_p(row["gwas_min_p"]),
        xy=(x, y),
        xytext=(0, -(radius_pts + 7)),
        textcoords="offset points",
        ha="center", va="top",
        fontsize=8, color="#333333",
        path_effects=[pe.withStroke(linewidth=2.0, foreground="white")],
        zorder=4,
    )

# Axis ticks
ax.set_xticks(range(len(gene_order)))
ax.set_xticklabels(gene_order, rotation=45, ha="right", fontsize=9)
ax.set_yticks(range(len(CAT_ORDER)))
ax.set_yticklabels(CAT_ORDER[::-1], fontsize=10)
ax.tick_params(axis="both", length=0)
ax.set_xlim(-0.7, len(gene_order) - 0.3)
ax.set_ylim(-0.7, len(CAT_ORDER) - 0.3 + 0.8)   # extra headroom for section banners

# ---------- Headers ----------
# Title only
ax.set_title(
    "Figure 9 — Gene × Functional Category Network",
    fontsize=13, fontweight="bold", pad=36,
)
# Subtitle, placed just under the title in figure coords (no overlap)
fig.text(0.5, 0.935,
         "Colour = GWAS tier   ·   Shape ▲/▼ = direction   ·"
         "   Size ∝ −log$_{10}$(GWAS p)   ·   Label below = GWAS p",
         ha="center", va="bottom", fontsize=10, color="#444444")

# UPREGULATED / DOWNREGULATED section banners, placed inside the plot
# at the top (above the top grid row) so they can't overlap the title.
banner_y = len(CAT_ORDER) - 0.3 + 0.55
ax.text((divider_x) / 2.0, banner_y, "UPREGULATED (top 15)",
        ha="center", va="center", fontsize=11, fontweight="bold",
        color="#7a4a00",
        bbox=dict(boxstyle="round,pad=0.35", facecolor="#fff3df",
                  edgecolor="#d6a84b", linewidth=0.8))
ax.text((divider_x + (len(gene_order) - 1)) / 2.0, banner_y,
        "DOWNREGULATED (top 10)",
        ha="center", va="center", fontsize=11, fontweight="bold",
        color="#1a3a66",
        bbox=dict(boxstyle="round,pad=0.35", facecolor="#e4effb",
                  edgecolor="#5185c2", linewidth=0.8))

# ---------- Legend ----------
handles = [
    Line2D([0],[0], marker="o", linestyle="",
           markerfacecolor=TIER_COLOR["STRONG"],   markeredgecolor="#222",
           markersize=10, label="STRONG"),
    Line2D([0],[0], marker="o", linestyle="",
           markerfacecolor=TIER_COLOR["MODERATE"], markeredgecolor="#222",
           markersize=10, label="MODERATE"),
    Line2D([0],[0], marker="o", linestyle="",
           markerfacecolor=TIER_COLOR["LIMITED"],  markeredgecolor="#222",
           markersize=10, label="LIMITED"),
    Line2D([0],[0], marker="o", linestyle="",
           markerfacecolor=TIER_COLOR["NONE"],     markeredgecolor="#222",
           markersize=10, label="NONE"),
    Line2D([0],[0], marker="^", linestyle="", color="#555555",
           markersize=10, label="Up"),
    Line2D([0],[0], marker="v", linestyle="", color="#555555",
           markersize=10, label="Down"),
]
ax.legend(handles=handles, loc="upper right",
          bbox_to_anchor=(1.14, 1.02),
          fontsize=9, frameon=True, framealpha=0.95)

plt.tight_layout(rect=[0, 0, 0.995, 0.92])

png = os.path.join(OUT, "Fig9_category_network.png")
pdf = os.path.join(OUT, "Fig9_category_network.pdf")
plt.savefig(png, dpi=150, bbox_inches="tight", facecolor="white")
plt.savefig(pdf,         bbox_inches="tight", facecolor="white")
plt.close()
print("Wrote:", png)
print("Wrote:", pdf)
