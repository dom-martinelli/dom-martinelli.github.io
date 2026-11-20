"""GSEA on the Emory diabetes-medication contrast, ranked by the DESeq2 stat.

The notebook's only waterfall came from a different, 8-sample senescence dataset.
This runs the same kind of analysis on the cohort the card is about.
"""
import json, urllib.request, pandas as pd, numpy as np

D = "/Users/dominiero/bioinfo/Emory_Vascular/"
res = pd.read_csv(D + "DESeq2_results.csv", index_col=0)
res = res[res.baseMean >= 10].dropna(subset=["stat"])
print("genes with stat, baseMean>=10:", len(res))

ids = [i.split(".")[0] for i in res.index]
sym = {}
for k in range(0, len(ids), 1000):
    chunk = ids[k:k+1000]
    body = urllib.parse.urlencode({"ids": ",".join(chunk), "fields": "symbol",
                                   "species": "human"}).encode()
    req = urllib.request.Request("https://mygene.info/v3/gene", data=body)
    for g in json.load(urllib.request.urlopen(req, timeout=120)):
        if g.get("symbol"): sym[g["query"]] = g["symbol"]
    print(f"  mapped {len(sym)} / {min(k+1000,len(ids))}", flush=True)

res["Symbol"] = [sym.get(i.split(".")[0]) for i in res.index]
rank = (res.dropna(subset=["Symbol"])[["Symbol", "stat"]]
          .drop_duplicates("Symbol").sort_values("stat", ascending=False))
print("ranked genes:", len(rank))
rank.to_csv("emory_rank.csv", index=False)
