"""Build the data behind the Paper 03 force-close explainer page.

Every number comes from the aggregate data and generated numbers file released with the
paper (github.com/bitcoindatalabs/ln-force-close-costs, data/*.json and paper/numbers.tex),
so the page quotes exactly what the paper quotes. Nothing here touches raw chain or
gossip tables; the output is aggregate only and names no node, operator or address.

    python run.py [--paper-repo PATH]

PATH defaults to ../../../ln-force-close-costs if present, otherwise
../../../arxiv-papers/papers/03-ln-force-close-costs.
"""
import argparse
import json
import re
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent


def r(x, nd=1):
    """Round half up, matching the paper's tables and prose."""
    q = Decimal(1).scaleb(-nd)
    return float(Decimal(str(x)).quantize(q, rounding=ROUND_HALF_UP))


def default_paper_repo():
    standalone = HERE.parents[2] / "ln-force-close-costs"
    if standalone.exists():
        return standalone
    return HERE.parents[2] / "arxiv-papers" / "papers" / "03-ln-force-close-costs"


def load(repo, name):
    return json.loads((repo / "data" / name).read_text(encoding="utf-8"))


def macros(repo):
    """Rendered values of paper/numbers.tex, e.g. {'NClosesAll': '973,581'}."""
    bs = chr(92)
    src = (repo / "paper" / "numbers.tex").read_text(encoding="utf-8")
    pat = re.escape(bs + "newcommand{" + bs) + r"([A-Za-z]+)\}\{(.*)\}\s*$"
    out = {}
    for k, v in re.findall(pat, src, re.M):
        out[k] = v.replace("{,}", ",").replace("~", " ").replace(bs + "textminus{}", "−")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper-repo", default=str(default_paper_repo()))
    repo = Path(ap.parse_args().paper_repo)

    m = macros(repo)
    man = load(repo, "snapshot_manifest.json")
    ce = load(repo, "census.json")
    pa = load(repo, "pre_anchor_2026.json")
    co = load(repo, "costs.json")
    lc = load(repo, "lifecycle.json")
    an = load(repo, "anchors.json")
    sw = load(repo, "sweepers.json")
    tp = load(repo, "taproot_anchor_paths.json")
    bw = load(repo, "breach_wave.json")
    fe = load(repo, "fees.json")
    fp = load(repo, "fees_placebo.json")
    ht = load(repo, "htlc.json")
    zf = load(repo, "zero_fee.json")

    # --- 1. Fee spikes & placebo tests ------------------------------------------------------------
    spikes = []
    for sp in fe["spikes"]:
        ratio_all = r(sp["organic_after"] / sp["organic_before"], 3)
        ratio_leg = r(sp["legacy_after"] / sp["legacy_before"], 3) if sp["legacy_before"] else None
        ratio_anc = r(sp["anchor_after"] / sp["anchor_before"], 3) if sp["anchor_before"] >= 10 else None
        spikes.append({
            "week": sp["week"],
            "p50": int(round(sp["p50"])),
            "p50_before": int(round(sp["p50_before"])),
            "ratio_all": ratio_all,
            "ratio_legacy": ratio_leg,
            "ratio_anchor": ratio_anc,
        })
    assert str(len(spikes)) == m["NSpikes"]

    ev = fp["calendar"]["random_weeks"]["year_matched"]["event_ratios"]
    spike_placebo = []
    for key, label, sub in (
        ("organic_w0_1", "All public, weeks 0 to +1", False),
        ("legacy_w0_1", "Pre-anchor, weeks 0 to +1", False),
        ("anchor_w0_1", "Anchor, weeks 0 to +1", False),
        ("organic_w2_3", "All public, weeks +2 to +3", True),
    ):
        e = ev[key]
        spike_placebo.append({
            "label": label,
            "sub": sub,
            "est": r(e["real"], 2),
            "ord_med": r(e["q50"], 2),
            "lo": r(e["q05"], 2),
            "hi": r(e["q95"], 2),
            "pctl": int(round(e["percentile"])),
        })
    assert f"{spike_placebo[0]['est']:.2f}" == m["PlEvAllNow"]
    assert f"{spike_placebo[1]['est']:.2f}" == m["PlEvLegacyNow"]
    assert f"{spike_placebo[2]['est']:.2f}" == m["PlEvAnchorNow"]
    assert f"{spike_placebo[3]['est']:.2f}" == m["PlEvAllLater"]

    # --- 2. Per-close costs, full channel lifecycle & breach wave --------------------------------
    close_fees = [
        {
            "y": d["y"],
            "force": int(round(d["med_party_fee"])),
            "coop": int(round(d["fee_med"])),
            "ratio": r(d["ratio_med"], 1),
            "force_vb": int(round(d["med_vb"])),
            "coop_vb": int(round(d["vb_med"])),
            "days": r(d["med_to_local_days"], 1),
        }
        for d in co["by_year"] if d["y"] >= 2019
    ]
    assert f"{close_fees[-1]['force']:,}" == m["CostMedTwentySix"]
    assert f"{close_fees[-1]['ratio']:.1f}" == m["CostRatioTwentySix"]

    # Break-even rate (paper: Methods "Time", Cost "The wait outweighs the fees only when fees are low"): the yearly
    # return on the closers' locked balances at which a year's BTC-days cost as much as that year's force-close fees.
    # The paper states 2025, 2026, the 2019-2024 range and the whole period; the other years come from the same
    # released costs.json, and the asserts tie the chart to the paper's numbers.
    breakeven = [
        {
            "y": d["y"],
            "rate": r(100 * d["total_party_btc"] / (d["btc_days_locked"] / 365), 1),
            "fees_btc": r(d["total_party_btc"], 2),
            "btc_days": int(round(d["btc_days_locked"])),
        }
        for d in co["by_year"] if d["y"] >= 2019
    ]
    be = {d["y"]: d["rate"] for d in breakeven}
    early = [v for y, v in be.items() if y <= 2024]
    assert f"{be[2025]:.1f}" == m["BreakEvenRateTwentyFive"]
    assert f"{be[2026]:.1f}" == m["BreakEvenRateTwentySix"]
    assert f"{min(early):.1f}" == m["BreakEvenRateEarlyMin"]
    assert f"{max(early):.1f}" == m["BreakEvenRateEarlyMax"]
    all_rate = 100 * sum(d["total_party_btc"] for d in co["by_year"] if d["y"] >= 2019) / (
        sum(d["btc_days_locked"] for d in co["by_year"] if d["y"] >= 2019) / 365)
    assert f"{r(all_rate, 1):.1f}" == m["BreakEvenRateAll"]

    # One-year cohort incidence (paper Fig. 2): the paper's own macros, 2019-2025.
    cohort_words = {2019: "Nineteen", 2020: "Twenty", 2021: "TwentyOne", 2022: "TwentyTwo",
                    2023: "TwentyThree", 2024: "TwentyFour", 2025: "TwentyFive"}
    cohort_one_year = [{"y": y, "pct": int(m[f"CohortOneYear{w}"])} for y, w in cohort_words.items()]

    reg_names = {
        "2019-20": "2019–20 closes",
        "2021": "2021 closes",
        "2022": "2022 closes",
        "2023-24": "2023–24 closes",
        "2025-26": "2025–26 closes",
    }
    lifecycle_regimes = [
        {
            "label": reg_names[d["close_regime"]],
            "n": d["n"],
            "force": int(round(d["med_total_force"])),
            "coop": int(round(d["med_total_coop"])),
            "open": int(round(d["med_open"])),
            "close": int(round(d["med_close"])),
        }
        for d in lc["lifecycle_by_close_regime"] if d["close_regime"] in reg_names
    ]
    lifecycle_regimes.append({
        "label": "All, 2019–26",
        "n": lc["n_lifecycles"],
        "force": int(m["LcForceMed"].replace(",", "")),
        "coop": int(m["LcCoopMed"].replace(",", "")),
        "open": int(m["LcOpenMed"].replace(",", "")),
        "close": int(m["LcCloseMed"].replace(",", "")),
    })
    assert str(bw["channels"]) == m["BreachWaveChannels"]
    assert f"{bw['btc_without_outlier']:.2f}" == m["BreachWaveBtc"]

    # --- 3. HTLC deadlines & fee guessing --------------------------------------------------------
    fb = ht["deadlines"]["timeout_ready_by_fee_format"]
    fee_labels = (("<5", "Under 5 sat/vB"), ("5-20", "5–20 sat/vB"), ("20-50", "20–50 sat/vB"), ("50+", "50+ sat/vB"))
    htlc_by_fee = [
        {
            "label": label,
            "legacy": r(100 * fb[f"{key}|legacy"]["share_gt40"], 1),
            "anchor": r(100 * fb[f"{key}|anchor"]["share_gt40"], 1),
            "n_legacy": fb[f"{key}|legacy"]["n"],
            "n_anchor": fb[f"{key}|anchor"]["n"],
        }
        for key, label in fee_labels
    ]
    assert f"{htlc_by_fee[-1]['legacy']:.1f}" == m["HtlcLateSpikeLegacy"]
    assert f"{htlc_by_fee[-1]['anchor']:.1f}" == m["HtlcLateSpikeAnchor"]

    gs_map = {(d["y"], d["fmt"]): d for d in fe["fee_guessing"]}
    fee_guessing = [
        {
            "y": str(yr),
            "legacy_over2x": r(100 * gs_map[(yr, "legacy")]["share_over_2x"], 1),
            "anchor_over2x": r(100 * gs_map[(yr, "anchor")]["share_over_2x"], 1),
            "legacy_ratio": r(gs_map[(yr, "legacy")]["med_ratio"], 2),
            "anchor_ratio": r(gs_map[(yr, "anchor")]["med_ratio"], 2),
        }
        for yr in range(2021, 2027)
    ]
    assert str(int(round(fee_guessing[-1]["legacy_over2x"]))) == m["LegacyOverTwoPctTwentySix"]

    # --- 4. Census rate & 2026 legacy concentration ----------------------------------------------
    census_monthly = [
        {
            "t": d["month"] + "-01",
            "rate": r(d["rate"], 1),
            "organic": r(d["rate_organic"], 1),
            "pub_force": d["force"],
            "ul_force": d["ul_force"],
            "open": d["open"],
        }
        for d in ce["monthly"] if d["month"] >= "2019-01"
    ]
    yr_map = {d["y"]: d for d in ce["yearly"]}
    legacy_share = [
        {"label": str(yr), "pct": r(100 * yr_map[yr]["pub_fmt_legacy"], 0), "kind": "year"}
        for yr in range(2021, 2026)
    ]
    legacy_share.append({
        "label": "2026, all public",
        "pct": r(100 * pa["pre_anchor_share"], 0),
        "kind": "all26",
        "note": f"{pa['pre_anchor']:,} of {pa['public_force_closes']:,} closes",
    })
    legacy_share.append({
        "label": "2026, excl. 5 nodes",
        "pct": r(100 * pa["without_top_nodes"]["pre_anchor_share"], 0),
        "kind": "ex5",
        "note": f"{pa['without_top_nodes']['pre_anchor']:,} of {pa['without_top_nodes']['public_force_closes']:,} closes (median age {m['LegacyOldAgeYears']} yr)",
    })
    assert str(int(legacy_share[-2]["pct"])) == m["PubLegacyPctTwentySix"]
    assert str(int(legacy_share[-1]["pct"])) == m["LegacyPctExClusterTwentySix"]

    # --- 5. Anchor fates & sweeper value split ---------------------------------------------------
    p2wsh = defaultdict(lambda: {"owner": 0, "third_fast": 0, "third_late": 0, "unspent": 0})
    for d in an["fate"]:
        y = p2wsh[d["y"]]
        y["owner"] += d["owner_bump"] + d["owner_cleanup"]
        y["third_fast"] += d["third_fast"]
        y["third_late"] += d["third_late"]
        y["unspent"] += d["unspent"]
    anchor_fates = [
        {"label": f"P2WSH {yr}", **p2wsh[yr]}
        for yr in sorted(p2wsh)
    ]
    anchor_fates.append({
        "label": "Simple taproot 2023–26",
        "owner": tp["anchor_spend_paths"]["key_path"],
        "third_fast": 0,
        "third_late": 0,
        "unspent": tp["anchor_spend_paths"]["unspent"],
    })
    assert f"{sum(sum(v.values()) for v in p2wsh.values()):,}" == m["AnchorsAll"]
    assert f"{tp['anchor_spend_paths']['unspent']:,}" == m["TaprootAnchorsUnspent"]

    sweeper_value = [
        {
            "label": str(d["y"]),
            "miners_sat": int(round(d["miners_btc"] * 1e8)),
            "sweepers_sat": int(round(d["sweepers_btc"] * 1e8)),
            "miners_btc": r(d["miners_btc"], 3),
            "sweepers_btc": r(d["sweepers_btc"], 3),
        }
        for d in an["sweep_economics"]
    ]

    # --- 6. Zero-fee counterfactual & Bitcoin closing bill ---------------------------------------
    cf = zf["counterfactual"]["totals"]
    zero_fee_space = [
        {
            "label": "Anchor channels (actual)",
            "vb": r(cf["anchor_vb_per_close"], 1),
            "note": "two 43-vB anchors + owner or third-party spends",
        },
        {
            "label": "Zero-fee counterfactual (P2A)",
            "vb": r(cf["p2a_vb_per_close"], 1),
            "note": f"{m['CfSavingPct']}% less: one 13-vB P2A output, its spend, plus child for the {m['CfNotBumpedPct']}% not bumped",
        },
    ]
    assert str(int(round(cf["anchor_vb_per_close"]))) == m["CfAnchorVb"]
    assert str(int(round(cf["p2a_vb_per_close"]))) == m["CfPtwoaVb"]

    closing_bill = [
        {
            "y": "2026 (to Oct)" if d["y"] == 2026 else str(d["y"]),
            "fee_pct": r(100 * d["fee_share"], 3),
            "fee_pct_disp": r(100 * d["fee_share"], 2),
            "btc": r(d["ln_fee_btc"], 1),
            "vb_pct": r(100 * d["vb_share"], 3),
        }
        for d in fe["closing_bill"]
    ]

    keep = [
        "CutoffDate", "CutoffHeight", "ScanStartDate", "NClosesTitle", "NClosesAll",
        "NPublicCloses", "NPublicMutual", "NPublicForce", "NUnlistedForce", "NAllForce",
        "NOutputs", "NOutputsSpent", "ValLakeCompared", "ValCompared", "ValAgreePct",
        "NSpikes", "NSpikesUp", "NSpikesDown", "PlEvAllNow", "PlEvAllNowMed",
        "PlEvLegacyNow", "PlEvAnchorNow", "PlEvAllLater", "PlFwPCirc", "PlFwPBlock",
        "SpikeMayTwentyThreePct", "SpikeMayTwentyThreeFee", "SpikeMayTwentyThreeFeeBefore",
        "SpikeAprTwentyFourPct", "SpikeMarNineteenPct",
        "CostMedTwentySix", "CostMedTwenty", "CostMedTwentyThree", "CostRatioMin", "CostRatioMax",
        "CostRatioTwentySix", "CostTotalBtcAll", "CostTotalBtcTwentyThree",
        "ToLocalMedDays", "ToLocalPNinetyMax", "DelayOneDayPct", "DelayTwoWeeksPct", "BtcDaysLockedAll",
        "VbRatioMin", "VbRatioMax", "LegacyVbMed", "AnchorVbMed",
        "LcMed", "LcOpenMed", "LcCloseMed", "LcCapPct", "LcCoopMed", "LcForceMed",
        "LcForceCoopRatio", "LcForceCoopRatioMin", "LcForceCoopRatioMax", "LcOpensPct",
        "LcOpensPctLowRegime", "LcOpenBtc", "LcTotalBtc",
        "PenaltyTxsAll", "PenaltyBtcAll", "PenaltyTxsTwentySix", "PenaltyWaveMaxBlocks",
        "BreachWavePenalised", "BreachWaveChannels", "BreachWaveBtc",
        "BreachOpenToSpliceMed", "BreachSpliceToCloseMed", "BreachLookAlikesWeek", "BreachRevokedSharePct",
        "HtlcTimeoutTxs", "HtlcMarginTight", "HtlcLateTwentyThree", "HtlcLateTwentyFour",
        "HtlcLateSpikeLegacy", "HtlcLateSpikeAnchor", "CascadePct", "CascadePayments",
        "CascadeMaxCloses", "CascadeAllTimeoutPct",
        "SplitResPayments", "SplitResBtc", "SplitResForwarderPayments", "SplitResForwarderBtc",
        "SplitResGapMed", "SplitResStagedPairs", "SplitResStagedBtc", "SplitResStagedToSelfDelay",
        "LegacyOverTwoPctTwentySix", "LegacyOverBtcAll",
        "PubForceTwentyTwo", "PubForceTwentySix", "UnlForceTwentySix", "UnlOverPubTwentySix",
        "OrganicRateTwentyTwo", "OrganicRateTwentySix", "RateAugTwentySix", "RateOrganicAugTwentySix",
        "OpenAtCutoff", "OpenPeak", "SepEventCloses", "SepEventBtc", "SepEventLegacy",
        "PubLegacyPctTwentyOne", "PubLegacyPctTwentySix", "LegacyTopFivePct",
        "LegacyClusterAgeDays", "LegacyPctExClusterTwentySix", "LegacyOldAgeYears",
        "AnchorsAll", "OwnerPctTwentyTwo", "OwnerPctTwentySix", "NotRaisedPctTwentySix",
        "SweepOperators", "SweepLargestPct", "SweepLargestPctTwentySix", "SweepLargestFirst",
        "SweepLargestNetBtc", "SweepBurnPct", "SweepValueBtc", "SweepMinersBtc", "SweepSweepersBtc",
        "MinersShareTwentyTwo", "MinersShareLateMin", "MinersShareLateMax", "BreakEven",
        "TaprootAnchors", "TaprootAnchorsSpent", "TaprootAnchorsUnspent", "TaprootAnchorsSpentPct",
        "TaprootKeyExposedUnspent", "TaprootKeyExposedDaysMed", "TaprootKeyPublicBtc",
        "TaprootCosweepToRemotePctEarly", "TaprootCosweepToRemotePctLate",
        "TaprootOwnerSweepFrEarly", "TaprootOwnerSweepFrLate",
        "ZfCloses", "ZfUnlisted", "ZfPublic", "ZfPublicNodes", "ZfFirst", "ZfFirstPublic",
        "ZfBeforeMerge", "ZfPkgFr", "CfCloses", "CfAnchorVb", "CfPtwoaVb", "CfSavingPct",
        "CfNotBumpedPct", "CfAnchorBtc",
        "BillBtcTwentyThree", "BillBtcTwentySix", "BillFeePctMin", "BillFeePctMax", "BillVbPctMax",
        "BreakEvenRateAll", "BreakEvenRateTwentyFive", "BreakEvenRateTwentySix", "BreakEvenRateEarlyMin",
        "BreakEvenRateEarlyMax", "SplitResStagedPreimageAfterMed", "SplitResPreimageFirstPct", "SplitResFromYear",
        "CohortOneYearNineteen", "CohortOneYearTwentyThree", "CohortOneYearTwentyFive", "HtlcTimeoutMedMin",
        "HtlcTimeoutMedMax",
    ]

    data = {
        "paper": {
            "arxiv": None,
            "cutoff": "2026-10-31",
            "cutoff_height": man["cutoff_height"],
            "repo": "https://github.com/bitcoindatalabs/ln-force-close-costs",
        },
        "numbers": {k: m[k] for k in keep},
        "spikes": spikes,
        "spike_placebo": spike_placebo,
        "close_fees": close_fees,
        "breakeven": breakeven,
        "htlc_by_fee": htlc_by_fee,
        "cohort_one_year": cohort_one_year,
        "legacy_share": legacy_share,
        "anchor_fates": anchor_fates,
        "sweeper_value": sweeper_value,
    }
    # lifecycle_regimes, fee_guessing, census_monthly, zero_fee_space and closing_bill are still built above for their
    # asserts against the paper, but the page no longer charts them (it quotes their headline numbers instead).

    proc = HERE / "data" / "processed"
    proc.mkdir(parents=True, exist_ok=True)
    for stale in proc.glob("*.json"):
        if stale.name != "paper03.json":
            stale.unlink()
            print(f"removed stale {stale.relative_to(HERE)}")
    dest = proc / "paper03.json"
    dest.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {dest.relative_to(HERE)}")


if __name__ == "__main__":
    main()
