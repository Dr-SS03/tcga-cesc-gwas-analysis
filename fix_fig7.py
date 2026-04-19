"""Regenerate Figure 7 (GWAS significance dot/bubble plot) with two fixes:

1. The largest bubbles (S100A9, PITX1 in the upregulated panel; MYH11 in the
   downregulated panel) were getting clipped because the y-axis upper limit
   was set tightly to the data maximum. Fix: add 35 % headroom above the
   tallest point and expand the lower bound slightly below 0 so bubbles
   near the genome-wide line are also fully shown.

2. The tier letter badges (S / M / L / N) were drawn as white-filled squares
   centred on the circle — visually heavy and they obscured the bubble.
   Fix: drop the white-box badge and place a small, lightweight tier letter
   just BELOW the bubble with matching tier colour. This keeps the tier
   information visible without covering the data.
"""
import os
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.lines import Line2D

OUT = "/sessions/vibrant-wizardly-thompson/mnt/outputs"

# -------- load --------
with open("/tmp/gwas_annotation.pkl", "rb") as f:
    gwas = pickle.load(f)
with open("/tmp/top25.pkl", "rb") as f:
    top25 = pickle.load(f)

# -------- prep --------
# -log10(p); clamp p=0 to p=1e-300 (floating-point floor)
def neglog10(p):
    if pd.isna(p) or p <= 0:
        return 300.0
    return -np.log10(p)

gwas = gwas.copy()
gwas["neglog10p"] = gwas["gwas_min_p"].apply(neglog10)

# Preserve the top25 rank order for each direction
rank_map = dict(zip(top25["gene_symbol"], top25["rank"]))
gwas["plot_rank"] = gwas["gene"].map(rank_map)
gwas = gwas.sort_values("plot_rank").reset_index(drop=True)

TIER_COLOR = {
    "STRONG":   "#2e7d32",
    "MODERATE": "#f9a825",
    "LIMITED":  "#1f6fb4",
    "NONE":     "#9e9e9e",
}
TIER_SHORT = {"STRONG": "S", "MODERATE": "M", "LIMITED": "L", "NONE": "N"}

# Bubble size: scale by number of GWAS associations (n_assoc).
# Clamp between 60 and 1200 so extremes stay readable.
def bubble_size(n):
    if pd.isna(n) or n <= 0:
        return 40
    # sqrt scaling so visually-proportional-to-radius
    s = 60 + 60 * np.sqrt(float(n))
    return float(min(max(s, 60), 1200))

gwas["bsize"] = gwas["gwas_n_assoc"].apply(bubble_size)

up   = gwas[gwas["direction"] == "up"].reset_index(drop=True)
down = gwas[gwas["direction"] == "down"].reset_index(drop=True)

# Genome-wide significance threshold on the -log10 scale
GW_LINE = -np.log10(5e-8)

# -------- plotting style --------
mpl.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor":   "#f8f9fa",
    "font.family":      "DejaVu Sans",
    "font.size":        11,
    "axes.spines.top":   False,
    "axes.spines.right": False,
})

fig, (ax_up, ax_dn) = plt.subplots(2, 1, figsize=(12, 10), dpi=150)
fig.patch.set_facecolor("white")

def draw_panel(ax, df, title):
    n = len(df)
    x = np.arange(n)
    y = df["neglog10p"].values
    sizes = df["bsize"].values
    colours = [TIER_COLOR.get(t, "#9e9e9e") for t in df["evidence_level"]]

    ax.scatter(x, y, s=sizes, c=colours,
               edgecolors="white", linewidths=1.2, alpha=0.9,
               zorder=3)

    # Tier letter placed BELOW the bubble, lightweight styling (no box).
    # Offset is in points so it's consistent across bubble sizes but still
    # sits just under the circle edge.
    for xi, (yi, s, tier) in enumerate(zip(y, sizes, df["evidence_level"])):
        # half-height of circle in points = sqrt(s)/2
        radius_pts = np.sqrt(s) / 2.0
        tier_col = TIER_COLOR.get(tier, "#9e9e9e")
        letter = TIER_SHORT.get(tier, "?")
        ax.annotate(
            letter,
            xy=(xi, yi),
            xytext=(0, -(radius_pts + 8)),
            textcoords="offset points",
            ha="center", va="top",
            fontsize=9, fontweight="bold",
            color=tier_col,
            zorder=4,
        )

    # Axis limits with headroom above + below so nothing gets clipped
    ymax = max(float(np.nanmax(y)) if len(y) else 0, GW_LINE)
    ax.set_ylim(-ymax * 0.08, ymax * 1.35)
    ax.set_xlim(-0.5, n - 0.5)

    # Genome-wide significance line
    ax.axhline(GW_LINE, color="#c0392b", linestyle="--", linewidth=1, alpha=0.6,
               zorder=1, label=f"Genome-wide sig. (p=5×10⁻⁸)")

    ax.set_xticks(x)
    ax.set_xticklabels(df["gene"].tolist(), rotation=45, ha="right", fontsize=10)
    ax.set_ylabel("-Log$_{10}$(GWAS p-value)", fontsize=11)
    ax.set_title(title, fontsize=12, fontweight="bold", pad=10)
    ax.grid(axis="y", linestyle=":", color="#cccccc", alpha=0.6, zorder=0)
    ax.tick_params(axis="x", length=0)

    ax.legend(loc="upper right", fontsize=9, frameon=True, framealpha=0.9)

draw_panel(ax_up, up,
           "Figure 7 — Upregulated (top 15): GWAS significance by gene")
draw_panel(ax_dn, down,
           "Figure 7 — Downregulated (top 10): GWAS significance by gene")

# Shared tier legend at the bottom
handles = [
    Line2D([0], [0], marker="o", color="w",
           markerfacecolor=TIER_COLOR["STRONG"],   markersize=12, label="STRONG"),
    Line2D([0], [0], marker="o", color="w",
           markerfacecolor=TIER_COLOR["MODERATE"], markersize=12, label="MODERATE"),
    Line2D([0], [0], marker="o", color="w",
           markerfacecolor=TIER_COLOR["LIMITED"],  markersize=12, label="LIMITED"),
    Line2D([0], [0], marker="o", color="w",
           markerfacecolor=TIER_COLOR["NONE"],     markersize=12, label="NONE"),
    Line2D([0], [0], marker="x", color="#555555", markersize=10,
           linestyle="None", label="No GWAS data"),
]
fig.legend(handles=handles, loc="lower center", ncol=5, frameon=False,
           fontsize=10, bbox_to_anchor=(0.5, -0.01))

plt.tight_layout(rect=[0, 0.04, 1, 0.98])

png = os.path.join(OUT, "Fig7_gwas_dot.png")
pdf = os.path.join(OUT, "Fig7_gwas_dot.pdf")
plt.savefig(png, dpi=150, bbox_inches="tight", facecolor="white")
plt.savefig(pdf,         bbox_inches="tight", facecolor="white")
plt.close()
print("Wrote:", png)
print("Wrote:", pdf)
