"""SQLite schema definitions for the Loblaw Bio clinical trial database."""

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS subjects (
    subject_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    condition TEXT NOT NULL,
    age INTEGER NOT NULL,
    sex TEXT NOT NULL CHECK (sex IN ('M', 'F')),
    treatment TEXT NOT NULL,
    response TEXT CHECK (response IN ('yes', 'no') OR response IS NULL),
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

CREATE TABLE IF NOT EXISTS samples (
    sample_id TEXT PRIMARY KEY,
    subject_id TEXT NOT NULL,
    sample_type TEXT NOT NULL,
    time_from_treatment_start INTEGER NOT NULL,
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
);

CREATE TABLE IF NOT EXISTS cell_populations (
    population_id INTEGER PRIMARY KEY AUTOINCREMENT,
    population_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS cell_counts (
    sample_id TEXT NOT NULL,
    population_id INTEGER NOT NULL,
    count INTEGER NOT NULL CHECK (count >= 0),
    PRIMARY KEY (sample_id, population_id),
    FOREIGN KEY (sample_id) REFERENCES samples(sample_id),
    FOREIGN KEY (population_id) REFERENCES cell_populations(population_id)
);

CREATE INDEX IF NOT EXISTS idx_subjects_project ON subjects(project_id);
CREATE INDEX IF NOT EXISTS idx_subjects_condition ON subjects(condition);
CREATE INDEX IF NOT EXISTS idx_subjects_treatment ON subjects(treatment);
CREATE INDEX IF NOT EXISTS idx_subjects_response ON subjects(response);
CREATE INDEX IF NOT EXISTS idx_samples_subject ON samples(subject_id);
CREATE INDEX IF NOT EXISTS idx_samples_type ON samples(sample_type);
CREATE INDEX IF NOT EXISTS idx_samples_time ON samples(time_from_treatment_start);
CREATE INDEX IF NOT EXISTS idx_cell_counts_population ON cell_counts(population_id);
"""
