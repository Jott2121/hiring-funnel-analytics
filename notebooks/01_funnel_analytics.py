# %% [markdown]
# # Hiring Funnel Analytics
#
# This notebook walks through the standard analytics a People Analytics team
# runs on the recruiting funnel — the analyses that actually change TA
# strategy and budget allocation.
#
# 1. Overall funnel conversion (where do candidates drop?)
# 2. Source effectiveness (which channels actually produce hires?)
# 3. Time-to-fill (how long does each role take?)
# 4. Bias detection (does pass-through vary by demographic?)

# %%
from src.simulate import simulate_funnel
from src.analyze import (
    conversion_matrix,
    source_effectiveness,
    time_to_fill_by_role,
    bias_test_phone_screen,
    bias_by_stage,
)

df = simulate_funnel()
print(f"{len(df):,} candidate applications simulated across {df['role'].nunique()} roles")

# %% [markdown]
# ## 1. Overall funnel conversion
#
# The single most important TA metric: what fraction of applicants actually
# get hired, and where does the biggest drop happen?

# %%
print(conversion_matrix(df))

# %% [markdown]
# **What this tells us:** ~1.5% of applicants ultimately get hired (realistic
# for mid-market tech roles). The steepest drop is `applied → screened`
# (~80% elimination, mostly by resume review) — which is exactly where AI
# resume-screening tools are now targeting.
#
# Offer-to-accept conversion (~88%) is the most important leading indicator
# for comp competitiveness. Drops below 75% typically mean offer packages
# are below market.

# %% [markdown]
# ## 2. Source effectiveness
#
# Where should recruiting spend go? Aggregate conversion flips the naive
# view based on top-of-funnel volume.

# %%
print(source_effectiveness(df).round(2).to_string(index=False))

# %% [markdown]
# **Referrals dominate.** Despite making up only ~15% of top-of-funnel volume,
# referrals produce disproportionate hires per applicant (~40x the hire rate
# of job-board applicants). This is the quantitative backing for every
# "referral bonus" program ever run.
#
# **Job boards are a volume trap.** They generate the most applications but
# convert to hires at the lowest rate by an order of magnitude. Reducing
# job-board spend in favor of referral bonuses or targeted sourcing usually
# improves hires per dollar.

# %% [markdown]
# ## 3. Time-to-fill
#
# Benchmarks: 30 days is "good", 50+ is "concerning." Here we show median
# days spent in the final (hire) stage by role — specialized roles (ML,
# Security) typically take longer end-to-end.

# %%
print(time_to_fill_by_role(df))

# %% [markdown]
# ## 4. Bias detection — the most important analysis
#
# **Does the funnel's pass-through rate differ by demographic class?**
# A two-proportion z-test on the phone-screen gate:

# %%
result = bias_test_phone_screen(df)
for k, v in result.items():
    if isinstance(v, float):
        print(f"  {k:25s} {v:.4f}")
    else:
        print(f"  {k:25s} {v}")

# %% [markdown]
# **URM candidates pass the phone-screen gate at ~43.5% vs ~48.1% for non-URM
# candidates** — a 4.5 percentage-point gap, or ~9% relative reduction, with
# p < 0.001.
#
# A p-value alone isn't enough to take action. This finding needs to be
# triangulated against: resume quality at screen, interviewer assignment,
# structured interview consistency, and (critically) whether it replicates
# in the next cohort. But it's the *starting* question a People Analytics
# team is expected to answer.

# %% [markdown]
# ## 5. Where exactly does the divergence appear?
#
# Headline bias numbers hide *which stage* the gap appears at. That matters
# operationally: a gap at phone screen points to one intervention (training
# for screeners), a gap at onsite points to another (interviewer calibration).

# %%
print(bias_by_stage(df).round(2).to_string(index=False))

# %% [markdown]
# ## 6. What a People Analytics team would actually do with this
#
# | Finding | Action |
# |---|---|
# | Referrals 40x better than job boards | Shift sourcing budget; expand referral bonus program. |
# | ML Eng / Security Eng: highest time-to-fill | Build pipelines before the req opens; consider contract-to-hire. |
# | URM phone-screen gap of 4.5pp, p<0.001 | Review screen rubric; audit which recruiters are driving the gap; implement blind screen trial in one business unit. |
# | Offer-accept rate < 80% for any role | Compensation benchmark review for that role. |
#
# **The measurement loop:** every quarterly review uses the same metrics
# against the same definitions, and the intervention's effect is visible
# in the *next* quarter's numbers. That's what distinguishes analytics
# from reporting.
