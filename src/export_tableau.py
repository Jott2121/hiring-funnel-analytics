"""Export Tableau-ready CSVs for hiring funnel analytics.

Run:
    python -m src.export_tableau

Produces three CSVs:
    tableau/candidates.csv            — raw per-candidate long table
    tableau/conversion_by_source.csv  — source × stage pass rates
    tableau/bias_by_stage.csv         — URM vs non-URM pass rate per stage
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.simulate import simulate_funnel, STAGES
from src.analyze import source_effectiveness, bias_by_stage

ROOT = Path(__file__).resolve().parents[1]
TABLEAU_DIR = ROOT / "tableau"
TABLEAU_DIR.mkdir(exist_ok=True)


def export() -> None:
    df = simulate_funnel()

    # 1. Candidates, flat
    flat = df.copy()
    flat["stage_reached_num"] = flat["stage_reached"].cat.codes
    flat["is_hired"] = (flat["stage_reached"] == "hired").astype(int)
    flat["reached_phone_screen"] = (flat["stage_reached_num"] >= STAGES.index("phone_screen")).astype(int)
    flat["reached_onsite"] = (flat["stage_reached_num"] >= STAGES.index("onsite")).astype(int)
    flat["reached_offer"] = (flat["stage_reached_num"] >= STAGES.index("offer")).astype(int)
    flat["applied_date"] = flat["applied_date"].astype(str)  # Tableau prefers ISO strings
    flat["applied_month"] = flat["applied_date"].str[:7]

    out1 = TABLEAU_DIR / "candidates.csv"
    flat.to_csv(out1, index=False)
    print(f"Wrote {len(flat):,} rows to {out1}")

    # 2. Source effectiveness
    out2 = TABLEAU_DIR / "conversion_by_source.csv"
    source_effectiveness(df).to_csv(out2, index=False)
    print(f"Wrote {out2}")

    # 3. Bias by stage (tidy)
    out3 = TABLEAU_DIR / "bias_by_stage.csv"
    bias_by_stage(df).to_csv(out3, index=False)
    print(f"Wrote {out3}")


if __name__ == "__main__":
    export()
