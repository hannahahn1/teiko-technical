"""Initialize the SQLite database and load cell-count.csv."""

import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from src.config import CELL_POPULATIONS, DATA_CSV, DB_PATH
from src.schema import SCHEMA_SQL


def initialize_database(connection: sqlite3.Connection) -> None:
    """Create tables and indexes."""
    connection.executescript(SCHEMA_SQL)


def load_csv(connection: sqlite3.Connection, csv_path: Path) -> None:
    """Load all rows from the clinical trial CSV into normalized tables."""
    df = pd.read_csv(csv_path)

    connection.executemany(
        "INSERT OR IGNORE INTO projects (project_id) VALUES (?)",
        [(project_id,) for project_id in df["project"].unique()],
    )

    subjects = df[
        ["subject", "project", "condition", "age", "sex", "treatment", "response"]
    ].drop_duplicates()
    connection.executemany(
        """
        INSERT OR REPLACE INTO subjects
            (subject_id, project_id, condition, age, sex, treatment, response)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                row.subject,
                row.project,
                row.condition,
                int(row.age),
                row.sex,
                row.treatment,
                row.response if pd.notna(row.response) else None,
            )
            for row in subjects.itertuples(index=False)
        ],
    )

    samples = df[["sample", "subject", "sample_type", "time_from_treatment_start"]].drop_duplicates()
    connection.executemany(
        """
        INSERT OR REPLACE INTO samples
            (sample_id, subject_id, sample_type, time_from_treatment_start)
        VALUES (?, ?, ?, ?)
        """,
        [
            (row.sample, row.subject, row.sample_type, int(row.time_from_treatment_start))
            for row in samples.itertuples(index=False)
        ],
    )

    connection.executemany(
        "INSERT OR IGNORE INTO cell_populations (population_name) VALUES (?)",
        [(population,) for population in CELL_POPULATIONS],
    )

    population_ids = {
        row[1]: row[0]
        for row in connection.execute(
            "SELECT population_id, population_name FROM cell_populations"
        )
    }

    count_rows = []
    for _, row in df.iterrows():
        sample_id = row["sample"]
        for population in CELL_POPULATIONS:
            count_rows.append(
                (sample_id, population_ids[population], int(row[population]))
            )

    connection.executemany(
        """
        INSERT OR REPLACE INTO cell_counts (sample_id, population_id, count)
        VALUES (?, ?, ?)
        """,
        count_rows,
    )

    connection.commit()


def main() -> None:
    if not DATA_CSV.exists():
        raise FileNotFoundError(f"Input file not found: {DATA_CSV}")

    if DB_PATH.exists():
        DB_PATH.unlink()

    with sqlite3.connect(DB_PATH) as connection:
        initialize_database(connection)
        load_csv(connection, DATA_CSV)

    print(f"Database created at {DB_PATH}")
    print(f"Loaded {len(pd.read_csv(DATA_CSV))} rows from {DATA_CSV.name}")


if __name__ == "__main__":
    main()
