"""Shared configuration for the Loblaw Bio analysis pipeline."""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_CSV = ROOT_DIR / "cell-count.csv"
DB_PATH = ROOT_DIR / "loblaw_bio.db"
OUTPUT_DIR = ROOT_DIR / "output"

CELL_POPULATIONS = [
    "b_cell",
    "cd8_t_cell",
    "cd4_t_cell",
    "nk_cell",
    "monocyte",
]
