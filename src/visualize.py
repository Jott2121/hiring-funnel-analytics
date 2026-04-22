"""Generate all README visualizations for hiring funnel analytics."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.simulate import simulate_funnel
from src.analyze import (
    STAGES,
    bias_by_stage,
    conversion_matrix,
    source_effectiveness,
    time_to_fill_by_role,
)

DOCS = Path(__file__).resolve().parents[1] / "docs"
DOCS.mkdir(exist_ok=True)

plt.rcParams.update({"figure.dpi": 110, "savefig.dpi": 160, "font.size": 11})


def plot_funnel(df: pd.DataFrame) -> None:
    conv = conversion_matrix(df)
    fig, ax = plt.subplots(figsize=(10, 5.5))
    bars = ax.barh(
        conv.index[::-1],
        conv["reached"].values[::-1],
        color=sns.color_palette("mako_r", n_colors=len(conv))[::-1],
    )
    for bar, count, pct in zip(bars, conv["reached"].values[::-1], conv["pct_of_applied"].values[::-1]):
        ax.text(
            bar.get_width() + conv["reached"].max() * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{int(count):,}  ({pct:.2f}%)",
            va="center",
            fontsize=10,
        )
    ax.set_xlabel("Candidates")
    ax.set_title("12-month hiring funnel — candidates reaching each stage", fontweight="bold")
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(DOCS / "funnel_overview.png", bbox_inches="tight")
    plt.close(fig)


def plot_source_effectiveness(df: pd.DataFrame) -> None:
    df_src = source_effectiveness(df)
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(df_src))
    w = 0.27
    ax.bar(x - w, df_src["pct_reach_phone_screen"], width=w, label="→ Phone screen", color="#2c7fb8")
    ax.bar(x, df_src["pct_reach_offer"], width=w, label="→ Offer", color="#8e44ad")
    ax.bar(x + w, df_src["pct_hired"], width=w, label="→ Hired", color="#27ae60")
    ax.set_xticks(x)
    ax.set_xticklabels(df_src["source"], rotation=20, ha="right")
    ax.set_ylabel("% of source applicants")
    ax.set_title("Source effectiveness — conversion at each gate", fontweight="bold")
    ax.grid(axis="y", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(DOCS / "source_effectiveness.png", bbox_inches="tight")
    plt.close(fig)


def plot_time_to_fill(df: pd.DataFrame) -> None:
    hired = df[df["stage_reached"] == "hired"].copy()
    # Total time-to-fill is a rough proxy: sum of median days per stage for each role.
    # For simulated data with only final-stage days, show median final stage days by role.
    by_role = hired.groupby("role")["days_in_stage"].median().sort_values()

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(by_role.index, by_role.values, color="#d35400")
    for bar, val in zip(bars, by_role.values):
        ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height() / 2, f"{val:.0f}d", va="center")
    ax.set_xlabel("Median days in final (hire) stage")
    ax.set_title("Time-to-hire by role (final stage only)", fontweight="bold")
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(DOCS / "time_to_fill.png", bbox_inches="tight")
    plt.close(fig)


def plot_bias_by_stage(df: pd.DataFrame) -> None:
    bb = bias_by_stage(df)
    piv = bb.pivot_table(index="to_stage", columns="group", values="pass_rate_pct")
    piv = piv.loc[[s for s in STAGES[1:] if s in piv.index]]

    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(piv))
    w = 0.38
    ax.bar(x - w / 2, piv["non-URM"], width=w, label="non-URM", color="#2c7fb8")
    ax.bar(x + w / 2, piv["URM"], width=w, label="URM", color="#e67e22")
    ax.set_xticks(x)
    ax.set_xticklabels(piv.index, rotation=20, ha="right")
    ax.set_ylabel("Pass rate (%)")
    ax.set_title(
        "Stage pass rates by URM status — where does demographic divergence appear?",
        fontweight="bold",
    )
    ax.grid(axis="y", alpha=0.3)
    ax.legend()

    # Annotate the divergent stage.
    diff = (piv["non-URM"] - piv["URM"]).abs()
    max_i = int(np.argmax(diff.values))
    ax.annotate(
        f"Largest gap: {diff.iloc[max_i]:.1f}pp\n({piv.index[max_i]})",
        xy=(max_i, piv.iloc[max_i].max() + 2),
        xytext=(max_i + 1, piv.iloc[max_i].max() + 15),
        fontsize=10,
        color="firebrick",
        fontweight="bold",
        arrowprops=dict(arrowstyle="->", color="firebrick"),
    )
    fig.tight_layout()
    fig.savefig(DOCS / "bias_by_stage.png", bbox_inches="tight")
    plt.close(fig)


def run() -> None:
    df = simulate_funnel()
    plot_funnel(df)
    plot_source_effectiveness(df)
    plot_time_to_fill(df)
    plot_bias_by_stage(df)
    print(f"Figures saved to {DOCS}/")


if __name__ == "__main__":
    run()
