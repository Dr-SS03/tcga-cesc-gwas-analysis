"""Figure 11 — Causal Integration Ladder Level II classification heatmap.

Six evidence axes per gene:
  TCGA DE   |  GWAS tier  |  cis-eQTL  |  Coloc HPV  |  Coloc cancer/immune  |  Published MR
Final classification badge on the right.
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.patches import Patch, Rectangle, FancyBboxPatch

OUT = "/sessions/vibrant-wizardly-thompson/mnt/outputs/level2"
master = pd.read_csv(f"{OUT}/level2_master_table.csv")

# Order genes: Full Level II first, then Partial coloc, then Partial only
RANK = {
    "Full Level II":                       0,
    "Partial Level II (eQTL + coloc)":     1,
    "Partial Level II (eQTL + suggestive)":2,
    "Partial Level II (eQTL/GWAS only)":   3,
    "Level I only":                        4,
}
master['rank'] = master['CIL_Level_II_Status'].map(RANK)
master = master.sort_values(['rank','Gene']).reset_index(drop=True)

# ----- evidence cells -----
def tcga_cell(r):
    arrow = "▲" if r['TCGA_direction']=="up" else "▼"
    return arrow, f"log2FC={r['TCGA_log2FC']:+.2f}", "#2e7d32" if r['TCGA_direction']=='up' else "#c0392b"

TIER_COLOR = {"STRONG":"#2e7d32","MODERATE":"#f9a825","LIMITED":"#1f6fb4","NONE":"#9e9e9e"}
def gwas_cell(r):
    t = r['GWAS_tier']
    return t, "", TIER_COLOR.get(t, "#9e9e9e")

def eqtl_cell(r):
    p = r['eQTL_p_value']
    nes = r['eQTL_NES']
    rsid = r['eQTL_lead_SNP']
    if pd.isna(p):
        return "—", "", "#9e9e9e"
    # Color by significance bands
    if p <= 5e-8:    color = "#2e7d32"
    elif p <= 1e-5:  color = "#f9a825"
    else:            color = "#1f6fb4"
    return f"{rsid}", f"NES={nes:+.2f}\np={p:.1e}", color

def coloc_cell(h4, partner, label):
    if h4 is None or pd.isna(h4):
        return "n.s.", "", "#9e9e9e"
    color = "#2e7d32" if h4 >= 0.80 else "#f9a825" if h4 >= 0.70 else "#1f6fb4" if h4 >= 0.50 else "#9e9e9e"
    pstr = (str(partner) or "")
    if len(pstr) > 26:
        pstr = pstr[:24] + "…"
    return f"H4={h4:.2f}", pstr, color

def mr_cell(r):
    cnt = int(r['Published_MR_count']) if not pd.isna(r['Published_MR_count']) else 0
    if cnt > 0:
        return f"{cnt} pub MR", "", "#2e7d32"
    if not pd.isna(r['MR_OR']):
        return f"OR={r['MR_OR']:.3f}", f"p={r['MR_p_value']:.1e}", "#f9a825"
    return "—", "", "#9e9e9e"

STATUS_COLOR = {
    "Full Level II":                       "#2e7d32",
    "Partial Level II (eQTL + coloc)":     "#f9a825",
    "Partial Level II (eQTL + suggestive)":"#f9a825",
    "Partial Level II (eQTL/GWAS only)":   "#1f6fb4",
    "Level I only":                        "#9e9e9e",
}

# ----- figure layout -----
mpl.rcParams.update({
    "font.family":"DejaVu Sans",
    "font.size":11,
    "figure.facecolor":"white",
})

n = len(master)
COLS = [
    ("TCGA DE",          tcga_cell,  None),
    ("GWAS tier",        gwas_cell,  None),
    ("cis-eQTL",         eqtl_cell,  None),
    ("Coloc · HPV/cervix",lambda r: coloc_cell(r['Coloc_HPV_PP_H4'], r['Coloc_HPV_partner'], 'HPV'), None),
    ("Coloc · cancer",   lambda r: coloc_cell(r['Coloc_cancer_PP_H4'], r['Coloc_cancer_partner'], 'cancer'), None),
    ("Coloc · immune",   lambda r: coloc_cell(r['Coloc_immune_PP_H4'], r['Coloc_immune_partner'], 'immune'), None),
    ("MR evidence",      mr_cell,    None),
]
n_cols = len(COLS) + 1   # +1 for the status badge column

fig, ax = plt.subplots(figsize=(20, 1.4 + n*1.05), dpi=150)
GENE_X   = 0.0
DATA_X0  = 1.6
CELL_W   = 1.50
STATUS_X = DATA_X0 + len(COLS)*CELL_W + 0.10
STATUS_W = 1.80
ax.set_xlim(-0.1, STATUS_X + STATUS_W + 0.2)
ax.set_ylim(-0.5, n + 0.9)
ax.invert_yaxis()
ax.axis('off')

# Header
HEADER_Y = -0.2

ax.text(GENE_X, HEADER_Y, "Gene", fontsize=12, fontweight="bold", ha='left', va='center')
for i, (label, _, _) in enumerate(COLS):
    cx = DATA_X0 + i*CELL_W + CELL_W/2
    ax.text(cx, HEADER_Y, label, fontsize=10, fontweight="bold", ha='center', va='center')
ax.text(STATUS_X + STATUS_W/2, HEADER_Y, "CIL Level II", fontsize=12, fontweight="bold", ha='center', va='center')

# Header rule
ax.plot([-0.1, STATUS_X + STATUS_W + 0.2], [0.15, 0.15], color="#333333", linewidth=1.0)

# Rows
for ri, row in master.iterrows():
    y = ri + 0.65
    # Gene name
    ax.text(GENE_X, y, row['Gene'], fontsize=12, fontweight='bold', ha='left', va='center')
    # Cells
    for ci, (label, fn, _) in enumerate(COLS):
        cx = DATA_X0 + ci*CELL_W
        head, sub, color = fn(row)
        # Coloured pill background
        box = FancyBboxPatch((cx+0.05, y-0.38), CELL_W-0.10, 0.76,
                             boxstyle="round,pad=0.02,rounding_size=0.10",
                             linewidth=0.0, facecolor=color, alpha=0.18, zorder=1)
        ax.add_patch(box)
        # Edge
        edge = FancyBboxPatch((cx+0.05, y-0.38), CELL_W-0.10, 0.76,
                              boxstyle="round,pad=0.02,rounding_size=0.10",
                              linewidth=1.0, facecolor='none', edgecolor=color, alpha=0.85, zorder=2)
        ax.add_patch(edge)
        # Head text
        ax.text(cx + CELL_W/2, y - (0.10 if sub else 0), head, ha='center',
                va='center', fontsize=10, fontweight='bold', color="#222222", zorder=3)
        if sub:
            ax.text(cx + CELL_W/2, y + 0.18, sub, ha='center', va='center',
                    fontsize=7.5, color="#444444", zorder=3)
    # Status badge
    status = row['CIL_Level_II_Status']
    sc = STATUS_COLOR.get(status, "#9e9e9e")
    badge = FancyBboxPatch((STATUS_X, y-0.40), STATUS_W, 0.80,
                           boxstyle="round,pad=0.02,rounding_size=0.10",
                           linewidth=1.4, facecolor=sc, edgecolor=sc, alpha=0.92, zorder=2)
    ax.add_patch(badge)
    # Wrap status to 2 lines
    short = status.replace("Partial Level II (eQTL + coloc)", "Partial II\neQTL + coloc")\
                  .replace("Partial Level II (eQTL/GWAS only)", "Partial II\neQTL/GWAS")\
                  .replace("Partial Level II (eQTL + suggestive)", "Partial II\neQTL + sugg.")\
                  .replace("Full Level II", "Full\nLevel II")
    ax.text(STATUS_X + STATUS_W/2, y, short, ha='center', va='center',
            fontsize=11, fontweight='bold', color='white', zorder=3)

# Title
fig.suptitle("Figure 11 — Causal Integration Ladder · Level II classification of TCGA-CESC priority genes",
             fontsize=13, fontweight='bold', y=0.995)
plt.figtext(0.5, 0.96,
            "Per-gene synthesis of differential expression (TCGA-CESC) · GWAS Catalog tier · "
            "GTEx cis-eQTL · Open Targets colocalization (PP.H4) · Wald-ratio MR / published MR",
            ha='center', va='top', fontsize=9.5, color="#444444")

# Legend
legend_handles = [
    Patch(facecolor="#2e7d32", alpha=0.18, edgecolor="#2e7d32", label="Strong (PP.H4 ≥ 0.80 / p ≤ 5×10⁻⁸ / STRONG tier)"),
    Patch(facecolor="#f9a825", alpha=0.18, edgecolor="#f9a825", label="Moderate (PP.H4 0.70–0.80 / p ≤ 1×10⁻⁵ / MODERATE tier)"),
    Patch(facecolor="#1f6fb4", alpha=0.18, edgecolor="#1f6fb4", label="Limited (PP.H4 0.50–0.70 / suggestive / LIMITED tier)"),
    Patch(facecolor="#9e9e9e", alpha=0.18, edgecolor="#9e9e9e", label="Not significant / no evidence"),
]
fig.legend(handles=legend_handles, loc='lower center', ncol=4, frameon=False,
           bbox_to_anchor=(0.5, -0.005), fontsize=9)

plt.tight_layout(rect=[0, 0.04, 1, 0.94])

png = os.path.join(OUT, "Fig11_level2_classification.png")
pdf = os.path.join(OUT, "Fig11_level2_classification.pdf")
plt.savefig(png, dpi=150, bbox_inches='tight', facecolor='white')
plt.savefig(pdf,         bbox_inches='tight', facecolor='white')
plt.close()
print("Wrote:", png)
print("Wrote:", pdf)
