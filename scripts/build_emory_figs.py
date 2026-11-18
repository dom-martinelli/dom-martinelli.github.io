"""Emory vascular cohort: remake the hierarchical-clustering figures in site style.

Source: Emory_Vasc_heatmaps.ipynb (Mar 2025). DESeq2 on `diabeticmed`, 200 subjects,
6 genes past padj<0.05 & |LFC|>0.5. No subject IDs are drawn: every row is one
participant, so the rows are left unlabelled and only aggregate counts are printed.
"""
import json
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
from scipy.stats import fisher_exact, mannwhitneyu

D   = "/Users/dominiero/bioinfo/Emory_Vascular/"
OUT = "/Users/dominiero/Documents/GitHub/dom-martinelli.github.io/assets/fig/emory/"
import os; os.makedirs(OUT, exist_ok=True)

HUE  = ["#3D7BB8", "#C4545C", "#00918A", "#B87C14", "#7B62A8"]
INK, SOFT, FAINT, GRID = "#1A1D1C", "#5A6160", "#8A918D", "#E4E7E4"
DIV = LinearSegmentedColormap.from_list("div", ["#2B5F8F", "#8FB4D4", "#F2F0EC",
                                                "#DC9A9E", "#A83A42"])
plt.rcParams.update({
    "font.size": 11, "axes.labelsize": 11, "axes.titlesize": 12,
    "xtick.labelsize": 10, "ytick.labelsize": 10, "legend.fontsize": 10,
    "font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial"],
    "axes.edgecolor": FAINT, "axes.linewidth": 0.8, "text.color": INK,
    "axes.labelcolor": INK, "xtick.color": SOFT, "ytick.color": SOFT,
    "figure.facecolor": "white", "savefig.facecolor": "white", "savefig.dpi": 200,
})

SYM = {"ENSG00000211943":"IGHV3-15","ENSG00000120306":"CYSTM1","ENSG00000163421":"PROK2",
       "ENSG00000124107":"SLPI","ENSG00000138772":"ANXA3","ENSG00000183019":"MCEMP1"}
ROLE = {"SLPI":"neutrophil / myeloid granule","ANXA3":"neutrophil granule",
        "MCEMP1":"myeloid activation","PROK2":"neutrophil-derived (Bv8)",
        "CYSTM1":"neutrophil granule","IGHV3-15":"B-cell immunoglobulin"}

# ── data ────────────────────────────────────────────────────────────────────
g  = pd.read_csv(D+"DESeq2_sigs.csv", index_col=0)
g.index = [SYM[i] for i in g.index]
md = pd.read_csv(D+"Clinical/Modified_Emory_Clinical_Data.csv")
md = md[md.individualID.isin(g.columns)].set_index("individualID")
md = md[~md.index.duplicated()]
cols = [c for c in g.columns if c in md.index]
g, md = g[cols], md.loc[cols]
dm = md["diabeticmed"].astype(int)

X = g.T                                  # subjects x genes, log1p normed counts
Z = (X - X.mean()) / X.std()

Lg = linkage(Z.T, method="average", metric="euclidean")
Ls = linkage(Z,   method="ward",    metric="euclidean")   # average gives 199/1; ward is what you use to ask "are there two patient groups"
Ls_avg = linkage(Z, method="average", metric="euclidean")
gene_order = dendrogram(Lg, no_plot=True)["leaves"]
subj_order = dendrogram(Ls, no_plot=True)["leaves"]
kg = fcluster(Lg, 2, criterion="maxclust")
ks = fcluster(Ls, 2, criterion="maxclust")

tab = pd.crosstab(ks, dm.values)
odds, pval = fisher_exact(tab.values)
rates = tab[1] / tab.sum(axis=1)

res = pd.read_csv(D+"DESeq2_results.csv", index_col=0).loc[list(SYM)]
res.index = [SYM[i] for i in res.index]

ks_avg = fcluster(Ls_avg, 2, criterion="maxclust")
tab_avg = pd.crosstab(ks_avg, dm.values)
_, p_avg = fisher_exact(tab_avg.values)

stats = {
    "average_linkage_sizes": [int(v) for v in tab_avg.sum(axis=1)], "average_linkage_p": float(p_avg),
    "n_subjects": int(len(cols)), "n_diabetic": int(dm.sum()),
    "gene_clusters": {int(k): [n for n, c in zip(Z.columns, kg) if c == k] for k in (1, 2)},
    "subject_cluster_sizes": [int(v) for v in tab.sum(axis=1)],
    "subject_cluster_diabetic_rate": [float(v) for v in rates],
    "fisher_p": float(pval), "fisher_or": float(odds),
}
print(json.dumps(stats, indent=2))

# ── figure 1: the heatmap ───────────────────────────────────────────────────
n_c1_dia = int(tab.loc[1, 1]); n_c1 = int(tab.sum(axis=1)[1]); n_dia = int(dm.sum())
stats.update(sensitivity=n_c1_dia / n_dia, ppv=n_c1_dia / n_c1,
             n_c1=n_c1, n_c1_diabetic=n_c1_dia)

fig = plt.figure(figsize=(6.6, 7.4))
gs = fig.add_gridspec(2, 2, height_ratios=[1, 7.5], width_ratios=[0.45, 10],
                      hspace=0.015, wspace=0.035, left=0.13, right=0.78,
                      top=0.86, bottom=0.26)

ax_d = fig.add_subplot(gs[0, 1])
dendrogram(Lg, ax=ax_d, color_threshold=0, no_labels=True,
           link_color_func=lambda k: SOFT)
ax_d.set_axis_off()

ax_s = fig.add_subplot(gs[1, 0])
ax_h = fig.add_subplot(gs[1, 1])
M = Z.values[np.ix_(subj_order, gene_order)]
im = ax_h.imshow(M, aspect="auto", cmap=DIV, vmin=-2.5, vmax=2.5, interpolation="nearest")
ax_h.set_xticks(range(len(gene_order)))
ax_h.set_xticklabels([Z.columns[i] for i in gene_order], rotation=55, ha="right",
                     fontsize=10.5)
ax_h.set_yticks([])
for sp in ax_h.spines.values(): sp.set_visible(False)

ax_s.imshow(dm.values[subj_order].reshape(-1, 1), aspect="auto", interpolation="nearest",
            cmap=LinearSegmentedColormap.from_list("s", ["#E8E6E1", HUE[3]]))
ax_s.set_xticks([]); ax_s.set_yticks([])
ax_s.set_ylabel(f"{len(cols)} participants", fontsize=10.5, color=SOFT, labelpad=8)
for sp in ax_s.spines.values(): sp.set_visible(False)

cax = fig.add_axes([0.805, 0.54, 0.022, 0.24])
cb = fig.colorbar(im, cax=cax)
cb.set_label("expression (z)", fontsize=10); cb.outline.set_visible(False)
cb.ax.tick_params(labelsize=9.5)
fig.add_artist(Rectangle((0.805, 0.475), 0.022, 0.022, color=HUE[3],
                         transform=fig.transFigure))
fig.text(0.838, 0.486, "on a diabetes\nmedication", fontsize=9.5, color=SOFT, va="center")

fig.text(0.13, 0.955, "Two blocks of genes, not two groups of people",
         fontsize=14.5, ha="left", va="top")
fig.text(0.13, 0.905,
         "the tree at the top splits one B-cell gene from five myeloid ones.\n"
         "nothing comparable happens down the side.",
         fontsize=10.5, ha="left", va="top", color=SOFT)
fig.text(0.13, 0.015,
         "Emory vascular cohort, AD Knowledge Portal. six genes past "
         "padj < 0.05 and |log$_2$FC| > 0.5\nfor diabetes medication. "
         "participant rows carry no identifiers.",
         fontsize=9, color=FAINT, ha="left", va="bottom")
fig.savefig(OUT + "clusters.png", bbox_inches="tight")
plt.close(fig)

# ── figure 1b: what the split is worth ──────────────────────────────────────
fig, ax = plt.subplots(figsize=(6.8, 3.7))
fig.subplots_adjust(top=0.70)
y = np.arange(2)
ax.barh(y, rates.values * 100, color=[HUE[1], HUE[0]], height=0.5, zorder=3)
base = dm.mean() * 100
ax.axvline(base, color=INK, lw=1.2, ls=(0, (4, 3)), zorder=4)
ax.text(base + 0.8, -0.72, f"cohort {base:.0f}%", fontsize=10, color=INK, va="center")
for i, (r, n) in enumerate(zip(rates.values, tab.sum(axis=1))):
    ax.text(max(r * 100, base) + 1.6, i, f"{r*100:.0f}%   n = {n}", va="center", fontsize=10.5, color=INK)
ax.set_yticks(y); ax.set_yticklabels(["cluster 1", "cluster 2"], fontsize=11)
ax.set_xlabel("participants on a diabetes medication (%)")
ax.set_xlim(0, max(rates.values * 100) + 13); ax.set_ylim(-0.95, 1.6)
ax.invert_yaxis()
for sp in ("top", "right", "left"): ax.spines[sp].set_visible(False)
ax.xaxis.grid(True, color=GRID, lw=0.8, zorder=0); ax.set_axisbelow(True)
ax.set_title("")
fig.text(0.015, 1.36, "The split is real and nearly useless", fontsize=13.5,
         transform=ax.transAxes, va="bottom", ha="left")
ax.text(0.015, 1.02, f"cluster 1 is {rates.values[0]/rates.values[1]:.1f}x enriched "
        f"(Fisher p = {pval:.3f}), and still catches only {n_c1_dia} of the "
        f"{n_dia} participants\non medication, with {n_c1 - n_c1_dia} of its "
        f"{n_c1} members not on any.",
        transform=ax.transAxes, fontsize=10.5, color=SOFT, va="bottom", ha="left")
fig.savefig(OUT + "separation.png", bbox_inches="tight")
plt.close(fig)

# ── figure 2: what the six genes are ────────────────────────────────────────
r = res.sort_values("log2FoldChange")
fig, ax = plt.subplots(figsize=(7.2, 4.4))
cols_ = [HUE[0] if v < 0 else HUE[1] for v in r.log2FoldChange]
yy = np.arange(len(r))
ax.barh(yy, r.log2FoldChange, xerr=r.lfcSE, height=0.6, color=cols_, zorder=3,
        error_kw=dict(ecolor=SOFT, lw=1.1, capsize=3))
ax.axvline(0, color=INK, lw=1)
ax.set_yticks(yy)
ax.set_yticklabels([f"{n}" for n in r.index], fontweight="bold")
for i, n in enumerate(r.index):
    ax.text(ax.get_xlim()[1], i, "  " + ROLE[n], va="center", fontsize=10, color=SOFT)
ax.set_xlabel("log$_2$ fold change, on diabetes medication vs not")
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.xaxis.grid(True, color=GRID, lw=0.8, zorder=0); ax.set_axisbelow(True)
ax.set_title("Five myeloid genes up, one B-cell gene down:\n"
             "a shift in which white cells are in the tube",
             fontsize=12.5, loc="left", pad=10)
fig.savefig(OUT + "genes.png", bbox_inches="tight")
plt.close(fig)

json.dump(stats, open(OUT + "../../../scripts/_emory_stats.json", "w"), indent=2)
print("wrote", OUT + "clusters.png", "and genes.png")
