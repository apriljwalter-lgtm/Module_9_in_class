# Plan: NHANES Health Correlation Explorer (`app.py`)

## Context
M9 exercise: a single-file Streamlit app that explores correlations between health measures in `nhanes_health.csv`. Every number shown (r, n) must be computed from the **filtered** data so it can be checked by hand in pandas (`verification.md`, checks 1–6).

## What the data looks like (read from the CSV)
- 4,433 rows, 11 columns. No missing values in the current file.
- `sex`: text, `Female` (2,263) / `Male` (2,170). It is **only a filter** and is never put into a correlation.
- 10 numeric columns: `age` (20–80, 80 = 80+), `bmi`, `waist_cm`, `systolic_bp`, `diastolic_bp`, `hba1c`, `total_chol`, `hdl_chol`, `sleep_hours`, `sedentary_minutes`.

## Stack
Python. `app.py` has exactly three imports: `streamlit`, `pandas` and `seaborn`. It does **not** import `numpy` or `matplotlib`. `scipy` is not needed either, because pandas computes Spearman itself. No other packages. One file, `app.py`, loading the CSV with the relative path `nhanes_health.csv`.

How plots work without importing matplotlib:
- Seaborn draws onto its own current figure and returns the axes. The app gets the figure with `ax.figure`, sizes it with `fig.set_size_inches(...)`, and renders it with `st.pyplot(fig, clear_figure=True)`. The figure is cleared after each render, so the scatter and heatmap don't draw on top of each other.
- Everything else is done in pandas: the binned means (`pd.qcut` and `groupby`), the per-square n (`notna().astype(int).T @ notna().astype(int)`), the heatmap's string labels (a DataFrame of strings), and the threshold groups (a labeled Series passed as `hue`).

Run command:
```bash
uv run --with streamlit,pandas,seaborn,scipy streamlit run app.py
```

## Rules for the numbers
- `NUMERIC_COLS` is a hard-coded list of the 10 numeric columns. `sex` is excluded everywhere.
- **Missing values:** dropped pairwise. In the pairwise view, n = rows where both X and Y are present. In the heatmap, pandas `df.corr()` already uses pairwise-complete data. There are no NaNs today, so every n equals the filtered row count, but the logic stays correct if that changes.
- **Method:** the pairwise r and the heatmap both use `Series.corr(method=…)` / `DataFrame.corr(method=…)` with the method from the sidebar toggle (`"pearson"` or `"spearman"`). This is the same call the verification snippet uses, so the numbers will match exactly.
- **n next to every r:** the pairwise view shows r and n side by side. Every heatmap square shows its own r and n, e.g. `0.53` above `n=2263`. Each square's n is the pairwise-complete count for that pair: `notna().T @ notna()` on the selected columns.
- **Heatmap colors:** `vmin=-1, vmax=1, center=0`, a diverging colormap (`RdBu_r`). The annotations are built as a string array (r to 2 decimals plus n) and passed with `annot=labels, fmt=""`. The font size shrinks as more variables are selected.
- **Small n:** if fewer than 3 rows remain after filtering, show a warning instead of r, n and the plots.

## Layout and data flow
```
load_data()  (@st.cache_data, reads CSV)
   │
sidebar: sex (All / Female / Male), age range slider (20–80), method toggle (Pearson / Spearman)
   │
filtered = df[sex match & age.between(lo, hi)]  ← computed once and passed to every section
   │
├─ 1. Data preview   – description, data dictionary, filter summary, st.dataframe(filtered)
├─ 2. Pairwise view  – X/Y selectboxes, threshold coloring, scatter + trend line, r, n
└─ 3. Heatmap        – multiselect of variables, annotated heatmap fixed to −1..1
```
Each section is a tab (`st.tabs`) so the page stays short. All three read the same `filtered` DataFrame, so changing a filter updates the table, scatter, r, n and heatmap together.

## Features in detail
1. **Data preview:** a few sentences about NHANES 2017–2018: adults aged 20+, one row per participant, the sample is oversampled so results describe this sample and not the US population, and age 80 means 80+. Below that, a compact data dictionary (column, units, threshold), a line such as "Showing 1,234 of 4,433 participants", and `st.dataframe(filtered)`.
2. **Pairwise view:**
   - X and Y selectboxes from `NUMERIC_COLS`, defaulting to `age` and `systolic_bp`. If X equals Y, show a note.
   - `st.metric` for r (3 decimals, labelled "Pearson r" or "Spearman ρ") and for n.
   - Seaborn scatter with small, semi-transparent points (about 4k rows), plus a trend overlay chosen with a radio, "Linear fit / Binned means". The linear fit is an OLS line (`sns.regplot`, `ci=None`). Binned means split X into about 10 quantile bins and plot the mean of Y at each bin's mean X. Binned means are the default because they show non-linear patterns like the U-shaped sleep curve.
   - "Color points by threshold" selectbox: None, SBP ≥ 130, DBP ≥ 80, BMI ≥ 30, HbA1c ≥ 6.5, Total chol ≥ 240. Points are colored by whether each participant meets the threshold, and the legend shows the count in each group.
   - Caption reminder: an r near 0 does not mean there is no relationship, so check the plot's shape.
3. **Heatmap:** a multiselect of `NUMERIC_COLS` (all selected by default). At least 2 variables are required. The heatmap uses `filtered[selected].corr(method)`, with an annotated square for every cell, including the diagonal, and a full matrix rather than a masked triangle so every square shows its value. Each square is labeled with both r and its n. The figure is sized so the two-line labels stay readable when all 10 variables are selected. Caption shows the method and the filters that are active.

## Build order (small steps, check each one in the browser)
1. Load the CSV, define `NUMERIC_COLS`, add the sidebar filters, build `filtered`, show the preview table and row count. Check that the row counts change with the filters.
2. Add the method toggle and the pairwise r and n metrics. Check them against the pandas snippet for check 4 (Female, all ages).
3. Add the scatter with the trend line or binned means, then the threshold coloring.
4. Add the heatmap with the multiselect. Check that the Female `age`/`systolic_bp` cell matches step 2.
5. Polish: description text, captions, edge cases (n < 3, X = Y, fewer than 2 heatmap vars).
6. Add `requirements.txt` (`streamlit`, `pandas`, `seaborn`) for deployment. This happens later in Part 5, only when you ask.

## Verification
- Run the app with the command above.
- For each row of `verification.md`, read r and n in the app and compare them with a separate pandas computation, e.g. `f = df[df.sex=="Female"]; f.age.corr(f.systolic_bp), len(f)`. They should match to 3 decimals.
- Switch to Spearman and confirm that the pairwise r and the heatmap cell both change and still agree with `corr(method="spearman")`.
- Move the age slider and the sex filter, then confirm that the table count, n, r, the scatter and the heatmap all change together.
- Confirm that the heatmap colorbar always runs from −1 to 1, even when the selected variables are only weakly correlated.

## Review checklist: where the plan meets each item
| Criterion | Where to look in this plan |
|---|---|
| All five features | "Features in detail" 1–3 cover the preview, pairwise view and heatmap. "Layout and data flow" covers the filters (sidebar) and the Pearson/Spearman toggle. |
| r and n from filtered data | "Layout and data flow": `filtered` is built once and passed to every tab. The preview table, r, n, scatter and heatmap all read `filtered`, never `df`. |
| `sex` left out | "Rules for the numbers": `NUMERIC_COLS` is hard-coded without `sex`. The X/Y dropdowns and heatmap multiselect only offer `NUMERIC_COLS`. |
| Heatmap fixed −1 to 1 | "Rules for the numbers": `vmin=-1, vmax=1, center=0`. Verification includes a check with weakly correlated variables. |
| n next to every r | Pairwise view: r and n metrics side by side. Heatmap: every square is labeled with its r and its own pairwise n. |
| Builds a little at a time | "Build order": step 1 is the data and filters only, and each step ends with a check. |
| Allowed packages only | "Stack": `app.py` imports only streamlit, pandas and seaborn. There's no numpy, matplotlib, scipy or plotly import. |

## Points I resolved with defaults (tell me if you want them changed)
- **Plotting library:** seaborn (static plots), not plotly. This matches the run command.
- **Sex filter:** a radio with All, Female and Male, defaulting to All.
- **Trend overlay:** you pick it yourself, separately from the correlation method. Binned means is the default.
- **Thresholds:** fixed to the list above, with no custom cutoff input.
