"""Execute the full Loblaw Bio analysis pipeline (Parts 2-4)."""

import sqlite3
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from src.analysis.overview import generate_frequency_summary
from src.analysis.statistics import analyze_response_differences
from src.analysis.subset import analyze_baseline_subset
from src.config import DB_PATH


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found at {DB_PATH}. Run `python load_data.py` first."
        )

    with sqlite3.connect(DB_PATH) as connection:
        generate_frequency_summary(connection)
        analyze_response_differences(connection)
        analyze_baseline_subset(connection)

    print("Pipeline completed successfully.")


if __name__ == "__main__":
    main()
