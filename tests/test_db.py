"""Unit tests for newstool.db.

Uses a real (file-based, temp-dir) SQLite database per test, without mocking
SQLAlchemy: unit-of-work diffing, upsert semantics and timestamp rules only
mean something against a real engine and session.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from newstool.db import (
    Database,
    DBDelivery,
    DBDocument,
    DBItemAnnotation,
    DBSource,
    DBSourceItem,
    DeliveryStatus,
    ProcessingStatus,
    next_annotation,
)
from newstool.models import (
    Annotation,
    AppletResult,
    Delivery,
    Document,
    DocumentFilter,
    EmittedDocument,
    ProcessingScope,
    SourceData,
    SourceItem,
)


def make_source(source_id: str = "example", name: str = "Example") -> SourceData:
    return SourceData(
        id=source_id,
        name=name,
        url=f"https://example.test/{source_id}",
        provider="exampleprovider",
    )


def make_item(
    source: SourceData,
    uid: str = "item-1",
    title: str = "Title",
    uri: str | None = None,
    content: bytes = b"content",
    data: dict | None = None,
    published_at: datetime | None = None,
    modified_at: datetime | None = None,
) -> SourceItem:
    return SourceItem(
        source=source,
        uid=uid,
        title=title,
        uri=uri if uri is not None else f"https://example.test/{uid}",
        content=content,
        mimetype="text/html",
        data=data if data is not None else {},
        published_at=published_at,
        modified_at=modified_at,
    )


class DatabaseTestCase(unittest.TestCase):
    """Base class: spins up a fresh temp-file SQLite DB per test."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp(prefix="newstool-test-")
        db_path = Path(self.tmp_dir) / "test.db"
        self.db = Database(f"sqlite:///{db_path}", Path(self.tmp_dir) / "content")

    def tearDown(self) -> None:
        self.db.close()
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def get_item(self, uid: str, source_id: str = "example") -> DBSourceItem | None:
        with self.db.session_scope() as sess:
            row = (
                sess.query(DBSourceItem)
                .filter_by(source_id=source_id, uid=uid)
                .one_or_none()
            )
            if row is not None:
                sess.expunge(row)
            return row

    def content_of(self, row: DBSourceItem) -> bytes:
        return self.db.contents.get(row.content_sha256)

    def stored_contents(self) -> set[str]:
        return set(self.db.contents.iter())

    def count(self, model: type) -> int:
        with self.db.session_scope() as sess:
            return sess.query(model).count()


class UpsertSourceItemsTests(DatabaseTestCase):
    def test_new_row_uses_provider_supplied_dates(self):
        source = make_source()
        pub = datetime(2026, 1, 1, tzinfo=UTC)
        mod = datetime(2026, 1, 2, tzinfo=UTC)

        self.db.upsert_source_items(
            [make_item(source, uid="a1", published_at=pub, modified_at=mod)]
        )

        row = self.get_item("a1")
        self.assertEqual(row.published_at, pub)
        self.assertEqual(row.modified_at, mod)

    def test_new_row_falls_back_to_now_when_provider_gives_no_dates(self):
        before = datetime.now(UTC)
        self.db.upsert_source_items([make_item(make_source(), uid="a1")])
        after = datetime.now(UTC)

        row = self.get_item("a1")
        self.assertTrue(before <= row.published_at <= after)
        self.assertTrue(before <= row.modified_at <= after)

    def test_identical_resend_is_a_complete_no_op(self):
        mod = datetime(2026, 1, 1, tzinfo=UTC)
        item = make_item(make_source(), uid="a1", modified_at=mod)
        self.db.upsert_source_items([item])

        self.db.upsert_source_items([item])

        self.assertEqual(self.get_item("a1").modified_at, mod)
        self.assertEqual(self.count(DBSourceItem), 1)

    def test_content_change_with_newer_provider_date_updates_modified_at(self):
        source = make_source()
        t1 = datetime(2026, 1, 1, tzinfo=UTC)
        t2 = datetime(2026, 1, 5, tzinfo=UTC)
        self.db.upsert_source_items(
            [make_item(source, uid="a1", content=b"v1", modified_at=t1)]
        )

        self.db.upsert_source_items(
            [make_item(source, uid="a1", content=b"v2", modified_at=t2)]
        )

        row = self.get_item("a1")
        self.assertEqual(self.content_of(row), b"v2")
        self.assertEqual(row.modified_at, t2)

    def test_content_change_with_older_or_equal_provider_date_trusts_database(self):
        source = make_source()
        t_stored = datetime(2026, 1, 10, tzinfo=UTC)
        self.db.upsert_source_items(
            [make_item(source, uid="a1", content=b"v1", modified_at=t_stored)]
        )

        for content, modified_at in (
            (b"v2", t_stored - timedelta(days=9)),
            (b"v3", t_stored),
        ):
            self.db.upsert_source_items(
                [make_item(source, uid="a1", content=content, modified_at=modified_at)]
            )
            row = self.get_item("a1")
            self.assertEqual(self.content_of(row), content)
            self.assertEqual(row.modified_at, t_stored)

    def test_content_change_with_no_provider_date_falls_back_to_now(self):
        source = make_source()
        t1 = datetime(2026, 1, 1, tzinfo=UTC)
        self.db.upsert_source_items(
            [make_item(source, uid="a1", content=b"v1", modified_at=t1)]
        )

        before = datetime.now(UTC)
        self.db.upsert_source_items([make_item(source, uid="a1", content=b"v2")])
        after = datetime.now(UTC)

        self.assertTrue(before <= self.get_item("a1").modified_at <= after)

    def test_published_at_is_set_once_and_never_overwritten(self):
        source = make_source()
        self.db.upsert_source_items([make_item(source, uid="a1", content=b"v1")])
        first_published_at = self.get_item("a1").published_at

        self.db.upsert_source_items(
            [
                make_item(
                    source,
                    uid="a1",
                    content=b"v2",
                    published_at=datetime(2030, 1, 1, tzinfo=UTC),
                )
            ]
        )

        self.assertEqual(self.get_item("a1").published_at, first_published_at)

    def test_imported_at_is_the_first_import_whatever_the_publication(self):
        source = make_source()
        before = datetime.now(UTC)
        old = datetime(2020, 1, 1, tzinfo=UTC)
        self.db.upsert_source_items(
            [make_item(source, uid="a1", content=b"v1", published_at=old)]
        )
        first_imported_at = self.get_item("a1").imported_at

        self.db.upsert_source_items([make_item(source, uid="a1", content=b"v2")])

        self.assertGreaterEqual(first_imported_at, before)
        self.assertEqual(self.get_item("a1").imported_at, first_imported_at)
        (item,) = self.db.get_items(ProcessingScope(imported_since=before))
        self.assertEqual(item.published_at, old)
        self.assertEqual(self.db.get_items(ProcessingScope(imported_until=before)), [])

    def test_data_dict_change_alone_counts_as_a_change(self):
        source = make_source()
        t1 = datetime(2026, 1, 1, tzinfo=UTC)
        t2 = datetime(2026, 1, 2, tzinfo=UTC)
        self.db.upsert_source_items(
            [make_item(source, uid="a1", data={"tags": ["a"]}, modified_at=t1)]
        )

        self.db.upsert_source_items(
            [make_item(source, uid="a1", data={"tags": ["a", "b"]}, modified_at=t2)]
        )

        row = self.get_item("a1")
        self.assertEqual(row.data, {"tags": ["a", "b"]})
        self.assertEqual(row.modified_at, t2)


class IdentityTests(DatabaseTestCase):
    def test_same_uid_in_two_sources_is_two_items(self):
        a, b = make_source("a"), make_source("b")

        self.db.upsert_source_items(
            [make_item(a, uid="same"), make_item(b, uid="same")]
        )

        self.assertEqual(self.count(DBSourceItem), 2)
        self.assertEqual(
            sorted(item.key for item in self.db.get_items()),
            [("a", "same"), ("b", "same")],
        )

    def test_uri_is_not_unique(self):
        source = make_source()

        self.db.upsert_source_items(
            [
                make_item(source, uid="a1", uri="https://x/1"),
                make_item(source, uid="a2", uri="https://x/1"),
            ]
        )

        self.assertEqual(self.count(DBSourceItem), 2)

    def test_upsert_sets_ids_that_reimports_keep(self):
        source = make_source()
        first = [make_item(source, uid="a1"), make_item(source, uid="a2")]
        self.db.upsert_source_items(first)
        again = make_item(source, uid="a2", title="Changed")
        self.db.upsert_source_items([again])

        self.assertEqual([item.id for item in first], [1, 2])
        self.assertEqual(again.id, 2)
        self.assertEqual([item.id for item in self.db.get_items()], [1, 2])

    def test_reimport_updates_the_source_row(self):
        self.db.upsert_source_items([make_item(make_source(name="Old"))])
        self.db.upsert_source_items([make_item(make_source(name="New"))])

        self.assertEqual(self.count(DBSource), 1)
        (item,) = self.db.get_items()
        self.assertEqual(item.source.name, "New")


class ContentStorageTests(DatabaseTestCase):
    def test_replaced_content_is_deleted(self):
        source = make_source()
        self.db.upsert_source_items([make_item(source, uid="a1", content=b"v1")])

        self.db.upsert_source_items([make_item(source, uid="a1", content=b"v2")])

        self.assertEqual(self.stored_contents(), {self.get_item("a1").content_sha256})

    def test_replaced_content_shared_with_another_item_is_kept(self):
        source = make_source()
        self.db.upsert_source_items(
            [
                make_item(source, uid="a1", content=b"shared"),
                make_item(source, uid="a2", content=b"shared"),
            ]
        )

        self.db.upsert_source_items([make_item(source, uid="a1", content=b"v2")])

        self.assertEqual(self.content_of(self.get_item("a2")), b"shared")

    def test_get_content_loads_from_storage(self):
        self.db.upsert_source_items(
            [make_item(make_source(), uid="a1", content=b"%PDF")]
        )

        (item,) = self.db.get_items()

        self.assertIsNone(item.content)
        self.assertEqual(self.db.get_content(item), b"%PDF")


class GetItemsTests(DatabaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        source = make_source()
        self.db.upsert_source_items(
            [
                make_item(
                    source,
                    uid=f"d{day}",
                    published_at=datetime(2026, 1, day, tzinfo=UTC),
                )
                for day in (1, 2, 3)
            ]
        )

    def uids(self, **kwargs) -> list[str]:
        return [item.uid for item in self.db.get_items(**kwargs)]

    def test_oldest_first_by_default_and_limit_keeps_the_first(self):
        self.assertEqual(self.uids(), ["d1", "d2", "d3"])
        self.assertEqual(self.uids(scope=ProcessingScope(limit=2)), ["d1", "d2"])

    def test_sort_keys_order_ascending_and_decide_what_limit_keeps(self):
        # d1 is the oldest published and the most recently updated.
        self.db.upsert_source_items(
            [
                make_item(
                    make_source(),
                    uid="d1",
                    content=b"changed",
                    published_at=datetime(2026, 1, 1, tzinfo=UTC),
                )
            ]
        )

        self.assertEqual(self.uids(sort="updated"), ["d2", "d3", "d1"])
        self.assertEqual(self.uids(sort="published"), ["d1", "d2", "d3"])
        self.assertEqual(
            self.uids(scope=ProcessingScope(limit=1), sort="updated"), ["d2"]
        )
        self.assertEqual(self.uids(sort="id"), ["d1", "d2", "d3"])

    def test_newest_first_with_limit_keeps_the_newest(self):
        self.assertEqual(
            self.uids(scope=ProcessingScope(limit=2), newest_first=True), ["d3", "d2"]
        )

    def test_scope_filters_by_source_dates_and_ids(self):
        since = datetime(2026, 1, 2, tzinfo=UTC)
        self.assertEqual(self.uids(scope=ProcessingScope(since=since)), ["d2", "d3"])
        self.assertEqual(self.uids(scope=ProcessingScope(until=since)), ["d1"])
        self.assertEqual(self.uids(scope=ProcessingScope(item_ids=(3,))), ["d3"])
        self.assertEqual(self.uids(scope=ProcessingScope(source="other")), [])


class ConnectionTests(DatabaseTestCase):
    def test_foreign_keys_are_enforced(self):
        with self.db.session_scope() as sess:
            enabled = sess.execute(text("PRAGMA foreign_keys")).scalar()
        self.assertEqual(enabled, 1)


class JSONColumnTests(DatabaseTestCase):
    def stored(self, app: str) -> tuple[str, object]:
        with self.db.session_scope() as sess:
            return sess.execute(
                text("SELECT typeof(state), state FROM apps WHERE id = :app"),
                {"app": app},
            ).one()

    def test_values_are_encoded_once_and_none_is_null(self):
        started = datetime(2026, 11, 11, tzinfo=UTC)
        for app, state in (("dict", {"cursor": "c"}), ("number", 42), ("none", None)):
            self.db.commit_app_run(app, started, AppletResult(state=state), {})

        self.assertEqual(self.stored("dict"), ("text", '{"cursor": "c"}'))
        self.assertEqual(self.stored("number"), ("text", "42"))
        self.assertEqual(self.stored("none"), ("null", None))
        runs = self.db.get_app_runs()
        self.assertEqual(
            [runs[app].state for app in ("dict", "number", "none")],
            [{"cursor": "c"}, 42, None],
        )

    def test_types_beyond_plain_json_round_trip(self):
        when = datetime(2026, 11, 11, 9, 30, tzinfo=UTC)
        self.db.commit_app_run("app", when, AppletResult(state={"at": when}), {})

        self.assertEqual(self.db.get_app_run("app").state, {"at": when})


class ProcessingTests(DatabaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.source = make_source()
        self.db.upsert_source_items([make_item(self.source, uid="a1", content=b"v1")])
        (self.item,) = self.db.get_items()

    def unprocessed_uids(self, key: str, **kwargs) -> list[str]:
        kwargs.setdefault("version", None)
        kwargs.setdefault("max_retries", 3)
        return [i.uid for i in self.db.get_unprocessed_items(key, **kwargs)]

    def attempts(self, key: str) -> int:
        with self.db.session_scope() as sess:
            return sess.query(DBItemAnnotation).filter_by(key=key).one().attempts

    def test_done_item_is_eligible_again_after_its_content_changes(self):
        self.db.record_result(
            self.item, "markdownify", "markdown", ProcessingStatus.DONE
        )
        self.assertEqual(self.unprocessed_uids("markdown"), [])

        self.db.upsert_source_items([make_item(self.source, uid="a1", content=b"v2")])

        self.assertEqual(self.unprocessed_uids("markdown"), ["a1"])

    def test_version_change_makes_done_items_eligible(self):
        self.db.record_result(
            self.item, "markdownify", "markdown", ProcessingStatus.DONE, version="1"
        )

        self.assertEqual(self.unprocessed_uids("markdown", version="1"), [])
        self.assertEqual(self.unprocessed_uids("markdown", version="2"), ["a1"])

    def test_ignored_item_is_only_revisited_when_forced(self):
        self.db.record_result(
            self.item, "markdownify", "markdown", ProcessingStatus.IGNORED
        )

        self.assertEqual(self.unprocessed_uids("markdown"), [])
        self.assertEqual(self.unprocessed_uids("markdown", force=True), ["a1"])

    def test_errors_stop_at_max_retries(self):
        for _ in range(3):
            self.db.record_result(
                self.item, "markdownify", "markdown", ProcessingStatus.ERROR
            )

        self.assertEqual(self.attempts("markdown"), 3)
        self.assertEqual(self.unprocessed_uids("markdown"), [])

    def test_forced_run_resets_attempts(self):
        for _ in range(3):
            self.db.record_result(
                self.item, "markdownify", "markdown", ProcessingStatus.ERROR
            )

        self.db.record_result(
            self.item,
            "markdownify",
            "markdown",
            ProcessingStatus.ERROR,
            reset_attempts=True,
        )

        self.assertEqual(self.attempts("markdown"), 1)

    def test_requires_waits_for_upstream_done_on_current_content(self):
        self.assertEqual(self.unprocessed_uids("tags", requires="markdown"), [])

        self.db.record_result(
            self.item, "markdownify", "markdown", ProcessingStatus.DONE
        )
        self.assertEqual(self.unprocessed_uids("tags", requires="markdown"), ["a1"])

        self.db.upsert_source_items([make_item(self.source, uid="a1", content=b"v2")])
        self.assertEqual(self.unprocessed_uids("tags", requires="markdown"), [])

    def test_each_key_of_a_processor_has_its_own_state(self):
        self.db.record_result(
            self.item, "summarize", "summary/es", ProcessingStatus.DONE, value="ES"
        )

        self.assertEqual(self.unprocessed_uids("summary/es"), [])
        self.assertEqual(self.unprocessed_uids("summary/en"), ["a1"])

    def test_failed_run_saves_no_annotation(self):
        self.db.record_result(
            self.item, "summarize", "summary", ProcessingStatus.ERROR, error="down"
        )

        self.assertEqual(self.db.get_annotations(self.item), {})
        self.assertEqual(self.attempts("summary"), 1)

    def test_requires_skips_items_upstream_ignored_even_with_force(self):
        self.db.record_result(
            self.item, "markdownify", "markdown", ProcessingStatus.IGNORED
        )

        self.assertEqual(
            self.unprocessed_uids("tags", requires="markdown", force=True), []
        )


class AnnotationTests(DatabaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.source = make_source()
        self.db.upsert_source_items([make_item(self.source, uid="a1", content=b"v1")])
        (self.item,) = self.db.get_items()

    def annotate(self, item: SourceItem, processor: str, key: str, value) -> None:
        self.db.record_result(item, processor, key, ProcessingStatus.DONE, value=value)

    def test_annotations_round_trip_through_storage(self):
        self.annotate(self.item, "markdownify", "markdown", "# Title")

        self.assertEqual(self.db.get_annotations(self.item), {"markdown": "# Title"})
        self.assertEqual(len(self.stored_contents()), 2)  # item content + value

    def test_replaced_annotation_value_is_released(self):
        self.annotate(self.item, "summarize", "summary", "first")
        self.annotate(self.item, "summarize", "summary", "second")

        self.assertEqual(
            self.db.get_annotations(self.item, key="summary"), {"summary": "second"}
        )
        self.assertEqual(len(self.stored_contents()), 2)

    def test_get_annotation_values_is_keyed_by_source_and_uid(self):
        other = make_source("other")
        self.db.upsert_source_items([make_item(other, uid="a1", content=b"x")])
        items = self.db.get_items()
        self.annotate(self.item, "tagger", "tags", ["a"])

        values = self.db.get_annotation_values(items, key="tags")

        self.assertEqual(values, {("example", "a1"): ["a"]})

    def test_get_annotation_keys_lists_ids_processors_and_keys_by_item(self):
        other = make_item(self.source, uid="a2", content=b"x")
        self.db.upsert_source_items([other])
        self.annotate(self.item, "tagger", "tags", ["a"])
        self.annotate(self.item, "embed", "tags/embedding", [0.5])
        self.annotate(self.item, "markdownify", "markdown", "# T")

        keys = self.db.get_annotation_keys([self.item.id, other.id])

        self.assertEqual(
            keys,
            {
                self.item.id: [
                    (2, "embed", "tags/embedding"),
                    (3, "markdownify", "markdown"),
                    (1, "tagger", "tags"),
                ]
            },
        )

    def test_find_annotations_combines_scope_processor_key_ids_and_limit(self):
        other = make_item(self.source, uid="a2", content=b"x")
        self.db.upsert_source_items([other])
        self.annotate(self.item, "tagger", "tags", ["a"])
        self.annotate(self.item, "embed", "tags/embedding", [0.5])
        self.annotate(other, "tagger", "tags", ["b"])
        self.annotate(other, "markdownify", "markdown", "# T")

        def found(scope=None, **filters) -> list[tuple[int, str, str]]:
            return [
                (a.item_id, f"{a.processor}.{a.key}", a.value)
                for a in self.db.find_annotations(scope, **filters)
            ]

        self.assertEqual(
            found(ProcessingScope(item_ids=(other.id,))),
            [
                (other.id, "markdownify.markdown", "# T"),
                (other.id, "tagger.tags", ["b"]),
            ],
        )
        self.assertEqual(
            found(processor="tagger", key="tags"),
            [(self.item.id, "tagger.tags", ["a"]), (other.id, "tagger.tags", ["b"])],
        )
        self.assertEqual(
            found(annotation_ids=[2]), [(self.item.id, "embed.tags/embedding", [0.5])]
        )
        self.assertEqual(len(found(ProcessingScope(limit=3))), 3)

    def test_delete_by_id_makes_the_item_pending_for_that_key(self):
        self.annotate(self.item, "markdownify", "markdown", "# Title")
        self.annotate(self.item, "tagger", "tags", ["a"])
        (markdown,) = self.db.find_annotations(key="markdown")

        deleted = self.db.delete_annotations([markdown.id])

        self.assertEqual(deleted, 1)
        self.assertEqual(self.db.get_annotations(self.item), {"tags": ["a"]})
        self.assertEqual(
            [
                i.uid
                for i in self.db.get_unprocessed_items(
                    "markdown", version=None, max_retries=3
                )
            ],
            ["a1"],
        )
        self.assertEqual(self.count(DBItemAnnotation), 1)
        self.assertEqual(len(self.stored_contents()), 2)  # item content + tags

    def test_delete_keeps_the_same_key_on_other_items(self):
        other = make_source("other")
        self.db.upsert_source_items([make_item(other, uid="b1", content=b"x")])
        for item in self.db.get_items():
            self.annotate(item, "tagger", "tags", [item.uid])
        first, _ = self.db.find_annotations(key="tags")

        self.assertEqual(self.db.delete_annotations([first.id]), 1)
        self.assertEqual(self.db.delete_annotations([]), 0)

        (kept,) = self.db.find_annotations()
        self.assertNotEqual(kept.item_id, first.item_id)
        self.assertEqual(self.count(DBItemAnnotation), 1)

    def test_runs_without_a_value_are_not_annotations(self):
        self.db.record_result(
            self.item, "summarize", "summary", ProcessingStatus.ERROR, error="down"
        )

        self.assertEqual(self.db.find_annotations(), [])
        self.assertEqual(self.db.get_annotation_keys([self.item.id]), {})
        self.assertEqual(self.db.get_annotation_values([self.item], key="summary"), {})

    def test_a_failed_run_after_a_finished_one_keeps_the_value(self):
        self.annotate(self.item, "summarize", "summary", "S")

        self.db.record_result(
            self.item,
            "summarize",
            "summary",
            ProcessingStatus.ERROR,
            error="down",
            reset_attempts=True,
        )

        (annotation,) = self.db.find_annotations()
        self.assertEqual(
            (annotation.status, annotation.attempts, annotation.value),
            (ProcessingStatus.ERROR, 1, "S"),
        )

    def test_a_finished_run_needs_a_value_in_the_schema(self):
        with self.assertRaises(IntegrityError), self.db.session_scope() as sess:
            sess.execute(
                text(
                    "INSERT INTO item_annotations (source_item_id, processor, key,"
                    " status, attempts, created_at, attempted_at)"
                    " VALUES (:item, 'p', 'k', 'done', 0, :now, :now)"
                ),
                {"item": self.item.id, "now": "2026-11-11 00:00:00"},
            )


class ContentChangeTests(DatabaseTestCase):
    """A content change deletes the item's annotations (decision 0018)."""

    def setUp(self) -> None:
        super().setUp()
        self.source = make_source()
        self.db.upsert_source_items([make_item(self.source, uid="a1", content=b"v1")])
        (self.item,) = self.db.get_items()
        for key, value in (("summary", "S"), ("tags", ["a"])):
            self.db.record_result(
                self.item, "p", key, ProcessingStatus.DONE, value=value
            )
        self.db.record_result(
            self.item, "p", "broken", ProcessingStatus.ERROR, error="down"
        )

    def test_content_change_deletes_annotations_and_releases_their_values(self):
        self.db.upsert_source_items([make_item(self.source, uid="a1", content=b"v2")])

        self.assertEqual(self.count(DBItemAnnotation), 0)
        self.assertEqual(self.stored_contents(), {self.get_item("a1").content_sha256})
        self.assertEqual(
            [
                i.uid
                for i in self.db.get_unprocessed_items(
                    "broken", version=None, max_retries=1
                )
            ],
            ["a1"],
        )

    def test_other_changes_keep_annotations(self):
        later = datetime(2030, 1, 1, tzinfo=UTC)
        self.db.upsert_source_items(
            [
                make_item(
                    self.source,
                    uid="a1",
                    content=b"v1",
                    title="New title",
                    data={"section": "x"},
                    modified_at=later,
                )
            ]
        )
        self.db.advance_modified_times(self.source.id, {"a1": later})

        self.assertEqual(self.get_item("a1").title, "New title")
        self.assertEqual(self.count(DBItemAnnotation), 3)
        self.assertEqual(
            self.db.get_annotations(self.item), {"summary": "S", "tags": ["a"]}
        )

    def test_the_trigger_applies_to_any_write(self):
        with self.db.session_scope() as sess:
            sess.execute(
                text("UPDATE source_items SET content_sha256 = :sha"),
                {"sha": "0" * 64},
            )

        self.assertEqual(self.count(DBItemAnnotation), 0)

    def test_a_shared_value_is_kept(self):
        other = make_item(self.source, uid="a2", content=b"other")
        self.db.upsert_source_items([other])
        self.db.record_result(other, "p", "summary", ProcessingStatus.DONE, value="S")

        self.db.upsert_source_items([make_item(self.source, uid="a1", content=b"v2")])

        self.assertEqual(self.db.get_annotations(other), {"summary": "S"})


class NextAnnotationTests(unittest.TestCase):
    NOW = datetime(2026, 11, 11, tzinfo=UTC)

    def result(self, previous, status, **kwargs) -> Annotation:
        kwargs.setdefault("value_sha256", "1" * 64 if status == "done" else None)
        return next_annotation(
            previous,
            item_id=1,
            processor="p",
            key="k",
            status=ProcessingStatus(status),
            error=kwargs.pop("error", None),
            version=kwargs.pop("version", None),
            reset_attempts=kwargs.pop("reset_attempts", False),
            now=kwargs.pop("now", self.NOW),
            **kwargs,
        )

    def test_errors_count_attempts_and_reset_starts_afresh(self):
        first = self.result(None, "error", error="e1")
        second = self.result(first, "error", error="e2")
        forced = self.result(second, "error", reset_attempts=True)

        self.assertEqual((first.attempts, second.attempts), (1, 2))
        self.assertEqual(second.last_error, "e2")
        self.assertEqual(forced.attempts, 1)

    def test_done_and_ignored_clear_attempts(self):
        failed = self.result(None, "error", error="e")

        self.assertEqual(self.result(failed, "done").attempts, 0)
        self.assertIsNone(self.result(failed, "ignored").last_error)

    def test_value_time_moves_only_when_the_value_changes(self):
        later = self.NOW + timedelta(days=1)
        done = self.result(None, "done")
        same = self.result(done, "done", now=later)
        changed = self.result(same, "done", value_sha256="2" * 64, now=later)

        self.assertEqual(
            (same.updated_at, same.attempted_at, same.created_at),
            (self.NOW, later, self.NOW),
        )
        self.assertEqual(changed.updated_at, later)

    def test_other_results_keep_the_value(self):
        done = self.result(None, "done")

        self.assertEqual(self.result(done, "ignored").value_sha256, "1" * 64)
        self.assertEqual(self.result(done, "error").value_sha256, "1" * 64)

    def test_done_without_a_value_is_refused(self):
        with self.assertRaises(ValueError):
            self.result(None, "done", value_sha256=None)


class DocumentTests(DatabaseTestCase):
    NOW = datetime(2026, 11, 6, tzinfo=UTC)

    def emit(
        self, app: str, *keys: str, output: str = "out", routes: tuple[str, ...] = ()
    ) -> list[Document]:
        result = AppletResult(
            documents=tuple(
                EmittedDocument(output, key, f"{app} {key}", "text/plain", title=key)
                for key in keys
            )
        )
        return self.db.commit_app_run(app, self.NOW, result, {output: routes}).documents

    def test_find_documents_filters_and_loads_content_on_request(self):
        self.emit("a", "k1", "k2")
        self.emit("b", "k1", output="other")

        def keys(**filters) -> list[str]:
            return [
                f"{d.app}/{d.key}"
                for d in self.db.find_documents(DocumentFilter(**filters))
            ]

        self.assertEqual(keys(), ["a/k1", "a/k2", "b/k1"])
        self.assertEqual(keys(app="a", key="k2"), ["a/k2"])
        self.assertEqual(keys(output="other"), ["b/k1"])
        self.assertEqual(keys(limit=1), ["a/k1"])
        (without,) = self.db.find_documents(DocumentFilter(app="b"))
        (with_content,) = self.db.find_documents(
            DocumentFilter(app="b"), with_content=True
        )
        self.assertIsNone(without.content)
        self.assertEqual((with_content.content, with_content.title), ("b k1", "k1"))

    def test_existing_document_keys(self):
        self.emit("a", "k1")

        self.assertEqual(
            self.db.existing_document_keys("a", [("out", "k1"), ("out", "k2")]),
            {("out", "k1")},
        )

    def test_deleting_documents_cascades_and_releases_their_contents(self):
        first, _ = self.emit("a", "k1", "k2", routes=("chat",))

        self.assertEqual(self.db.delete_documents([first.id]), 1)
        self.assertEqual(self.db.delete_documents([]), 0)

        self.assertEqual([d.key for d in self.db.find_documents()], ["k2"])
        self.assertEqual(self.count(DBDelivery), 1)
        self.assertEqual(len(self.stored_contents()), 1)

    def test_one_document_per_app_output_and_key(self):
        (document,) = self.emit("a", "k1")

        with self.assertRaises(IntegrityError), self.db.session_scope() as sess:
            sess.add(DBDocument.from_dto(document))


class DeliveryTests(DatabaseTestCase):
    NOW = datetime(2026, 11, 6, tzinfo=UTC)

    def emit(self, app: str, *keys: str, routes: tuple[str, ...]) -> None:
        result = AppletResult(
            documents=tuple(
                EmittedDocument("out", key, key, "text/plain") for key in keys
            )
        )
        self.db.commit_app_run(app, self.NOW, result, {"out": routes})

    def test_deliveries_of_a_sink_in_document_order(self):
        self.emit("a", "k1", "k2", routes=("chat", "file"))

        rows = self.db.deliveries_of("chat")

        self.assertEqual([document.key for _, document in rows], ["k1", "k2"])
        self.assertTrue(all(row.status == DeliveryStatus.QUEUED for row, _ in rows))
        self.assertEqual(rows[0][0].document_label, "a/out/k1")

    def test_last_delivered_at_counts_done_rows_of_the_sink_only(self):
        self.emit("a", "k1", "k2", routes=("chat", "file"))
        self.assertIsNone(self.db.last_delivered_at("chat"))
        (first, _), (second, _) = self.db.deliveries_of("chat")
        first.status = DeliveryStatus.DONE
        self.db.save_delivery(first)
        second.status = DeliveryStatus.ERROR
        self.db.save_delivery(second)

        self.assertEqual(self.db.last_delivered_at("chat"), first.updated_at)
        self.assertIsNone(self.db.last_delivered_at("file"))

    def test_find_deliveries_filters_by_document_sink_and_status(self):
        self.emit("a", "k1", "k2", routes=("chat",))
        self.emit("b", "k1", routes=("chat", "file"))

        def found(documents=None, **filters) -> list[tuple[str, str]]:
            return [
                (row.sink, row.document_label)
                for row in self.db.find_deliveries(documents, **filters)
            ]

        self.assertEqual(len(found()), 4)
        self.assertEqual(
            found(DocumentFilter(app="b"), sink="file"), [("file", "b/out/k1")]
        )
        self.assertEqual(len(found(status=DeliveryStatus.QUEUED, sink="chat")), 3)
        self.assertEqual(found(limit=1), [("chat", "a/out/k1")])
        self.assertEqual(found(status=DeliveryStatus.DONE), [])

    def test_added_deliveries_are_stamped_now(self):
        self.emit("a", "k1", routes=())
        (document,) = self.db.find_documents()

        added = self.db.add_deliveries(
            [Delivery("chat", document.id, DeliveryStatus.DONE)]
        )

        (row,) = self.db.find_deliveries()
        self.assertEqual(added, 1)
        self.assertEqual((row.sink, row.status), ("chat", DeliveryStatus.DONE))
        self.assertIsNotNone(row.created_at)
        self.assertEqual(row.created_at, row.updated_at)

    def test_deleting_deliveries_keeps_their_documents(self):
        self.emit("a", "k1", routes=("chat", "file"))
        (row,) = self.db.find_deliveries(sink="chat")

        self.assertEqual(self.db.delete_deliveries([row.id]), 1)
        self.assertEqual(self.db.delete_deliveries([]), 0)

        self.assertEqual([d.sink for d in self.db.find_deliveries()], ["file"])
        self.assertEqual(len(self.db.find_documents()), 1)


class DeleteTests(DatabaseTestCase):
    def test_deleting_items_cascades_and_releases_their_contents(self):
        source = make_source()
        kept, gone = (
            make_item(source, uid="a1", content=b"kept"),
            make_item(source, uid="a2", content=b"gone"),
        )
        self.db.upsert_source_items([kept, gone])
        for item in (kept, gone):
            self.db.record_result(
                item,
                "summarize",
                "summary",
                ProcessingStatus.DONE,
                value=f"S {item.uid}",
            )

        self.assertEqual(self.db.delete_items([gone.id]), 1)
        self.assertEqual(self.db.delete_items([]), 0)

        self.assertEqual([item.uid for item in self.db.get_items()], ["a1"])
        self.assertEqual(self.count(DBItemAnnotation), 1)
        self.assertEqual(len(self.stored_contents()), 2)  # a1 content + summary


if __name__ == "__main__":
    unittest.main()
