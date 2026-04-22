# Building the Funnel Dashboard in Tableau

The Streamlit app (`streamlit run app/streamlit_app.py`) is the primary interactive dashboard. For Tableau users, generate the data with `python -m src.export_tableau` and build the four views below.

## Generated CSVs

| File | Rows | Purpose |
|---|---|---|
| `tableau/candidates.csv` | ~50,000 | One row per candidate with stage_reached, source, role, demographics |
| `tableau/conversion_by_source.csv` | 6 | Source × stage pass rates (pre-aggregated) |
| `tableau/bias_by_stage.csv` | ~12 | URM vs non-URM pass rate per stage |

## Four dashboard views

### 1. Funnel bar chart
- **From** `candidates.csv`
- **Rows:** `stage_reached` (sorted in funnel order: applied → screened → phone_screen → onsite → offer → accepted → hired)
- **Columns:** Record count
- **Color:** same-stage gradient (darker = later stage)

### 2. Source effectiveness (grouped bar)
- **From** `conversion_by_source.csv`
- **Columns:** `source`
- **Rows:** three measures side-by-side: `pct_reach_phone_screen`, `pct_reach_offer`, `pct_hired`
- Sort source by `pct_hired` descending.

### 3. Volume vs hire rate scatter
- **From** `conversion_by_source.csv`
- **Columns:** `applicants`
- **Rows:** `pct_hired`
- **Size:** `applicants`
- **Color / label:** `source`
- The "budget reallocation" chart — the ideal source sits top-right, budget drains sit bottom-right.

### 4. Bias-by-stage diverging bar
- **From** `bias_by_stage.csv`
- **Columns:** `to_stage` (in order)
- **Rows:** `pass_rate_pct`
- **Color:** `group` (URM vs non-URM)
- Highlight largest-gap stage with a text annotation.

## Filters

- `role` (multi-select)
- `location` (multi-select)
- `applied_month` (range)
- `source` (multi-select)

## Notes

- **Aggregate before visualizing.** With 50k rows Tableau will be slow if you color by individual candidate — roll up to month × source × role first.
- **Order matters.** Set `stage_reached` as an ordered dimension so the funnel bar chart doesn't render alphabetically.
- **The bias view is the most important chart for a People Analytics dashboard.** Keep it prominent.
