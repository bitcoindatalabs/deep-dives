# ⚡ Who Patches the Lightning Network? (paper 02, explained)

> **Status:** Published with the paper; data cutoff 2026-10-13
> **Interactive Report:** [`./index.html`](./index.html)
> **Paper:** [arXiv:2610.30350](https://arxiv.org/abs/2610.30350) · code and data: [bitcoindatalabs/ln-upgrade-dynamics](https://github.com/bitcoindatalabs/ln-upgrade-dynamics)

---

## 📌 What this page is
A short guide to the paper, with interactive charts. Nothing here is new analysis: every number and chart comes from
the aggregate data and the generated numbers file released with the paper.

### Findings
1. **A node's release line can be read from gossip,** by matching its announced feature bits against the source of
   every LND, Core Lightning, Eclair and LDK release since 2019 (exact for 132 of 136 CLN node–line pairs that state
   their version).
2. **Most operators upgrade within months;** half of LND nodes move within 88 days (CLN 137). Small nodes and nodes
   already behind lag.
3. **Platforms set the pace.** The three largest LND waves came about a day after Umbrel shipped a new LND version; the
   48 hours after an Umbrel or BTCPay release cover 4.4% of the time but hold 17% of LND upgrades.
4. **Advisories come late (median 256 days after the fix) and move few of the nodes still behind.** Of 12 testable
   disclosures, only Core Lightning's of July 2026 sped up upgrades, and only among nodes one line behind.
5. **Most exposed LND nodes stayed exposed** (71% two months after Lightning Labs' August 2026 batch), and Core
   Lightning's offline call was followed mostly by nodes already on the newest line.

---

## 📁 Files
* **[`index.html`](./index.html)**: the page (serve the folder over HTTP; it fetches `data/processed/paper02.json`).
* **`run.py`**: builds `data/processed/paper02.json` from a clone of the paper's repository (`data/*.json` and
  `paper/numbers.tex`). Run `python run.py --paper-repo /path/to/ln-upgrade-dynamics`.
* **`data/processed/paper02.json`**: the aggregates behind every chart. Aggregate only; no node is listed.
* Shared with the paper 01 page: `../../shared/css/explainer.css`, `../../shared/js/explainer-charts.js`.
