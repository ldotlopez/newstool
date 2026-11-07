import hashlib
import shutil
import sqlite3
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from foundation.storage import DiskStorage, EntryNotFoundError

from newstool.db import Database, ProcessingStatus
from newstool.models import SourceData, SourceItem
from scripts.migrate_applets import migrate

SOURCE = SourceData(id="a", name="A", url="https://a.test/", provider="plaza")
PUBLISHED = datetime(2026, 10, 1, tzinfo=UTC)


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


class MigrateAppletsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="newstool-test-"))
        self.db_path = self.tmp_dir / "data.db"
        self.content_dir = self.tmp_dir / "content"
        url = f"sqlite:///{self.db_path}"

        item = SourceItem(
            source=SOURCE,
            uid="i1",
            title="I",
            uri="https://a.test/i1",
            content=b"item",
            mimetype="text/html",
            published_at=PUBLISHED,
        )
        db = Database(url, self.content_dir)
        db.upsert_source_items([item])
        db.record_result(item, "summarize", "summary", ProcessingStatus.DONE, value="S")
        db.contents.set(sha256(b"artifact"), b"artifact")
        db.close()

        # The schema before decision 0015.
        connection = sqlite3.connect(self.db_path)
        ((self.annotation_sha,),) = connection.execute(
            "SELECT content_sha256 FROM item_annotations"
        ).fetchall()
        connection.executescript(
            """
            DROP INDEX ix_source_items_source_id_imported_at;
            ALTER TABLE source_items DROP COLUMN imported_at;
            DROP TABLE deliveries;
            DROP TABLE documents;
            DROP TABLE apps;
            CREATE TABLE artifacts (
                id INTEGER PRIMARY KEY, remixer TEXT, name TEXT, content_sha256 TEXT
            );
            CREATE TABLE deliveries (
                id INTEGER PRIMARY KEY, sink TEXT,
                source_item_id INTEGER, artifact_id INTEGER
            );
            """
        )
        connection.executemany(
            "INSERT INTO artifacts (remixer, name, content_sha256) VALUES (?, ?, ?)",
            [
                ("digest", "a/1", sha256(b"artifact")),
                # Shares its content with the annotation: it must stay.
                ("digest", "a/2", self.annotation_sha),
            ],
        )
        connection.execute(
            "INSERT INTO deliveries (sink, source_item_id) VALUES ('t', 1)"
        )
        connection.commit()
        connection.close()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def query(self, sql: str) -> list[tuple]:
        connection = sqlite3.connect(self.db_path)
        try:
            return connection.execute(sql).fetchall()
        finally:
            connection.close()

    def test_migrates_once(self) -> None:
        summary = migrate(self.db_path, self.content_dir)

        self.assertTrue(summary.imported_at_added)
        self.assertEqual(summary.dropped, ["deliveries", "artifacts"])
        self.assertEqual(summary.released, 1)
        tables = {
            name
            for (name,) in self.query(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        self.assertTrue({"apps", "documents", "deliveries"} <= tables)
        self.assertNotIn("artifacts", tables)
        self.assertIn(
            ("document_id",),
            self.query("SELECT name FROM pragma_table_info('deliveries')"),
        )

        storage = DiskStorage(self.content_dir)
        try:
            with self.assertRaises(EntryNotFoundError):
                storage.get(sha256(b"artifact"))
            self.assertTrue(storage.get(self.annotation_sha))
        finally:
            storage.close()

        again = migrate(self.db_path, self.content_dir)
        self.assertFalse(again.imported_at_added)
        self.assertEqual(again.dropped, [])

    def test_items_are_imported_when_published(self) -> None:
        migrate(self.db_path, self.content_dir)

        db = Database(f"sqlite:///{self.db_path}", self.content_dir)
        try:
            (item,) = db.get_items()
        finally:
            db.close()
        self.assertEqual(item.imported_at, PUBLISHED)


if __name__ == "__main__":
    unittest.main()
