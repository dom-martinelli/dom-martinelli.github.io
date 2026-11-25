"""Benchmark item audit: two panels, site style.

Numbers are the committed baselines in the Growth-MedQA release
(tests/baselines/*.json) and the output of scripts/curated_defect_report.py.
Nothing here is recomputed from item text, so the figure cannot drift from the
repository's own tests without the tests failing first.

Palette and rcParams copied from scripts/build_emory_figs.py, which is the house
style already used by every other figure on the site.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "fig", "benchmark-audit")
os.makedirs(OUT, exist_ok=True)

HUE = ["#3D7BB8", "#C4545C", "#00918A", "#B87C14", "#7B62A8"]
INK, SOFT, FAINT, GRID = "#1A1D1C", "#5A6160", "#8A918D", "#E4E7E4"
plt.rcParams.update({
    "font.size": 11, "axes.labelsize": 11, "axes.titlesize": 12,
    "xtick.labelsize": 10, "ytick.labelsize": 10, "legend.fontsize": 10,
    "font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial"],
    "axes.edgecolor": FAINT, "axes.linewidth": 0.8, "text.color": INK,
    "axes.labelcolor": INK, "xtick.color": SOFT, "ytick.color": SOFT,
    "figure.facecolor": "white", "savefig.facecolor": "white", "savefig.dpi": 200,
})

# panel A: what reached the 960 scored items
SCORED = 960
REACHED = [
    ("corrupted text", 74, HUE[1]),
    ("padded with a filler choice", 19, HUE[3]),
    ("unanswerable", 1, INK),
]
# panel B: the 144 identical stems whose keys disagree
DECOMP = [
    ("a different answer", 62, HUE[1]),
    ("spacing only", 32, FAINT),
    ("a typo", 25, FAINT),
    ("one copy corrupted", 16, FAINT),
    ("one truncating the other", 9, FAINT),
]

fig, (axA, axB) = plt.subplots(1, 2, figsize=(11.2, 3.5), gridspec_kw={"width_ratios": [1, 1.05]})

# ── A ───────────────────────────────────────────────────────────────────────
clean = SCORED - sum(n for _, n, _ in REACHED)
left = 0
axA.barh([0], [clean], color=GRID, edgecolor="white", height=0.52)
left = clean
for label, n, colour in REACHED:
    axA.barh([0], [n], left=[left], color=colour, edgecolor="white", height=0.52)
    left += n
axA.set_xlim(0, SCORED)
axA.set_ylim(-0.6, 1.5)
axA.set_yticks([])
axA.set_xticks([0, 240, 480, 720, 960])
axA.spines[["top", "right", "left"]].set_visible(False)
axA.set_xlabel("items in the scored benchmark")
axA.set_title("92 of 960 scored items carry a defect", loc="left", pad=16)

axA.annotate("92", xy=(clean + 46, 0.30), xytext=(clean - 30, 0.95),
             ha="right", color=INK, fontsize=11,
             arrowprops=dict(arrowstyle="-", color=SOFT, lw=0.8))
axA.text(clean / 2, 0, f"{clean} with no defect found", ha="center", va="center",
         color=SOFT, fontsize=10)
# the three defect slices are slivers at this scale, so they get a real legend
# with swatches rather than a line of text no colour maps onto
from matplotlib.patches import Patch
axA.legend(handles=[Patch(facecolor=c, label=f"{l}  {n}") for l, n, c in REACHED],
           loc="upper left", bbox_to_anchor=(0, -0.30), ncol=1, frameon=False,
           handlelength=0.9, handleheight=0.9, labelspacing=0.35,
           borderpad=0, labelcolor=SOFT, fontsize=9.5)

# ── B ───────────────────────────────────────────────────────────────────────
labels = [l for l, _, _ in DECOMP]
vals = [n for _, n, _ in DECOMP]
colours = [c for _, _, c in DECOMP]
ypos = list(range(len(labels)))[::-1]
axB.barh(ypos, vals, color=colours, edgecolor="white", height=0.62)
for y, v in zip(ypos, vals):
    axB.text(v + 1.5, y, str(v), va="center", color=SOFT, fontsize=10)
axB.set_yticks(ypos)
axB.set_yticklabels(labels)
axB.set_xlim(0, 72)
axB.set_xticks([0, 20, 40, 60])
axB.spines[["top", "right", "left"]].set_visible(False)
axB.set_xlabel("identical questions, of 144")
axB.set_title("the same question keyed two ways, and why", loc="left", pad=16)


fig.subplots_adjust(left=0.055, right=0.985, top=0.80, bottom=0.34, wspace=0.42)
fig.text(0.775, 0.055, "only the top bar is a disagreement about medicine",
         color=SOFT, fontsize=9.5, ha="center")
path = os.path.join(OUT, "audit-overview.png")
fig.savefig(path)
print("wrote", os.path.normpath(path))
