"""Hiring Funnel Analytics — interactive dashboard.

Multi-page Streamlit app:
    Home (this file)          → Funnel overview + KPIs
    1_📣_Source_Effectiveness → Sourcing channel deep-dive
    2_⚖️_Bias_Detection        → Demographic pass-rate analysis
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.simulate import simulate_funnel  # noqa: E402
from src.analyze import conversion_matrix, STAGES  # noqa: E402

st.set_page_config(
    page_title="Hiring Funnel Analytics",
    page_icon="📈",
    layout="wide",
)


@st.cache_data
def get_funnel(n_months: int, urm_bias: float, seed: int) -> pd.DataFrame:
    return simulate_funnel(n_months=n_months, urm_bias=urm_bias, seed=seed)


# --- Sidebar controls --------------------------------------------------------
st.sidebar.header("Funnel parameters")
st.sidebar.caption("Configure the simulated funnel. In real deployment this is replaced with an ATS export.")
n_months = st.sidebar.slider("Months", 3, 24, 12)
urm_bias = st.sidebar.slider("Injected URM screen bias (%)", 0.0, 25.0, 12.0, step=1.0) / 100
seed = st.sidebar.number_input("Random seed", 1, 9999, 42)

df = get_funnel(int(n_months), urm_bias, int(seed))

# Persist for sub-pages.
st.session_state["funnel_df"] = df
st.session_state["config"] = {"months": n_months, "urm_bias": urm_bias, "seed": seed}

# Sidebar drill filters ------------------------------------------------------
st.sidebar.divider()
st.sidebar.header("Drill-down filters")
roles_all = sorted(df["role"].unique().tolist())
selected_roles = st.sidebar.multiselect("Role", roles_all, default=roles_all)
locs_all = sorted(df["location"].unique().tolist())
selected_locs = st.sidebar.multiselect("Location", locs_all, default=locs_all)

filtered = df[df["role"].isin(selected_roles) & df["location"].isin(selected_locs)]

# --- Main --------------------------------------------------------------------
st.title("📈 Hiring Funnel Analytics")
st.caption("Conversion, source effectiveness, time-to-fill, and bias detection — the quarterly TA review in one dashboard.")

# KPI strip
conv = conversion_matrix(filtered)
applied = int(conv.loc["applied", "reached"])
hired = int(conv.loc["hired", "reached"])
offer_accept = conv.loc["accepted", "reached"] / max(conv.loc["offer", "reached"], 1)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Applications", f"{applied:,}")
c2.metric("Hires", f"{hired:,}")
c3.metric("Applied→Hired", f"{hired / max(applied, 1):.2%}")
c4.metric("Offer→Accept", f"{offer_accept:.1%}")
top_role = filtered.groupby("role").size().idxmax()
c5.metric("Top role volume", top_role)

st.divider()

# --- Funnel bar chart --------------------------------------------------------
st.subheader("Candidate volume at each stage")
funnel_display = pd.DataFrame(
    {"Stage": conv.index, "Reached": conv["reached"].values}
)
st.bar_chart(funnel_display, x="Stage", y="Reached", use_container_width=True)

# Conversion table
st.subheader("Stage-to-stage conversion rates")
st.dataframe(
    conv.style.format(
        {"reached": "{:,}", "pct_of_applied": "{:.2f}%", "stage_pass_rate_pct": "{:.2f}%"}
    ).background_gradient(subset=["stage_pass_rate_pct"], cmap="Greens"),
    use_container_width=True,
)
st.caption(
    "**Read**: 'stage_pass_rate_pct' is the % of candidates at this stage who "
    "advance to the next. The biggest drop is always applied→screened (resume review)."
)

st.divider()

st.markdown(
    """
### Navigate

- **📣 Source Effectiveness** — which channels actually produce hires per applicant?
- **⚖️ Bias Detection** — where in the funnel does demographic pass-through diverge?
"""
)

# Export
st.download_button(
    label="⬇️ Download filtered funnel data (CSV)",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="hiring_funnel_export.csv",
    mime="text/csv",
)
