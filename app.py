"""NHANES Health Correlation Explorer.

Run with:
    uv run --with streamlit,pandas,seaborn,scipy streamlit run app.py
"""

import pandas as pd
import seaborn as sns
import streamlit as st

DATA_PATH = "nhanes_health.csv"

# Every column except `sex`. `sex` is only a filter and never enters a correlation.
NUMERIC_COLS = [
    "age",
    "bmi",
    "waist_cm",
    "systolic_bp",
    "diastolic_bp",
    "hba1c",
    "total_chol",
    "hdl_chol",
    "sleep_hours",
    "sedentary_minutes",
]

DATA_DICTIONARY = pd.DataFrame(
    [
        ("age", "Age at screening (80 means 80 or older)", "years", ""),
        ("sex", "Female or Male (filter only)", "text", ""),
        ("bmi", "Body mass index", "kg/m²", "Obesity: ≥ 30"),
        ("waist_cm", "Waist circumference", "cm", "Abdominal obesity"),
        ("systolic_bp", "Mean of up to 3 systolic readings", "mmHg", "High BP: ≥ 130"),
        ("diastolic_bp", "Mean of up to 3 diastolic readings", "mmHg", "High BP: ≥ 80"),
        ("hba1c", "Glycohemoglobin (~3-month blood sugar)", "%", "Diabetes: ≥ 6.5"),
        ("total_chol", "Total cholesterol", "mg/dL", "High: ≥ 240"),
        ("hdl_chol", "HDL ('good') cholesterol", "mg/dL", "Low HDL is a risk factor"),
        ("sleep_hours", "Usual sleep on workdays (self-reported)", "hours", ""),
        ("sedentary_minutes", "Time sitting on a typical day (self-reported)", "minutes", ""),
    ],
    columns=["Column", "Meaning", "Units", "Health threshold"],
)

# Label -> (column, cutoff). A participant "meets" the threshold when value >= cutoff.
THRESHOLDS = {
    "None": None,
    "SBP ≥ 130 mmHg": ("systolic_bp", 130),
    "DBP ≥ 80 mmHg": ("diastolic_bp", 80),
    "BMI ≥ 30": ("bmi", 30),
    "HbA1c ≥ 6.5%": ("hba1c", 6.5),
    "Total cholesterol ≥ 240 mg/dL": ("total_chol", 240),
}

MIN_N = 3


@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)


st.set_page_config(page_title="NHANES Health Correlation Explorer", layout="wide")
st.title("NHANES Health Correlation Explorer")

df = load_data()

# ---------------------------------------------------------------- sidebar
st.sidebar.header("Filters")
sex = st.sidebar.radio("Sex", ["All", "Female", "Male"])
age_lo, age_hi = int(df["age"].min()), int(df["age"].max())
age_range = st.sidebar.slider("Age range (years)", age_lo, age_hi, (age_lo, age_hi))
st.sidebar.caption("Age 80 means 80 or older.")

st.sidebar.header("Correlation method")
method_label = st.sidebar.radio("Method", ["Pearson", "Spearman"], horizontal=True)
method = method_label.lower()
r_name = "Pearson r" if method == "pearson" else "Spearman ρ"

# One filtered DataFrame feeds every view below.
mask = df["age"].between(age_range[0], age_range[1])
if sex != "All":
    mask &= df["sex"] == sex
filtered = df[mask]

filter_text = f"Sex: {sex} · Age: {age_range[0]}–{age_range[1]}"
st.sidebar.markdown(f"**{len(filtered):,}** of {len(df):,} participants selected")

tab_data, tab_pair, tab_heat = st.tabs(["Data preview", "Pairwise view", "Correlation heatmap"])

# ---------------------------------------------------------------- data preview
with tab_data:
    st.markdown(
        f"""
This dataset holds **{len(df):,} adults aged 20 and over** from the CDC's 2017–2018
National Health and Nutrition Examination Survey (NHANES). Each row is one participant,
with body measurements, blood pressure, blood tests and self-reported sleep and sitting time.

NHANES oversamples some groups, so these correlations describe *this sample*, not the
US population.
"""
    )
    with st.expander("Data dictionary"):
        st.dataframe(DATA_DICTIONARY, hide_index=True, width="stretch")

    st.markdown(f"Showing **{len(filtered):,}** of {len(df):,} participants ({filter_text})")
    st.dataframe(filtered, hide_index=True, width="stretch")

# ---------------------------------------------------------------- pairwise view
with tab_pair:
    c1, c2, c3 = st.columns(3)
    x = c1.selectbox("X variable", NUMERIC_COLS, index=NUMERIC_COLS.index("age"))
    y = c2.selectbox("Y variable", NUMERIC_COLS, index=NUMERIC_COLS.index("systolic_bp"))
    threshold_label = c3.selectbox("Color points by threshold", list(THRESHOLDS))
    trend = st.radio("Trend overlay", ["Binned means", "Linear fit"], horizontal=True)

    if x == y:
        st.info("Pick two different variables for X and Y.")
    else:
        # Pairwise deletion: keep rows where both X and Y are present.
        pair = filtered[[x, y]].dropna()
        n = len(pair)

        if n < MIN_N:
            st.warning(f"Only {n} participants match the filters. At least {MIN_N} are needed.")
        else:
            r = pair[x].corr(pair[y], method=method)
            r_text = "undefined" if pd.isna(r) else f"{r:.3f}"

            m1, m2 = st.columns(2)
            m1.metric(r_name, r_text)
            m2.metric("n (participants)", f"{n:,}")
            st.caption(f"{filter_text} · {method_label} correlation of {x} and {y}")

            plot_df = pair.copy()
            hue, hue_order, palette = None, None, None
            threshold = THRESHOLDS[threshold_label]
            if threshold is not None:
                col, cutoff = threshold
                meets = filtered.loc[plot_df.index, col] >= cutoff
                yes = f"{threshold_label} (n={meets.sum():,})"
                no = f"Below threshold (n={(~meets).sum():,})"
                plot_df["group"] = meets.map({True: yes, False: no})
                hue, hue_order, palette = "group", [no, yes], ["#8da0b3", "#d1495b"]

            ax = sns.scatterplot(
                data=plot_df,
                x=x,
                y=y,
                hue=hue,
                hue_order=hue_order,
                palette=palette,
                color="#4c72b0",
                s=12,
                alpha=0.45,
                edgecolor=None,
            )

            if plot_df[x].nunique() > 1:
                if trend == "Linear fit":
                    sns.regplot(
                        data=plot_df,
                        x=x,
                        y=y,
                        scatter=False,
                        ci=None,
                        color="black",
                        line_kws={"label": "Linear fit", "linewidth": 2},
                        ax=ax,
                    )
                else:
                    bins = pd.qcut(plot_df[x], q=10, duplicates="drop").rename("bin")
                    means = plot_df.groupby(bins, observed=True)[[x, y]].mean()
                    sns.lineplot(
                        data=means,
                        x=x,
                        y=y,
                        color="black",
                        marker="o",
                        linewidth=2,
                        label="Binned means (quantile bins of X)",
                        ax=ax,
                    )

            ax.set_title(f"{y} vs {x}  ({r_name} = {r_text}, n = {n:,})")
            if ax.get_legend_handles_labels()[0]:
                ax.legend(fontsize="small", loc="best")
            fig = ax.figure
            fig.set_size_inches(8, 5)
            st.pyplot(fig, clear_figure=True)

            st.caption(
                "An r near zero does not mean 'no relationship'. r measures only "
                "straight-line (Pearson) or steadily rising/falling (Spearman) patterns, "
                "so a U-shape such as sleep hours vs health can give r ≈ 0. "
                "Check the binned means for the shape."
            )

# ---------------------------------------------------------------- heatmap
with tab_heat:
    selected = st.multiselect("Variables to include", NUMERIC_COLS, default=NUMERIC_COLS)

    if len(selected) < 2:
        st.info("Pick at least two variables.")
    elif len(filtered) < MIN_N:
        st.warning(
            f"Only {len(filtered)} participants match the filters. At least {MIN_N} are needed."
        )
    else:
        sub = filtered[selected]
        corr = sub.corr(method=method)

        # n for each square: rows where both variables are present (pairwise deletion).
        present = sub.notna().astype(int)
        n_mat = present.T @ present
        labels = corr.map(lambda v: "–" if pd.isna(v) else f"{v:.2f}") + "\nn=" + n_mat.astype(str)

        k = len(selected)
        ax = sns.heatmap(
            corr,
            vmin=-1,
            vmax=1,
            center=0,
            cmap="RdBu_r",
            annot=labels,
            fmt="",
            annot_kws={"size": 9 if k > 6 else 11},
            square=True,
            linewidths=0.5,
            cbar_kws={"label": r_name, "shrink": 0.8},
        )
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
        ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
        ax.set_title(f"{method_label} correlations ({filter_text})")
        fig = ax.figure
        fig.set_size_inches(0.8 * k + 2.5, 0.75 * k + 1.5)
        st.pyplot(fig, clear_figure=True)

        st.caption(
            f"Each square shows the {method_label} coefficient and the number of participants "
            "with both values. The color scale is fixed from −1 (dark blue) to +1 (dark red)."
        )
