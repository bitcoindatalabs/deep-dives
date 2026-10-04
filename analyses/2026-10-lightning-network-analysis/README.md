# ⚡ Lightning Network Macro Resilience Study (August–October 2026)

> **Status:** Research Scope Defined &bull; Telemetry Ingestion In Progress  
> **Interactive Report:** [`./index.html`](./index.html)  

---

## 📌 Investigation Overview
An empirical analysis evaluating how the Lightning Network responded to the consecutive security incidents and software bugs across **LND / BTCPay Server** and **Core Lightning (CLN)** over the past 60 days.

### Core Objectives:
1. **Quantify Channel Attrition:** Measure force-close cascades vs. mutual closes across the incident windows.
2. **Evaluate Liquidity Flight:** Track net BTC capacity movements among routing hubs and payment processors.
3. **Measure Patch Velocity:** Calculate the upgrade adoption curve across public nodes.
4. **On-Chain Footprint:** Assess the mempool congestion and fee burden created by emergency sweeps.

---

## 📁 Artifacts & Pipeline
* **[`index.html`](./index.html)**: Interactive visual dashboard and executive summary report.
* **`run.py`**: Extraction and analysis script pipeline.
* **`data/processed/`**: Lightweight aggregated datasets powering the visualization.
