"""Simulate a realistic 12-month hiring funnel.

Models the standard stages:
    applied → screened → phone_screen → onsite → offer → accepted → hired

Each stage has a stage-specific base pass-through rate. The simulator injects
three realistic dynamics a People Analytics team wants to detect:

1. **Source variance** — referrals convert ~3x LinkedIn inbound at later stages.
2. **Role difficulty** — specialized roles (ML, security) have lower screened→phone
   rates (fewer qualified applicants per top-of-funnel).
3. **Diversity drop-off** — all else equal, non-URM candidates pass the phone-
   screen gate at a higher rate, modeling an "affinity bias" signal that
   analytics is supposed to surface.

The simulated data is *not* intended to represent any real employer — it's
calibrated on typical benchmarks from the Talent Board, LinkedIn Talent
Insights, and SHRM reports (2023-2024).
"""
from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd

STAGES = ["applied", "screened", "phone_screen", "onsite", "offer", "accepted", "hired"]

# Base pass-through rates between adjacent stages. These match roughly
# published funnel conversion benchmarks (~0.5% applied → hired industry-wide
# for corporate roles).
BASE_PASS_RATES = {
    ("applied", "screened"): 0.20,
    ("screened", "phone_screen"): 0.45,
    ("phone_screen", "onsite"): 0.40,
    ("onsite", "offer"): 0.35,
    ("offer", "accepted"): 0.80,
    ("accepted", "hired"): 0.95,
}

SOURCE_MIX = {
    "Referral": 0.15,
    "LinkedIn": 0.35,
    "Job Board": 0.25,
    "Company Site": 0.15,
    "Agency": 0.05,
    "Event/Conference": 0.05,
}

# Source-specific adjustments applied to pass-through rates.
SOURCE_MULT = {
    "Referral": 1.60,         # referrals convert much better
    "LinkedIn": 1.00,
    "Job Board": 0.80,
    "Company Site": 0.95,
    "Agency": 1.20,
    "Event/Conference": 1.10,
}

ROLES = {
    "Sales Rep": {"applicants_per_open": 120, "difficulty": 1.00},
    "Software Engineer": {"applicants_per_open": 180, "difficulty": 0.90},
    "ML Engineer": {"applicants_per_open": 90, "difficulty": 0.75},  # harder to clear screen
    "Product Manager": {"applicants_per_open": 250, "difficulty": 1.00},
    "Data Analyst": {"applicants_per_open": 160, "difficulty": 1.00},
    "Security Engineer": {"applicants_per_open": 60, "difficulty": 0.70},
    "Recruiter": {"applicants_per_open": 140, "difficulty": 1.00},
    "HR Generalist": {"applicants_per_open": 130, "difficulty": 1.00},
}

LOCATIONS = ["NY", "SF", "Austin", "Remote", "Seattle", "Denver"]


def simulate_funnel(
    n_months: int = 12,
    seed: int = 42,
    urm_bias: float = 0.12,
) -> pd.DataFrame:
    """Generate a candidate-level funnel dataset.

    Each row = one candidate application. Stage reached is the furthest point
    they got to; days_in_stage is the time they spent at their terminal stage.

    Parameters
    ----------
    n_months : how many months of applications to simulate.
    urm_bias : fractional reduction in phone-screen pass rate for URM
        candidates. 0.12 means URM candidates pass the screen at (1-0.12)=0.88
        the rate of non-URM candidates with otherwise identical characteristics.
    """
    rng = np.random.default_rng(seed)

    start_date = datetime(2025, 4, 1)
    rows: list[dict] = []

    for month_offset in range(n_months):
        month_start = start_date + timedelta(days=30 * month_offset)
        seasonal = 1.0 + 0.15 * np.sin(month_offset / 12 * 2 * np.pi)

        for role, role_cfg in ROLES.items():
            # 2-6 requisitions open per role per month, roughly.
            n_reqs = int(rng.integers(2, 7))
            for _ in range(n_reqs):
                n_applicants = int(role_cfg["applicants_per_open"] * seasonal * rng.normal(1, 0.15))
                n_applicants = max(10, n_applicants)

                sources = rng.choice(
                    list(SOURCE_MIX.keys()),
                    size=n_applicants,
                    p=list(SOURCE_MIX.values()),
                )
                locations = rng.choice(LOCATIONS, size=n_applicants)
                # Demographic distribution (bias only affects pass rates, not applicant mix)
                gender = rng.choice(["F", "M", "NB"], size=n_applicants, p=[0.45, 0.53, 0.02])
                urm = rng.random(n_applicants) < 0.28  # ~28% URM applicants

                for i in range(n_applicants):
                    applied_date = month_start + timedelta(
                        days=int(rng.integers(0, 28))
                    )
                    source = str(sources[i])
                    stage_reached = "applied"
                    pass_mult = SOURCE_MULT[source] * role_cfg["difficulty"]

                    for from_stage, to_stage in zip(STAGES[:-1], STAGES[1:]):
                        p = BASE_PASS_RATES[(from_stage, to_stage)] * pass_mult
                        # URM bias kicks in at phone screen specifically — a
                        # realistic place for affinity bias to manifest.
                        if urm[i] and to_stage == "phone_screen":
                            p *= 1 - urm_bias
                        p = min(max(p, 0.01), 0.98)
                        if rng.random() < p:
                            stage_reached = to_stage
                        else:
                            break

                    # Days-in-stage at terminal stage — rough benchmarks.
                    days_in_stage = {
                        "applied": int(rng.integers(1, 8)),
                        "screened": int(rng.integers(2, 10)),
                        "phone_screen": int(rng.integers(3, 14)),
                        "onsite": int(rng.integers(5, 21)),
                        "offer": int(rng.integers(3, 14)),
                        "accepted": int(rng.integers(3, 21)),
                        "hired": int(rng.integers(7, 30)),
                    }[stage_reached]

                    rows.append(
                        {
                            "candidate_id": f"{role[:3].upper()}-{month_offset:02d}-{len(rows):06d}",
                            "role": role,
                            "location": str(locations[i]),
                            "source": source,
                            "gender": str(gender[i]),
                            "is_urm": bool(urm[i]),
                            "applied_date": applied_date.date(),
                            "stage_reached": stage_reached,
                            "days_in_stage": days_in_stage,
                        }
                    )

    df = pd.DataFrame(rows)
    # Order stages categorically so pandas preserves the funnel order.
    df["stage_reached"] = pd.Categorical(df["stage_reached"], categories=STAGES, ordered=True)
    return df


if __name__ == "__main__":
    df = simulate_funnel()
    print(f"{len(df):,} candidate applications across {df['role'].nunique()} roles")
    print(df.head())
    print("\nStage distribution:")
    print(df["stage_reached"].value_counts().sort_index())
