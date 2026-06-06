"""Part 2: Relative frequency summary per sample."""

import sqlite3
from pathlib import Path

import pandas as pd

from src.config import OUTPUT_DIR


FREQUENCY_QUERY = """
SELECT
    s.sample_id AS sample,
    SUM(cc.count) OVER (PARTITION BY s.sample_id) AS total_count,
    cp.population_name AS population,
    cc.count AS count,
    ROUND(100.0 * cc.count / SUM(cc.count) OVER (PARTITION BY s.sample_id), 4) AS percentage
FROM samples s
JOIN cell_counts cc ON s.sample_id = cc.sample_id
JOIN cell_populations cp ON cc.population_id = cp.population_id
ORDER BY s.sample_id, cp.population_name
"""


def generate_frequency_summary(
    connection: sqlite3.Connection,
    output_path: Path | None = None,
) -> pd.DataFrame:
    """Compute relative cell population frequencies for every sample."""
    summary = pd.read_sql_query(FREQUENCY_QUERY, connection)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if output_path is None:
        output_path = OUTPUT_DIR / "frequency_summary.csv"

    summary.to_csv(output_path, index=False)
    print(f"Part 2: Wrote frequency summary ({len(summary)} rows) to {output_path}")
    return summary
