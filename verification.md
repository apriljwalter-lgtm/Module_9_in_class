# Verification

| # | Check | App shows | pandas gives | Match? |
|---|---|---|---|---|
| 1 | r for `age` vs `systolic_bp`, all participants | 0.463 | 0.46269| yes|
| 2 | r for `bmi` vs `waist_cm`, all participants | 0.903 | 0.90253| yes|
| 3 | r for `waist_cm` vs `hdl_chol`, all participants | -0.335 | -0.334986 | yes |
| 4 | r and n for `age` vs `systolic_bp`, **Female only** | r= 0.555, n= 2263 | r= 0.555342 n=2263| yes |
| 5 | r and n for `age` vs `systolic_bp`, **Male only** | r= 0.351, n= 2170 | r = 0.350697 n=2170| yes |
| 6 | With the filter set to Female, does the heatmap's `age`/`systolic_bp` square match row 4? | r= 0.56, n=2263 | r=0.555342, n=2263| yes |
