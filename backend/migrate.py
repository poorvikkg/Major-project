"""
migrate.py
Run this once to add new columns introduced in the FIR-level schema upgrade.
Safe to run multiple times (uses IF NOT EXISTS via exception handling).

Usage:
    cd backend
    python migrate.py
"""
from app.database.db import engine
from sqlalchemy import text

NEW_COLUMNS = [
    # missing_persons table
    ("missing_persons", "nickname",             "VARCHAR(120)"),
    ("missing_persons", "date_of_birth",        "VARCHAR(20)"),
    ("missing_persons", "height",               "VARCHAR(20)"),
    ("missing_persons", "weight",               "VARCHAR(20)"),
    ("missing_persons", "complexion",           "VARCHAR(50)"),
    ("missing_persons", "blood_group",          "VARCHAR(10)"),
    ("missing_persons", "nationality",          "VARCHAR(60)"),
    ("missing_persons", "identification_marks", "TEXT"),
    ("missing_persons", "face_shape",           "VARCHAR(50)"),
    ("missing_persons", "hair_color",           "VARCHAR(50)"),
    ("missing_persons", "eye_color",            "VARCHAR(50)"),
    ("missing_persons", "beard_mustache",       "VARCHAR(100)"),
    ("missing_persons", "has_disability",       "BOOLEAN DEFAULT FALSE"),
    ("missing_persons", "disability_details",   "TEXT"),
    ("missing_persons", "last_seen_location",   "TEXT"),
    ("missing_persons", "last_seen_date",       "VARCHAR(20)"),
    ("missing_persons", "last_seen_time",       "VARCHAR(20)"),
    ("missing_persons", "last_seen_wearing",    "TEXT"),
    ("missing_persons", "accompanied_by",       "TEXT"),
    ("missing_persons", "suspected_location",   "TEXT"),
    ("missing_persons", "occupation",           "VARCHAR(120)"),
    ("missing_persons", "habits",               "TEXT"),
    ("missing_persons", "languages_known",      "TEXT"),
    ("missing_persons", "medical_conditions",   "TEXT"),
    ("missing_persons", "behavioral_notes",     "TEXT"),
    # complainants table
    ("complainants", "alternate_phone", "VARCHAR(20)"),
]


def run_migration():
    with engine.connect() as conn:
        for table, column, col_type in NEW_COLUMNS:
            try:
                conn.execute(text(
                    f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {col_type};"
                ))
                conn.commit()
                print(f"  ✅  {table}.{column} — added")
            except Exception as e:
                conn.rollback()
                print(f"  ⚠️   {table}.{column} — skipped ({e})")
    print("\n🎉  Migration complete.")


if __name__ == "__main__":
    # ensure models are imported so Base.metadata is populated
    import app.models  # noqa
    run_migration()
