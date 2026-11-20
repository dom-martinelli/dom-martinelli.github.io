"""The four cell-identity gene sets, which reproduce the six-gene story
independently across all 13,994 genes."""
import pandas as pd, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = "/Users/dominiero/Documents/GitHub/dom-martinelli.github.io/assets/fig/emory/"
HUE = ["#3D7BB8", "#C4545C", "#00918A", "#B87C14", "#7B62A8"]
INK, SOFT, FAINT, GRID = "#1A1D1C", "#5A6160", "#8A918D", "#E4E7E4"
plt.rcParams.update({
    "font.size": 11, "axes.labelsize": 11, "xtick.labelsize": 10, "ytick.labelsize": 11,
    "font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial"],
    "axes.edgecolor": FAINT, "axes.linewidth": 0.8, "text.color": INK,
    "axes.labelcolor": INK, "xtick.color": SOFT, "ytick.color": SOFT,
    "figure.facecolor": "white", "savefig.facecolor": "white", "savefig.dpi": 200})

r = pd.read_csv("emory_gsea_results.csv")
r["Term"] = r.Term.str.replace("GO_Biological_Process_2021__", "", regex=False)
PICK = {
    "antimicrobial humoral immune response mediated by antimicrobial peptide (GO:0061844)":
        ("antimicrobial peptide response", "neutrophil granule products"),
    "antibacterial humoral response (GO:0019731)":
        ("antibacterial humoral response", "neutrophil granule products"),
    "regulation of lymphocyte differentiation (GO:0045619)":
        ("lymphocyte differentiation", "adaptive compartment"),
    "B cell activation (GO:0042113)":
        ("B cell activation", "the compartment IGHV3-15 belongs to"),
}
d = r[r.Term.isin(PICK)].copy()
d["label"] = [PICK[t][0] for t in d.Term]
d["gloss"] = [PICK[t][1] for t in d.Term]
d = d.sort_values("NES")
print(d[["label", "NES", "FDR q-val"]].to_string(index=False))

fig, ax = plt.subplots(figsize=(7.2, 3.9))
fig.subplots_adjust(top=0.70)
y = np.arange(len(d))
ax.barh(y, d.NES, color=[HUE[1] if v > 0 else HUE[0] for v in d.NES], height=0.6, zorder=3)
ax.axvline(0, color=INK, lw=1)
ax.set_yticks(y); ax.set_yticklabels(d.label)
lim = max(abs(d.NES)) * 1.75
ax.set_xlim(-lim, lim)
for i, (v, q, g) in enumerate(zip(d.NES, d["FDR q-val"], d.gloss)):
    off = 0.10 if v > 0 else -0.10
    ax.text(v + off, i, f"FDR {q:.3f}", va="center", fontsize=9.5, color=SOFT,
            ha="left" if v > 0 else "right")
    ax.text(-lim * 0.97 if v > 0 else lim * 0.97, i, g, va="center", fontsize=9.5,
            color=FAINT, ha="left" if v > 0 else "right")
ax.set_xlabel("normalised enrichment score")
for sp in ("top", "right", "left"): ax.spines[sp].set_visible(False)
ax.xaxis.grid(True, color=GRID, lw=0.8, zorder=0); ax.set_axisbelow(True)
fig.text(0.02, 1.30, "The same story, found a second way",
         transform=ax.transAxes, fontsize=13.5, va="bottom", ha="left")
fig.text(0.02, 1.02,
         "the six significant genes were five myeloid up and one B-cell down. running\n"
         "enrichment over all 13,994 genes, without picking any, puts neutrophil granule\n"
         "products up and the B-cell compartment down. nothing told it to.",
         transform=ax.transAxes, fontsize=10.5, color=SOFT, va="bottom", ha="left")
fig.savefig(OUT + "immune-axis.png", bbox_inches="tight")
print("wrote immune-axis.png")
