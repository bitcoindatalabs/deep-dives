"""
The Summer Lightning Broke (a Little) — data pipeline for the TABConf 2026 deep dive.

Reads the local Lightning data lake (gossip_daily, onchain close tables) through the shared
metrics module python/automation/shared/lightning/incident_metrics.py (also used by the
client-monoculture paper) and writes compact aggregates to data/processed/*.json.

Audience: Bitcoin/Lightning developers. Named nodes appear only for large public operators'
closing behavior (mass-close events, top closers) — never as lists of vulnerable/unpatched nodes.

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
from shared.lightning.client_fingerprint import RULES_VERSION  # noqa: E402

DATA_PROCESSED = SCRIPT_DIR / "data" / "processed"
SCANNER_STATE = im.PARQUET / "onchain" / "scanner_state.json"
WINDOW_START = "2026-05-01"


def records(df: pd.DataFrame, round_to: int = 3) -> list:
    df = df.copy()
    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            df[c] = df[c].dt.strftime("%Y-%m-%d")
    return json.loads(df.round(round_to).to_json(orient="records"))


def write(name: str, payload) -> None:
    path = DATA_PROCESSED / f"{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"), ensure_ascii=False)
    print(f"  {path.name:<28} {path.stat().st_size / 1024:7.1f} KB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh-labels", action="store_true")
    args = ap.parse_args()
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    print("Client labels …")
    labels = im.node_labels(refresh=args.refresh_labels)
    dates = [d for d in im.gossip_dates() if d >= WINDOW_START.replace("-", "")]   # gossip goes back to 2023

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

    # Q3 — cohort census (nodes and node capacity per client, daily)
    census = daily[["date", "target", "nodes", "cap_btc"]].copy()
    tot = census.groupby("date")[["nodes", "cap_btc"]].transform("sum")
    census["node_share"] = 100 * census["nodes"] / tot["nodes"]
    census["cap_share"] = 100 * census["cap_btc"] / tot["cap_btc"]
    write("cohort_census", records(census))

    # Q2 — closes
    print("Closes and commitment spends …")
    closes = im.load_closes(labels)
    closes = closes[closes["date"] >= WINDOW_START]
    spends = im.load_spends()
    spends = spends[spends["date"] >= WINDOW_START]
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

    # Metadata and caveats travel with the data
    state = json.loads(SCANNER_STATE.read_text(encoding="utf-8")) if SCANNER_STATE.exists() else {}
    breach = spends[spends["spend_type"].str.contains("breach")]
    write("meta", {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "gossip_days": len(dates), "gossip_first": dates[0], "gossip_last": dates[-1],
        "onchain_from": WINDOW_START,
        "onchain_complete_through_utc": datetime.fromtimestamp(state.get("last_block_time", 0), timezone.utc).strftime("%Y-%m-%d %H:%M"),
        "closes": int(len(closes)), "commitment_spends": int(len(spends)),
        "breach_spends": int(len(breach)),
        "client_rules": RULES_VERSION, "label_ref_date": im.REF_DATE,
        "mass_close_min": im.MASS_CLOSE_MIN, "dark_share": im.DARK_SHARE,
        "incidents": im.INCIDENTS,
        "caveats": [
            "Gossip is one LND node's view of the public (announced) graph; private channels are not counted.",
            "Gossip gaps: 2026-06-13 (corrupt), 06-15, 06-16, 07-22.",
            "Node capacity counts each channel for both endpoints.",
            "Chain data does not show which side broadcast a force close; mass-close events (one node in "
            f">= {im.MASS_CLOSE_MIN} force closes in a day) are separated from organic force closes.",
            "A successful theft leaves no justice transaction; breach counts are a lower bound on attempts.",
        ],
    })
    print("Done.")


if __name__ == "__main__":
    main()
