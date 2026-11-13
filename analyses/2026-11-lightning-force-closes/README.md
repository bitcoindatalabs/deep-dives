# ⚡ What Does It Cost to Force-Close a Lightning Channel? (paper 03, explained)

> **Paper:** [arXiv:2611.16311](https://arxiv.org/abs/2611.16311) · data cutoff 2026-10-31 (block 974,041)
> **Interactive Report:** [`./index.html`](./index.html)
> **Paper code and data:** [bitcoindatalabs/ln-force-close-costs](https://github.com/bitcoindatalabs/ln-force-close-costs)

---

## 📌 What this page is
A short guide to Paper 03 (*What Does It Cost to Force-Close a Lightning Channel? Evidence from 974,000 Channel
Closes, 2018–2026*), with interactive charts. Nothing here is new analysis: every number and chart comes from the
aggregate data and `numbers.tex` generated in the paper repository.

### Findings
1. **Fee spikes do not bring a wave of force closes.** In a spike week and the next, public force closes were 0.97
   times the four weeks before, against 1.02 after ordinary weeks.
2. **A force close costs two to six times a cooperative close, and days of locked funds.** The closer waits a median
   1.7 days; the wait outweighs the fees only in low-fee years.
3. **When fees spike, HTLC timeouts run late, but few payments were lost.** In 2023, 18.2% confirmed over 40 blocks
   late; since 2021, forwarding nodes lost 38 payments.
4. **Owners abandoned their anchors, and no third party sweeps taproot ones.** Owners spent 5% of 2026's P2WSH
   anchors; sweepers took the rest, and miners most of its value.
5. **Force closes became rarer per channel, and most now happen off the public graph.** 35% of public channels funded
   in 2019 were force-closed within a year; 17% of 2025's.

### Writing rules followed (specific to this page)
* The break-even chart's yearly values come from the paper's released `costs.json`; the paper states 2025, 2026, the
  2019–2024 range and the whole period, and `run.py` asserts all of them.
* The one-year cohort shares are the paper's `CohortOneYear*` macros.
* The nodes in the 2026 pre-anchor cluster, the dominant sweeper and the staged test pairs are not named.

---

## 📁 Files
* **[`index.html`](./index.html)**: the page (serve the folder over HTTP; it fetches `data/processed/paper03.json`).
* **`run.py`**: builds `data/processed/paper03.json` from the paper's repository (`data/*.json` and
  `paper/numbers.tex`). Run `python3 run.py --paper-repo /path/to/ln-force-close-costs`.
* **`data/processed/paper03.json`**: the aggregates behind every chart. Aggregate only; no node, channel, transaction
  ID or address is listed.
* Shared with papers 01 and 02: `../../shared/css/explainer.css`, `../../shared/js/explainer-charts.js`.
