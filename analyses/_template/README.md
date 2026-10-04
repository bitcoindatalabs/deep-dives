# [Investigation Title]

> **Date:** YYYY-MM-DD  
> **Author:** Bitcoin Data Labs  
> **Tags:** `#bitcoin` `#lightning` `#security`  
> **Interactive Report:** [View GitHub Pages Report](./index.html)

---

## 1. Executive Summary
Brief 2–3 paragraph summary of the event or investigation. What happened? Why does it matter? What is the headline finding?

## 2. Key Findings & Insights
- **Key Finding 1:** Core insight with supporting metrics.
- **Key Finding 2:** Second insight.
- **Key Finding 3:** Third insight.

## 3. Data Sources & Methodology
- **Data Source:** (e.g. Bitcoin Core RPC, Mempool.space API, CLN Gossip, BigQuery public dataset)
- **Timeframe:** From YYYY-MM-DD to YYYY-MM-DD
- **Methodology:** Describe filtering, clustering, or statistical queries used.

## 4. Pipeline & Reproducibility
To reproduce the findings locally:

```bash
# 1. Run data extraction
python run.py

# 2. Open interactive report locally
# Open index.html in a browser or run a simple HTTP server:
python -m http.server 8000
```

## 5. Artifacts & Datasets
- Cleaned / aggregated dataset: `data/processed/`
- Full reports / visuals: `index.html`
