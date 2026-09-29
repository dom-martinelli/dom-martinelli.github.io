"""build_sirna_mods.py: sirna-1, modification frequencies in the training set, redrawn on the sea ramp.
Counts copied from cell 19 of ~/Projects/siRNA_efficacy/siRNA_efficacy_prediction.ipynb (the original bar chart)."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

SEA = LinearSegmentedColormap.from_list("sea", ["#B7E6A5", "#7CCBA2", "#46AEA0", "#089099", "#00718B", "#045275", "#003147"])
counts = {"2′-O-methyl": 376, "2′-fluoro": 188, "2′-deoxy": 72, "4′-thioribose": 64,
          "hexitol nucleic acid": 37, "locked nucleic acid": 37, "unlocked nucleic acid": 17}
plt.rcParams.update({"font.family": ["Helvetica", "Arial", "DejaVu Sans"], "font.size": 12})
names, vals = list(counts)[::-1], list(counts.values())[::-1]
fig, ax = plt.subplots(figsize=(7.2, 3.6))
top = max(vals)
ax.barh(names, vals, color=[SEA(0.25 + 0.75 * v / top) for v in vals], height=0.66)
for y, v in enumerate(vals):
    ax.text(v + 5, y, str(v), va="center", fontsize=11, color="#1f2a33")
ax.spines[["top", "right", "left"]].set_visible(False)
ax.tick_params(axis="y", length=0, labelcolor="#1f2a33"); ax.tick_params(axis="x", colors="#7b8794")
ax.set_xlabel("modified positions in the training siRNAs", color="#7b8794")
ax.set_xlim(0, top * 1.12)
fig.savefig("assets/fig/sirna-1.png", dpi=240, bbox_inches="tight", facecolor="white")
print("WROTE assets/fig/sirna-1.png")
