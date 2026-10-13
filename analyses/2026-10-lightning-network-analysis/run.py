"""
The Summer Lightning Broke (a Little) — data pipeline for the TABConf 2026 deep dive.

Reads the local Lightning data lake (gossip_daily, onchain close tables) through the shared
metrics module python/automation/shared/lightning/incident_metrics.py (also used by the
client-monoculture paper) and writes compact aggregates to data/processed/*.json.
The resilience results (placebo windows, hub criticality, null model, contraction) are copied from the
paper's committed aggregates, so the page and the paper quote the same numbers; run the paper's
pipeline first when those change.

Audience: Bitcoin/Lightning developers. Named nodes appear only for large public operators'
closing behavior (mass-close events, top closers) and ACINQ's hub role — never as lists of
vulnerable/unpatched nodes.

Usage:
  python run.py                  # full rebuild
  python run.py --refresh-labels # re-run client inference (after rule changes)
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
DEV_ROOT = SCRIPT_DIR.parents[3]
sys.path.insert(0, str(DEV_ROOT / "python" / "automation"))

from shared.lightning import incident_metrics as im  # noqa: E402
from shared.lightning.client_fingerprint import RULES_VERSION, classify_node  # noqa: E402

DATA_PROCESSED = SCRIPT_DIR / "data" / "processed"
SCANNER_STATE = im.PARQUET / "onchain" / "scanner_state.json"
PAPER_DATA = DEV_ROOT / "github" / "ln-client-diversity" / "data"   # the paper moved here from arxiv-papers/papers/01-…
WINDOW_START = "2026-05-01"
DATA_CUTOFF = "2026-10-04"          # same as the paper (src/config.py), so the talk and the paper agree


def records(df: pd.DataFrame, round_to: int = 3) -> list:
    df = df.copy()
    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            df[c] = df[c].dt.strftime("%Y-%m-%d")
    return json.loads(df.round(round_to).to_json(orient="records"))


def write(name: str, payload) -> None:
    path = DATA_PROCESSED / f"{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    print(f"  {path.name:<28} {path.stat().st_size / 1024:7.1f} KB")


CENSUS_CLIENTS = ["LND", "CLN", "Eclair", "LDK", "Unknown"]
HIGH_CONFIDENCE = {"high", "operator"}


def client_census(date: str) -> pd.DataFrame:
    """Client shares on one gossip day, same method as the paper's Table 1
    (ln-client-diversity src/01_client_census.py): nodes with >= 1 channel that day, labels classified
    from that day's announcements (not the frozen REF_DATE cohort labels), Unknown kept in the
    denominator, node capacity counting each channel for both endpoints."""
    pol = im.read_policies(date, ["channel_id", "capacity", "node_pub", "peer_pub", "time_lock_delta"])
    ch = pol.drop_duplicates("channel_id")
    ends = pd.concat([ch[["node_pub", "capacity"]].rename(columns={"node_pub": "pub_key"}),
                      ch[["peer_pub", "capacity"]].rename(columns={"peer_pub": "pub_key"})])
    per = ends.groupby("pub_key")["capacity"].sum()
    cltv = im._cltv_modes(pol[["node_pub", "time_lock_delta"]])
    nodes = im.read_nodes(date, ["pub_key", "alias", "color", "feature_bits"]).set_index("pub_key")
    rows = []
    for pk, cap in per.items():
        if pk in nodes.index:
            n = nodes.loc[pk]
            bits = list(n["feature_bits"]) if n["feature_bits"] is not None else []
            color, alias = n["color"], n["alias"]
        else:
            bits, color, alias = [], None, None
        mode = cltv.get(pk)
        client, conf, _ = classify_node(bits, color, alias, pk, float(mode) if mode is not None else None)
        rows.append((client, conf in HIGH_CONFIDENCE, cap))
    df = pd.DataFrame(rows, columns=["client", "high", "capacity"])
    g = (df.groupby("client").agg(nodes=("high", "size"), high_nodes=("high", "sum"), cap=("capacity", "sum"))
           .reindex(CENSUS_CLIENTS, fill_value=0))
    return pd.DataFrame({
        "date": f"{date[:4]}-{date[4:6]}-{date[6:]}", "target": g.index, "nodes": g["nodes"].values,
        "cap_btc": g["cap"].values / 1e8, "node_share": 100 * g["nodes"].values / len(df),
        "high_node_share": 100 * g["high_nodes"].values / len(df), "cap_share": 100 * g["cap"].values / g["cap"].sum(),
    })


def paper_findings() -> dict:
    """The paper's resilience and robustness results, as committed in its data/ folder."""
    paths = [PAPER_DATA / f for f in ("supporting_numbers.json", "resilience_results.json", "observed_outage_calibration.json")]
    for p in paths:
        if not p.exists():
            raise SystemExit(f"Missing {p} — run the paper pipeline (src/03 to src/05) first.")
    sup, res, obs = (json.loads(p.read_text(encoding="utf-8")) for p in paths)
    if sup.get("data_cutoff") != DATA_CUTOFF.replace("-", ""):
        raise SystemExit(f"Paper data cutoff {sup.get('data_cutoff')} != {DATA_CUTOFF}; align DATA_CUTOFF with the paper.")
    if "series" not in sup["placebo"] or "top10_critical" not in sup["hubs"]:
        raise SystemExit("supporting_numbers.json predates the placebo series / hub ranking — rerun src/05_supporting_analyses.py.")
    keep = ["n_failed", "cap_removed", "R@100000", "R_all@100000", "R_CLN@100000", "R_CLN_all@100000"]
    # NaN (e.g. R_CLN when every CLN node fails) is not valid JSON for the browser
    scen = {name: {k: (None if v != v else v) for k, v in s.items() if k in keep} for name, s in res["scenarios"].items()}
    return {
        "graph_date": res["graph_date"],
        "core_nodes": res["observed_graphs"][res["graph_date"]]["n_nodes_usable"],
        "churn": {c: sup["outage"][f"dark_rate_{c}"] for c in ("CLN", "LND")},
        "compliance_by_transport": sup["outage"]["compliance_by_transport"],
        "recovery_back_within_3_7_days": sup["outage"]["recovery_back_within_3_7_days"],
        "went_dark": {k: obs[k] for k in ("cln_nodes_at_risk", "cln_nodes_went_dark", "p_hat_nodes", "p_hat_capacity",
                                          "T_hat_median_days_dark_returners", "share_never_returned_by_last_snapshot",
                                          "share_dark_on_last_snapshot", "last_snapshot")},
        "placebo": sup["placebo"],
        "scenarios": scen,
        "stratified_calibration": {k: sup["calibrated_stratified_100k"][k] for k in ("R@100000", "R_all@100000", "R_CLN_all@100000")},
        "hubs": sup["hubs"],
        "null_model": sup["mixing_null_model"],
        "closes_two_weeks": {k: sup["closing"][f"closes_two_weeks_{k}"] for k in ("went_dark", "stayed_up")},
        "contraction": {k: v for k, v in sup["closing"]["contraction"].items() if k != "top10_operators"}
                       | {"top_operator": sup["closing"]["contraction"]["top10_operators"][0]},
        "justice": {"spends": sup["data"]["justice_spends"], "since": sup["data"]["closes_first_date"],
                    "last": sup["data"]["last_justice_spend"]},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh-labels", action="store_true")
    args = ap.parse_args()
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    lo, hi = WINDOW_START.replace("-", ""), DATA_CUTOFF.replace("-", "")

    print("Client labels …")
    labels = im.node_labels(refresh=args.refresh_labels)
    dates = [d for d in im.gossip_dates() if lo <= d <= hi]   # gossip goes back to 2023
    calendar = pd.date_range(WINDOW_START, DATA_CUTOFF).strftime("%Y%m%d")
    gaps = [f"{d[:4]}-{d[4:6]}-{d[6:]}" for d in calendar if d not in set(dates)]

    # Q1 — outage (peer-disabled share toward each cohort) + cohort size from the same snapshots
    print(f"Outage metrics over {len(dates)} gossip days …")
    daily = im.outage_daily(labels, dates)
    daily = daily[daily["target"] != "Unknown"]          # mostly stale / channel-less entries
    write("outage_daily", records(daily[["date", "target", "dirs", "nodes", "cap_btc",
                                         "pct_disabled", "pct_cap_disabled"]]))
    write("outage_effect", records(im.outage_effect(daily)))

    bynet = im.outage_by_network(labels, dates)
    bynet = bynet[bynet["target"].isin(["CLN", "LND"]) & bynet["net"].isin(["tor-only", "both", "clearnet-only"])]
    write("outage_by_transport", records(bynet[["date", "target", "net", "dirs", "pct_disabled"]]))

    panel = im.node_dark_panel(labels, "CLN", dates)
    write("cln_compliance_by_size", records(im.compliance_by_size(panel)))
    write("cln_recovery", records(im.recovery_curve(panel)))

    # Q3 — client census on the 1st of each month and the cutoff (paper method, see client_census)
    census_dates = [d for d in dates if d.endswith("01")] + ([hi] if hi in dates and not hi.endswith("01") else [])
    write("cohort_census", records(pd.concat([client_census(d) for d in census_dates], ignore_index=True)))

    # Q2 — closes
    print("Closes and commitment spends …")
    closes = im.load_closes(labels)
    closes = closes[(closes["date"] >= WINDOW_START) & (closes["date"] <= DATA_CUTOFF)]
    spends = im.load_spends()
    spends = spends[(spends["date"] >= WINDOW_START) & (spends["date"] <= DATA_CUTOFF)]
    cd = im.closes_daily(closes)
    write("closes_daily", records(cd))
    mass = im.mass_events(closes, labels)
    mass["hub_pub"] = mass["hub_pub"].str[:16]
    write("mass_close_events", records(mass))
    # early-August mutual-close wave (Aug 2–16): who drove it
    top = im.top_closers(closes, labels, "2026-08-02", "2026-08-16", n=10)
    top["pub"] = top["pub"].str[:16]
    write("top_closers_aug", records(top))
    exposure = im.channels_by_cohort(labels, dates)
    write("force_close_rates", records(im.force_close_rates(cd, exposure), 4))

    sd = im.spend_events_daily(spends)
    write("spend_events_daily", records(sd))

    # Q5 — cost
    write("fees_by_close_type", records(im.fee_summary(closes, spends)))

    # Q4 — blast radius, from the paper's pipeline
    write("paper_findings", paper_findings())

    # Metadata and caveats travel with the data
    state = json.loads(SCANNER_STATE.read_text(encoding="utf-8")) if SCANNER_STATE.exists() else {}
    breach = spends[spends["spend_type"].str.contains("breach")]
    write("meta", {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "data_cutoff": DATA_CUTOFF,
        "gossip_days": len(dates), "gossip_first": dates[0], "gossip_last": dates[-1], "gossip_gaps": gaps,
        "onchain_from": WINDOW_START,
        "onchain_scanned_through_utc": datetime.fromtimestamp(state.get("last_block_time", 0), timezone.utc).strftime("%Y-%m-%d %H:%M"),
        "closes": int(len(closes)), "commitment_spends": int(len(spends)),
        "breach_spends": int(len(breach)),
        "client_rules": RULES_VERSION, "label_ref_date": im.REF_DATE,
        "mass_close_min": im.MASS_CLOSE_MIN, "dark_share": im.DARK_SHARE,
        "incidents": im.INCIDENTS,
        "caveats": [
            "Gossip is one LND node's view of the public (announced) graph; private channels are not counted.",
            f"Gossip gaps ({len(gaps)} days): {', '.join(gaps)}.",
            "Node capacity counts each channel for both endpoints.",
            "Chain data does not show which side broadcast a force close; mass-close events (one node in "
            f">= {im.MASS_CLOSE_MIN} force closes in a day) are separated from organic force closes.",
            "A successful theft leaves no justice transaction; breach counts are a lower bound on attempts.",
            "Reachability is connectivity under a capacity threshold, an upper bound on payment success "
            "(no fees, balances or in-flight HTLCs).",
        ],
    })
    print("Done.")


if __name__ == "__main__":
    main()
