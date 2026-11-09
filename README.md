# 🔬 Deep Dives

Bitcoin Data Labs measures the Bitcoin and Lightning networks from our own nodes. Each deep dive asks one question
and answers it with interactive charts, and each one stands on its own.

👉 **Read them at [bitcoindatalabs.github.io/deep-dives](https://bitcoindatalabs.github.io/deep-dives/)**

---

## ⚡ Analyses

Newest first.

**[Who Patches the Lightning Network?](https://bitcoindatalabs.github.io/deep-dives/analyses/2026-11-who-patches-lightning/)**
· 2023 – 2026<br>
A short guide to our paper *Who Patches the Lightning Network? Evidence from Release Lines in Gossip, 2023–2026*.
Nodes patch when their platform ships an update, not when an advisory comes out. Two months after Lightning Labs'
August 2026 advisories, 71% of the exposed LND nodes still ran an affected release.<br>
[arXiv:2610.30350](https://arxiv.org/abs/2610.30350) · [source](analyses/2026-11-who-patches-lightning/)

**[Does Client Diversity Protect Lightning?](https://bitcoindatalabs.github.io/deep-dives/analyses/2026-11-client-diversity-explained/)**
· Aug – Oct 2026<br>
A short guide to our paper *Does Client Diversity Protect the Lightning Network? Evidence from the 2026 Core Lightning
Shutdown*. When a fifth of Core Lightning nodes went offline in August 2026, the rest of the network barely noticed.
How far a failure spreads depends on the software of a few hubs, and 19 of the 20 most critical run LND.<br>
[arXiv:2610.20952](https://arxiv.org/abs/2610.20952) · [source](analyses/2026-11-client-diversity-explained/)

**[The Summer Lightning Broke (a Little)](https://bitcoindatalabs.github.io/deep-dives/analyses/2026-10-lightning-network-analysis/)**
· May – Oct 2026<br>
Every Lightning implementation shipped security fixes in summer 2026. This deep dive measures what the network felt,
from daily gossip and every on-chain channel close: a contained Core Lightning outage, force-close spikes from single
operators, and a Tor DoS wave that cost more reachability than the outage did. Presented at TABConf 2026.<br>
[source](analyses/2026-10-lightning-network-analysis/)

---

## 📡 Data

* **Sources:** our own Bitcoin Core node, for every on-chain transaction, and our own LND node, for daily snapshots
  of the public Lightning gossip graph.
* **In each analysis folder:** the page (`index.html`), the script that builds its data (`run.py`), and the
  aggregates the charts read (`data/processed/`). Raw data is not stored here.
* **Aggregates only.** We don't publish lists of vulnerable or unpatched nodes. The nodes we name are large public
  operators and hubs.
* **The paper guides add nothing new.** Every number comes from the paper's public repository, and `run.py`
  rebuilds the data from it.

## 💻 Run locally

```bash
git clone https://github.com/bitcoindatalabs/deep-dives.git
cd deep-dives
python3 -m http.server 8000      # then open http://localhost:8000/
```

Open the pages over HTTP, not as local files: they load their data with `fetch()`.

To rebuild a paper guide's data from the paper's repository:

```bash
cd analyses/2026-11-client-diversity-explained
python3 run.py --paper-repo /path/to/ln-client-diversity
```

## 🔗 Related

* Paper code and data: [ln-client-diversity](https://github.com/bitcoindatalabs/ln-client-diversity) ·
  [ln-upgrade-dynamics](https://github.com/bitcoindatalabs/ln-upgrade-dynamics)
* [Bitcoin Data Labs](https://bitcoindatalabs.org)
* Questions or corrections: open an issue, or write to
  [sorukumar@bitcoindatalabs.org](mailto:sorukumar@bitcoindatalabs.org).
