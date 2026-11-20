"""Does the clustermap workflow manufacture significance on pure noise?

Emory's shape: 200 participants, 17.5% on a medication, ~14,000 genes.
Here the label is assigned at random and the expression is pure noise, so the
true answer is always "no association". Then run the standard workflow:
  select genes that differ by the label  ->  cluster participants on those genes
  ->  cut the tree in two  ->  Fisher test the cut against the same label.
"""
import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.stats import ttest_ind, fisher_exact
import pandas as pd

rng = np.random.default_rng(7)
N, G, RATE, TOPK, REPS = 200, 2000, 0.175, 6, 400
hon, circ = [], []
for _ in range(REPS):
    X = rng.standard_normal((N, G))             # pure noise, no structure at all
    y = (rng.random(N) < RATE).astype(int)      # label unrelated to X
    t, p = ttest_ind(X[y == 1], X[y == 0], axis=0)
    sel = np.argsort(p)[:TOPK]                  # the six "significant" genes

    Z = (X[:, sel] - X[:, sel].mean(0)) / X[:, sel].std(0)
    k = fcluster(linkage(Z, "ward"), 2, criterion="maxclust")
    tab = pd.crosstab(k, y).values
    if tab.shape == (2, 2):
        circ.append(fisher_exact(tab)[1])

    # the honest version: cluster on genes chosen without looking at the label
    hon_sel = rng.choice(G, TOPK, replace=False)
    Zh = (X[:, hon_sel] - X[:, hon_sel].mean(0)) / X[:, hon_sel].std(0)
    kh = fcluster(linkage(Zh, "ward"), 2, criterion="maxclust")
    tabh = pd.crosstab(kh, y).values
    if tabh.shape == (2, 2):
        hon.append(fisher_exact(tabh)[1])

circ, hon = np.array(circ), np.array(hon)
print(f"pure noise, {REPS} runs, true association is zero by construction\n")
print(f"  select on the label, then test it : {(circ<.05).mean():6.1%} of runs give p < 0.05")
print(f"  select genes at random instead    : {(hon<.05).mean():6.1%} of runs give p < 0.05")
print(f"\n  a correct test should sit at 5.0%")
print(f"  median p, circular: {np.median(circ):.3f}   honest: {np.median(hon):.3f}")
print(f"  runs reaching p < 0.015 (Emory's value), circular: {(circ<.015).mean():.1%}")

# ── figure ──────────────────────────────────────────────────────────────────
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
OUT = "/Users/dominiero/Documents/GitHub/dom-martinelli.github.io/assets/fig/emory/"
HUE = ["#3D7BB8", "#C4545C"]
INK, SOFT, FAINT, GRID = "#1A1D1C", "#5A6160", "#8A918D", "#E4E7E4"
plt.rcParams.update({
    "font.size": 11, "axes.labelsize": 11, "xtick.labelsize": 10.5, "ytick.labelsize": 10.5,
    "font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial"],
    "axes.edgecolor": FAINT, "axes.linewidth": 0.8, "text.color": INK,
    "axes.labelcolor": INK, "xtick.color": SOFT, "ytick.color": SOFT,
    "figure.facecolor": "white", "savefig.facecolor": "white", "savefig.dpi": 200})

fig, ax = plt.subplots(figsize=(7.2, 4.0))
fig.subplots_adjust(top=0.70)
bins = np.linspace(0, 1, 26)
ax.hist(circ, bins=bins, color=HUE[1], alpha=0.85, label="genes picked using the label", zorder=3)
ax.hist(hon, bins=bins, color=HUE[0], alpha=0.70, label="genes picked at random", zorder=2)
ax.axvline(0.05, color=INK, lw=1.2, ls=(0, (4, 3)), zorder=5)
ax.text(0.062, ax.get_ylim()[1] * 0.93, "p = 0.05", fontsize=10, color=INK, va="top")
ax.axvline(0.015, color=SOFT, lw=1.0, zorder=5)
ax.annotate("Emory's p = 0.015", xy=(0.015, ax.get_ylim()[1] * 0.52),
            xytext=(0.18, ax.get_ylim()[1] * 0.62), fontsize=10, color=SOFT,
            arrowprops=dict(arrowstyle="-", color=SOFT, lw=0.9))
ax.set_xlabel("Fisher exact p for the cluster split against the label")
ax.set_ylabel(f"runs (of {REPS})")
for sp in ("top", "right"): ax.spines[sp].set_visible(False)
ax.yaxis.grid(True, color=GRID, lw=0.8, zorder=0); ax.set_axisbelow(True)
ax.legend(frameon=False, loc="upper right", bbox_to_anchor=(1.0, 0.88))
fig.text(0.015, 1.30, "The same workflow on data with nothing in it",
         transform=ax.transAxes, fontsize=13.5, va="bottom")
fig.text(0.015, 1.02,
         f"{REPS} runs of pure noise, 200 fake participants, a label assigned by coin flip.\n"
         f"select six genes on that label, cluster, cut in two, test the same label:\n"
         f"{(circ<.05).mean():.0%} of runs come out significant. pick the six genes at random "
         f"instead and it is {(hon<.05).mean():.0%}.",
         transform=ax.transAxes, fontsize=10.5, color=SOFT, va="bottom")
fig.savefig(OUT + "circularity.png", bbox_inches="tight")
print("wrote circularity.png")
