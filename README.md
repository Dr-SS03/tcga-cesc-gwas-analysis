# TCGA-CESC Differential Expression + GWAS Integration

Analysis pipeline integrating **TCGA-CESC** (cervical squamous cell carcinoma & endocervical adenocarcinoma) RNA-seq differential expression with **GWAS Catalog** evidence to identify candidate driver genes with supporting human genetic evidence.

---

## Project overview

Starting from TCGA-CESC STAR-normalised TPM expression (tumour vs. normal), this pipeline:

1. Runs differential expression (DE) analysis and extracts the top 25 DEGs (15 up-regulated, 10 down-regulated).
2. Queries the **GWAS Catalog** for each DEG and annotates every gene with an evidence tier: `STRONG`, `MODERATE`, `LIMITED`, or `NONE`.
3. Generates ten publication-ready figures (Fig 1 – Fig 10) and a consolidated Word report.

The final deliverable is `TCGA_CESC_Analysis_Report.docx` together with PNG/PDF versions of every figure and reproducible CSVs of the underlying tables.

---

## Directory layout

```
analysis of genes TGCA+GEo/
├── code/                          <-- YOU ARE HERE (this folder is GitHub-ready)
│   ├── build_report.py            Assembles the final .docx report, embeds all figures
│   ├── fix_fig3.py                Volcano plot of DE results (Fig 3)
│   ├── fix_fig45.py               Top-25 bar charts with p-value stars (Fig 4 + Fig 5)
│   ├── fix_fig6.py                Top-25 bar charts with GWAS tier colouring (Fig 6)
│   ├── fix_fig7.py                GWAS significance bubble plot by gene (Fig 7)
│   ├── fix_fig8.py                GWAS loci lollipop + DE triangle scatter (Fig 8a/8b)
│   ├── fix_fig9.py                Gene × functional-category network (Fig 9)
│   └── README.md                  This file
│
├── TCGA_CESC_Analysis_Report.docx Final narrative report
├── Fig1_*.png / .pdf              Study design / data flow
├── Fig2_*.png / .pdf              Sample-level QC
├── Fig3_volcano.png / .pdf        DE volcano
├── Fig4_top15_up.png / .pdf       Top-15 upregulated bar
├── Fig5_top10_down.png / .pdf     Top-10 downregulated bar
├── Fig6_gwas_bar.png / .pdf       Top-25 with GWAS tier colouring
├── Fig7_gwas_dot.png / .pdf       GWAS significance bubble plot
├── Fig8_gwas_loci_lollipop.*      GWAS loci (8a) + DE profile (8b)
├── Fig9_category_network.*        Gene × functional-category network
├── Fig10_*.png / .pdf             Summary / conclusion panel
│
└── CSV outputs (reproducible inputs for the scripts above)
    ├── differential_expression_full.csv
    ├── top15_upregulated.csv
    ├── top10_downregulated.csv
    ├── gwas_annotation.csv
    ├── gwas_raw_summary.csv
    ├── age_stratified_expression.csv
    ├── stage_expression.csv
    └── clinical_metadata.csv
```

---

## Dependencies

```bash
pip install pandas numpy scipy matplotlib python-docx adjustText
```

Tested with Python 3.11. Matplotlib ≥ 3.7 recommended (figures use `path_effects.withStroke`).

---

## How to reproduce the figures

Each `fix_figN.py` script is self-contained — it reads the CSVs (or `/tmp/*.pkl` artefacts if present) and writes a matching PNG + PDF into the outputs folder.

```bash
# From the project root:
cd "analysis of genes TGCA+GEo"

# Figures
python code/fix_fig3.py        # Fig 3  — volcano
python code/fix_fig45.py       # Fig 4 + Fig 5
python code/fix_fig6.py        # Fig 6  — bars with GWAS tier
python code/fix_fig7.py        # Fig 7  — bubble plot
python code/fix_fig8.py        # Fig 8  — lollipop + DE scatter
python code/fix_fig9.py        # Fig 9  — category network

# Final report (embeds every figure above)
python code/build_report.py
```

The scripts write to `./` (same directory). Each looks for pickled intermediates at `/tmp/gwas_annotation.pkl` and `/tmp/top25.pkl` first; if those are not present it falls back to the CSVs shipped alongside.

---

## Figure legend

| Figure | What it shows |
|---|---|
| **Fig 1** | Study design & data-flow diagram (TCGA-CESC → DE → GWAS) |
| **Fig 2** | Sample-level QC overview |
| **Fig 3** | Volcano plot of all DE genes |
| **Fig 4** | Top-15 upregulated genes (bar chart, log₂FC) |
| **Fig 5** | Top-10 downregulated genes (bar chart, log₂FC) |
| **Fig 6** | Top-25 DEGs colour-coded by GWAS evidence tier |
| **Fig 7** | Per-gene GWAS significance bubbles (size ∝ √n_assoc), split by direction |
| **Fig 8a** | Lollipop of GWAS p-values across the 25 genes; ★ marks MR-confirmed causal genes (S100A9, CDKN2A) |
| **Fig 8b** | DE profile of the 25 genes, coloured by functional category, labelled via leader lines |
| **Fig 9** | Gene × functional-category network with GWAS p-value annotations |
| **Fig 10** | Summary panel (priority list for follow-up) |

---

## Evidence tiers

Tiers are assigned per gene based on GWAS Catalog association data:

| Tier | Colour | Criteria |
|---|---|---|
| `STRONG`   | green  | Genome-wide-significant associations (p ≤ 5×10⁻⁸) with ≥ 2 independent loci |
| `MODERATE` | orange | Genome-wide-significant association at a single locus |
| `LIMITED`  | blue   | Sub-genome-wide-significant but suggestive (p ≤ 1×10⁻⁵) |
| `NONE`     | grey   | No GWAS hit returned |

---

## Notes on reproducibility

* The **upstream pipeline** (TCGA-GDC TPM retrieval, DE computation, live GWAS Catalog REST queries) was executed in an interactive session; only the downstream figure-regeneration scripts and report-builder are captured here. All intermediate tables are provided as CSVs so the figures are fully reproducible from this repo.
* `build_report.py` expects the 10 PNG figures to exist in the same directory. Run the `fix_figN.py` scripts first.
* MR-confirmed genes (S100A9, CDKN2A) are hard-coded from the report narrative — edit the `MR_CONFIRMED` set in `fix_fig8.py` if your follow-up work changes this list.

---

## Citation / data sources

* **TCGA-CESC** — Cancer Genome Atlas CESC cohort (GDC data portal).
* **GWAS Catalog** — https://www.ebi.ac.uk/gwas/ (queried by gene symbol).
* Genome-wide significance threshold: p = 5 × 10⁻⁸.
