"""Figure 12 — CIL Level III-A classification heatmap.

Six evidence axes per gene:
  CRISPR | RNAi | GDSC drug | LINCS reversal | scRNA-seq compartment | Final tier
"""
import os, pandas as pd, numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.patches import Patch, FancyBboxPatch

OUT = "/sessions/vibrant-wizardly-thompson/mnt/outputs/level3a"
master = pd.read_csv(f"{OUT}/level3a_master_table.csv")

# Order: Strong first, then Moderate, then Level II only
RANK = {
    "Strong Level III-A": 0,
    "Moderate Level III-A": 1,
    "Moderate Level III-A (drug-response)": 2,
    "Moderate Level III-A (cell-context)":  3,
    "Level II only": 4,
}
master['rank'] = master['CIL_Level_III_A_status'].map(RANK).fillna(99)
master = master.sort_values(['rank','Gene']).reset_index(drop=True)

# ----- per-axis cell rendering -----
def crispr_cell(r):
    score = r['CRISPR_best_cerv']
    tier = r['CRISPR_tier']
    if pd.isna(score):
        return "—", "", "#9e9e9e"
    if score < -1.0:
        color = "#2e7d32"
    elif score < -0.5:
        color = "#f9a825"
    else:
        color = "#9e9e9e"
    return f"{score:+.2f}", f"{tier}", color

def rnai_cell(r):
    score = r['RNAi_best_cerv']
    tier = r['RNAi_tier']
    if pd.isna(score):
        return "—", "", "#9e9e9e"
    if score < -1.0:
        color = "#2e7d32"
    elif score < -0.5:
        color = "#f9a825"
    else:
        color = "#9e9e9e"
    return f"{score:+.2f}", f"{tier}", color

def gdsc_cell(r):
    n = int(r['GDSC_n_significant']) if not pd.isna(r['GDSC_n_significant']) else 0
    if n >= 10:
        color = "#2e7d32"
    elif n >= 3:
        color = "#f9a825"
    elif n >= 1:
        color = "#1f6fb4"
    else:
        color = "#9e9e9e"
    if n == 0:
        return "—", "", color
    top = (str(r['GDSC_top_drug']) or '?')[:18]
    return f"{n} drugs", f"top: {top}", color

def lincs_cell(r):
    # Panel-wide signature evidence — all genes get the same color
    return "panel rev.", "MG-132/olaparib/dasatinib", "#f9a825"

def scrna_cell(r):
    comp = r['scRNA_compartment']
    if pd.isna(comp): return "—", "", "#9e9e9e"
    color_map = {
        "Myeloid/inflammatory":     "#2e7d32",
        "Squamous/basal epithelial":"#2e7d32",
        "Progenitor / cycling":     "#2e7d32",
        "Lymphoid":                 "#f9a825",
        "Glandular epithelial":     "#f9a825",
        "Stromal":                  "#1f6fb4",
        "Endothelial":              "#1f6fb4",
        "Other":                    "#9e9e9e",
    }
    color = color_map.get(comp, "#9e9e9e")
    short_top = (str(r['scRNA_top_celltype']) or '?')[:22]
    return comp.replace('/inflammatory','').replace('Squamous/basal ',''), short_top, color

STATUS_COLOR = {
    "Strong Level III-A":                    "#2e7d32",
    "Moderate Level III-A":                  "#f9a825",
    "Moderate Level III-A (drug-response)":  "#f9a825",
    "Moderate Level III-A (cell-context)":   "#1f6fb4",
    "Level II only":                         "#9e9e9e",
}

mpl.rcParams.update({
    "font.family":"DejaVu Sans",
    "font.size":11,
    "figure.facecolor":"white",
})

n = len(master)
COLS = [
    ("CRISPR\n(Chronos cervical)",   crispr_cell),
    ("RNAi\n(DEMETER2 cervical)",    rnai_cell),
    ("Drug response\n(GDSC1+2)",     gdsc_cell),
    ("LINCS L1000\nreversers",       lincs_cell),
    ("scRNA-seq\ncompartment",       scrna_cell),
]

fig, ax = plt.subplots(figsize=(20, 1.4 + n*1.05), dpi=150)
GENE_X   = 0.0
DATA_X0  = 1.6
CELL_W   = 1.65
STATUS_X = DATA_X0 + len(COLS)*CELL_W + 0.10
STATUS_W = 1.95
ax.set_xlim(-0.1, STATUS_X + STATUS_W + 0.2)
ax.set_ylim(-0.6, n + 1.0)
ax.invert_yaxis()
ax.axis('off')

HEADER_Y = -0.25
ax.text(GENE_X, HEADER_Y, "Gene", fontsize=12, fontweight="bold", ha='left', va='center')
for i, (label, _) in enumerate(COLS):
    cx = DATA_X0 + i*CELL_W + CELL_W/2
    ax.text(cx, HEADER_Y, label, fontsize=10, fontweight="bold", ha='center', va='center')
ax.text(STATUS_X + STATUS_W/2, HEADER_Y, "CIL Level III-A", fontsize=12, fontweight="bold", ha='center', va='center')
ax.plot([-0.1, STATUS_X + STATUS_W + 0.2], [0.20, 0.20], color="#333333", linewidth=1.0)

for ri, row in master.iterrows():
    y = ri + 0.7
    ax.text(GENE_X, y, row['Gene'], fontsize=12, fontweight='bold', ha='left', va='center')
    for ci, (label, fn) in enumerate(COLS):
        cx = DATA_X0 + ci*CELL_W
        head, sub, color = fn(row)
        # Pill background
        box = FancyBboxPatch((cx+0.05, y-0.40), CELL_W-0.10, 0.80,
                             boxstyle="round,pad=0.02,rounding_size=0.10",
                             linewidth=0.0, facecolor=color, alpha=0.18, zorder=1)
        ax.add_patch(box)
        edge = FancyBboxPatch((cx+0.05, y-0.40), CELL_W-0.10, 0.80,
                              boxstyle="round,pad=0.02,rounding_size=0.10",
                              linewidth=1.0, facecolor='none', edgecolor=color, alpha=0.85, zorder=2)
        ax.add_patch(edge)
        ax.text(cx + CELL_W/2, y - (0.10 if sub else 0), head, ha='center',
                va='center', fontsize=10, fontweight='bold', color="#222222", zorder=3)
        if sub:
            ax.text(cx + CELL_W/2, y + 0.18, sub, ha='center', va='center',
                    fontsize=7.5, color="#444444", zorder=3)

    status = row['CIL_Level_III_A_status']
    sc = STATUS_COLOR.get(status, "#9e9e9e")
    badge = FancyBboxPatch((STATUS_X, y-0.42), STATUS_W, 0.84,
                           boxstyle="round,pad=0.02,rounding_size=0.10",
                           linewidth=1.4, facecolor=sc, edgecolor=sc, alpha=0.92, zorder=2)
    ax.add_patch(badge)
    short = status.replace("Strong Level III-A", "Strong\nLevel III-A")\
                  .replace("Moderate Level III-A (drug-response)", "Moderate III-A\n(drug-response)")\
                  .replace("Moderate Level III-A (cell-context)",  "Moderate III-A\n(cell-context)")\
                  .replace("Moderate Level III-A", "Moderate\nLevel III-A")
    ax.text(STATUS_X + STATUS_W/2, y, short, ha='center', va='center',
            fontsize=11, fontweight='bold', color='white', zorder=3)

fig.suptitle("Figure 12 — Causal Integration Ladder · Level III-A computational functional support",
             fontsize=13, fontweight='bold', y=0.99)
plt.figtext(0.5, 0.96,
            "Per-gene synthesis of CRISPR Chronos dependency · DEMETER2 RNAi · GDSC drug-IC50 correlations · "
            "LINCS L1000 signature reversal · CellxGene Census cell-type compartment",
            ha='center', va='top', fontsize=9.5, color="#444444")

legend_handles = [
    Patch(facecolor="#2e7d32", alpha=0.18, edgecolor="#2e7d32",
          label="Strong (CRISPR < −1.0 / ≥10 drug hits / on-pathway compartment)"),
    Patch(facecolor="#f9a825", alpha=0.18, edgecolor="#f9a825",
          label="Moderate (CRISPR < −0.5 / 3–9 drug hits / supportive compartment)"),
    Patch(facecolor="#1f6fb4", alpha=0.18, edgecolor="#1f6fb4",
          label="Limited (1–2 drug hits / off-pathway compartment)"),
    Patch(facecolor="#9e9e9e", alpha=0.18, edgecolor="#9e9e9e",
          label="Not significant"),
]
fig.legend(handles=legend_handles, loc='lower center', ncol=4, frameon=False,
           bbox_to_anchor=(0.5, -0.005), fontsize=9)

plt.tight_layout(rect=[0, 0.04, 1, 0.94])

png = os.path.join(OUT, "Fig12_level3a_classification.png")
pdf = os.path.join(OUT, "Fig12_level3a_classification.pdf")
plt.savefig(png, dpi=150, bbox_inches='tight', facecolor='white')
plt.savefig(pdf,         bbox_inches='tight', facecolor='white')
plt.close()
print("Wrote:", png)
print("Wrote:", pdf)
