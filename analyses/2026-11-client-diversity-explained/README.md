# ⚡ Does Client Diversity Protect the Lightning Network? (paper 01, explained)

> **Status:** Published with the paper; data cutoff 2026-10-04
> **Interactive Report:** [`./index.html`](./index.html)
> **Paper:** [arXiv:2610.20952](https://arxiv.org/abs/2610.20952) · code and data: [bitcoindatalabs/ln-client-diversity](https://github.com/bitcoindatalabs/ln-client-diversity)

---

## 📌 What this page is
A short guide to the paper, with interactive charts. Nothing here is new analysis: every number and chart comes from
the aggregate data released with the paper.

### Findings
1. **LND dominates, and raw node counts hide how much.** LND runs 80% of public nodes (without one operator's managed
   fleet of about 2,000 tiny nodes) and holds 84% of public channel capacity.
2. **On 26 August 2026 a fifth of Core Lightning nodes went dark** after the maintainers' call to upgrade or restart
   `--offline`: 22% within two days, against 2.3% on an ordinary day. No other client moved.
3. **The rest of the network barely noticed.** Reachability fell 7.8 points; 4 of 94 ordinary two-day windows lost more,
   and the July Tor attack cost twice as much. Among CLN pairs it fell 24.5 points.
4. **Hubs, not cohorts, decide how far a failure reaches.** ACINQ's Eclair node alone outweighs all 619 routable CLN
   nodes four times over; 19 of the 20 most critical nodes run LND.
5. **Minority clients rely on LND about as much as their size implies,** against a capacity-matched null model.

---

## 📁 Files
* **[`index.html`](./index.html)**: the page (serve the folder over HTTP; it fetches `data/processed/paper01.json`).
* **`run.py`**: builds `data/processed/paper01.json` from a clone of the paper's repository (`data/*.json` and
  `paper/tables/table3_outage_effect.tex`). Run `python run.py --paper-repo /path/to/ln-client-diversity`.
* **`data/processed/paper01.json`**: the aggregates behind every chart.
* Shared with the paper 02 page: `../../shared/css/explainer.css`, `../../shared/js/explainer-charts.js`.
