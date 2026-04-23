# Hiring Funnel Analytics

End-to-end recruiting funnel analytics: **conversion rates, source effectiveness, time-to-fill, and demographic bias detection** — the analyses a People Analytics team actually delivers to the CHRO every quarter.

**Built by a former Fortune 500 talent acquisition leader who spent 15+ years running the operations this project analyzes.**

### 🚀 [Live demo: hiring-funnel-analytics-jotterson.streamlit.app](https://hiring-funnel-analytics-jotterson.streamlit.app/)

Interactive funnel, source effectiveness, and demographic bias detection — adjust the injected bias slider to see how the audit holds up.

![Hiring funnel](docs/funnel_overview.png)

---

## The business problem

Recruiting is one of the largest HR operating budgets at any employer, but the *quality* of that spend is rarely measured. Most TA organizations track applications, interviews, and hires — not the ratios between them, the variance across sources, or the demographic differences in pass rates.

This project demonstrates the four analyses that drive real TA strategy decisions:

1. **Funnel conversion** — where in the pipeline do candidates drop?
2. **Source effectiveness** — which channels actually produce hires per dollar spent?
3. **Time-to-fill** — which roles need pipelines built before reqs open?
4. **Demographic pass-rate analysis** — does the funnel treat candidates equally at each gate?

---

## The data

Simulated 12-month hiring funnel: **~50,000 candidate applications across 8 roles, 6 sources, 6 locations**.

### Per-candidate schema

| Field | Type | Notes |
|---|---|---|
| `candidate_id` | string | Unique identifier |
| `role` | categorical | 8 roles: Sales Rep, Software Engineer, ML Engineer, Product Manager, Data Analyst, Security Engineer, Recruiter, HR Generalist |
| `location` | categorical | 6 locations: NY, SF, Austin, Remote, Seattle, Denver |
| `source` | categorical | 6 sources: Referral, LinkedIn, Job Board, Company Site, Agency, Event/Conference |
| `gender` | categorical | F / M / NB (non-binary) |
| `is_urm` | boolean | URM flag (Black, Hispanic, Other/Multi) |
| `applied_date` | date | Application date across 12-month window |
| `stage_reached` | ordered categorical | Furthest stage: applied → screened → phone_screen → onsite → offer → accepted → hired |
| `days_in_stage` | integer | Days spent at terminal stage |

### Calibration

Real hiring funnel data is always proprietary. The simulator is calibrated against published industry benchmarks:

- **Overall applied → hired conversion**: ~1.5% (aligns with Talent Board / Jobvite corporate-role data)
- **Source mix**: ~15% referrals, ~35% LinkedIn, ~25% job boards (SHRM 2023)
- **Phone screen → onsite**: ~40–45% pass rate
- **Offer → accept**: ~80–90% (role dependent)

### Injected signals (to be recovered by analysis)

| Signal | Effect | Where it shows up |
|---|---|---|
| **Referral boost** | 1.6x pass-rate multiplier at every stage | Source effectiveness page: referrals show ~40x hire rate vs job boards |
| **Role difficulty** | ML and Security roles: ~30% lower screened→phone pass rate | Specialized roles show lower overall conversion and longer time-to-fill |
| **URM screen bias** | 12% lower relative URM pass rate at the phone-screen gate only | Bias detection page: 4-5 percentage point absolute gap, p < 0.001 |

---

## What the analytics recover

### Funnel conversion

```
              reached  pct_of_applied  stage_pass_rate_pct
applied         50138          100.00                19.81
screened         9932           19.81                46.81
phone_screen     4649            9.27                45.13
onsite           2098            4.18                43.76
offer             918            1.83                88.78
accepted          815            1.63                95.83
hired             781            1.56                  NaN
```

**What this tells us**: the single biggest drop is at the applied→screened gate (80% elimination at resume review). Offer→accept at ~89% is healthy — below 75% would flag a comp-competitiveness problem.

### Source effectiveness

![Source effectiveness](docs/source_effectiveness.png)

**Referrals produce hires at 6.5% rate. Job boards produce hires at 0.15% rate — a 42x difference.**

This is the quantitative backing for every referral bonus program ever run. It's also why TA budget should rarely be dominated by job-board spend: high volume, terrible conversion. The number of organizations that still allocate 60%+ of sourcing budget to Indeed/LinkedIn ads despite this finding is one of the most robust patterns in TA operations.

### Time-to-hire by role

![Time-to-fill](docs/time_to_fill.png)

Specialized roles (ML, Security) show the most variance in fill time. This is the argument for *pipelining before the req opens* — the roles where waiting to source until a req is approved means 2-3 months of missed productivity.

### Bias detection (the most important analysis)

A two-proportion z-test compares URM and non-URM candidate pass rates at a specific funnel gate. This is the same hypothesis test used in clinical trials for comparing outcome rates between treatment arms — applied here to hiring gates instead of medical endpoints.

**The math.** For two groups with pass rates p_URM and p_nonURM and sample sizes n_URM and n_nonURM:

```
p_pooled = (passes_URM + passes_nonURM) / (n_URM + n_nonURM)

            √( p_pooled × (1 − p_pooled) × (1/n_URM + 1/n_nonURM) )
standard_error = ────────────────────────────────────────────────────

z = (p_URM − p_nonURM) / standard_error

p_value = 2 × (1 − Φ(|z|))      where Φ is the standard normal CDF
```

A p-value below 0.05 indicates the observed pass-rate difference is unlikely to have arisen by chance under the null hypothesis of equal pass rates. This is evidence of a systematic difference — not proof of discrimination, but enough to trigger a targeted review.

**Recovered result on simulated data** (injected 12% relative URM screen bias):

```
  n_urm                     2,759
  n_nonurm                  7,173
  pass_rate_urm             0.4353
  pass_rate_nonurm          0.4807
  absolute_gap_pp           4.54
  relative_gap_pct          9.44
  z_stat                    -4.06
  p_value                   < 0.001
```

A 4.5 percentage-point gap at the phone-screen gate, p < 0.001.

### Null-effect sanity check

Set the injected URM bias to zero and re-run. The recovered gap drops to 0.7 percentage points with `p = 0.51` — not statistically distinguishable from zero. The test is not generating false positives, which is the check that matters for any bias-detection methodology.

![Bias by stage](docs/bias_by_stage.png)

The stage-by-stage breakdown shows the gap concentrates at phone screen — exactly where the affinity-bias signal was injected. A real audit would use this to target intervention specifically at that gate (structured screen rubric, recruiter calibration, blind screen trial) rather than applying generic "DEI training" to the whole pipeline.

---

## What's in this repo

| File | Purpose |
|---|---|
| `src/simulate.py` | Generates a calibrated 12-month hiring funnel dataset. |
| `src/analyze.py` | Core analytics: conversion, sources, time-to-fill, bias tests. |
| `src/visualize.py` | Regenerates every figure in this README. |
| `notebooks/01_funnel_analytics.ipynb` | Full analyst walkthrough with TA-side interpretation. |
| `docs/` | Generated visualizations. |

---

## Interactive dashboard

A multi-page Streamlit app ships with the repo. [Try the live version](https://hiring-funnel-analytics-jotterson.streamlit.app/) or run it locally.

### Home page

- **Sidebar**: funnel parameters (months to simulate, injected URM bias percent, random seed) and drill-down filters (role, location multi-select)
- **KPI strip**: total applications, total hires, applied→hired rate, offer→accept rate, top role by volume
- **Candidate volume bar chart** at each stage of the funnel
- **Stage-to-stage conversion rates table** with green gradient on pass rate
- CSV export of filtered candidate data

### Source Effectiveness

Where recruiting investment actually produces hires.

- **KPI strip**: best source and its hire rate, worst source and its hire rate, best-to-worst multiplier
- **Grouped bar chart**: conversion at three gates (phone screen, offer, hire) by source
- **Source ranking table** with green gradient on hire rate
- **Volume-vs-effectiveness scatter** (Plotly): each source plotted by application volume versus hire rate, with bubble size proportional to volume. The ideal sits top-right (high volume, high hire rate); budget drains sit bottom-right (high volume, low hire rate)
- **Dynamic budget reallocation recommendation** that names the specific high-yield and low-yield sources based on the current filtered data
- CSV export

### Bias Detection

The most important page for a People Analytics audience.

- **KPI strip**: URM pass rate with sample size, non-URM pass rate with sample size, absolute percentage-point gap, p-value (color-coded significant vs not)
- **Alert banner**: green success if no significant gap detected, red error if gap is statistically significant — includes the relative gap percentage and suggested next-step language
- **Stage-by-stage pass rate bar chart** split by URM status — shows where in the funnel the divergence occurs (intervention at phone screen is a different operational response than intervention at onsite)
- **Stage detail table** with red-green heatmap on the gap column
- **Phone-screen gap by role**: aggregate bias numbers hide variance across hiring managers and screeners. This view identifies which specific roles to focus intervention on rather than applying generic training across the board
- **Disclaimer block** explaining what the test does and does not mean (evidence of something, not proof of discrimination; could reflect resume quality, recruiter assignment, rubric design, or structured vs unstructured screens)

```bash
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

**Tableau / Power BI users:** generate Tableau-ready CSVs:
```bash
python -m src.export_tableau  # writes tableau/candidates.csv + aggregated CSVs
```
Then follow [docs/TABLEAU.md](docs/TABLEAU.md) for the recipe to build four dashboard views.

## Run the core analytics scripts

```bash
python -m src.analyze       # runs all analytics, prints tables
python -m src.visualize     # regenerates the visualizations
jupyter lab notebooks/01_funnel_analytics.ipynb
```

---

## What People Analytics teams actually do with this

| Finding | Action |
|---|---|
| Referrals 40x better than job boards | Shift sourcing budget; expand referral bonus program. |
| ML Eng / Security Eng: highest time-to-fill | Build pipelines 30-60 days before the req opens; consider contract-to-hire. |
| URM phone-screen gap of 4.5pp, p<0.001 | Review screen rubric; audit which recruiters drive the gap; pilot structured screens. |
| Offer-accept rate < 80% for any role | Comp benchmark review; geographic premium review. |
| Top-of-funnel volume by source ≠ hires by source | Reallocate recruiter time to high-yield channels. |

**The measurement loop:** every quarterly review uses the same metrics against the same definitions. The intervention's effect is visible in the *next* quarter's numbers. That's what distinguishes analytics from reporting.

---

## What a serious reviewer will ask

1. **"These bias tests control for nothing."** Correct — the headline tests are marginal. A complete audit regresses pass rate on demographics *after* controlling for resume strength, role, source, and time period. Included in the notebook as a follow-on analysis.

2. **"Referral boost is confounded with role/level."** Also correct — referrals tend to concentrate in higher-level engineering hires, where overall pass rates are higher anyway. A rigorous source analysis would include fixed effects for role.

3. **"Simulated data can't demonstrate this works on real data."** Fair. The value is showing the *methodology* — what metrics to compute, what tests to run, what breakdowns to present. Any real deployment would port the same analysis functions to an actual ATS export (Greenhouse, Lever, Workday Recruiting).

4. **"Bias detection alone doesn't fix the problem."** Absolutely. Detection is step 1; intervention design is step 2; impact measurement is step 3. The loop is what creates change, not any single quarter's analysis.

---

## About

Built by **Jeff Otterson** — talent acquisition leader with Fortune 500 experience at Amazon and Oracle. Building a portfolio of people analytics projects applying modern data science and ML to the operational problems I've seen firsthand.

- **Companion projects**: [hr-attrition-predictor](https://github.com/Jott2121/hr-attrition-predictor) · [compensation-equity-analysis](https://github.com/Jott2121/compensation-equity-analysis)
- **MeritForge AI**: [meritforgeai.com](https://www.meritforgeai.com)

MIT licensed.
