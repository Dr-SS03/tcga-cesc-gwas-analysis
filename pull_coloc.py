"""Pull Open Targets coloc per credible-set studyLocusId in chunks.
Usage: python pull_coloc.py <chunk_index> <chunk_size>
"""
import sys, requests, json, time, pandas as pd, os

OT = "https://api.platform.opentargets.org/api/v4/graphql"
OUT = "/sessions/vibrant-wizardly-thompson/mnt/outputs/level2"

QUERY_COLOC = """
query CS($id: String!) {
  credibleSet(studyLocusId: $id) {
    studyLocusId
    colocalisation(page:{index:0,size:50}) {
      rows {
        h3 h4 clpp colocalisationMethod rightStudyType
        otherStudyLocus {
          studyLocusId studyType
          variant { id rsIds }
          study {
            id traitFromSource studyType publicationFirstAuthor publicationDate
            nCases nControls
            diseases { id name }
          }
        }
      }
    }
  }
}
"""

def main():
    chunk_i = int(sys.argv[1])
    chunk_n = int(sys.argv[2])

    cs_df = pd.read_csv(f"{OUT}/ot_credible_sets.csv")
    start = chunk_i * chunk_n
    end   = min(start + chunk_n, len(cs_df))
    sub = cs_df.iloc[start:end]
    print(f"Chunk {chunk_i}: rows {start}..{end-1} of {len(cs_df)}")

    rows_out = []
    for _, row in sub.iterrows():
        sid = row['studyLocusId']
        sym = row['querySymbol']
        try:
            r = requests.post(OT, json={"query":QUERY_COLOC, "variables":{"id":sid}}, timeout=30).json()
            if 'errors' in r:
                continue
            crows = ((r.get('data') or {}).get('credibleSet') or {}).get('colocalisation', {}).get('rows', [])
            for c in crows:
                other = (c.get('otherStudyLocus') or {})
                ostudy = other.get('study') or {}
                ovar = other.get('variant') or {}
                o_rsids = ovar.get('rsIds') or []
                rows_out.append({
                    "querySymbol": sym,
                    "left_studyLocusId": sid,
                    "left_studyType":   row['studyType'],
                    "left_studyId":     row['studyId'],
                    "left_trait":       row['trait'],
                    "left_biosample":   row['biosample'],
                    "left_rsId":        row.get('rsId'),
                    "left_variant_id":  row.get('variant_id'),
                    "left_beta":        row.get('beta'),
                    "left_se":          row.get('se'),
                    "left_pMantissa":   row.get('pMantissa'),
                    "left_pExp":        row.get('pExp'),
                    "coloc_method":     c.get('colocalisationMethod'),
                    "coloc_h3":         c.get('h3'),
                    "coloc_h4":         c.get('h4'),
                    "coloc_clpp":       c.get('clpp'),
                    "right_studyType":  c.get('rightStudyType'),
                    "right_studyLocusId": other.get('studyLocusId'),
                    "right_studyId":    ostudy.get('id'),
                    "right_trait":      ostudy.get('traitFromSource'),
                    "right_studyAuthor":ostudy.get('publicationFirstAuthor'),
                    "right_studyDate": ostudy.get('publicationDate'),
                    "right_nCases":     ostudy.get('nCases'),
                    "right_nControls":  ostudy.get('nControls'),
                    "right_diseases":   "; ".join([d['name'] for d in (ostudy.get('diseases') or [])]),
                    "right_rsId":       o_rsids[0] if o_rsids else None,
                    "right_variant_id": ovar.get('id'),
                })
        except Exception as e:
            print(f"  ! {sid}: {e}")
        time.sleep(0.05)

    out_df = pd.DataFrame(rows_out)
    out_path = f"{OUT}/ot_colocalization_chunk{chunk_i}.csv"
    out_df.to_csv(out_path, index=False)
    print(f"Wrote {len(out_df)} rows -> {out_path}")

if __name__ == "__main__":
    main()
