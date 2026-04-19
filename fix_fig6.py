"""Regenerate Figure 6 (Top 25 DEGs with GWAS evidence tier annotation)
with proper spacing between y-tick gene labels and inline value annotations.

Previous version: on the right (downregulated) panel, the value label for the
top bar (DES, -9.19) rendered right next to the gene label ("DES [L]") with
no gap, producing visual overlap like "DES [L]9.19". Fix: (a) give the x-axis
a bit more headroom so value labels are not jammed against the y-axis, and
(b) place value labels strictly OUTSIDE the bar tip with a small pixel offset
so they cannot touch the y-tick label column.
"""
import os
import pickle
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.patches import Patch

OUT = "/sessions/vibrant-wizardly-thompson/mnt/outputs"

# -------- load --------
with open("/tmp/top25.pkl", "rb") as f:
    top25 = pickle.load(f)
with open("/tmp/gwas_annotation.pkl", "rb") as f:
    gwas = pickle.load(f)

# Merge tier info onto top25
tier_map = dict(zip(gwas["gene"], gwas["evidence_level"]))
top25 = top25.copy()
top25["tier"] = top25["gene_symbol"].map(tier_map).fillna("NONE")

# Tier styling
TIER_COLOR = {
    "STRONG":   "#2e7d32",   # green
    "MODERATE": "#f9a825",   # orange
    "LIMITED":  "#1f6fb4",   # blue
    "NONE":     "#9e9e9e",   # grey
}
TIER_SHORT = {"STRONG": "S", "MODERATE": "M", "LIMITED": "L", "NONE": "N"}

# Split up/down
up = top25[top25["direction"] == "up"].sort_values("log2fc", ascending=True).reset_index(drop=True)
down = top25[top25["direction"] == "down"].sort_values("log2fc", ascending=False).reset_index(drop=True)

# -------- plot --------
mpl.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor":   "#f8f9fa",
    "font.family":      "DejaVu Sans",
    "font.size":        11,
    "axes.spines.top":   False,
    "axes.spines.right": False,
})

fig, (ax_up, ax_dn) = plt.subplots(
    1, 2, figsize=(12, 7), dpi=150,
    gridspec_kw={"width_ratios": [1, 1], "wspace": 0.45},
)
fig.patch.set_facecolor("white")

def panel(ax, df, title, invert_x):
    labels = [f"{g} [{TIER_SHORT.get(t,'N')}]" for g, t in zip(df["gene_symbol"], df["tier"])]
    colours = [TIER_COLOR.get(t, "#9e9e9e") for t in df["tier"]]
    y = np.arange(len(df))
    ax.barh(y, df["log2fc"], color=colours, edgecolor="white", linewidth=0.7)

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlabel("Log$_{2}$ Fold Change", fontsize=11)
    ax.set_title(title, fontsize=12, fontweight="bold", pad=6)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", linestyle=":", color="#cccccc", alpha=0.7)

    # x-axis: give padding on the OUTSIDE end so value labels have room
    xmax = df["log2fc"].abs().max()
    pad = xmax * 0.28                           # 28 % headroom for value labels
    if invert_x:
        # downregulated: bars are negative. After invert_xaxis(), x=0 renders
        # on the LEFT of the panel (so the bar starts at the gene label) and
        # the negative tip renders on the RIGHT. Padding goes on the negative
        # side (which becomes the right side of the panel on screen).
        ax.set_xlim(-(xmax + pad), 0)
        ax.invert_xaxis()
    else:
        ax.set_xlim(0, xmax + pad)

    # Value annotations — always placed OUTSIDE the bar tip. With an inverted
    # x-axis, "more negative data" = "further right on screen", so we use
    # ha='left' to anchor the LEFT edge of the text just past the bar tip and
    # let the text grow further right (away from the bar).
    for yi, v in enumerate(df["log2fc"].values):
        if invert_x:
            x_text = v - xmax * 0.02
            ax.text(x_text, yi, f"{v:+.2f}", ha="left", va="center",
                    fontsize=9, color="#222222")
        else:
            x_text = v + xmax * 0.02
            ax.text(x_text, yi, f"{v:+.2f}", ha="left", va="center",
                    fontsize=9, color="#222222")

panel(ax_up, up,  "Top 15 Upregulated",  invert_x=False)
panel(ax_dn, down,"Top 10 Downregulated", invert_x=True)

fig.suptitle("Figure 6 — Top 25 DEGs with GWAS evidence tier annotation",
             fontsize=13, fontweight="bold", y=0.98)

# Shared tier legend at the bottom
legend_handles = [
    Patch(facecolor=TIER_COLOR["STRONG"],   label="STRONG"),
    Patch(facecolor=TIER_COLOR["MODERATE"], label="MODERATE"),
    Patch(facecolor=TIER_COLOR["LIMITED"],  label="LIMITED"),
    Patch(facecolor=TIER_COLOR["NONE"],     label="NONE"),
]
fig.legend(handles=legend_handles, loc="lower center",
           ncol=4, frameon=False, fontsize=10,
           bbox_to_anchor=(0.5, -0.01))

plt.tight_layout(rect=[0, 0.04, 1, 0.95])

png = os.path.join(OUT, "Fig6_gwas_bar.png")
pdf = os.path.join(OUT, "Fig6_gwas_bar.pdf")
plt.savefig(png, dpi=150, bbox_inches="tight", facecolor="white")
plt.savefig(pdf,         bbox_inches="tight", facecolor="white")
plt.close()
print("Wrote:", png)
print("Wrote:", pdf)
