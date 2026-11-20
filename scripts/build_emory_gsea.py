"""Emory GSEA: pathway bars + a redesigned enrichment/waterfall figure."""
import json, numpy as np, pandas as pd, gseapy as gp
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

OUT = "/Users/dominiero/Documents/GitHub/dom-martinelli.github.io/assets/fig/emory/"
HUE = ["#3D7BB8", "#C4545C", "#00918A", "#B87C14", "#7B62A8"]
INK, SOFT, FAINT, GRID = "#1A1D1C", "#5A6160", "#8A918D", "#E4E7E4"
plt.rcParams.update({
    "font.size": 11, "axes.labelsize": 11, "xtick.labelsize": 10,
    "ytick.labelsize": 10, "legend.fontsize": 10,
    "font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial"],
    "axes.edgecolor": FAINT, "axes.linewidth": 0.8, "text.color": INK,
    "axes.labelcolor": INK, "xtick.color": SOFT, "ytick.color": SOFT,
    "figure.facecolor": "white", "savefig.facecolor": "white", "savefig.dpi": 200,
})

rank = pd.read_csv("emory_rank.csv")
print("ranked genes:", len(rank))
pre = gp.prerank(rnk=rank, gene_sets=["GO_Biological_Process_2021"],
                 permutation_num=1000, seed=6, threads=4, min_size=15,
                 max_size=500, no_plot=True, outdir=None)
r = pre.res2d.copy()
for c in ("NES", "FDR q-val", "NOM p-val", "ES"):
    r[c] = pd.to_numeric(r[c], errors="coerce")
r["Term"] = r.Term.str.replace("GO_Biological_Process_2021__", "", regex=False)
r = r.dropna(subset=["NES"]).sort_values("NES")
r.to_csv("emory_gsea_results.csv", index=False)
sig = r[r["FDR q-val"] < 0.05]
print(f"{len(sig)} sets at FDR < 0.05 of {len(r)}")
print("\nTOP UP:"); print(r.tail(12)[["Term","NES","FDR q-val"]].iloc[::-1].to_string())
print("\nTOP DOWN:"); print(r.head(8)[["Term","NES","FDR q-val"]].to_string())

def short(t, n=52):
    t = t.split(" (GO:")[0]
    return t if len(t) <= n else t[:n-1] + "…"

# ── figure A: the pathway bars ──────────────────────────────────────────────
top = pd.concat([sig.tail(10), sig.head(5)]).drop_duplicates("Term").sort_values("NES")
fig, ax = plt.subplots(figsize=(7.4, 0.42 * len(top) + 2.3))
y = np.arange(len(top))
ax.barh(y, top.NES, color=[HUE[1] if v > 0 else HUE[0] for v in top.NES],
        height=0.62, zorder=3)
ax.axvline(0, color=INK, lw=1)
ax.set_yticks(y); ax.set_yticklabels([short(t) for t in top.Term])
ax.set_xlabel("normalised enrichment score\n(positive = higher in people on a diabetes medication)")
for sp in ("top", "right", "left"): ax.spines[sp].set_visible(False)
ax.xaxis.grid(True, color=GRID, lw=0.8, zorder=0); ax.set_axisbelow(True)
for sp in ("top", "right", "left"): ax.spines[sp].set_visible(False)
fig.subplots_adjust(top=0.80)
fig.text(0.02, 1.115, "Protein synthesis up, nuclear RNA export down",
         transform=ax.transAxes, fontsize=13.5, va="bottom", ha="left")
fig.text(0.02, 1.015,
         f"{len(sig)} of {len(r)} GO biological processes pass FDR < 0.05; the strongest are shown.\n"
         "two antimicrobial sets sit in the top band, and they are the only part that\n"
         "matches the neutrophil reading of the six significant genes.",
         transform=ax.transAxes, fontsize=10.5, color=SOFT, va="bottom", ha="left")
fig.savefig(OUT + "pathways.png", bbox_inches="tight"); plt.close(fig)

# ── figure B: the redesigned waterfall ──────────────────────────────────────
term = r.iloc[-1].Term                       # most positively enriched
key = [k for k in pre.results if k.endswith(term)][0]
d = pre.results[key]
hits = np.array(d["hits"]); run = np.array(d["RES"])
metric = rank.stat.values
n = len(metric)
peak = int(np.argmax(np.abs(run)))

fig, (a1, a2) = plt.subplots(2, 1, figsize=(7.2, 6.4), sharex=True,
                             gridspec_kw=dict(height_ratios=[1.35, 1], hspace=0.12))

lead = hits[hits <= peak] if run[peak] > 0 else hits[hits >= peak]
a1.axvspan(min(lead.min(), peak), max(lead.max(), peak), color=HUE[1], alpha=0.10, zorder=0)
a1.plot(run, color=HUE[1], lw=2.4, zorder=3)
a1.axhline(0, color=FAINT, lw=0.9)
a1.plot([peak], [run[peak]], "o", ms=7, color=HUE[1], zorder=4)
a1.annotate(f"peak {run[peak]:.2f}", (peak, run[peak]), textcoords="offset points",
            xytext=(12, -2), fontsize=10.5, color=INK, va="center")
a1.set_ylabel("running enrichment score")
for sp in ("top", "right"): a1.spines[sp].set_visible(False)
a1.text(0.985, 0.045, f"NES {r.iloc[-1].NES:.2f}   FDR < 0.001   "
        f"{len(lead)} of {len(hits)} genes in the leading edge",
        transform=a1.transAxes, ha="right", fontsize=10, color=SOFT)

a2.fill_between(np.arange(n), metric, 0, where=metric > 0, color=HUE[1],
                alpha=0.55, lw=0, zorder=2)
a2.fill_between(np.arange(n), metric, 0, where=metric <= 0, color=HUE[0],
                alpha=0.55, lw=0, zorder=2)
a2.axhline(0, color=FAINT, lw=0.9)
top_m = metric.max() * 1.10
a2.vlines(hits, top_m, top_m * 1.30, color=INK, lw=0.7, alpha=0.75, zorder=4)
a2.set_ylim(metric.min() * 1.08, top_m * 1.62)
a2.set_ylabel("DESeq2 test statistic")
a2.set_xlabel(f"all {n:,} genes, ranked")
a2.set_xlim(0, n)
for sp in ("top", "right"): a2.spines[sp].set_visible(False)
a2.text(0.012, 0.995, f"each tick is one of the {len(hits)} genes in this set",
        transform=a2.transAxes, fontsize=10, color=INK, va="top")
a2.text(0.012, 0.30, "higher on medication", transform=a2.transAxes,
        fontsize=10, color=HUE[1], va="center")
a2.text(0.988, 0.12, "lower on medication", transform=a2.transAxes,
        fontsize=10, color=HUE[0], ha="right", va="center")

fig.text(0.012, 1.025, short(term, 70), fontsize=13.5, transform=a1.transAxes,
         va="bottom")
fig.savefig(OUT + "waterfall-emory.png", bbox_inches="tight"); plt.close(fig)
print("\nwrote pathways.png and waterfall-emory.png; top term:", term)
