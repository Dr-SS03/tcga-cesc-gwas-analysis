# TCGA-CESC Differential Expression + GWAS Integration + CIL Level II + Level III-A

Analysis pipeline integrating **TCGA-CESC** (cervical squamous cell carcinoma & endocervical adenocarcinoma) RNA-seq differential expression with **GWAS Catalog**, **GTEx cis-eQTLs**, **Open Targets colocalization**, **Mendelian randomization**, **DepMap CRISPR/RNAi**, **GDSC drug response**, **LINCS L1000 connectivity**, and **CellxGene Census cell-type assignment** to identify candidate driver genes under the Causal Integration Ladder (CIL) framework — Levels I, II, and III-A.

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

### Headline Level III-A result

| Tier | Genes |
|---|---|
| **Strong Level III-A** | CDC20, KRT6A |
| **Moderate Level III-A** | S100A9, S100A8, CDKN2A, PITX1, KRT5, SERPINB5 |

CDC20 is a near-universal CRISPR essential gene (Chronos < −1 in 100 % of 1,208 DepMap models; cervical lines −1.86 to −2.74) — a textbook mitotic-checkpoint vulnerability. KRT6A shows partial CRISPR dependency in 2/18 cervical lines plus 16 GDSC drug-response correlations and confirmed squamous epithelial compartment. The 6 Moderate-tier genes have functional support without CRISPR essentiality, biologically expected for inflammatory mediators (S100A8/A9 → myeloid/neutrophil compartment) and tumour suppressors (CDKN2A). SERPINB5 has the broadest drug-response signal (40 correlations p < 0.01), positive across PARP / PI3K / CDK / platinum classes — a chemo-resistance biomarker. LINCS therapeutic shortlist: MG-132 (proteasome / APC-Cdc20), GSK-1070916 (Aurora B/C), olaparib (PARP — converges with SERPINB5), selumetinib (MEK), scriptaid (HDAC), calcitriol (differentiation).

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
│  --- CIL Level II completion ---
├── pull_coloc.py                       Open Targets Platform GraphQL — coloc puller (chunked)
├── build_level2_table.py               Assembles the Level II master evidence table (CSV)
├── make_fig11_level2.py                Renders Fig 11 — Level II classification heatmap
├── append_level2_addendum.py           Appends Level II section to TCGA_CESC_Analysis_Report.docx
│
├── level2/                             Level II analysis outputs (reproducible artefacts)
│   ├── level2_master_table.csv         Master per-gene evidence + final classification
│   ├── Fig11_level2_classification.png Heatmap figure
│   ├── Fig11_level2_classification.pdf
│   ├── gtex_independent_eqtls.csv      GTEx v8 independent cis-eQTLs across all tissues
│   ├── gtex_best_eqtl_priority_tissue.csv
│   ├── ot_credible_sets.csv            Open Targets credible sets per gene
│   ├── ot_colocalization.csv           Open Targets QTL × disease-GWAS coloc (PP.H3, PP.H4)
│   └── mr_results_cervix_hpv.csv       Wald-ratio MR results vs HPV / cervical / CIN GWAS
│
│  --- CIL Level III-A completion (this addendum) ---
├── pull_depmap_crispr.py               DepMap 26Q1 CRISPR Chronos extraction (cervical × 8 genes)
├── build_level3a_table.py              Assembles the Level III-A master evidence table (CSV)
├── make_fig12_level3a.py               Renders Fig 12 — Level III-A classification heatmap
├── append_level3a_addendum.py          Appends Level III-A section to TCGA_CESC_Analysis_Report.docx
│
└── level3a/                            Level III-A analysis outputs (reproducible artefacts)
    ├── level3a_master_table.csv        Master per-gene evidence + final classification
    ├── Fig12_level3a_classification.png Heatmap figure
    ├── Fig12_level3a_classification.pdf
    ├── cervical_cell_lines.csv         26 cervical models from DepMap Model.csv
    ├── depmap_crispr_cervical.csv      Chronos scores: 18 cervical lines × 8 genes
    ├── depmap_crispr_pancancer_summary.csv  Pan-cancer dependency summary
    ├── depmap_rnai_cervical.csv        DEMETER2 RNAi: HeLa, ME-180, SiHa × 8 genes
    ├── depmap_rnai_pancancer_summary.csv
    ├── depmap_expression_8genes.csv    DepMap TPM expression for the 8 genes (1719 models)
    ├── gdsc_correlations_priority_drugs.csv  Spearman rho per (gene, drug)
    ├── gdsc_correlations_significant.csv     Filtered to p < 0.01
    ├── gdsc_cervical_priority_drugs.csv      GDSC IC50 raw subset (cervical × priority drug list)
    ├── lincs_top_reversers.csv         LINCS L1000 perturbagens reversing the cancer signature
    ├── lincs_top_mimickers.csv         LINCS L1000 perturbagens reproducing the cancer signature
    └── cellxgene_wmg_celltypes.csv     CellxGene Census per-cell-type expression (8 genes × all tissues)
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

### CIL Level III-A reproduction

```bash
# 0. (one-time) Pull DepMap 26Q1 CRISPR file (440 MB) and extract 8 priority genes × cervical lines
python pull_depmap_crispr.py            # writes level3a/depmap_crispr_cervical.csv

# 1. Build master evidence table (CRISPR + RNAi + GDSC + LINCS + scRNA-seq)
python build_level3a_table.py           # writes level3a/level3a_master_table.csv

# 2. Generate Figure 12 classification heatmap
python make_fig12_level3a.py            # writes level3a/Fig12_level3a_classification.png/.pdf

# 3. Append the Level III-A section to the existing Word report
python append_level3a_addendum.py       # appends to TCGA_CESC_Analysis_Report.docx in place
```

The master CSV (`level3a_master_table.csv`) and the figure are sufficient to reproduce all narrative claims. Re-pulling the source data (DepMap 26Q1 CRISPR, DEMETER2, GDSC, LINCS, CellxGene Census) requires internet access to the respective public APIs.

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
| **Fig 12** | CIL Level III-A classification heatmap — 8 priority genes × 5 evidence axes (CRISPR, RNAi, GDSC drug response, LINCS reversal, scRNA-seq compartment), with final tier badge |

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
* **DepMap Public 26Q1** — Chronos CRISPR gene effect (Pacini C et al. 2024, *Nat Commun*; https://depmap.org).
* **DEMETER2 v6** — combined RNAi gene dependency (Tsherniak A et al. 2017, *Cell*; figshare https://doi.org/10.6084/m9.figshare.7733923).
* **GDSC release 8.5** — fitted dose-response (Iorio F et al. 2016, *Cell*; https://www.cancerrxgene.org).
* **SigCom LINCS** — signature search API (Evangelista JE et al. 2022, *Nucleic Acids Res*; https://maayanlab.cloud/sigcom-lincs).
* **CellxGene Discover Census** — Where-My-Gene v2 API (CZI Cell Science; https://cellxgene.cziscience.com).
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

---

## CIL Level III-A decision rules

A gene is classified as **Strong Level III-A** if it has:
1. CRISPR dependency (Chronos < −0.5 in cervical lines or pan-cancer)
2. AND at least one of: RNAi support, ≥3 drug-response correlations, supportive scRNA-seq compartment

**Moderate Level III-A:** No CRISPR dependency but functional support from drug-response (≥3 hits) or supportive scRNA-seq compartment.
**Level II only:** Genetic evidence (Level II) but no functional support.
