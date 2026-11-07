#!/usr/bin/env python
"""Move an existing database to applets, documents and routes (decision
0015):

- `source_items` gets `imported_at`, filled with each item's
  `published_at`;
- the remixers' `artifacts` and the old delivery ledger are dropped, with
  the artifact contents no annotation or item references;
- the new `apps`, `documents` and `deliveries` tables are created.

The delivery history is lost: `itemfeed` instances start from their first
run (`since_first_run`), so nothing already posted is posted again. Running
it again does nothing.

Back the database up first. It takes the write lock, so it fails at once
if another newstool command is using the database.

Usage:
    python scripts/migrate_applets.py -c config.yaml
"""  # noqa: EXE001

from __future__ import annotations

import dataclasses
import sqlite3
from pathlib import Path

import rich_click as click
from foundation.storage import DiskStorage
from sqlalchemy import create_engine, make_url

from newstool.app import LockedError, write_lock
from newstool.config import Config
from newstool.db import Base

# Tables whose rows reference stored contents after the migration.
CONTENT_TABLES = ("source_items", "item_annotations")


@dataclasses.dataclass(slots=True)
class MigrationSummary:
    """What `migrate` did."""

    imported_at_added: bool = False
    dropped: list[str] = dataclasses.field(default_factory=list)
    released: int = 0  # artifact contents deleted from storage


def columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')}


def has_table(connection: sqlite3.Connection, table: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)
    ).fetchone()
    return row is not None


def migrate_tables(connection: sqlite3.Connection) -> tuple[MigrationSummary, set[str]]:
    """Change the tables in one transaction; return the summary and the
    sha256 of the artifact contents nothing references any more."""
    summary = MigrationSummary()
    released: set[str] = set()
    connection.execute("BEGIN")
    try:
        if "imported_at" not in columns(connection, "source_items"):
            connection.execute(
                "ALTER TABLE source_items ADD COLUMN imported_at DATETIME"
            )
            connection.execute("UPDATE source_items SET imported_at = published_at")
            connection.execute(
                "CREATE INDEX ix_source_items_source_id_imported_at"
                " ON source_items (source_id, imported_at)"
            )
            summary.imported_at_added = True
        # The old ledger referenced items and artifacts; the new one, documents.
        if has_table(connection, "deliveries") and "document_id" not in columns(
            connection, "deliveries"
        ):
            connection.execute("DROP TABLE deliveries")
            summary.dropped.append("deliveries")
        if has_table(connection, "artifacts"):
            released = {
                sha256
                for (sha256,) in connection.execute(
                    "SELECT content_sha256 FROM artifacts"
                )
            }
            connection.execute("DROP TABLE artifacts")
            summary.dropped.append("artifacts")
            for table in CONTENT_TABLES:
                released -= {
                    sha256
                    for (sha256,) in connection.execute(
                        f'SELECT content_sha256 FROM "{table}"'
                    )
                }
        connection.execute("COMMIT")
    except BaseException:
        connection.execute("ROLLBACK")
        raise
    return summary, released


def migrate(db_path: Path, content_dir: Path) -> MigrationSummary:
    """Migrate the database at `db_path`, whose contents are in
    `content_dir`, then create the missing tables."""
    connection = sqlite3.connect(db_path, isolation_level=None)
    try:
        summary, released = migrate_tables(connection)
    finally:
        connection.close()

    # Released after the commit: a failed migration loses no content.
    storage = DiskStorage(content_dir)
    try:
        for sha256 in released:
            storage.delete(sha256)
    finally:
        storage.close()
    summary.released = len(released)

    engine = create_engine(f"sqlite:///{db_path}")
    try:
        Base.metadata.create_all(engine)
    finally:
        engine.dispose()
    return summary


@click.command()
@click.option("-c", "--config", "config_path", type=Path, default=None)
def main(config_path: Path | None) -> None:
    config = Config.from_file(config_path) if config_path else Config()
    url = make_url(config.database_uri)
    if url.get_backend_name() != "sqlite" or not url.database:
        raise click.ClickException(f"not a SQLite database file: {config.database_uri}")
    db_path = Path(url.database)
    if not db_path.exists():
        raise click.ClickException(f"database not found: {db_path}")

    try:
        lock = write_lock(config.database_uri)
    except LockedError as e:
        raise click.ClickException(str(e)) from e
    try:
        summary = migrate(db_path, config.content_dir)
    finally:
        if lock is not None:
            lock.close()
    if summary.imported_at_added:
        click.echo("Added source_items.imported_at")
    if summary.dropped:
        click.echo(
            f"Dropped {', '.join(summary.dropped)};"
            f" released {summary.released} artifact content(s)"
        )
    if not (summary.imported_at_added or summary.dropped):
        click.echo("Nothing to migrate")


if __name__ == "__main__":
    main()
