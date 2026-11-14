from __future__ import annotations

import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET
from datetime import UTC, datetime, time, timedelta
from pathlib import Path
from typing import ClassVar
from unittest.mock import Mock

import pydantic

from newstool.applets import (
    AppletReader,
    AppletType,
    Outputs,
    Schedule,
    check_result,
    run_key,
)
from newstool.db import Database, ProcessingStatus
from newstool.errors import PluginFailure
from newstool.models import (
    AppletResult,
    AppletRun,
    EmittedDocument,
    SourceData,
    SourceItem,
)
from newstool.plugins import Services, digest, feed, itemfeed

SOURCE = SourceData(id="s", name="S", url="https://s.test/", provider="plaza")
NOW = datetime(2026, 11, 6, 12, 0, tzinfo=UTC)
NEVER_RUN = AppletRun(app="a")


class AppletTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="newstool-test-"))
        self.db = Database(
            f"sqlite:///{self.tmp_dir}/data.db", self.tmp_dir / "content"
        )
        self.reader = AppletReader(self.db, [SOURCE.id])
        self.services = Services(db=self.db, fetcher=Mock())

    def tearDown(self) -> None:
        self.db.close()
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def add_items(self, *days: int, data: dict | None = None) -> list[SourceItem]:
        self.db.upsert_source_items(
            [
                SourceItem(
                    source=SOURCE,
                    uid=f"d{day}",
                    title=f"Day {day}",
                    uri=f"https://s.test/{day}",
                    content=f"<p>{day}</p>".encode(),
                    mimetype="text/html",
                    data=data or {},
                    published_at=datetime(2026, 10, day, tzinfo=UTC),
                )
                for day in days
            ]
        )
        return self.db.get_items()

    def annotate(self, item: SourceItem, key: str, value: object) -> None:
        self.db.record_result(item, "p", key, ProcessingStatus.DONE, value=value)


class ScheduleTests(unittest.TestCase):
    def test_unrestricted_is_always_due(self) -> None:
        self.assertTrue(Schedule().is_due(NOW, NOW))

    def test_every_counts_from_the_last_success(self) -> None:
        schedule = Schedule(every=3600)

        self.assertTrue(schedule.is_due(NOW, None))
        self.assertFalse(schedule.is_due(NOW, NOW - timedelta(minutes=59)))
        self.assertTrue(schedule.is_due(NOW, NOW - timedelta(hours=1)))

    def test_days_restrict_the_weekday(self) -> None:
        schedule = Schedule(days=frozenset({4}), tz=UTC)  # Friday

        self.assertTrue(schedule.is_due(NOW, None))  # 2026-11-06 is a Friday
        self.assertFalse(schedule.is_due(NOW + timedelta(days=1), None))

    def test_at_runs_once_a_day_from_that_time(self) -> None:
        schedule = Schedule(at=time(7, 0), tz=UTC)
        morning = NOW.replace(hour=7)

        self.assertFalse(schedule.is_due(NOW.replace(hour=6), None))
        self.assertTrue(schedule.is_due(NOW, None))
        self.assertTrue(schedule.is_due(NOW, morning - timedelta(days=1)))
        self.assertFalse(schedule.is_due(NOW, morning))

    def test_next_due(self) -> None:
        weekly = Schedule(at=time(7, 0), days=frozenset({0}), tz=UTC)  # Monday

        self.assertEqual(
            weekly.next_due(NOW, NOW), datetime(2026, 11, 9, 7, 0, tzinfo=UTC)
        )
        hourly = Schedule(every=3600)
        self.assertEqual(hourly.next_due(NOW, NOW), NOW + timedelta(hours=1))
        self.assertEqual(hourly.next_due(NOW, None), NOW)


class CheckResultTests(unittest.TestCase):
    OUTPUTS: ClassVar[Outputs] = {"out": frozenset({"text/plain"})}

    def result(self, *documents: EmittedDocument) -> AppletResult:
        return AppletResult(documents=documents)

    def document(
        self, output: str = "out", key: str = "k", content_type: str = "text/plain"
    ) -> EmittedDocument:
        return EmittedDocument(output, key, "text", content_type)

    def test_declared_outputs_and_types_pass(self) -> None:
        check_result(self.result(self.document(), self.document(key="j")), self.OUTPUTS)

    def test_undeclared_output_type_or_repeated_key_fail(self) -> None:
        for result in (
            self.result(self.document(output="other")),
            self.result(self.document(content_type="text/html")),
            self.result(self.document(), self.document()),
        ):
            with self.subTest(result=result), self.assertRaises(PluginFailure):
                check_result(result, self.OUTPUTS)


class ReaderTests(AppletTestCase):
    def test_items_filter_by_import_and_publication_time(self) -> None:
        before = datetime.now(UTC)
        self.add_items(1, 2)

        imported = self.reader.items(imported_since=before)
        published = self.reader.items(published_since=datetime(2026, 10, 2, tzinfo=UTC))

        self.assertEqual([item.uid for item in imported], ["d1", "d2"])
        self.assertEqual([item.uid for item in published], ["d2"])
        self.assertEqual(self.reader.items(imported_until=before), [])

    def test_documents_of_other_instances_with_content(self) -> None:
        self.db.commit_app_run(
            "other",
            NOW,
            AppletResult(
                documents=(EmittedDocument("out", "k", "hello", "text/plain"),)
            ),
            {},
        )

        (document,) = self.reader.documents(app="other", output="out")

        self.assertEqual((document.key, document.content), ("k", "hello"))


class FeedTests(AppletTestCase):
    def feed(self, **params) -> ET.Element:
        applet = feed.FeedApplet(feed.Options(**params), self.services)
        result = applet.run(NOW, NEVER_RUN, self.reader)
        check_result(result, feed.FeedApplet.outputs)
        (document,) = result.documents
        self.assertEqual(
            (document.output, document.key, document.content_type),
            ("feed", run_key(NOW), "application/rss+xml"),
        )
        return ET.fromstring(document.content)

    def test_newest_items_first_capped_at_max_items(self) -> None:
        self.add_items(1, 2, 3)

        channel = self.feed(max_items=2).find("channel")

        titles = [item.findtext("title") for item in channel.findall("item")]
        self.assertEqual(titles, ["Day 3", "Day 2"])

    def test_channel_has_required_elements_and_unique_guids(self) -> None:
        self.add_items(1)

        channel = self.feed(title="News", link="https://news.test/").find("channel")

        self.assertEqual(channel.findtext("title"), "News")
        self.assertEqual(channel.findtext("link"), "https://news.test/")
        self.assertEqual(channel.findtext("description"), "News")
        self.assertEqual(channel.find("item").findtext("guid"), "s/d1")

    def test_link_is_omitted_when_not_configured(self) -> None:
        self.assertIsNone(self.feed().find("channel").find("link"))

    def test_reads_only_its_workflow_sources(self) -> None:
        self.add_items(1)
        self.reader = AppletReader(self.db, ["elsewhere"])

        channel = self.feed().find("channel")

        self.assertEqual(channel.findall("item"), [])

    def test_sources_is_not_an_option(self) -> None:
        with self.assertRaises(pydantic.ValidationError):
            feed.Options(sources=["s"])


class ItemFeedTests(AppletTestCase):
    def applet(self, **options) -> itemfeed.ItemFeedApplet:
        return itemfeed.ItemFeedApplet(
            itemfeed.ItemFeedOptions(**options), self.services
        )

    def test_first_run_only_sets_the_cursor(self) -> None:
        for item in self.add_items(1):
            self.annotate(item, "summary", "S")
        now = datetime.now(UTC)

        result = self.applet().run(now, NEVER_RUN, self.reader)

        self.assertEqual(result.documents, ())
        self.assertEqual(
            result.state, {"cursor": now.isoformat(), "start": now.isoformat()}
        )

    def test_items_stored_before_the_first_run_are_never_emitted(self) -> None:
        # Import, then two runs seconds apart: `wait` must not reach back to
        # the items imported before the first run.
        for item in self.add_items(1, 2):
            self.annotate(item, "summary", "S")
        applet = self.applet(wait="1d")
        first_at = datetime.now(UTC)
        first = applet.run(first_at, NEVER_RUN, self.reader)

        run = AppletRun(app="a", state=first.state)
        second = applet.run(first_at + timedelta(seconds=5), run, self.reader)

        self.assertEqual(second.documents, ())
        self.assertEqual(second.state["start"], first_at.isoformat())

    def test_items_imported_after_the_first_run_are_emitted(self) -> None:
        start = datetime.now(UTC) - timedelta(hours=1)
        (item,) = self.add_items(1)
        self.annotate(item, "summary", "New")
        state = {"cursor": datetime.now(UTC).isoformat(), "start": start.isoformat()}

        result = self.applet(wait="1d").run(
            datetime.now(UTC), AppletRun(app="a", state=state), self.reader
        )

        self.assertEqual([d.content for d in result.documents], ["New"])

    def test_emits_summarized_items_imported_since_the_cursor(self) -> None:
        cursor = datetime.now(UTC)
        image = {"image": "https://s.test/i.jpg"}
        first, _unsummarized = self.add_items(1, 2, data=image)
        self.annotate(first, "summary", "One")
        run = AppletRun(app="a", state={"cursor": cursor.isoformat()})

        result = self.applet(wait=0).run(datetime.now(UTC), run, self.reader)

        (document,) = result.documents
        self.assertEqual(
            (document.key, document.content, document.title, document.url),
            ("item:s/d1", "One", "Day 1", "https://s.test/1"),
        )
        self.assertEqual(document.image_url, "https://s.test/i.jpg")

    def test_an_item_waits_for_its_annotation(self) -> None:
        (item,) = self.add_items(1)
        later = datetime.now(UTC) + timedelta(hours=1)
        run = AppletRun(app="a", state={"cursor": later.isoformat()})
        self.annotate(item, "summary", "Late")

        # Imported before the cursor, but within `wait` of it.
        result = self.applet(wait="1d").run(later, run, self.reader)
        self.assertEqual([d.key for d in result.documents], ["item:s/d1"])
        result = self.applet(wait="1m").run(later, run, self.reader)
        self.assertEqual(result.documents, ())

    def test_emits_the_oldest_item_first(self) -> None:
        # Stored newest first; one without a publication time counts by its
        # import time, which is now: the newest.
        items = self.add_items(9, 3, 6)
        self.db.upsert_source_items(
            [
                SourceItem(
                    source=SOURCE,
                    uid="undated",
                    title="Undated",
                    uri="https://s.test/undated",
                    content=b"<p></p>",
                    mimetype="text/html",
                )
            ]
        )
        for item in self.db.get_items():
            self.annotate(item, "summary", item.uid)
        self.assertEqual(len(items), 3)

        result = self.applet(backfill="all").run(
            datetime.now(UTC), NEVER_RUN, self.reader
        )

        self.assertEqual(
            [d.content for d in result.documents], ["d3", "d6", "d9", "undated"]
        )

    def test_backfill_all_emits_everything(self) -> None:
        (item,) = self.add_items(1)
        self.annotate(item, "summary/es", "Uno")

        result = self.applet(backfill="all", annotation="summary/es").run(
            datetime.now(UTC), NEVER_RUN, self.reader
        )

        self.assertEqual([d.content for d in result.documents], ["Uno"])
        self.assertNotIn("start", result.state)

    def test_backfill_emits_what_was_imported_within_it_on_the_first_run(
        self,
    ) -> None:
        (item,) = self.add_items(1)
        self.annotate(item, "summary", "Recent")
        now = datetime.now(UTC)

        recent = self.applet(backfill="1h").run(now, NEVER_RUN, self.reader)
        # Imported (just now) before a start a day after it: left out.
        later = now + timedelta(days=1, hours=1)
        too_old = self.applet(backfill="1h").run(later, NEVER_RUN, self.reader)

        self.assertEqual([d.content for d in recent.documents], ["Recent"])
        self.assertEqual(
            recent.state,
            {
                "cursor": now.isoformat(),
                "start": (now - timedelta(hours=1)).isoformat(),
            },
        )
        self.assertEqual(too_old.documents, ())
        # Later runs keep `start` and never read before it.
        run = AppletRun(app="a", state=recent.state)
        again = self.applet(backfill="1h", wait="1d").run(
            now + timedelta(minutes=5), run, self.reader
        )
        self.assertEqual(again.state["start"], recent.state["start"])

    def test_rejects_an_unknown_backfill(self) -> None:
        with self.assertRaises(pydantic.ValidationError):
            itemfeed.ItemFeedOptions(backfill="forever")

    def test_required_keys_name_the_annotation(self) -> None:
        options = itemfeed.ItemFeedOptions(annotation="summary/es")

        self.assertEqual(
            itemfeed.ItemFeedApplet.required_keys(options), ("summary/es",)
        )


class PluginRegistrationTests(unittest.TestCase):
    def test_registers_every_applet_class(self) -> None:
        registered = [
            *digest.__newstool_plugin__(),
            *feed.__newstool_plugin__(),
            *itemfeed.__newstool_plugin__(),
        ]

        names = [name for name, _, _ in registered]
        self.assertEqual(names, ["digest", "feed", "itemfeed"])
        for _, protocol, cls in registered:
            self.assertIs(protocol, AppletType)
            self.assertIsInstance(cls, AppletType)


if __name__ == "__main__":
    unittest.main()
