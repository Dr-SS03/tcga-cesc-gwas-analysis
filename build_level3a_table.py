"""Assemble the master CIL Level III-A evidence table.

Inputs (already produced earlier in the session):
  - depmap_crispr_cervical.csv             (CRISPR Chronos in 18 cervical lines)
  - depmap_crispr_pancancer_summary.csv    (CRISPR pan-cancer dependency summary)
  - depmap_rnai_cervical.csv               (DEMETER2 RNAi in 3 cervical lines)
  - depmap_rnai_pancancer_summary.csv      (RNAi pan-cancer dependency)
  - gdsc_correlations_priority_drugs.csv   (Gene-expression × drug LN_IC50 Spearman rho)
  - gdsc_correlations_significant.csv      (filtered to p<0.01)
  - lincs_top_reversers.csv                (LINCS L1000 reversers of TCGA-CESC signature)
  - cellxgene_wmg_celltypes.csv            (CellxGene Census per-cell-type expression)

Output:
  - level3a_master_table.csv               (one row per gene, all evidence + classification)
"""
import os
import pandas as pd
import numpy as np

OUT = "/sessions/vibrant-wizardly-thompson/mnt/outputs/level3a"
GENES = ["S100A9","S100A8","CDKN2A","PITX1","KRT5","KRT6A","SERPINB5","CDC20"]

# ----- TCGA Level I + II carry-forward -----
LEVEL2 = pd.read_csv("/sessions/vibrant-wizardly-thompson/mnt/outputs/level2/level2_master_table.csv")
LEVEL2_status = dict(zip(LEVEL2['Gene'], LEVEL2['CIL_Level_II_Status']))

# ----- CRISPR -----
crispr_cerv = pd.read_csv(f"{OUT}/depmap_crispr_cervical.csv")
crispr_pan  = pd.read_csv(f"{OUT}/depmap_crispr_pancancer_summary.csv", index_col=0)
def crispr_for(g):
    """Return: best score in cervical, # cervical lines with score<-0.5, dependency tier."""
    if g not in crispr_cerv.columns:
        return None
    vals = crispr_cerv[g].dropna()
    if not len(vals):
        return None
    best = float(vals.min())
    n_cerv_dep = int((vals < -0.5).sum())
    n_cerv_strong = int((vals < -1.0).sum())
    pan_pct = float(crispr_pan.loc[g, 'pct_dep_lt_neg0_5']) if g in crispr_pan.index else None
    pan_n_strong = int(crispr_pan.loc[g, 'n_strong_dep_lt_neg1']) if g in crispr_pan.index else 0
    if best < -1.0 and n_cerv_strong >= 1:
        tier = "Strong dependency"
    elif best < -0.5:
        tier = "Dependency"
    else:
        tier = "Not dependent"
    return {
        "best_cerv":       best,
        "n_cerv_dep":      n_cerv_dep,
        "n_cerv_strong":   n_cerv_strong,
        "pan_pct_dep":     pan_pct,
        "pan_n_strong":    pan_n_strong,
        "tier":            tier,
    }

# ----- RNAi -----
rnai_cerv = pd.read_csv(f"{OUT}/depmap_rnai_cervical.csv")
rnai_pan  = pd.read_csv(f"{OUT}/depmap_rnai_pancancer_summary.csv", index_col=0)
def rnai_for(g):
    if g not in rnai_cerv.columns:
        return None
    vals = rnai_cerv[g].dropna()
    if not len(vals):
        return None
    best = float(vals.min())
    n_cerv_dep = int((vals < -0.5).sum())
    pan_pct = float(rnai_pan.loc[g, 'n_dep_lt_neg0_5']) / max(int(rnai_pan.loc[g,'n_lines']),1) * 100 if g in rnai_pan.index else None
    pan_n_dep = int(rnai_pan.loc[g, 'n_dep_lt_neg0_5']) if g in rnai_pan.index else 0
    if best < -1.0:
        tier = "Strong dependency"
    elif best < -0.5:
        tier = "Dependency"
    else:
        tier = "Not dependent"
    return {
        "best_cerv":  best,
        "n_cerv_dep": n_cerv_dep,
        "pan_pct_dep_lt05": pan_pct,
        "pan_n_dep":  pan_n_dep,
        "tier":       tier,
    }

# ----- GDSC drug correlations -----
gdsc = pd.read_csv(f"{OUT}/gdsc_correlations_priority_drugs.csv")
def gdsc_for(g):
    sub = gdsc[(gdsc['gene']==g) & (gdsc['p']<0.01)].copy()
    if not len(sub):
        return None
    sub = sub.sort_values('p').reset_index(drop=True)
    top = sub.iloc[0]
    return {
        "n_significant": len(sub),
        "top_drug":      top['drug'],
        "top_pathway":   top['pathway'],
        "top_target":    top['target'],
        "top_rho":       float(top['rho']),
        "top_p":         float(top['p']),
        "top5_drugs":    " | ".join(sub['drug'].head(5).tolist()),
    }

# ----- LINCS reversers -----
lincs_rev = pd.read_csv(f"{OUT}/lincs_top_reversers.csv")
# Derived from full signature (not per-gene), so flag as supportive for all genes
lincs_summary = {
    "n_reversers":      len(lincs_rev),
    "top_reverser":     lincs_rev.iloc[0]['perturbagen'] if len(lincs_rev) else None,
    "top_reverser_z":   float(lincs_rev.iloc[0]['z_sum']) if len(lincs_rev) else None,
    "top_in_HELA":      lincs_rev[lincs_rev['cell_line']=='HELA']['perturbagen'].head(3).tolist(),
}

# ----- scRNA-seq cell-type assignment -----
sc = pd.read_csv(f"{OUT}/cellxgene_wmg_celltypes.csv")
def scrna_for(g):
    sub = sc[(sc['gene']==g) & (sc['n_cells']>=100) & (sc['cell_type_id']!='CL:0000000')].copy()
    sub = sub[~sub['cell_type'].isin(['cell','animal cell','eukaryotic cell'])]
    sub['composite'] = sub['mean_expr'] * sub['pct_cells']
    sub = sub.sort_values('composite', ascending=False).drop_duplicates(subset=['cell_type'], keep='first')
    if not len(sub):
        return None
    top = sub.iloc[0]
    # Categorise compartment based on TOP 3 cell types (not just #1, since #1 can be specific)
    top3 = " | ".join(sub['cell_type'].head(3).tolist()).lower()
    if any(x in top3 for x in ['neutrophil','monocyte','macrophage','myelo','granulocyte','dendritic']):
        compartment = "Myeloid/inflammatory"
    elif any(x in top3 for x in ['pre-b','pro-b','b-ii cell','red blood','erythroid','erythrocyte','blast','progenitor','neural crest']):
        compartment = "Progenitor / cycling"
    elif any(x in top3 for x in ['keratinocyte','squamous','basal','epidermis','epithelial cell of esophagus','epithelial']):
        compartment = "Squamous/basal epithelial"
    elif any(x in top3 for x in ['t cell','b cell','lymphocyte','nk','plasma cell']):
        compartment = "Lymphoid"
    elif any(x in top3 for x in ['fibroblast','stromal','smooth muscle','myofibroblast']):
        compartment = "Stromal"
    elif any(x in top3 for x in ['endothelial']):
        compartment = "Endothelial"
    elif any(x in top3 for x in ['secretory','glandular']):
        compartment = "Glandular epithelial"
    else:
        compartment = "Other"
    return {
        "top_celltype":   top['cell_type'],
        "top_tissue":     top['tissue'],
        "top_n_cells":    int(top['n_cells']),
        "top_mean_expr":  float(top['mean_expr']),
        "top_pct_cells":  float(top['pct_cells']),
        "compartment":    compartment,
        "top3_celltypes": " | ".join(sub['cell_type'].head(3).tolist()),
    }

# ----- Decision rules -----
def classify(row):
    crispr_strong = row['CRISPR_tier'] == "Strong dependency"
    crispr_any    = row['CRISPR_tier'] in ("Strong dependency","Dependency")
    rnai_any      = row.get('RNAi_tier','-') in ("Strong dependency","Dependency")
    drug_n        = int(row.get('GDSC_n_significant') or 0)
    sc_supportive = row['scRNA_compartment'] in ("Myeloid/inflammatory","Squamous/basal epithelial","Progenitor / cycling","Lymphoid","Glandular epithelial")

    # Strong Level III-A: CRISPR dep + at least one supporting line
    n_supporting = sum([rnai_any, drug_n>=3, sc_supportive, True])  # LINCS supports the whole signature
    # LINCS counts toward the panel-wide signature evidence, not per-gene — handle below
    if crispr_strong and (rnai_any or drug_n>=3 or sc_supportive):
        return "Strong Level III-A"
    if crispr_any and (rnai_any or drug_n>=3 or sc_supportive):
        return "Strong Level III-A"
    # Moderate: no CRISPR dep, but functional support (drug or sc or LINCS)
    if (drug_n>=3 and sc_supportive):
        return "Moderate Level III-A"
    if drug_n>=3:
        return "Moderate Level III-A (drug-response)"
    if sc_supportive:
        return "Moderate Level III-A (cell-context)"
    return "Level II only"

# ----- Build table -----
rows = []
for g in GENES:
    cr = crispr_for(g) or {}
    rn = rnai_for(g) or {}
    dr = gdsc_for(g) or {}
    sc_ = scrna_for(g) or {}
    row = {
        "Gene":                 g,
        "Level_II_status":      LEVEL2_status.get(g, "—"),

        # CRISPR
        "CRISPR_best_cerv":     cr.get("best_cerv"),
        "CRISPR_n_cerv_dep":    cr.get("n_cerv_dep"),
        "CRISPR_n_cerv_strong": cr.get("n_cerv_strong"),
        "CRISPR_pan_pct_dep":   cr.get("pan_pct_dep"),
        "CRISPR_pan_n_strong":  cr.get("pan_n_strong"),
        "CRISPR_tier":          cr.get("tier","—"),

        # RNAi
        "RNAi_best_cerv":       rn.get("best_cerv"),
        "RNAi_n_cerv_dep":      rn.get("n_cerv_dep"),
        "RNAi_pan_n_dep":       rn.get("pan_n_dep"),
        "RNAi_tier":            rn.get("tier","—"),

        # GDSC drug
        "GDSC_n_significant":   dr.get("n_significant", 0),
        "GDSC_top_drug":        dr.get("top_drug"),
        "GDSC_top_pathway":     dr.get("top_pathway"),
        "GDSC_top_target":      dr.get("top_target"),
        "GDSC_top_rho":         dr.get("top_rho"),
        "GDSC_top_p":           dr.get("top_p"),
        "GDSC_top5":            dr.get("top5_drugs"),

        # LINCS (panel-wide evidence — same for every gene)
        "LINCS_top_reverser":         lincs_summary["top_reverser"],
        "LINCS_top_reverser_zsum":    lincs_summary["top_reverser_z"],
        "LINCS_top_HELA_reversers":   "; ".join(lincs_summary["top_in_HELA"]),

        # scRNA-seq
        "scRNA_top_celltype":   sc_.get("top_celltype"),
        "scRNA_top_tissue":     sc_.get("top_tissue"),
        "scRNA_compartment":    sc_.get("compartment"),
        "scRNA_top_n_cells":    sc_.get("top_n_cells"),
        "scRNA_top_mean_expr":  sc_.get("top_mean_expr"),
        "scRNA_top3_celltypes": sc_.get("top3_celltypes"),
    }
    row["CIL_Level_III_A_status"] = classify(row)
    rows.append(row)

master = pd.DataFrame(rows)
master.to_csv(f"{OUT}/level3a_master_table.csv", index=False)

COMPACT = ['Gene','Level_II_status','CRISPR_tier','CRISPR_best_cerv',
           'RNAi_tier','GDSC_n_significant','GDSC_top_drug','GDSC_top_pathway',
           'scRNA_compartment','scRNA_top_celltype','CIL_Level_III_A_status']
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 220)
pd.set_option('display.max_colwidth', 35)
print("=== COMPACT MASTER TABLE ===")
print(master[COMPACT].to_string(index=False))

print("\n=== Status counts ===")
print(master['CIL_Level_III_A_status'].value_counts())
