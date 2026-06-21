from __future__ import annotations

import os
from pathlib import Path
import sqlite3
import time

DATABASE = Path(os.getenv("DISCRETE_DATABASE_PATH", "./discrete_art_studio.db")).resolve()

MIGRATIONS: list[tuple[int, str]] = [
    (
        1,
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL,
            credits INTEGER NOT NULL DEFAULT 20,
            created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS creations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            prompt TEXT NOT NULL,
            style TEXT NOT NULL,
            mode TEXT NOT NULL,
            image_url TEXT NOT NULL DEFAULT '',
            likes INTEGER NOT NULL DEFAULT 0,
            created_at INTEGER NOT NULL,
            FOREIGN KEY(owner_id) REFERENCES users(id)
        );
        """,
    ),
    (
        2,
        """
        CREATE INDEX IF NOT EXISTS idx_creations_created_at
        ON creations(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_creations_owner_id
        ON creations(owner_id);
        """,
    ),
]


def migrate() -> list[int]:
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    applied: list[int] = []
    with sqlite3.connect(DATABASE) as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at INTEGER NOT NULL
            )
            """
        )
        current = {
            row[0]
            for row in db.execute("SELECT version FROM schema_migrations").fetchall()
        }
        for version, sql in MIGRATIONS:
            if version in current:
                continue
            db.executescript(sql)
            db.execute(
                "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                (version, int(time.time())),
            )
            applied.append(version)
        db.commit()
    return applied


if __name__ == "__main__":
    versions = migrate()
    if versions:
        print(f"Applied database migrations: {versions}")
    else:
        print("Database schema is current")
