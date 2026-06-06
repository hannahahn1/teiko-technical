"""Part 3: Responder vs non-responder statistical comparison."""

import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

from src.config import OUTPUT_DIR

MIRACLIB_PBMC_QUERY = """
SELECT
    s.sample_id AS sample,
    sub.subject_id AS subject,
    sub.response,
    cp.population_name AS population,
    cc.count,
    ROUND(
        100.0 * cc.count / SUM(cc.count) OVER (PARTITION BY s.sample_id),
        4
    ) AS percentage
FROM samples s
JOIN subjects sub ON s.subject_id = sub.subject_id
JOIN cell_counts cc ON s.sample_id = cc.sample_id
JOIN cell_populations cp ON cc.population_id = cp.population_id
WHERE sub.condition = 'melanoma'
  AND sub.treatment = 'miraclib'
  AND s.sample_type = 'PBMC'
  AND sub.response IN ('yes', 'no')
ORDER BY s.sample_id, cp.population_name
"""


def _mann_whitney_test(responders: pd.Series, non_responders: pd.Series) -> dict:
    """Run Mann-Whitney U test and report effect size."""
    statistic, p_value = stats.mannwhitneyu(
        responders,
        non_responders,
        alternative="two-sided",
    )
    return {
        "u_statistic": statistic,
        "p_value": p_value,
        "responder_median": responders.median(),
        "non_responder_median": non_responders.median(),
        "responder_mean": responders.mean(),
        "non_responder_mean": non_responders.mean(),
        "responder_n": len(responders),
        "non_responder_n": len(non_responders),
    }


def analyze_response_differences(
    connection: sqlite3.Connection,
    alpha: float = 0.05,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compare population frequencies between responders and non-responders."""
    data = pd.read_sql_query(MIRACLIB_PBMC_QUERY, connection)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    for population, group in data.groupby("population"):
        responders = group.loc[group["response"] == "yes", "percentage"]
        non_responders = group.loc[group["response"] == "no", "percentage"]
        test_result = _mann_whitney_test(responders, non_responders)
        results.append(
            {
                "population": population,
                **test_result,
                "significant": test_result["p_value"] < alpha,
            }
        )

    significance_df = pd.DataFrame(results).sort_values("p_value")
    p_values = significance_df["p_value"].to_numpy()
    n_tests = len(p_values)
    order = p_values.argsort()
    ranked = p_values[order]
    adjusted = np.minimum.accumulate((ranked * n_tests / (np.arange(n_tests) + 1))[::-1])[::-1]
    fdr_adjusted = np.empty(n_tests)
    fdr_adjusted[order] = np.minimum(adjusted, 1.0)
    significance_df["p_value_adjusted"] = fdr_adjusted
    significance_df["significant_fdr"] = significance_df["p_value_adjusted"] < alpha

    significance_path = OUTPUT_DIR / "significance_report.csv"
    significance_df.to_csv(significance_path, index=False)

    plot_path = OUTPUT_DIR / "response_comparison_boxplot.png"
    _create_boxplot(data, plot_path)

    significant = significance_df.loc[significance_df["significant"], "population"].tolist()
    print(f"Part 3: Wrote significance report to {significance_path}")
    print(f"Part 3: Wrote boxplot to {plot_path}")
    if significant:
        print(
            "Part 3: Populations with significant differences (p < "
            f"{alpha}): {', '.join(significant)}"
        )
    else:
        print(f"Part 3: No populations reached significance at alpha = {alpha}")

    comparison_path = OUTPUT_DIR / "miraclib_pbmc_comparison.csv"
    data.to_csv(comparison_path, index=False)

    return data, significance_df


def _create_boxplot(data: pd.DataFrame, output_path: Path) -> None:
    """Create boxplots comparing responders vs non-responders per population."""
    sns.set_theme(style="whitegrid")
    populations = sorted(data["population"].unique())
    fig, axes = plt.subplots(1, len(populations), figsize=(4 * len(populations), 5), sharey=True)

    if len(populations) == 1:
        axes = [axes]

    for ax, population in zip(axes, populations):
        subset = data[data["population"] == population]
        sns.boxplot(
            data=subset,
            x="response",
            y="percentage",
            hue="response",
            ax=ax,
            palette={"yes": "#2a9d8f", "no": "#e76f51"},
            legend=False,
        )
        ax.set_title(population.replace("_", " ").title())
        ax.set_xlabel("Response")
        ax.set_ylabel("Relative Frequency (%)")

    fig.suptitle(
        "Miraclib Melanoma PBMC: Population Frequencies by Treatment Response",
        fontsize=14,
        y=1.02,
    )
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
