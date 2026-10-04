# 🔬 Deep Dives (`bitcoin-data-labs/deep-dives`)

Ad-hoc investigations, incident forensics, node anomaly evaluations, and on-chain curiosities across Bitcoin and Lightning.

Hosted publicly via GitHub Pages at:  
👉 **`https://bitcoindatalabs.github.io/deep-dives/`**

---

## 📁 Repository Structure

Each investigation lives in its own self-contained folder under `analyses/`:

```text
deep-dives/
├── index.html                   # Master GitHub Pages Hub & searchable catalog
├── shared/                      # Shared styling & assets
├── analyses/
│   ├── _template/               # Starter template for new analyses
│   │   ├── index.html           # Public interactive report / visual dashboard
│   │   ├── README.md            # Technical methodology & executive summary
│   │   ├── run.py               # Data extraction & aggregation script
│   │   └── data/
│   │       ├── raw/             # Git-ignored raw logs/dumps
│   │       └── processed/       # Lightweight cleaned data (<25MB)
│   │
│   ├── YYYY-MM-coldcard-forensics/
│   ├── YYYY-MM-cln-channel-closures/
│   └── ...
└── README.md
```

---

## 🚀 Starting a New Deep Dive

1. **Copy the starter template:**
   ```bash
   cp -r analyses/_template analyses/2026-10-my-investigation
   ```

2. **Extract & clean data:**
   - Put raw queries/scripts in `analyses/2026-10-my-investigation/run.py`
   - Store processed / aggregated datasets under `data/processed/` (keep files < 25MB).

3. **Write the report:**
   - Update `analyses/2026-10-my-investigation/README.md` with methodology and takeaways.
   - Edit `analyses/2026-10-my-investigation/index.html` to build the interactive visualization.

4. **Register on the Hub:**
   - Add a new card entry into the root `index.html` pointing to `./analyses/2026-10-my-investigation/index.html`.

---

## 📊 Data Management Rules
- **Repository Size Budget:** Keep the overall Git repository lightweight.
- **Raw Data vs Processed Data:** Never commit multi-gigabyte block logs or node debug logs. Keep heavy raw files in `data/raw/` (ignored by `.gitignore`).
- **Heavy Datasets:** If an analysis requires large data distributions, attach them to a GitHub Release or external storage (R2/S3/GCS) and provide a download script.

---

## 🌐 GitHub Pages Deployment
1. Go to repository **Settings** &rarr; **Pages**.
2. Under **Build and deployment**:
   - **Source:** Deploy from a branch
   - **Branch:** `main`
   - **Folder:** `/ (root)`
3. Save. GitHub will publish the site at `https://bitcoindatalabs.github.io/deep-dives/`.
