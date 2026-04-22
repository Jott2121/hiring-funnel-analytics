"""Demographic pass-rate analysis — where does the funnel diverge by group?"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.analyze import bias_test_phone_screen, bias_by_stage, STAGES  # noqa: E402

st.set_page_config(page_title="Bias Detection", page_icon="⚖️", layout="wide")

if "funnel_df" not in st.session_state:
    st.warning("👋 Open the main page first to generate the funnel.")
    st.stop()

df = st.session_state["funnel_df"]

st.title("⚖️ Demographic Pass-Rate Analysis")
st.caption(
    "Does the funnel treat candidates equally at each gate? A statistically "
    "significant gap is *evidence of something* — not proof of discrimination, "
    "but enough to trigger a targeted review."
)

# --- Headline test -----------------------------------------------------------
result = bias_test_phone_screen(df)

c1, c2, c3, c4 = st.columns(4)
c1.metric(
    "URM pass rate",
    f"{result['pass_rate_urm']:.1%}",
    f"n = {result['n_urm']:,}",
)
c2.metric(
    "Non-URM pass rate",
    f"{result['pass_rate_nonurm']:.1%}",
    f"n = {result['n_nonurm']:,}",
)
c3.metric(
    "Absolute gap",
    f"{result['absolute_gap_pp']:.1f} pp",
    help="Percentage-point difference between non-URM and URM phone-screen pass rate",
)
c4.metric(
    "p-value",
    f"{result['p_value']:.4f}",
    "Significant" if result["p_value"] < 0.05 else "Not significant",
    delta_color="inverse",
)

if result["p_value"] < 0.05:
    st.error(
        f"⚠️ **Statistically significant gap detected** — URM candidates pass "
        f"the phone-screen gate at {result['relative_gap_pct']:.1f}% lower "
        f"*relative* rate than non-URM candidates (p = {result['p_value']:.4f}). "
        f"This warrants a targeted review of screen rubrics and recruiter calibration."
    )
else:
    st.success(
        f"✅ No statistically significant gap detected at the phone-screen gate "
        f"(p = {result['p_value']:.4f}). Continue routine monitoring."
    )

st.divider()

# --- Stage-by-stage breakdown -----------------------------------------------
st.subheader("Pass rate at each stage, by URM status")
st.caption(
    "Pinpointing *which* stage diverges drives the intervention. A gap at "
    "phone screen points to rubric/recruiter training. A gap at onsite "
    "points to interviewer calibration."
)

bb = bias_by_stage(df)
piv = bb.pivot_table(index="to_stage", columns="group", values="pass_rate_pct")
piv = piv.loc[[s for s in STAGES[1:] if s in piv.index]]
piv["gap_pp"] = piv["non-URM"] - piv["URM"]

st.bar_chart(piv[["non-URM", "URM"]], use_container_width=True)

st.dataframe(
    piv.style.format("{:.2f}%").background_gradient(subset=["gap_pp"], cmap="RdYlGn_r"),
    use_container_width=True,
)

st.divider()

# --- Gap by role ------------------------------------------------------------
st.subheader("Phone-screen gap by role")
st.caption(
    "Aggregate bias numbers hide variance across roles. Hiring managers and "
    "screeners vary by role — this view tells you where to focus intervention."
)

past_screened = df[df["stage_reached"].cat.codes >= STAGES.index("screened")].copy()
past_screened["past_phone"] = (
    past_screened["stage_reached"].cat.codes >= STAGES.index("phone_screen")
)
by_role = (
    past_screened.groupby(["role", "is_urm"])["past_phone"]
    .mean()
    .unstack()
    .rename(columns={False: "non-URM", True: "URM"})
)
by_role["gap_pp"] = (by_role["non-URM"] - by_role["URM"]) * 100
by_role = by_role.sort_values("gap_pp", ascending=False)

st.bar_chart(by_role["gap_pp"], use_container_width=True)
st.dataframe(
    by_role.style.format({"non-URM": "{:.1%}", "URM": "{:.1%}", "gap_pp": "{:.2f}"}),
    use_container_width=True,
)

st.divider()

# --- Disclaimer -------------------------------------------------------------
st.warning(
    """
**What this analysis is and isn't**

This tests whether URM and non-URM candidates pass the screen gate at statistically
different rates. A significant gap is *evidence of something* worth investigating —
it is **not** proof of discrimination.

Real causes might include:
- Resume quality differences upstream (itself a signal of representation in sourcing channels)
- Recruiter assignment patterns
- Screen rubric design
- Structured vs unstructured screen differences

The audit's job is to surface the gap with statistical rigor. HR, Legal, and TA then
design the intervention and measure its effect in the next quarter's data.
"""
)
