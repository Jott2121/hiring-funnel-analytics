"""Sourcing channel effectiveness deep-dive."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.analyze import source_effectiveness, STAGES  # noqa: E402

st.set_page_config(page_title="Source Effectiveness", page_icon="📣", layout="wide")

if "funnel_df" not in st.session_state:
    st.warning("👋 Open the main page first to generate the funnel.")
    st.stop()

df = st.session_state["funnel_df"]

st.title("📣 Source Effectiveness")
st.caption(
    "Where does recruiting investment produce hires? Volume at the top of "
    "the funnel is misleading — conversion at each gate is what matters."
)

src = source_effectiveness(df)

# KPI strip
best = src.iloc[0]
worst = src.iloc[-1]
c1, c2, c3 = st.columns(3)
c1.metric("Best source", best["source"], f"{best['pct_hired']:.2f}% hire rate")
c2.metric("Worst source", worst["source"], f"{worst['pct_hired']:.2f}% hire rate")
c3.metric(
    "Best vs worst multiplier",
    f"{best['pct_hired'] / max(worst['pct_hired'], 0.01):.0f}x",
    help="Hire rate of best source divided by worst source",
)

st.divider()

# Conversion by source
st.subheader("Conversion at each gate, by source")
pivot = src.set_index("source")[["pct_reach_phone_screen", "pct_reach_offer", "pct_hired"]]
pivot.columns = ["→ Phone screen", "→ Offer", "→ Hired"]
st.bar_chart(pivot, use_container_width=True)

st.dataframe(
    src.style.format(
        {
            "applicants": "{:,}",
            "pct_reach_phone_screen": "{:.2f}%",
            "pct_reach_offer": "{:.2f}%",
            "pct_hired": "{:.2f}%",
        }
    ).background_gradient(subset=["pct_hired"], cmap="Greens"),
    use_container_width=True,
    hide_index=True,
)

st.divider()

# --- Volume vs effectiveness: the "budget reallocation" chart ---------------
st.subheader("Volume-vs-effectiveness matrix")
st.caption(
    "The quadrant you want to be in: high volume × high hire rate. The "
    "quadrant you want to fix: high volume × low hire rate (budget drain). "
    "Referrals typically sit in low-volume × high-rate — the case for "
    "expanding a referral bonus program."
)

matrix = src.copy()
matrix["bubble"] = matrix["applicants"] / matrix["applicants"].max() * 200 + 50

# Simple scatter using st.plotly_chart if available, else st.scatter_chart
try:
    import plotly.express as px

    fig = px.scatter(
        matrix,
        x="applicants",
        y="pct_hired",
        size="bubble",
        color="source",
        text="source",
        labels={"applicants": "Applications (volume)", "pct_hired": "% hired"},
        title="Source volume vs hire rate",
    )
    fig.update_traces(textposition="top center")
    st.plotly_chart(fig, use_container_width=True)
except ImportError:
    st.scatter_chart(
        matrix,
        x="applicants",
        y="pct_hired",
        size="bubble",
        color="source",
        use_container_width=True,
    )

st.divider()

# --- Recommendation box ------------------------------------------------------
st.subheader("Budget reallocation recommendation")
top3 = src.head(3)["source"].tolist()
bottom_sources = src[src["pct_hired"] < 0.5]["source"].tolist()

st.info(
    f"""
**Shift spend toward:** {', '.join(top3)} — these channels produce hires at 5–40x the rate of the worst performers.

**Audit spend on:** {', '.join(bottom_sources) if bottom_sources else 'no sources below 0.5% hire rate — funnel is healthy'}.
These produce volume but not hires; reducing spend here is typically the biggest cost-per-hire win.

**Protect referrals at all costs.** Despite being a smaller share of top-of-funnel volume,
referrals almost always show the highest per-applicant hire rate. Expand referral bonus
programs before expanding job-board spend.
"""
)

# Export
st.download_button(
    label="⬇️ Download source effectiveness (CSV)",
    data=src.to_csv(index=False).encode("utf-8"),
    file_name="source_effectiveness.csv",
    mime="text/csv",
)
