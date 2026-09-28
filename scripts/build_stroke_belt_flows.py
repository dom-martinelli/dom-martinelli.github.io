"""build_stroke_belt_flows.py: Medicare patient-county -> hospital-county flows for tools/stroke-belt-flows.html.

Recycles the PUBPOL 2130 Week 7 migration-flow pattern (origin/dest/count + centroids) on health data.
Inputs (all public, downloaded into DIR):
  hsaf2025.csv   CMS Hospital Service Area File 2025 (provider x patient ZIP; '*' = suppressed <11)
  zcta_county.txt  Census 2020 ZCTA-to-county relationship file (ZIP assigned to its largest-land county)
  hosp_info.csv  CMS Hospital General Information (facility ZIP)
  2020_Gaz_counties_national.txt  Census gazetteer (county centroids)
    python3 scripts/build_stroke_belt_flows.py DIR
"""
import json, sys
import pandas as pd

D = sys.argv[1]
BELT = {"37", "45", "13", "01", "28", "47", "05", "22"}   # NC SC GA AL MS TN AR LA

h = pd.read_csv(f"{D}/hsaf2025.csv", dtype=str)
h = h[h.TOTAL_CASES != "*"].copy()
h["cases"] = h.TOTAL_CASES.str.replace(",", "").astype(int)
z = pd.read_csv(f"{D}/zcta_county.txt", sep="|", dtype=str).dropna(subset=["GEOID_ZCTA5_20"])
z["a"] = z.AREALAND_PART.astype(float)
z = z.sort_values("a").drop_duplicates("GEOID_ZCTA5_20", keep="last")
z2c = dict(zip(z.GEOID_ZCTA5_20, z.GEOID_COUNTY_20))
info = pd.read_csv(f"{D}/hosp_info.csv", dtype=str)
hz = dict(zip(info["Facility ID"], info["ZIP Code"].str[:5]))
h["pc"] = h.ZIP_CD_OF_RESIDENCE.map(z2c)
h["hc"] = h.MEDICARE_PROV_NUM.map(hz).map(z2c)
h = h.dropna(subset=["pc", "hc"])

byc = h.groupby("pc").agg(n=("cases", "sum"))
byc["out"] = (h[h.pc != h.hc].groupby("pc").cases.sum() / byc.n).fillna(0)
byc["belt"] = byc.index.str[:2].isin(BELT)
print(byc.groupby("belt").out.median().round(3).to_dict())

g = pd.read_csv(f"{D}/2020_Gaz_counties_national.txt", sep="\t", dtype={"GEOID": str})
g.columns = [c.strip() for c in g.columns]
pos = {r.GEOID: (round(r.INTPTLONG, 4), round(r.INTPTLAT, 4), f"{r.NAME}, {r.USPS}") for r in g.itertuples()}
f = h[h.pc != h.hc].groupby(["pc", "hc"]).cases.sum().reset_index()
f = f[f.pc.str[:2].isin(BELT) & (f.cases >= 20) & f.pc.isin(pos) & f.hc.isin(pos)]
arcs = [[*pos[a][:2], *pos[b][:2], int(c), pos[a][2], pos[b][2]] for a, b, c in f[["pc", "hc", "cases"]].values]
cty = [[*pos[i][:2], round(float(r.out), 3), int(r.n), pos[i][2]] for i, r in byc[byc.belt].iterrows() if i in pos]
json.dump({"arcs": arcs, "counties": cty}, open("tools/data/stroke-belt-flows.json", "w"), separators=(",", ":"))
print(len(arcs), "arcs,", len(cty), "counties")
