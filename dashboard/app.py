"""Interactive dashboard for Loblaw Bio immune cell analysis."""

import json
import sqlite3
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.analysis.overview import FREQUENCY_QUERY
from src.analysis.statistics import MIRACLIB_PBMC_QUERY
from src.analysis.subset import BASELINE_SUBSET_QUERY
from src.config import DB_PATH, OUTPUT_DIR

st.set_page_config(
    page_title="Loblaw Bio Immune Cell Dashboard",
    page_icon="🧬",
    layout="wide",
)

st.title("Loblaw Bio — Immune Cell Population Analysis")
st.caption("Clinical trial dashboard for Bob Loblaw's miraclib treatment study")


@st.cache_data
def load_table(query: str) -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as connection:
        return pd.read_sql_query(query, connection)


@st.cache_data
def load_output_file(filename: str) -> pd.DataFrame | None:
    path = OUTPUT_DIR / filename
    if not path.exists():
        return None
    return pd.read_csv(path)


def main() -> None:
    if not DB_PATH.exists():
        st.error("Database not found. Run `make pipeline` to initialize data and outputs.")
        st.stop()

    tab_overview, tab_response, tab_baseline, tab_outputs = st.tabs(
        ["Frequency Overview", "Response Analysis", "Baseline Subset", "Generated Outputs"]
    )

    with tab_overview:
        st.header("Part 2: Population Frequencies by Sample")
        frequency_df = load_table(FREQUENCY_QUERY)

        projects = load_table(
            "SELECT sample_id AS sample, subject_id AS subject FROM samples"
        )
        subjects = load_table(
            "SELECT subject_id AS subject, project_id AS project, condition, treatment FROM subjects"
        )
        enriched = frequency_df.merge(projects, on="sample").merge(subjects, on="subject")

        col1, col2, col3 = st.columns(3)
        with col1:
            project_filter = st.multiselect(
                "Project",
                sorted(enriched["project"].unique()),
                default=sorted(enriched["project"].unique()),
            )
        with col2:
            condition_filter = st.multiselect(
                "Condition",
                sorted(enriched["condition"].unique()),
                default=sorted(enriched["condition"].unique()),
            )
        with col3:
            population_filter = st.multiselect(
                "Population",
                sorted(enriched["population"].unique()),
                default=sorted(enriched["population"].unique()),
            )

        filtered = enriched[
            enriched["project"].isin(project_filter)
            & enriched["condition"].isin(condition_filter)
            & enriched["population"].isin(population_filter)
        ]

        st.dataframe(filtered, use_container_width=True, hide_index=True)

        if not filtered.empty:
            fig = px.box(
                filtered,
                x="population",
                y="percentage",
                color="condition",
                points="outliers",
                title="Relative Frequency Distribution by Condition",
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab_response:
        st.header("Part 3: Miraclib Response Comparison (Melanoma PBMC)")
        comparison_df = load_table(MIRACLIB_PBMC_QUERY)
        significance_df = load_output_file("significance_report.csv")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Samples", len(comparison_df["sample"].unique()))
        with col2:
            st.metric("Populations Tested", len(comparison_df["population"].unique()))

        if significance_df is not None:
            st.subheader("Statistical Significance (Mann-Whitney U)")
            st.dataframe(significance_df, use_container_width=True, hide_index=True)

            significant = significance_df.loc[
                significance_df["significant"], "population"
            ].tolist()
            if significant:
                st.success(
                    "Significant populations (p < 0.05): "
                    + ", ".join(significant)
                )
            else:
                st.info("No populations reached nominal significance at alpha = 0.05.")

        population_choice = st.selectbox(
            "Select population for detailed view",
            sorted(comparison_df["population"].unique()),
        )
        subset = comparison_df[comparison_df["population"] == population_choice]
        fig = px.box(
            subset,
            x="response",
            y="percentage",
            color="response",
            points="all",
            labels={"response": "Responder", "percentage": "Relative Frequency (%)"},
            title=f"{population_choice.replace('_', ' ').title()} — Responders vs Non-Responders",
            color_discrete_map={"yes": "#2a9d8f", "no": "#e76f51"},
        )
        st.plotly_chart(fig, use_container_width=True)

        boxplot_path = OUTPUT_DIR / "response_comparison_boxplot.png"
        if boxplot_path.exists():
            st.subheader("Static Boxplot (Pipeline Output)")
            st.image(str(boxplot_path))

    with tab_baseline:
        st.header("Part 4: Baseline Miraclib Melanoma PBMC Subset")
        baseline_df = load_table(BASELINE_SUBSET_QUERY)
        subjects = baseline_df.drop_duplicates(subset=["subject"])

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Baseline Samples", len(baseline_df))
        with col2:
            st.metric("Unique Subjects", len(subjects))
        with col3:
            st.metric("Projects", baseline_df["project"].nunique())

        st.subheader("Samples per Project")
        project_counts = baseline_df.groupby("project").size().reset_index(name="sample_count")
        st.dataframe(project_counts, use_container_width=True, hide_index=True)
        st.plotly_chart(
            px.bar(project_counts, x="project", y="sample_count", title="Baseline Samples by Project"),
            use_container_width=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Subjects by Response")
            response_counts = subjects.groupby("response").size().reset_index(name="subject_count")
            st.dataframe(response_counts, use_container_width=True, hide_index=True)
            st.plotly_chart(
                px.pie(response_counts, names="response", values="subject_count", title="Response"),
                use_container_width=True,
            )
        with col2:
            st.subheader("Subjects by Sex")
            sex_counts = subjects.groupby("sex").size().reset_index(name="subject_count")
            st.dataframe(sex_counts, use_container_width=True, hide_index=True)
            st.plotly_chart(
                px.pie(sex_counts, names="sex", values="subject_count", title="Sex"),
                use_container_width=True,
            )

        st.subheader("Baseline Sample Records")
        st.dataframe(baseline_df, use_container_width=True, hide_index=True)

    with tab_outputs:
        st.header("Pipeline Output Files")
        summary_path = OUTPUT_DIR / "baseline_subset_summary.json"
        if summary_path.exists():
            with summary_path.open(encoding="utf-8") as handle:
                st.json(json.load(handle))

        output_files = sorted(OUTPUT_DIR.glob("*")) if OUTPUT_DIR.exists() else []
        for path in output_files:
            st.markdown(f"**{path.name}**")
            if path.suffix == ".csv":
                st.dataframe(pd.read_csv(path), use_container_width=True, hide_index=True)
            elif path.suffix == ".json":
                with path.open(encoding="utf-8") as handle:
                    st.json(json.load(handle))
            elif path.suffix == ".png":
                st.image(str(path))


if __name__ == "__main__":
    main()
