"""
One-shot migration script — adds dynamic point columns to `challenges` table.
Run once: python migrate_dynamic_points.py
"""
from app import create_app
from app.extensions import db

app = create_app()

with app.app_context():
    stmts = [
        "ALTER TABLE challenges ADD COLUMN initial_points INTEGER NOT NULL DEFAULT 500",
        "ALTER TABLE challenges ADD COLUMN minimum_points INTEGER NOT NULL DEFAULT 50",
        "ALTER TABLE challenges ADD COLUMN decay_limit INTEGER NOT NULL DEFAULT 10",
    ]
    for s in stmts:
        try:
            db.session.execute(db.text(s))
            print("OK  :", s[:60])
        except Exception as e:
            print("SKIP:", e)

    # Seed initial_points with existing points value for any pre-existing rows
    db.session.execute(db.text("UPDATE challenges SET initial_points = points"))
    db.session.commit()
    print("Migration complete.")
