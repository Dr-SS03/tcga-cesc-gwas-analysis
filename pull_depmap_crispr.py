"""Stream the DepMap 26Q1 CRISPRGeneEffect.csv and extract scores for our
8 priority genes across cervical cancer cell lines only. The full file is
~250MB; we don't need it all in memory.

Output: depmap_crispr_cervical.csv (rows = cell lines, cols = 8 genes + ModelID)
"""
import sys, os, csv, io, requests, pandas as pd

OUT = "/sessions/vibrant-wizardly-thompson/mnt/outputs/level3a"
URL = ("https://depmap.org/portal/download/api/download?"
       "file_name=downloads-by-canonical-id%2F26q1-public-3b44.1%2FCRISPRGeneEffect.csv"
       "&dl_name=CRISPRGeneEffect.csv&bucket=depmap-external-downloads")
HEADERS = {"User-Agent":"Mozilla/5.0"}

GENES = ["S100A9","S100A8","CDKN2A","PITX1","KRT5","KRT6A","SERPINB5","CDC20"]

cervical = pd.read_csv(f"{OUT}/cervical_cell_lines.csv")
cervical_ids = set(cervical['ModelID'].tolist())
print(f"Looking for {len(cervical_ids)} cervical models, {len(GENES)} genes")

# Stream the CSV
print("Starting download...")
r = requests.get(URL, headers=HEADERS, stream=True, timeout=300, allow_redirects=True)
r.raise_for_status()
print("  status=", r.status_code, "  content-length=", r.headers.get('content-length'))

# Read line by line
rows_kept = []
header = None
ncols = 0
gene_indices = []
for i, raw in enumerate(r.iter_lines(decode_unicode=True)):
    if not raw:
        continue
    parts = next(csv.reader([raw]))   # robust CSV split
    if header is None:
        header = parts
        ncols = len(header)
        # find columns matching "GENE (entrez)" pattern
        gene_indices = []
        for g in GENES:
            # match "GENE (123)" or "GENE"
            for j, col in enumerate(header):
                if col.startswith(g + " (") or col == g:
                    gene_indices.append((g, j, col))
                    break
        print(f"  Header has {ncols} cols. Found gene cols:")
        for g, j, c in gene_indices:
            print(f"    {g:10s}  col#{j}  '{c}'")
        continue
    # Data row: first col is ModelID
    model_id = parts[0]
    if model_id in cervical_ids:
        rec = {"ModelID": model_id}
        for g, j, _ in gene_indices:
            try:
                v = parts[j]
                rec[g] = float(v) if v else None
            except (ValueError, IndexError):
                rec[g] = None
        rows_kept.append(rec)
        print(f"    matched {model_id}  ({len(rows_kept)}/{len(cervical_ids)})")
    if i % 200 == 0 and i > 0:
        print(f"    processed {i} rows; kept {len(rows_kept)}")

print(f"\nDone. Kept {len(rows_kept)} cervical models.")
df = pd.DataFrame(rows_kept)
# Merge with metadata
meta = cervical[['ModelID','StrippedCellLineName','OncotreeSubtype']]
df = df.merge(meta, on='ModelID', how='left')
df = df[['ModelID','StrippedCellLineName','OncotreeSubtype'] + GENES]
df.to_csv(f"{OUT}/depmap_crispr_cervical.csv", index=False)
print(df.to_string())
