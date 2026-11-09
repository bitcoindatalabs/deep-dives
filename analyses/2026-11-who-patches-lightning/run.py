"""Build the data behind the "Who patches the Lightning Network?" explainer page.

Every number comes from the aggregate data released with the paper
(github.com/bitcoindatalabs/ln-upgrade-dynamics: data/*.json and paper/numbers.tex), so the
page quotes exactly what the paper quotes. Nothing here touches the node-day panel; the
output is aggregate only and labels no individual node.

    python run.py [--paper-repo PATH]

PATH is a clone of bitcoindatalabs/ln-upgrade-dynamics (default: ../../../ln-upgrade-dynamics,
a clone next to this repository).
"""
import argparse
import json
import re
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent


def r(x, nd=1):
    """Round half up, as the paper does."""
    q = Decimal(1).scaleb(-nd)
    return float(Decimal(str(x)).quantize(q, rounding=ROUND_HALF_UP))


def load(repo, name):
    return json.loads((repo / "data" / name).read_text(encoding="utf-8"))


def macros(repo):
    """Rendered values of paper/numbers.tex, e.g. {'MedianLNDAll': '88'}."""
    bs = chr(92)
    src = (repo / "paper" / "numbers.tex").read_text(encoding="utf-8")
    pat = re.escape(bs + "newcommand{" + bs) + r"([A-Za-z]+)\}\{(.*)\}\s*$"
    return {k: v.replace("{,}", ",").replace("~", " ") for k, v in re.findall(pat, src, re.M)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper-repo", default=str(HERE.parents[2] / "ln-upgrade-dynamics"))
    repo = Path(ap.parse_args().paper_repo)

    m = macros(repo)
    up = load(repo, "upgrade_dynamics.json")
    adv = load(repo, "advisory_exposure.json")

    # Nodes first seen on a newer LND line per day (managed fleet excluded), summed over lines.
    daily = defaultdict(int)
    for key, n in up["waves"]["LND"]["daily"].items():
        daily[key.split("|")[0]] += n
    snapshot_days = adv["series"]["lnd-2026-ll-batch"]["date"]
    snapshot_days = [d if "-" in d else f"{d[:4]}-{d[4:6]}-{d[6:]}" for d in snapshot_days]
    start = "2024-07-01"
    waves = [{"d": d, "n": daily.get(d, 0)} for d in snapshot_days if d >= start]

    lnd_releases = [{"line": line, "date": f"{a['released'][:4]}-{a['released'][4:6]}-{a['released'][6:]}"}
                    for line, a in up["adoption"]["LND"].items()]
    platform_releases = [{"platform": p["platform"], "version": p["version"], "utc": p["utc"],
                          "line": p["line"], "landed": r(100 * p["share_on_shipped_line"])}
                         for p in up["platform_lines"]["LND"]]
    big_waves = [{"line": w["line"], "nodes": w["nodes"], "first_day": w["first_day"],
                  "platform": w["platform"].get("platform") if w["platform"].get("attributed") else None,
                  "days_after_release": w["days_after_release"]}
                 for w in up["waves"]["LND"]["waves"]]

    ttu = []
    for client in ("LND", "CLN"):
        for q, label in (("smallest 25%", "Smallest quarter"), ("Q2", "Second quarter"),
                         ("Q3", "Third quarter"), ("largest 25%", "Largest quarter")):
            t = up["time_to_upgrade"][client][q]
            ttu.append({"client": client, "quartile": label, "median_days": t["median_days"],
                        "within_year": r(100 * t["upgraded_by_365d"], 0)})

    # Days from the first fixed release to disclosure, for the LND and CLN advisories gossip can see.
    fix_to_disc = [{"client": a["client"], "title": a["title"], "disclosed": a["disclosed"],
                    "fixed_in": a["fixed_in"], "days": a["fix_to_disclosure_days"], "count": a["count"]}
                   for a in adv["advisories"] if a["client"] in ("LND", "CLN")]

    def resp_row(x, label=None, subset=False):
        # Ratio and test outside platform releases (the paper's test); weekly rates over all moves, as in its table.
        o, a = x["operator"], x["all"]
        return {"client": x["client"], "title": x["title"], "disclosed": x["disclosed"],
                "affected": x["affected_span"], "label": label, "subset": subset,
                "rr": r(o["rr"], 2), "lo": r(o["rr_lo"], 2), "hi": r(o["rr_hi"], 2), "p": r(o["p_perm"], 3),
                "rr_all": r(a["rr"], 2), "before": r(100 * a["rate_before"]), "after": r(100 * a["rate_after"]),
                "at_risk": x["at_risk_at_disclosure"]}

    response = []
    for x in adv["response"]:
        response.append(resp_row(x))
        if x["key"] == "cln-2026-gossipd":
            response.append(resp_row(adv["response_cln_one_line_behind"], subset=True))

    def fate(key, label, when):
        last = adv["cases"][key]["fate"][-1]
        n = last["exposed"] + last["upgraded"] + last["left"]
        return {"label": label, "when": when, "date": last["date"], "cohort": n,
                "still": last["exposed"], "upgraded": last["upgraded"], "left": last["left"]}

    fates = [
        fate("lnd-2026-ll-batch", "LND, Lightning Labs batch (11 Aug 2026)", "two months later"),
        fate("lnd-2025-sweeper", "LND, Morehouse disclosures (4 Dec 2025)", "four months later"),
        fate("cln-2026-gossipd", "CLN, gossipd bug (19 Jul 2026)", "at the cutoff"),
    ]
    # The page quotes the paper's rounded shares; check the counts behind them agree.
    for f, k in zip(fates, ("LLBatch", "LndSweeper", "ClnGossipd")):
        assert str(f["still"]) == m[f"CohortStill{k}"] and str(f["upgraded"]) == m[f"CohortUp{k}"] \
            and str(f["left"]) == m[f"CohortLeft{k}"], (k, f)

    call = adv["cln_offline_call"]["event"]
    offline_call = [
        {"group": "All live CLN nodes", "newest": r(100 * call["newest"]["left"]), "behind": r(100 * call["behind"]["left"])},
        {"group": "Tor-only nodes", "newest": r(100 * call["newest"]["left_tor_only"], 0), "behind": r(100 * call["behind"]["left_tor_only"], 0)},
        {"group": "Other nodes", "newest": r(100 * call["newest"]["left_other"], 0), "behind": r(100 * call["behind"]["left_other"], 0)},
    ]

    keep = ["NVerNodeLinesExact", "NVerNodeLines", "NVerNodes", "PlatLineMin", "PlatLineMax", "MedianLNDAll",
            "MedianCLNAll", "MedianLNDSmall", "MedianLNDLarge", "ByYearLNDAll", "ByYearCLNAll", "ORBehind",
            "WaveUmbrelMinNodes", "WaveUmbrelMaxNodes", "WaveUmbrelDaysMin", "WaveUmbrelDaysMax",
            "WaveUmbrelSignedMin", "WaveUmbrelHoursMin", "WaveUmbrelHoursMax", "PlatShareLND", "PlatTimeLND",
            "PlatShareCLN", "PlatTimeCLN", "WaveBTCPayNodes", "WaveBTCPayOlder", "WaveBTCPayTor", "WaveBTCPayBase",
            "FleetWaveNodes", "FleetPeakNodes", "FleetPeakShare", "FixToDiscMedian", "FixToDiscLLBatch", "NResp",
            "NAdvTotal", "NAdvRows", "ExpLLBatchDisc", "ExpCapLLBatchDisc", "PctCohortStillLLBatch",
            "PctCohortUpLLBatch", "PctCohortLeftLLBatch", "PctCohortStillLndSweeper", "PctCohortUpClnGossipd",
            "PctCohortLeftClnGossipd", "ExpClnGossipdDisc", "ExpClnGossipdCutoff", "NOldLndChan", "NOldLndLive",
            "PctOldLndNaive", "PctOldLndLive", "OffCallNewestLeft", "OffCallBehindLeft", "OffCallNewestNodes",
            "OffCallBehindNodes", "OffCallP", "OffCallMovedMax", "OffCallOrdNewestMedian",
            "OffCallOrdBehindMedian", "DataUsableDays", "RROpClnRecent", "WkBeforeAllClnGossipd",
            "WkAfterAllClnGossipd"]
    data = {
        "paper": {"arxiv": "2610.30350", "version": "v1", "cutoff": "2026-10-13",
                  "repo": "https://github.com/bitcoindatalabs/ln-upgrade-dynamics"},
        "numbers": {k: m[k] for k in keep},
        "waves": waves,
        "lnd_releases": lnd_releases,
        "platform_releases": platform_releases,
        "big_waves": big_waves,
        "time_to_upgrade": ttu,
        "fix_to_disclosure": fix_to_disc,
        "response": response,
        "fates": fates,
        "offline_call": offline_call,
    }

    dest = HERE / "data" / "processed" / "paper02.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {dest.relative_to(HERE)}")


if __name__ == "__main__":
    main()
