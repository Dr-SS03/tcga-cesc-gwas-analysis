# TCGA-CESC Differential Expression + GWAS Integration + CIL Level II

Analysis pipeline integrating **TCGA-CESC** (cervical squamous cell carcinoma & endocervical adenocarcinoma) RNA-seq differential expression with **GWAS Catalog**, **GTEx cis-eQTLs**, **Open Targets colocalization**, and **Mendelian randomization** to identify candidate driver genes with genetically-constrained causal evidence under the Causal Integration Ladder (CIL) framework.

---

## Project overview

Starting from TCGA-CESC STAR-normalised TPM expression (tumour vs. normal), this pipeline:

1. Runs differential expression (DE) analysis and extracts the top 25 DEGs (15 up-regulated, 10 down-regulated). *(Level I)*
2. Queries the **GWAS Catalog** for each DEG and annotates every gene with an evidence tier: `STRONG`, `MODERATE`, `LIMITED`, or `NONE`. *(Level I + GWAS annotation)*
3. Generates ten publication-ready figures (Fig 1 – Fig 10) and a consolidated Word report.
4. **CIL Level II completion** for the 8 highest-priority genes (S100A9, S100A8, CDKN2A, PITX1, KRT5, KRT6A, SERPINB5, CDC20):
   - cis-eQTL mapping via **GTEx Portal v8 API** (per-tissue independent eQTLs)
   - colocalization (PP.H4) via **Open Targets Platform v25 GraphQL** (eQTL × disease GWAS)
   - Wald-ratio Mendelian randomization where instrument + outcome are both available
   - cross-disease MR evidence from PubMed literature
   - final classification: `Full Level II`, `Partial Level II (eQTL + coloc)`, `Partial Level II (eQTL/GWAS only)`, or `Level I only`

The final deliverable is `TCGA_CESC_Analysis_Report.docx` together with PNG/PDF versions of every figure (including Fig 11 — CIL Level II classification heatmap) and reproducible CSVs of the underlying tables.

### Headline Level II result

| Tier | Genes |
|---|---|
| **Full Level II** | KRT5, S100A8, S100A9 |
| **Partial II — eQTL + coloc** | KRT6A, CDKN2A, PITX1, CDC20 |
| **Partial II — eQTL/GWAS only** | SERPINB5 |

Most striking signal: KRT5 and KRT6A cis-eQTLs (multi-tissue, including a blood plasma pQTL) colocalize with the Verma 2024 *Viral warts & HPV* GWAS (n = 21,895 cases / 403,003 controls) at **PP.H4 ≈ 0.97–0.98**. Wald-ratio MR for KRT5 (rs599466 skin eQTL): OR = 1.017 per 1-SD higher expression on HPV/wart risk (95% CI 1.012–1.023, p = 8.3×10⁻¹⁰), direction concordant with TCGA upregulation. HPV is the necessary cause of cervical cancer.

---

## Directory layout

```
code/                                   <-- THIS REPO ROOT (GitHub-ready)
├── README.md                           This file
├── requirements.txt                    pip dependencies
├── .gitignore
│
│  --- Level I figures + report (TCGA-CESC DE + GWAS Catalog) ---
├── build_report.py                     Assembles the final .docx report, embeds Fig 1–11
├── fix_fig3.py                         Volcano plot of DE results (Fig 3)
├── fix_fig45.py                        Top-25 bar charts with p-value stars (Fig 4 + Fig 5)
├── fix_fig6.py                         Top-25 bar charts with GWAS tier colouring (Fig 6)
├── fix_fig7.py                         GWAS significance bubble plot by gene (Fig 7)
├── fix_fig8.py                         GWAS loci lollipop + DE triangle scatter (Fig 8a/8b)
├── fix_fig9.py                         Gene × functional-category network (Fig 9)
│
│  --- CIL Level II completion (this addendum) ---
├── pull_coloc.py                       Open Targets Platform GraphQL — coloc puller (chunked)
├── build_level2_table.py               Assembles the Level II master evidence table (CSV)
├── make_fig11_level2.py                Renders Fig 11 — Level II classification heatmap
├── append_level2_addendum.py           Appends Level II section to TCGA_CESC_Analysis_Report.docx
│
└── level2/                             Level II analysis outputs (reproducible artefacts)
    ├── level2_master_table.csv         Master per-gene evidence + final classification
    ├── Fig11_level2_classification.png Heatmap figure
    ├── Fig11_level2_classification.pdf
    ├── gtex_independent_eqtls.csv      GTEx v8 independent cis-eQTLs across all tissues
    ├── gtex_best_eqtl_priority_tissue.csv  Best disease-relevant tissue eQTL per gene
    ├── ot_credible_sets.csv            Open Targets credible sets per gene (eQTL/pQTL/sQTL/tuQTL/sceQTL)
    ├── ot_colocalization.csv           Open Targets QTL × disease-GWAS coloc (PP.H3, PP.H4)
    └── mr_results_cervix_hpv.csv       Wald-ratio MR results vs HPV / cervical / CIN GWAS
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
# Level I (DE + GWAS Catalog figures)
python fix_fig3.py        # Fig 3  — volcano
python fix_fig45.py       # Fig 4 + Fig 5
python fix_fig6.py        # Fig 6  — bars with GWAS tier
python fix_fig7.py        # Fig 7  — bubble plot
python fix_fig8.py        # Fig 8  — lollipop + DE scatter
python fix_fig9.py        # Fig 9  — category network
```

### CIL Level II reproduction

```bash
# 1. Pull Open Targets Platform colocalization (chunked, 30 credible sets per chunk)
#    Inputs:  level2/ot_credible_sets.csv  (provided in this repo, regenerable from Platform API)
#    Outputs: level2/ot_colocalization_chunk{0..5}.csv  -> merged into ot_colocalization.csv
for i in 0 1 2 3 4 5; do python pull_coloc.py $i 30; done

# 2. Build master evidence table (combines GTEx eQTL + OT coloc + MR + literature)
python build_level2_table.py            # writes level2/level2_master_table.csv

# 3. Generate Figure 11 classification heatmap
python make_fig11_level2.py             # writes level2/Fig11_level2_classification.png/.pdf

# 4. Append the Level II section to the existing Word report
python append_level2_addendum.py        # appends to TCGA_CESC_Analysis_Report.docx in place

# 5. (optional) Rebuild the full Word report including Fig 11
python build_report.py
```

The scripts read the CSVs in `level2/` (or `/tmp/*.pkl` artefacts if present) and write output files to the same folder. Live API calls to GTEx Portal and Open Targets Platform GraphQL are only required to *regenerate* the CSVs from scratch — to reproduce the figures and report, the shipped CSVs are sufficient.

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
| **Fig 11** | CIL Level II classification heatmap — 8 priority genes × 6 evidence axes (DE, GWAS tier, eQTL, coloc HPV/cancer/immune, MR), with final tier badge |

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
* **GTEx Portal v8** — https://gtexportal.org/api/v2/ (cis-eQTL and pQTL).
* **Open Targets Platform v25** — https://api.platform.opentargets.org/api/v4/graphql (credible-set fine-mapping + colocalization).
* **Verma A et al. 2024** — Viral warts & HPV (PheCode 78) GWAS, GCST90475555 (primary HPV outcome for KRT5/KRT6A coloc + MR).
* **Koel M et al. 2024** — Cervical cancer GWAS, n = 9,229 cases / 490,304 controls (GCST90246359, GCST90246358).
* **Ma J et al. 2024**, *Nat Commun* — S100A8/A9 causal mediator of post-MI heart failure (TSMR + 3 cohorts). [doi:10.1038/s41467-024-46973-7](https://doi.org/10.1038/s41467-024-46973-7)
* **Mo J et al. 2024**, *Br J Haematol* — TSMR for S100A8 → primary immune thrombocytopenia (OR 0.856, p = 0.045). [doi:10.1111/bjh.19489](https://doi.org/10.1111/bjh.19489)
* **Zhang L et al. 2024**, *Int Immunopharmacol* — S100A8 risk factor for ulcerative colitis via MR. [doi:10.1016/j.intimp.2024.113765](https://doi.org/10.1016/j.intimp.2024.113765)
* **Li Y et al. 2025**, *Mediators Inflamm* — RSAD2 MR + coloc with cervical carcinoma in situ (PP.H4 = 0.62). [doi:10.1155/mi/2582989](https://doi.org/10.1155/mi/2582989). Methodological precedent for QTL × HPV-related coloc in cervical biology.
* Genome-wide significance threshold: p = 5 × 10⁻⁸.

---

## CIL Level II decision rules

A gene is classified as **Full Level II** if it has *all* of:
1. TCGA-CESC differential expression
2. A significant cis-eQTL instrument (p ≤ 1×10⁻⁴ in a disease-relevant tissue)
3. MR evidence in the biologically expected direction (this work or published)
4. Colocalization PP.H4 ≥ 0.70

**Partial Level II (eQTL + coloc):** (1) + (2) + (4) without satisfying (3).
**Partial Level II (eQTL/GWAS only):** (1) + (2) or GWAS tier annotation, without colocalization.
**Level I only:** meeting only (1).
