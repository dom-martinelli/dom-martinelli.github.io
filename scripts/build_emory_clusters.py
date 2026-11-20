"""The Emory clustermap, rebuilt so the groups are visually separate.

Changes from the seaborn original and from my first remake:
  - the shared figstyle DIV ramp (teal / cream / magenta), the same one the
    sweetspace correlation heatmap uses, instead of RdYlBu_r or a custom blue-red
  - the two participant clusters drawn as two blocks with a real gap and a label,
    instead of one continuous panel you have to read a dendrogram to parse
  - the two gene blocks likewise split, so the B-cell gene is visibly apart
"""
import json, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster

D   = "/Users/dominiero/bioinfo/Emory_Vascular/"
OUT = "/Users/dominiero/Documents/GitHub/dom-martinelli.github.io/assets/fig/emory/"
HUE  = ["#3D7BB8", "#C4545C", "#00918A", "#B87C14", "#7B62A8"]
INK, SOFT, FAINT, GRID = "#1A1D1C", "#5A6160", "#8A918D", "#E4E7E4"
# figstyle's shared diverging ramp, as used by the sweetspace heatmap
DIV = LinearSegmentedColormap.from_list(
    "div", ["#045275", "#2F8F95", "#A9D8D0", "#F7F4EC", "#F7C9A6", "#E05C5C", "#AB1866"])
plt.rcParams.update({
    "font.size": 11, "axes.labelsize": 11, "xtick.labelsize": 10.5, "ytick.labelsize": 10.5,
    "font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial"],
    "axes.edgecolor": FAINT, "axes.linewidth": 0.8, "text.color": INK,
    "axes.labelcolor": INK, "xtick.color": SOFT, "ytick.color": SOFT,
    "figure.facecolor": "white", "savefig.facecolor": "white", "savefig.dpi": 200})

SYM = {"ENSG00000211943":"IGHV3-15","ENSG00000120306":"CYSTM1","ENSG00000163421":"PROK2",
       "ENSG00000124107":"SLPI","ENSG00000138772":"ANXA3","ENSG00000183019":"MCEMP1"}
g = pd.read_csv(D+"DESeq2_sigs.csv", index_col=0); g.index = [SYM[i] for i in g.index]
md = pd.read_csv(D+"Clinical/Modified_Emory_Clinical_Data.csv")
md = md[md.individualID.isin(g.columns)].set_index("individualID")
md = md[~md.index.duplicated()]
cols = [c for c in g.columns if c in md.index]
g, md = g[cols], md.loc[cols]
dm = md["diabeticmed"].astype(int)
X = g.T; Z = (X - X.mean()) / X.std()

Ls = linkage(Z, method="ward", metric="euclidean")
ks = fcluster(Ls, 2, criterion="maxclust")
leaf = dendrogram(Ls, no_plot=True)["leaves"]
# keep dendrogram order, but split into the two clusters
blocks = [[i for i in leaf if ks[i] == k] for k in (1, 2)]
blocks.sort(key=len)                                  # small block on top
GENES = [["IGHV3-15"], ["SLPI", "ANXA3", "MCEMP1", "PROK2", "CYSTM1"]]

fig = plt.figure(figsize=(6.9, 7.6))
gs = fig.add_gridspec(2, 3, height_ratios=[len(blocks[0]), len(blocks[1])],
                      width_ratios=[0.45, 1, 5], hspace=0.055, wspace=0.055,
                      left=0.26, right=0.775, top=0.775, bottom=0.215)
VM = 2.5
for bi, rows in enumerate(blocks):
    sub = Z.iloc[rows]
    ax_s = fig.add_subplot(gs[bi, 0])
    ax_s.imshow(dm.iloc[rows].values.reshape(-1, 1), aspect="auto", vmin=0, vmax=1,
                interpolation="nearest",
                cmap=LinearSegmentedColormap.from_list("s", ["#ECEAE4", HUE[3]]))
    ax_s.set_xticks([]); ax_s.set_yticks([])
    for sp in ax_s.spines.values(): sp.set_visible(False)
    rate = dm.iloc[rows].mean()
    ax_s.set_ylabel(f"cluster {bi+1}   n = {len(rows)}\n{rate:.0%} on a medication",
                    fontsize=10, color=INK, labelpad=12, linespacing=1.6)
    for gi, genes in enumerate(GENES):
        ax = fig.add_subplot(gs[bi, gi + 1])
        im = ax.imshow(sub[genes].values, aspect="auto", cmap=DIV, vmin=-VM, vmax=VM,
                       interpolation="nearest")
        ax.set_yticks([])
        for sp in ax.spines.values(): sp.set_visible(False)
        if bi == len(blocks) - 1:
            ax.set_xticks(range(len(genes)))
            ax.set_xticklabels(genes, rotation=55, ha="right")
        else:
            ax.set_xticks([])
            ax.set_title("B cell" if gi == 0 else "myeloid", fontsize=10.5,
                         color=SOFT, pad=9)

cax = fig.add_axes([0.80, 0.50, 0.021, 0.21])
cb = fig.colorbar(im, cax=cax); cb.set_label("expression (z)", fontsize=10)
cb.outline.set_visible(False); cb.ax.tick_params(labelsize=9.5)
fig.add_artist(Rectangle((0.80, 0.435), 0.021, 0.021, color=HUE[3], transform=fig.transFigure))
fig.text(0.831, 0.4455, "on a diabetes\nmedication", fontsize=9.5, color=SOFT, va="center")

fig.text(0.035, 0.985, "Two blocks of genes, two blocks of people,", fontsize=14.5, va="top")
fig.text(0.035, 0.945, "and only one of the splits was free to disagree", fontsize=14.5, va="top")
fig.text(0.035, 0.898,
         "cluster 1 really is warmer across the myeloid genes, but it was defined by those\n"
         "genes, so it could not have come out otherwise. the open question was whether the\n"
         "medication stripe would follow it, and the stripe is scattered through both blocks.",
         fontsize=10.5, color=SOFT, va="top")
fig.text(0.035, 0.005,
         "Emory vascular cohort, AD Knowledge Portal. six genes past padj < 0.05 and "
         "|log$_2$FC| > 0.5 for\ndiabetes medication; Ward linkage on the participants. "
         "rows carry no identifiers.",
         fontsize=9, color=FAINT, va="bottom")
fig.savefig(OUT + "clusters.png", bbox_inches="tight")
print("cluster sizes", [len(b) for b in blocks],
      "rates", [round(dm.iloc[b].mean(), 3) for b in blocks])
