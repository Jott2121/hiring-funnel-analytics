"""Funnel analytics: conversion rates, time-to-fill, source effectiveness, bias detection."""
from __future__ import annotations

import pandas as pd
import numpy as np
from scipy import stats

STAGES = ["applied", "screened", "phone_screen", "onsite", "offer", "accepted", "hired"]


def conversion_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Overall funnel conversion at each stage."""
    counts = df["stage_reached"].value_counts().reindex(STAGES, fill_value=0)
    # Candidates who reached at least stage X:
    at_or_past = counts[::-1].cumsum()[::-1]
    conv = pd.DataFrame(
        {
            "reached": at_or_past.values,
            "pct_of_applied": (at_or_past / at_or_past.iloc[0] * 100).round(2).values,
        },
        index=STAGES,
    )
    conv["stage_pass_rate_pct"] = (
        (at_or_past.shift(-1) / at_or_past * 100).round(2).values
    )
    return conv


def source_effectiveness(df: pd.DataFrame) -> pd.DataFrame:
    """For each source, what % of applicants ultimately get hired?

    Returns a tidy DataFrame ranked by conversion rate.
    """
    def pct_reached(sub: pd.DataFrame, stage: str) -> float:
        at_or_past = (sub["stage_reached"].cat.codes >= STAGES.index(stage)).mean()
        return float(at_or_past)

    rows = []
    for src, sub in df.groupby("source"):
        rows.append(
            {
                "source": src,
                "applicants": len(sub),
                "pct_reach_phone_screen": pct_reached(sub, "phone_screen") * 100,
                "pct_reach_offer": pct_reached(sub, "offer") * 100,
                "pct_hired": pct_reached(sub, "hired") * 100,
            }
        )
    return pd.DataFrame(rows).sort_values("pct_hired", ascending=False).reset_index(drop=True)


def time_to_fill_by_role(df: pd.DataFrame) -> pd.DataFrame:
    """Median days-in-stage for hired candidates, rolled up by role."""
    hired = df[df["stage_reached"] == "hired"].copy()
    if hired.empty:
        return pd.DataFrame()
    summary = hired.groupby("role").agg(
        hires=("candidate_id", "count"),
        median_days_in_final_stage=("days_in_stage", "median"),
    )
    return summary.sort_values("hires", ascending=False)


def bias_test_phone_screen(df: pd.DataFrame) -> dict:
    """Test whether URM vs non-URM candidates pass the phone-screen gate at
    different rates. Uses a two-proportion z-test.

    Returns a dict with group sizes, pass rates, absolute gap, relative gap,
    and a p-value.
    """
    past_screened = df[df["stage_reached"].cat.codes >= STAGES.index("screened")]
    urm = past_screened["is_urm"]
    past_phone = past_screened["stage_reached"].cat.codes >= STAGES.index("phone_screen")

    ct = pd.crosstab(urm, past_phone)
    # ct index: False/True for URM; columns: False/True for past_phone
    n_urm = int(ct.loc[True].sum())
    pass_urm = int(ct.loc[True, True]) / n_urm if n_urm else 0.0
    n_nonurm = int(ct.loc[False].sum())
    pass_nonurm = int(ct.loc[False, True]) / n_nonurm if n_nonurm else 0.0

    # Two-proportion z-test
    pooled_p = (int(ct.loc[True, True]) + int(ct.loc[False, True])) / (n_urm + n_nonurm)
    se = np.sqrt(pooled_p * (1 - pooled_p) * (1 / n_urm + 1 / n_nonurm))
    z = (pass_urm - pass_nonurm) / se if se else 0.0
    p = 2 * (1 - stats.norm.cdf(abs(z)))

    return {
        "n_urm": n_urm,
        "n_nonurm": n_nonurm,
        "pass_rate_urm": pass_urm,
        "pass_rate_nonurm": pass_nonurm,
        "absolute_gap_pp": (pass_nonurm - pass_urm) * 100,
        "relative_gap_pct": (1 - pass_urm / pass_nonurm) * 100 if pass_nonurm else 0.0,
        "z_stat": z,
        "p_value": p,
    }


def bias_by_stage(df: pd.DataFrame) -> pd.DataFrame:
    """Pass rates by (previous stage → next stage) split by URM status.

    Useful for pinpointing *which* stage shows demographic divergence, not
    just whether there's divergence overall.
    """
    rows = []
    for from_stage, to_stage in zip(STAGES[:-1], STAGES[1:]):
        i_from = STAGES.index(from_stage)
        i_to = STAGES.index(to_stage)
        past_from = df[df["stage_reached"].cat.codes >= i_from]
        for label, subset in past_from.groupby("is_urm"):
            n = len(subset)
            n_past = (subset["stage_reached"].cat.codes >= i_to).sum()
            rows.append(
                {
                    "from_stage": from_stage,
                    "to_stage": to_stage,
                    "group": "URM" if label else "non-URM",
                    "n": n,
                    "pass_rate_pct": (n_past / n * 100) if n else 0.0,
                }
            )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    from src.simulate import simulate_funnel

    df = simulate_funnel()
    print(f"\nFunnel ({len(df):,} applications):\n")
    print(conversion_matrix(df))
    print("\nSource effectiveness (ranked by hire rate):\n")
    print(source_effectiveness(df).round(2).to_string(index=False))
    print("\nTime-to-fill by role:\n")
    print(time_to_fill_by_role(df))
    print("\nPhone-screen bias test (URM vs non-URM):\n")
    for k, v in bias_test_phone_screen(df).items():
        if isinstance(v, float):
            print(f"  {k:25s} {v:.4f}")
        else:
            print(f"  {k:25s} {v}")
