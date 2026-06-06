"""Part 4: Baseline melanoma PBMC miraclib subset analysis."""

import json
import sqlite3
from pathlib import Path

import pandas as pd

from src.config import OUTPUT_DIR

BASELINE_SUBSET_QUERY = """
SELECT
    sub.project_id AS project,
    sub.subject_id AS subject,
    sub.response,
    sub.sex,
    s.sample_id AS sample
FROM samples s
JOIN subjects sub ON s.subject_id = sub.subject_id
WHERE sub.condition = 'melanoma'
  AND sub.treatment = 'miraclib'
  AND s.sample_type = 'PBMC'
  AND s.time_from_treatment_start = 0
ORDER BY sub.project_id, sub.subject_id
"""


def analyze_baseline_subset(connection: sqlite3.Connection) -> dict:
    """Summarize baseline miraclib melanoma PBMC samples and subjects."""
    data = pd.read_sql_query(BASELINE_SUBSET_QUERY, connection)
    subjects = data.drop_duplicates(subset=["subject"])

    summary = {
        "filter_criteria": {
            "condition": "melanoma",
            "sample_type": "PBMC",
            "treatment": "miraclib",
            "time_from_treatment_start": 0,
        },
        "total_samples": int(len(data)),
        "samples_per_project": data.groupby("project").size().astype(int).to_dict(),
        "subjects_by_response": subjects.groupby("response").size().astype(int).to_dict(),
        "subjects_by_sex": subjects.groupby("sex").size().astype(int).to_dict(),
        "total_subjects": int(len(subjects)),
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    json_path = OUTPUT_DIR / "baseline_subset_summary.json"
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    table_rows = []
    for project, count in summary["samples_per_project"].items():
        table_rows.append({"category": "samples_per_project", "group": project, "count": count})
    for response, count in summary["subjects_by_response"].items():
        table_rows.append({"category": "subjects_by_response", "group": response, "count": count})
    for sex, count in summary["subjects_by_sex"].items():
        table_rows.append({"category": "subjects_by_sex", "group": sex, "count": count})

    csv_path = OUTPUT_DIR / "baseline_subset_summary.csv"
    pd.DataFrame(table_rows).to_csv(csv_path, index=False)
    samples_path = OUTPUT_DIR / "baseline_subset_samples.csv"
    data.to_csv(samples_path, index=False)

    print(f"Part 4: Wrote baseline subset summary to {json_path}")
    print(f"Part 4: Found {summary['total_samples']} baseline samples across "
          f"{len(summary['samples_per_project'])} projects")
    return summary
