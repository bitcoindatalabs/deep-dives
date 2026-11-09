"""Build the data behind the client-diversity explainer page.

Every number comes from the aggregate data released with the paper
(github.com/bitcoindatalabs/ln-client-diversity, data/ and paper/tables/), so the page
quotes exactly what the paper quotes. Nothing here touches raw gossip or chain data.

    python run.py [--paper-repo PATH]

PATH is a clone of bitcoindatalabs/ln-client-diversity (default: ../../../ln-client-diversity,
a clone next to this repository).
"""
import argparse
import json
import re
import statistics
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLIENTS = ["LND", "CLN", "Eclair", "LDK"]


def r(x, nd=1):
    """Round half up, as the paper's tables do (80.05 -> 80.1)."""
    q = Decimal(1).scaleb(-nd)
    return float(Decimal(str(x)).quantize(q, rounding=ROUND_HALF_UP))


def load(repo, name):
    return json.loads((repo / "data" / name).read_text(encoding="utf-8"))


def outage_table(repo):
    """Disabled share toward each client, baseline mean and 27 August peak (paper Table IV)."""
    tex = (repo / "paper" / "tables" / "table3_outage_effect.tex").read_text(encoding="utf-8")
    rows = {}
    for client in CLIENTS:
        m = re.search(rf"^{client} & ([\d.]+) \$\\pm\$ [\d.]+ & ([\d.]+) & (-?[\d.]+) & ([\d.]+) \$\\pm\$ [\d.]+ & ([\d.]+)",
                      tex, re.M)
        if not m:
            raise SystemExit(f"table3: no row for {client}")
        rows[client] = {"base": float(m[1]), "peak": float(m[2]), "z": float(m[3]),
                        "base_cap": float(m[4]), "peak_cap": float(m[5])}
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper-repo", default=str(HERE.parents[2] / "ln-client-diversity"))
    repo = Path(ap.parse_args().paper_repo)

    sup = load(repo, "supporting_numbers.json")
    fleet = load(repo, "fleet_check.json")
    cal = load(repo, "observed_outage_calibration.json")

    latest = fleet["latest"]
    census = [{
        "client": c,
        "node_share": r(latest["node_share"][c]),
        "node_share_exfleet": r(latest["node_share_exfleet"][c]),
        "cap_share": r(latest["cap_share_exfleet"][c]),
    } for c in CLIENTS]

    # LND's shares, first snapshot of each month, second vantage epoch only (levels are not
    # comparable across the change of gossip node in mid-2024).
    monthly = [{
        "date": m["date"],
        "node_share": r(m["node_share"]["LND"]),
        "node_share_exfleet": r(m["node_share_exfleet"]["LND"]),
        "cap_share": r(m["cap_share_exfleet"]["LND"]),
        "fleet_nodes": m["fleet_nodes"],
    } for m in fleet["monthly"] if m["date"] >= "2024-07-01"]

    out = sup["outage"]
    transport = out["compliance_by_transport"]
    placebo = [{
        "from": w["from"], "kind": w["kind"],
        "all": r(-100 * w["dR_all"]), "cln": r(-100 * w["dR_CLN_all"]),
    } for w in sup["placebo"]["series"]]
    ordinary = [w for w in placebo if w["kind"] == "ordinary"]

    hubs = sup["hubs"]
    top20_median = r(-hubs["top20_critical_dR_median_pp"])
    mix = sup["mixing_null_model"]

    data = {
        "paper": {"arxiv": "2610.20952", "version": "v2", "cutoff": "2026-10-04",
                  "repo": "https://github.com/bitcoindatalabs/ln-client-diversity"},
        "fleet": {"nodes_latest": latest["fleet_nodes"], "nodes_peak": fleet["epoch_b_lnd_node_share"]["max_fleet_nodes"],
                  "cap_btc": r(latest["fleet_cap_btc"]), "cap_share": r(latest["fleet_cap_share"], 2),
                  "node_share": r(latest["fleet_node_share"])},
        "census": census,
        "lnd_monthly": monthly,
        "outage": outage_table(repo),
        "went_dark": {
            "cln_event": r(100 * out["dark_rate_CLN"]["event"]),
            "cln_ordinary": r(100 * out["dark_rate_CLN"]["ordinary_median"]),
            "lnd_event": r(100 * out["dark_rate_LND"]["event"]),
            "lnd_ordinary": r(100 * out["dark_rate_LND"]["ordinary_median"]),
            "at_risk": cal["cln_nodes_at_risk"], "dark": cal["cln_nodes_went_dark"],
        },
        "transport": [
            {"label": "Tor only", "share": r(100 * transport["tor-only"]["went_dark"], 0), "n": transport["tor-only"]["nodes"]},
            {"label": "Tor and clearnet", "share": r(100 * transport["both"]["went_dark"], 0), "n": transport["both"]["nodes"]},
            {"label": "Clearnet only", "share": r(100 * transport["clearnet-only"]["went_dark"], 0), "n": transport["clearnet-only"]["nodes"]},
        ],
        "recovery": {
            "back_3d": r(100 * out["recovery_back_within_3_7_days"][0], 0),
            "back_7d": r(100 * out["recovery_back_within_3_7_days"][1], 0),
            "dark_oct4": r(100 * cal["share_dark_on_last_snapshot"], 0),
            "never": r(100 * cal["share_never_returned_by_last_snapshot"], 0),
        },
        "placebo": placebo,
        "placebo_summary": {
            "ordinary_windows": len(ordinary),
            "ordinary_median_all": r(statistics.median(w["all"] for w in ordinary)),
            "ordinary_worse_all": sum(w["all"] > r(-100 * sup["placebo"]["outage"]["dR_all"]) for w in ordinary),
            "outage_all": r(-100 * sup["placebo"]["outage"]["dR_all"]),
            "outage_cln": r(-100 * sup["placebo"]["outage"]["dR_CLN_all"]),
            "ordinary_max_cln": max(w["cln"] for w in ordinary),
        },
        # Reachability lost among the surviving nodes when a single hub fails (paper §VII).
        # The paper describes ranks 2 and 3 by type and names only ACINQ.
        "hubs": [
            {"label": "ACINQ's Eclair node", "client": "Eclair", "pp": r(-hubs["top10_critical"][0]["dR_pp"])},
            {"label": "2nd most critical: an LSP (LND)", "client": "LND", "pp": r(-hubs["top10_critical"][1]["dR_pp"])},
            {"label": "3rd: a payment processor (LND)", "client": "LND", "pp": r(-hubs["top10_critical"][2]["dR_pp"])},
            {"label": "Typical top-20 hub (median)", "client": None, "pp": top20_median},
            {"label": "All 619 routable CLN nodes at once", "client": "CLN", "pp": r(-hubs["all_CLN_dR_pp"])},
        ],
        "top20_by_client": hubs["top20_critical_by_client"],
        "null_model": [
            {"label": "CLN capacity on channels to LND", "observed": r(100 * mix["share_facing_LND"]["CLN"]["observed"], 0),
             "chance": r(100 * mix["share_facing_LND"]["CLN"]["null"], 0)},
            {"label": "CLN capacity on channels to CLN", "observed": r(100 * mix["same_client_share"]["CLN"]["observed"], 0),
             "chance": r(100 * mix["same_client_share"]["CLN"]["null"], 0)},
            {"label": "CLN pairs still connected without LND", "observed": r(100 * mix["R_without_LND_100k"]["CLN"]["observed"], 0),
             "chance": r(100 * mix["R_without_LND_100k"]["CLN"]["null_mean"], 0),
             "chance_p95": r(100 * mix["R_without_LND_100k"]["CLN"]["null_p95"], 0)},
        ],
    }

    dest = HERE / "data" / "processed" / "paper01.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {dest.relative_to(HERE)}")


if __name__ == "__main__":
    main()
