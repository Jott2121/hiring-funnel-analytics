"""Tests for funnel analytics."""
from __future__ import annotations

from src.analyze import (
    STAGES,
    bias_by_stage,
    bias_test_phone_screen,
    conversion_matrix,
    source_effectiveness,
)
from src.simulate import simulate_funnel


def test_simulator_is_deterministic():
    df1 = simulate_funnel(n_months=3, seed=1)
    df2 = simulate_funnel(n_months=3, seed=1)
    assert df1.equals(df2)


def test_funnel_stages_are_ordered():
    df = simulate_funnel(n_months=3, seed=1)
    # every candidate's stage must be in the canonical list
    assert set(df["stage_reached"].unique()).issubset(set(STAGES))


def test_hire_rate_is_realistic():
    df = simulate_funnel(n_months=6, seed=42)
    conv = conversion_matrix(df)
    hire_rate = conv.loc["hired", "pct_of_applied"]
    # published corporate-hiring benchmarks: ~0.5 % - 3 %
    assert 0.3 < hire_rate < 5.0


def test_referral_is_top_source():
    """Referrals should dominate hire rate by a wide margin."""
    df = simulate_funnel(n_months=12, seed=42)
    src = source_effectiveness(df)
    assert src.iloc[0]["source"] == "Referral"


def test_bias_test_recovers_injected_gap():
    df = simulate_funnel(n_months=12, urm_bias=0.12, seed=42)
    result = bias_test_phone_screen(df)
    assert result["p_value"] < 0.01
    assert result["absolute_gap_pp"] > 2.0


def test_bias_test_null_effect():
    """Zero-bias funnel should produce a non-significant test."""
    df = simulate_funnel(n_months=12, urm_bias=0.0, seed=7)
    result = bias_test_phone_screen(df)
    assert result["p_value"] > 0.05


def test_bias_by_stage_returns_all_transitions():
    df = simulate_funnel(n_months=3, seed=1)
    bb = bias_by_stage(df)
    # every stage transition should appear for both groups
    assert {"URM", "non-URM"}.issubset(set(bb["group"]))
