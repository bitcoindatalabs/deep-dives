# ⚡ The Summer Lightning Broke (a Little): the 2026 Lightning security wave, measured

> **Status:** Complete; data cutoff 2026-10-04 &bull; TABConf, October 11, 2026
> **Interactive Report:** [`./index.html`](./index.html)

---

## 📌 Investigation Overview
Between July and October 2026 every Lightning implementation (LND, Core Lightning, Eclair, LDK) shipped security fixes,
BTCPay Server leaked merchants' LND credentials, a DoS wave hit the Tor network, and Core Lightning's maintainers asked
operators to restart their nodes offline until a fix shipped. This deep dive measures what the network felt,
from daily gossip snapshots and every on-chain channel close.

### Findings
1. **The CLN outage was real and contained:** 22% of CLN nodes went dark within a day of the call (an ordinary day: 2.3%);
   other clients did not move. Half were back within a week; a third were dark five weeks later.
2. **Force-close spikes were single operators;** organic force closes on CLN channels doubled for two weeks.
3. **The public graph shrank by 38% of its channels** from Aug 1 to Oct 4, across all clients, led by large operators' exits.
4. **Hubs, not client shares, set the blast radius:** the Tor DoS wave cost the network twice the reachability of the
   CLN shutdown, and one hub (ACINQ) outweighs the entire CLN cohort.

---

## 📁 Artifacts & Pipeline
* **[`index.html`](./index.html)**: interactive report (serve the folder over HTTP; it fetches `data/processed/*.json`).
* **`run.py`**: builds `data/processed/*.json` from the local data lake and the companion paper's aggregates.
* **`data/processed/`**: lightweight aggregated datasets powering the page.
