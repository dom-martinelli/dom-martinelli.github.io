# Handoff prompt for editing a portfolio notebook

Paste this into a fresh Claude Code session, then add the one-line task at the bottom.
Written 2026-10-26.

---

You are working on Dominic Martinelli's portfolio. Read these first, in order:

1. `/Users/dominiero/Library/Mobile Documents/iCloud~md~obsidian/Documents/Master/HOME.md`
   — the locked decisions. If something you are about to do contradicts a locked
   fact there, stop and say so instead of re-deriving it.
2. `Master/STYLE.md`, the **Figures** section — the figure rules, including the
   ones added 15 Oct 2026 after a run of bad figures. The ones that get broken most:
   run `audit(fig)` before every `savefig`; default to portrait because he reads on
   a phone; nothing below 11pt and titles 16pt or more; marks take the five saturated
   hues and never `PALETTES["pastel_classes"]`; a title that asserts a difference must
   be tested before it is written.
3. `~/Documents/GitHub/dom-martinelli.github.io/content/_archive.json` — the notebook
   inventory. Its `provenance` field is **unreliable**: his own siRNA and
   patient-involvement notebooks are labelled "unclear". Use it as a filter, never
   as a gate.

## The running theme

neuropsychiatry → Alzheimer's → insulin resistance → diabetes → GLP-1 agonists.
He wants every project read as part of that chain rather than as separate side
quests, because it is the specialism he is positioning on. When a piece of work
could point at several topics, point it here.

## How the site works

- Cards are JSON in `content/`, one per project. `python3 build.py` regenerates
  `index.html` and every page in `projects/`. Never hand-edit the HTML.
- `public: false` hides a card. `featured: <1-4>` puts it in the Selected work shelf
  at the top, in that rank order. `paper_only: true` keeps the project page but drops
  the tile, for work already on the Papers shelf.
- Figures live in `assets/fig/`. `figstyle.py` (copy it from
  `~/Documents/GitHub/patient-innovation-index/figstyle.py`) carries the house style:
  `use_style()`, `topography()` for density maps, `audit()`, `save()`.
- Before publishing prose, run the tell check in the session scratchpad, and read
  the `ai-tell-check` skill.

## Rules that have actually bitten

- **Test the premise, not just the numbers.** The bupropion card shipped claiming
  it entered a serotonin-dominated market. Drugs@FDA: bupropion approved 30 Dec 1985,
  Prozac 29 Dec 1987. Bupropion was first. A present-day count was being used to
  describe a 1985 decision.
- **Check a card against its own text.** growth-medqa carried 37 figures while
  saying it showed no scores; 16 were score panels.
- **Say what is measured.** Open Payments records reportable payments, not a
  detailing budget. A figure built on assumed inputs is labelled a scenario on the
  figure, not only in the limitations.
- Dollar signs in matplotlib text start math mode. Escape them as `\$`.

---

## Your task


---

## Appendix: the DiCAD result, if the task touches it

Run 2026-10-26. Olink proteomics, 196 subjects, 1,197 proteins, diabetic against
non-diabetic in an Alzheimer's cohort. Outputs in `~/bioinfo/DiCAD/out/`.

| model | proteins passing FDR 5% |
|---|---|
| unadjusted | 100 |
| + BMI, age, sex | 123 |
| + metformin | **9** |

**Do not quote the unadjusted numbers.** 36 of the 46 diabetic subjects are on
metformin, so diabetes and metformin are nearly collinear here. GDF15 was the
strongest unadjusted hit (d = +1.15) and metformin is independently known to raise
it; with metformin in the model it falls to q = 0.08 and is no longer significant.

The nine survivors are MRC2, GPNMB, ICAM2, CD79B, DPP6, PDCD1LG2 and three more,
which lean adhesion and immune rather than metabolic.

The defensible framing is the collinearity itself: in a real clinic cohort the
treated-disease signature cannot be separated from the treatment, and a proteomic
study that does not model medication is measuring the pharmacy. That is a better
card than a list of hits.
