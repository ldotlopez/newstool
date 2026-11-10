"""Application end to end on a temp database, with real plugins that need no
network (markdownify, feed, file) and a stubbed HTTP fetcher."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from foundation.plugin import PluginError, ProtocolConformanceError

from newstool.app import (
    PLUGIN_ENTRY_POINT,
    PLUGINS_NAMESPACE,
    SET_BY_HAND,
    Application,
    LockedError,
    MarkSummary,
)
from newstool.applets import run_key
from newstool.config import Config, ConfigError
from newstool.db import DeliveryStatus, ProcessingStatus
from newstool.errors import PluginFailure
from newstool.models import (
    DocumentFilter,
    PreflightSourceItemData,
    ProcessingScope,
    SourceItem,
    SourceItemData,
)
from newstool.plugins import ClassRegister, Services, feedreader, markdownify
from newstool.plugins.markdownify import MarkdownifyProcessor
from newstool.plugins.ollama import OllamaLLM
from newstool.processors import ProcessorOptions, ProcessorType

SAMPLE = Path(__file__).parent / "samples" / "prensaiberica-item-132310503.html"
SAMPLE_UID = "ec16b09f034ca03296e75d7e5c304f10337f2e77a0327b0d045c54f0a1d970e8"

APRIL = datetime(2026, 4, 30, 10, tzinfo=UTC)
MAY = datetime(2026, 5, 28, 10, tzinfo=UTC)
JUNE = datetime(2026, 6, 25, 10, tzinfo=UTC)
NOW = datetime(2026, 11, 6, 12, tzinfo=UTC)


def listed(
    uid: str, modified_at: datetime | None = None
) -> PreflightSourceItemData[str]:
    return PreflightSourceItemData(
        uid=uid, ref=f"https://x.test/{uid}.pdf", modified_at=modified_at
    )


def retrieved(
    item: PreflightSourceItemData[str],
    *,
    uid: str | None = None,
    modified_at: datetime | None = None,
) -> SourceItemData:
    modified_at = modified_at or item.modified_at
    return SourceItemData(
        uid=uid or item.uid,
        title=item.uid,
        uri=item.ref,
        # A new date is a new revision: the store only updates changed content.
        content=f"%PDF {modified_at}".encode(),
        mimetype="application/pdf",
        modified_at=modified_at,
    )


class ApplicationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="newstool-test-"))
        self.app = self.make_app()

    def tearDown(self) -> None:
        self.app.close()
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def make_app(
        self,
        plugins: str = "  feed: {title: Test feed}\n",
        catalog: str = "processors: [markdownify]\napps: [{id: news, app: feed}]\n",
        workflows: str = "",
    ) -> Application:
        config = Config.from_text(
            f"""
sources:
  - id: mediterraneo
    name: Mediterraneo
    provider: prensaiberica
    url: https://www.elperiodicomediterraneo.com/castello
  - id: juntas
    name: Juntas
    provider: csjuntasgobierno
    url: https://www.castello.es/es/sesiones
plugins:
  prensaiberica:
{plugins}
{catalog}
{workflows}
storage_dir: {self.tmp_dir}
cache_dir: {self.tmp_dir}/cache
"""
        )
        return Application(config)

    def object_of(self, workflow: str, key: str) -> object:
        """The object of the workflow's process run that writes `key`."""
        run = self.app._catalog.process[workflow, key]
        return self.app._object(run.profile)

    def import_sample(self) -> SourceItem:
        provider = self.app._object(self.app._catalog.sources["mediterraneo"])
        item_data = provider.parse_item(SAMPLE.read_bytes())
        preflight_item = PreflightSourceItemData(uid=item_data.uid, ref=item_data.uri)
        with (
            patch.object(provider, "iter_items", return_value=iter([preflight_item])),
            patch.object(provider, "retrieve_item", return_value=item_data),
        ):
            (item,) = self.app.import_source("mediterraneo")
        return item

    def test_import_stores_the_item_in_the_configured_source(self) -> None:
        item = self.import_sample()

        (stored,) = self.app.get_items()
        self.assertEqual(stored.key, ("mediterraneo", SAMPLE_UID))
        self.assertEqual(self.app.get_content(stored), item.content)
        self.assertEqual(item.key, stored.key)
        self.assertEqual(item.id, stored.id)

    def import_preflight(
        self,
        listed: list[PreflightSourceItemData[str]],
        retrieve: Callable[..., SourceItemData] | None = None,
    ) -> tuple[list[SourceItem], Mock]:
        """Import `juntas` from a stubbed listing; `retrieve` stands for
        `retrieve_item` and defaults to an item dated as listed."""
        provider = self.app._object(self.app._catalog.sources["juntas"])
        retrieve_item = Mock(side_effect=retrieve or retrieved)
        with (
            patch.object(provider, "iter_items", return_value=iter(listed)),
            patch.object(provider, "retrieve_item", retrieve_item),
        ):
            items = self.app.import_source("juntas")
        return items, retrieve_item

    def test_stored_items_listed_as_unchanged_are_not_fetched(self) -> None:
        self.import_preflight([listed("new", MAY)])
        # A late upload of an older session lands behind the stored one.
        (imported,), retrieve_item = self.import_preflight(
            [listed("new", MAY), listed("late", APRIL)]
        )

        self.assertEqual(imported.uid, "late")
        retrieve_item.assert_called_once()
        self.assertEqual({item.uid for item in self.app.get_items()}, {"new", "late"})

    def test_import_stores_new_items_oldest_first(self) -> None:
        def retrieve_published(item: PreflightSourceItemData[str]) -> SourceItemData:
            item_data = retrieved(item)
            item_data.published_at = item.modified_at
            return item_data

        items, _ = self.import_preflight(
            [listed("june", JUNE), listed("undated"), listed("april", APRIL)],
            retrieve_published,
        )

        expected = ["april", "june", "undated"]
        self.assertEqual([item.uid for item in items], expected)
        stored = sorted(self.app.get_items(), key=lambda item: item.id)
        self.assertEqual([item.uid for item in stored], expected)

    def test_items_listed_without_a_date_are_always_fetched(self) -> None:
        self.import_preflight([listed("a")])
        (imported,), _ = self.import_preflight([listed("a")])
        self.assertEqual(imported.uid, "a")

    def test_stored_items_listed_as_newer_are_updated(self) -> None:
        self.import_preflight([listed("a", APRIL)])
        (imported,), _ = self.import_preflight([listed("a", MAY)])

        self.assertEqual(imported.modified_at, MAY)
        (stored,) = self.app.get_items()
        self.assertEqual(stored.modified_at, MAY)

    def test_items_not_newer_once_retrieved_are_not_updated(self) -> None:
        self.import_preflight([listed("a", MAY)])
        stale = lambda item: retrieved(item, modified_at=MAY)
        with self.assertLogs("newstool.app", "WARNING") as logs:
            imported, _ = self.import_preflight([listed("a", JUNE)], stale)

        self.assertEqual(imported, [])
        self.assertIn("not newer once retrieved", logs.output[0])
        # The listed date was checked: the next run doesn't fetch it again.
        _, retrieve_item = self.import_preflight([listed("a", JUNE)], stale)
        retrieve_item.assert_not_called()

    def test_items_unchanged_once_retrieved_are_not_fetched_again(self) -> None:
        self.import_preflight([listed("a", APRIL)])

        # The page bumps its date, but its content is still April's: the
        # store writes nothing, yet the listed date counts as checked.
        def same(item) -> SourceItemData:
            april = retrieved(item, modified_at=APRIL)
            return april.model_copy(update={"modified_at": MAY})

        listed_newer = [listed("a", MAY)]
        self.import_preflight(listed_newer, same)

        (stored,) = self.app.get_items()
        self.assertEqual(stored.modified_at, MAY)
        _, retrieve_item = self.import_preflight(listed_newer, same)
        retrieve_item.assert_not_called()

    def test_a_uid_other_than_listed_is_warned_about_and_stored(self) -> None:
        renamed = lambda item: retrieved(item, uid="other")
        with self.assertLogs("newstool.app", "WARNING") as logs:
            (imported,), _ = self.import_preflight([listed("a")], renamed)

        self.assertEqual(imported.uid, "other")
        self.assertIn("retrieved as 'other'", logs.output[0])

    def test_a_bad_item_is_skipped(self) -> None:
        def retrieve(item) -> SourceItemData:
            if item.uid == "bad":
                raise PluginFailure("not a PDF")
            return retrieved(item)

        with self.assertLogs("newstool.app", "ERROR"):
            (imported,), _ = self.import_preflight(
                [listed("bad"), listed("good")], retrieve
            )
        self.assertEqual(imported.uid, "good")

    def test_items_fetched_before_a_failure_are_stored(self) -> None:
        def retrieve(item) -> SourceItemData:
            if item.uid == "second":
                raise ConnectionError("timed out")
            return retrieved(item)

        with self.assertRaises(ConnectionError):
            self.import_preflight([listed("first"), listed("second")], retrieve)
        self.assertEqual([item.uid for item in self.app.get_items()], ["first"])

    def test_listed_dates_must_be_timezone_aware(self) -> None:
        with self.assertRaises(ValueError):
            listed("a", MAY.replace(tzinfo=None))

    def test_source_options_over_the_section_build_its_provider(self) -> None:
        for options, expected in (
            ("{}", "nav"),
            ("{article_selector: .body}", ".body"),
        ):
            with self.subTest(options=options):
                app = self.make_rss_app(options)
                provider = app._object(app._catalog.sources["blog"])
                with patch.object(
                    provider, "retrieve_items", return_value=iter([])
                ) as call:
                    app.import_source("blog")
                app.close()

                self.assertEqual(
                    provider.options, feedreader.Options(article_selector=expected)
                )
                call.assert_called_once_with(app.config.get_source("blog"))

    def test_unknown_provider_option_is_a_config_error(self) -> None:
        with self.assertRaisesRegex(
            ConfigError, r"sources\.blog\.options\.selector: Extra inputs"
        ):
            self.make_rss_app("{selector: .body}")

    def make_rss_app(self, options: str) -> Application:
        return Application(
            Config.from_text(
                f"""
sources:
  - id: blog
    name: Blog
    provider: feedreader
    url: https://blog.test/feed
    options: {options}
plugins:
  feedreader: {{article_selector: nav}}
storage_dir: {self.tmp_dir}/rss
cache_dir: {self.tmp_dir}/cache
"""
            )
        )

    def test_unknown_source_is_a_config_error(self) -> None:
        with self.assertRaises(ConfigError):
            self.app.import_source("missing")

    def test_objects_are_built_when_a_run_needs_them(self) -> None:
        self.assertEqual(self.app._objects, {})
        self.import_sample()
        self.app.run_process("markdown")

        self.assertEqual(
            sorted(profile.name for profile in self.app._objects),
            ["markdownify", "prensaiberica"],
        )

    def test_process_then_run_an_applet(self) -> None:
        item = self.import_sample()

        self.assertEqual(self.app.run_process("markdown").done, 1)
        self.assertEqual(self.app.run_process("markdown").done, 0)
        markdown = self.app.get_annotations(item)["markdown"]
        self.assertIn("asedio carlista", markdown)

        report = self.app.run_app("news", NOW)

        self.assertEqual(report.new, (("feed", run_key(NOW)),))
        (feed,) = self.app.find_documents(with_content=True)
        self.assertEqual((feed.app, feed.output), ("news", "feed"))
        self.assertIn("<title>Test feed</title>", feed.content)
        self.assertIn(f"mediterraneo/{SAMPLE_UID}", feed.content)

    def test_delete_annotations_makes_the_item_pending_again(self) -> None:
        item = self.import_sample()
        self.app.run_process("markdown")

        (annotation,) = self.app.find_annotations(key="markdown")
        self.assertEqual(self.app.delete_annotations([annotation.id]), 1)

        self.assertEqual(self.app.get_annotations(item), {})
        scope = ProcessingScope(source="mediterraneo")
        self.assertEqual(self.app.run_process("markdown", scope=scope).done, 1)

    def test_write_lock_is_exclusive_until_close(self) -> None:
        self.app.lock()
        other = self.make_app()

        with self.assertRaisesRegex(LockedError, "another newstool command"):
            other.lock()
        self.app.close()
        other.lock()
        self.app = other

    def test_only_configured_runs_run(self) -> None:
        with self.assertRaisesRegex(ConfigError, "processor 'nope' does not exist"):
            self.app.process_keys("nope")
        with self.assertRaisesRegex(
            ConfigError, "no process run of workflow 'default' writes the key"
        ):
            self.app.run_process("summary")
        with self.assertRaisesRegex(ConfigError, "app 'nope' is not configured"):
            self.app.run_app("nope", NOW)
        with self.assertRaisesRegex(ConfigError, "sink 'nope' is not configured"):
            self.app.deliver("nope", NOW)
        with self.assertRaisesRegex(ConfigError, "workflow 'nope' is not configured"):
            self.app.process_keys(workflow="nope")

    def test_default_runs_the_catalog_in_order_without_skip_default(self) -> None:
        self.app.close()
        self.app = self.make_app(
            catalog="""
processors:
  - markdownify
  - {processor: markdownify, key: markdown/copy, skip_default: true}
apps:
  - {id: news, app: feed}
  - {id: short, app: feed, options: {max_items: 1}}
"""
        )

        self.assertEqual(self.app.process_keys(), ["markdown"])
        self.assertEqual(self.app.app_ids, ["news", "short"])

    def test_an_applet_runs_when_due_and_its_runs_are_recorded(self) -> None:
        self.app.close()
        self.app = self.make_app(
            catalog="apps:\n  - {id: news, app: feed, every: 1h}\n"
        )
        self.import_sample()

        dry = self.app.run_app("news", NOW, dry_run=True)
        self.assertEqual((dry.due, len(dry.new)), (True, 1))
        self.assertEqual(self.app.find_documents(), [])

        self.assertTrue(self.app.run_app("news", NOW).due)
        self.assertFalse(self.app.run_app("news", NOW + timedelta(minutes=59)).due)
        forced = self.app.run_app("news", NOW, force=True)
        # The same run time: the same key, already stored.
        self.assertEqual((forced.new, len(forced.ignored)), ((), 1))
        (status,) = self.app.app_status(NOW)
        self.assertEqual(status.run.last_success, NOW)
        self.assertEqual(status.next_due, NOW + timedelta(hours=1))

    def test_a_failed_run_is_recorded_and_stores_nothing(self) -> None:
        applet = self.app._object(self.app.app_instance("news").profile)

        with (
            patch.object(applet, "run", side_effect=PluginFailure("broken")),
            self.assertLogs("newstool.app", "ERROR"),
        ):
            report = self.app.run_app("news", NOW)

        self.assertEqual(report.error, "broken")
        (status,) = self.app.app_status(NOW)
        self.assertEqual(
            (status.run.last_started, status.run.last_success, status.run.last_error),
            (NOW, None, "broken"),
        )
        self.assertEqual(self.app.find_documents(), [])

    def test_routed_documents_are_delivered_by_their_sinks(self) -> None:
        site = self.tmp_dir / "site"
        self.app.close()
        self.app = self.make_app(catalog=self.routed_catalog(site))
        self.import_sample()

        self.app.run_app("news", NOW)
        self.assertEqual(len(self.app.plan_delivery("site", NOW)), 1)
        summary = self.app.deliver("site", NOW)

        self.assertEqual(summary.done, 1)
        self.assertIn("<title>Test feed</title>", (site / "news.xml").read_text())
        self.assertEqual(self.app.deliver("site", NOW).done, 0)
        (row,) = self.app.find_deliveries()
        self.assertEqual(row.external_ref, {"path": str(site / "news.xml")})

    @patch("newstool.plugins.telegram.requests.post")
    def test_itemfeed_posts_each_summarized_item_once(self, post: Mock) -> None:
        post.return_value.json.return_value = {"ok": True, "result": {"message_id": 1}}
        self.app.close()
        self.app = self.make_app(
            "  telegram: {bot_token: t}\n",
            catalog="""
llms: [ollama]
processors: [markdownify, summarize]
sinks:
  - {id: chat, sink: telegram, options: {chat_id: main, images: false}}
apps:
  - id: items
    app: itemfeed
    options: {sources: [mediterraneo], since_first_run: false}
    sink: chat
""",
        )
        item = self.import_sample()
        self.app._db.record_result(
            item, "summarize", "summary", ProcessingStatus.DONE, value="S"
        )

        self.app.run_app("items", datetime.now(UTC))
        self.app.deliver("chat", datetime.now(UTC))
        self.app.run_app("items", datetime.now(UTC), force=True)
        self.app.deliver("chat", datetime.now(UTC))

        post.assert_called_once()
        self.assertIn("S", post.call_args.kwargs["json"]["text"])
        (row,) = self.app.find_deliveries()
        self.assertEqual(row.external_ref, {"chat_id": "main", "message_id": 1})

    def routed_catalog(self, site: Path) -> str:
        return f"""
sinks:
  - {{id: site, sink: file, options: {{path: '{site}/{{app}}.xml'}}}}
apps:
  - {{id: news, app: feed, sink: site}}
  - {{id: other, app: feed}}
"""

    def test_deliveries_are_marked_and_sent_again_by_id(self) -> None:
        self.app.close()
        self.app = self.make_app(catalog=self.routed_catalog(self.tmp_dir / "site"))
        self.app.run_app("news", NOW)
        self.app.deliver("site", NOW)
        (row,) = self.app.find_deliveries()

        summaries = self.app.send_deliveries([row])

        self.assertEqual(summaries["site"].done, 1)
        marked = self.app.set_delivery_status(
            self.app.find_deliveries(delivery_ids=[row.id]), DeliveryStatus.QUEUED
        )
        self.assertEqual(marked, 1)
        (row,) = self.app.find_deliveries(status=DeliveryStatus.QUEUED)
        self.assertEqual(row.attempts, 0)
        with self.assertRaises(ValueError):
            self.app.set_delivery_status([row], DeliveryStatus.SENDING)
        row.sink = "gone"
        with self.assertLogs("newstool.app", "WARNING"):
            self.assertEqual(self.app.send_deliveries([row]), {})

    def test_mark_gives_rows_to_documents_routed_to_the_sink(self) -> None:
        self.app.close()
        self.app = self.make_app(catalog=self.routed_catalog(self.tmp_dir / "site"))
        self.app.run_app("other", NOW)  # not routed to `site`
        self.app.run_app("news", NOW)
        (row,) = self.app.find_deliveries()
        self.app._db.delete_deliveries([row.id])

        dry = self.app.mark_deliveries("site", DeliveryStatus.DONE, dry_run=True)
        self.assertEqual(dry, MarkSummary(created=1))
        self.assertEqual(self.app.find_deliveries(), [])

        self.assertEqual(
            self.app.mark_deliveries("site", DeliveryStatus.DONE),
            MarkSummary(created=1),
        )
        self.assertEqual(
            self.app.mark_deliveries("site", DeliveryStatus.QUEUED),
            MarkSummary(kept=1),
        )
        self.assertEqual(
            self.app.mark_deliveries(
                "site",
                DeliveryStatus.ERROR,
                DocumentFilter(app="news"),
                overwrite=True,
            ),
            MarkSummary(changed=1),
        )
        (row,) = self.app.find_deliveries()
        self.assertEqual((row.sink, row.status), ("site", DeliveryStatus.ERROR))
        with self.assertRaisesRegex(ConfigError, "sink 'nope' is not configured"):
            self.app.mark_deliveries("nope", DeliveryStatus.DONE)

        self.app._db.delete_deliveries([row.id])
        self.app.mark_deliveries("site", DeliveryStatus.ERROR)
        (row,) = self.app.find_deliveries()
        self.assertEqual(row.last_error, SET_BY_HAND)

    def test_routed_sinks_of_applet_instances(self) -> None:
        self.app.close()
        self.app = self.make_app(catalog=self.routed_catalog(self.tmp_dir / "site"))

        self.assertEqual(self.app.routed_sinks(["news", "other"]), ["site"])
        self.assertEqual(self.app.routed_sinks(["other"]), [])

    def test_mark_with_filters_queues_documents_not_routed_to_the_sink(self) -> None:
        self.app.close()
        self.app = self.make_app(catalog=self.routed_catalog(self.tmp_dir / "site"))
        self.app.run_app("other", NOW)  # not routed to `site`

        # --all takes the routed documents only.
        self.assertEqual(
            self.app.mark_deliveries("site", DeliveryStatus.QUEUED), MarkSummary()
        )
        self.assertEqual(
            self.app.mark_deliveries(
                "site", DeliveryStatus.QUEUED, DocumentFilter(app="other")
            ),
            MarkSummary(created=1),
        )
        (row,) = self.app.find_deliveries()
        self.assertEqual((row.sink, row.status), ("site", DeliveryStatus.QUEUED))
        self.assertEqual(self.app.deliver("site", NOW).done, 1)
        self.assertTrue((self.tmp_dir / "site" / "other.xml").exists())

    def test_mark_refuses_content_types_the_sink_does_not_accept(self) -> None:
        self.app.close()
        self.app = self.make_app(
            catalog="""
sinks:
  - {id: chat, sink: telegram, options: {bot_token: t, chat_id: c}}
apps:
  - {id: news, app: feed}
"""
        )
        self.app.run_app("news", NOW)

        with self.assertRaisesRegex(ConfigError, "does not accept application/rss"):
            self.app.mark_deliveries(
                "chat", DeliveryStatus.QUEUED, DocumentFilter(app="news")
            )
        self.assertEqual(self.app.find_deliveries(), [])

    def test_a_route_added_later_queues_what_the_applet_emits_again(self) -> None:
        self.app.close()
        self.app = self.make_app(catalog=self.routed_catalog(self.tmp_dir / "site"))
        self.app.run_app("other", NOW)
        self.app.close()
        self.app = self.make_app(
            catalog=self.routed_catalog(self.tmp_dir / "site").replace(
                "{id: other, app: feed}", "{id: other, app: feed, sink: site}"
            )
        )

        dry = self.app.run_app("other", NOW, force=True, dry_run=True)
        report = self.app.run_app("other", NOW, force=True)

        self.assertEqual((dry.routed, report.routed, report.new), (1, 1, ()))
        (row,) = self.app.find_deliveries()
        self.assertEqual((row.sink, row.status), ("site", DeliveryStatus.QUEUED))

    def test_documents_with_pending_deliveries_are_not_deleted(self) -> None:
        self.app.close()
        self.app = self.make_app(catalog=self.routed_catalog(self.tmp_dir / "site"))
        self.app.run_app("news", NOW)
        self.app.run_app("other", NOW)
        news, other = self.app.find_documents()

        summary = self.app.delete_documents([news.id, other.id])

        self.assertEqual((summary.deleted, summary.refused), (1, [news.id]))
        self.app.deliver("site", NOW)
        self.assertEqual(self.app.delete_documents([news.id]).deleted, 1)

    def test_reset_forgets_the_run_and_with_documents_their_deliveries(self) -> None:
        self.app.close()
        self.app = self.make_app(catalog=self.routed_catalog(self.tmp_dir / "site"))
        self.app.run_app("news", NOW)

        self.assertEqual(self.app.reset_app("news", dry_run=True), 0)
        self.assertEqual(
            self.app.reset_app("news", with_documents=True, dry_run=True), 1
        )
        self.assertEqual(self.app.reset_app("news"), 0)
        (status, _) = self.app.app_status(NOW)
        self.assertIsNone(status.run.last_success)
        self.assertEqual(self.app.run_app("news", NOW).new, ())

        self.assertEqual(self.app.reset_app("news", with_documents=True), 1)
        self.assertEqual(self.app.find_deliveries(), [])
        self.assertEqual(len(self.app.run_app("news", NOW).new), 1)

    def test_invalid_entries_are_config_errors(self) -> None:
        workflow = "workflows:\n  - {name: w, sources: [juntas], %s}\n"
        sinks = "sinks:\n  - {id: chat, sink: telegram, options: {bot_token: t, chat_id: c}}\n"
        for catalog, message in (
            (
                "apps: [{id: a, app: nope}]\n",
                r"apps\.0: no plugin provides the applet 'nope'",
            ),
            (
                "apps: [{id: a, app: feed, options: {color: red}}]\n",
                r"apps\.0\.options\.color: Extra inputs are not permitted",
            ),
            (
                "apps: [{id: a, app: feed, sink: nope}]\n",
                r"apps\.0: no sink has the id 'nope'",
            ),
            (
                "apps: [{id: a, app: feed, routes: {items: [x]}}]\n",
                r"apps\.0: feed has no output 'items' \(it has feed\)",
            ),
            (
                sinks + "apps: [{id: a, app: feed, sink: chat}]\n",
                (
                    r"apps\.0: sink 'chat' \(telegram\) does not accept the content"
                    r" of output 'feed' \(application/rss\+xml\)"
                ),
            ),
            (
                "apps: [{id: a, app: feed, options: {sources: [nope]}}]\n",
                r"apps\.0: unknown source\(s\) nope",
            ),
            (
                "sinks: [{id: s, sink: nope}]\n",
                r"sinks\.0: no plugin provides the sink 'nope'",
            ),
            (
                "processors: [markdownify]\n"
                + workflow % "process: [{processor: tagger, key: markdown}]",
                (
                    r"workflows\.w\.process\.0: key 'markdown' is written by"
                    r" markdownify too \(processors\.0\) on the same sources"
                ),
            ),
            (
                "processors:\n  - {processor: markdownify, id: tagger}\n",
                r"processors\.0: the id 'tagger' is a processor type's name",
            ),
        ):
            with (
                self.subTest(catalog=catalog),
                self.assertRaisesRegex(ConfigError, message),
            ):
                self.make_app(catalog=catalog)

    def test_what_runs_read_must_be_written_on_their_sources(self) -> None:
        for catalog, workflows, message in (
            (
                "llms: [ollama]\nprocessors: [summarize]\n",
                "",
                (
                    r"processors\.0: summarize reads 'markdown', and no process run"
                    r" writes it on the sources of workflow 'default'"
                ),
            ),
            (
                (
                    "processors: [markdownify]\n"
                    "apps: [{id: a, app: itemfeed, options: {sources: [juntas]}}]\n"
                ),
                "",
                r"apps\.0: itemfeed reads 'summary', and no process run writes it",
            ),
            (
                "apps: [{id: a, app: singlelink}]\n",
                "",
                r"apps\.0: singlelink reads 'tags', and no process run",
            ),
            (
                (
                    "processors: [{processor: markdownify, skip_default: true}]\n"
                    "apps: [{id: a, app: digest, options: {sources: [juntas]}}]\n"
                ),
                "workflows:\n  - {name: w, sources: [mediterraneo], process: [markdownify]}\n",
                r"apps\.0: digest reads 'markdown'",
            ),
        ):
            with (
                self.subTest(catalog=catalog),
                self.assertRaisesRegex(ConfigError, message),
            ):
                self.make_app(catalog=catalog, workflows=workflows)

    def test_workflows_with_disjoint_sources_may_write_a_key_differently(
        self,
    ) -> None:
        self.app.close()
        self.app = self.make_app(
            catalog="",
            workflows="""
workflows:
  - {name: a, sources: [juntas], process: [markdownify]}
  - name: b
    sources: [mediterraneo]
    process: [{processor: markdownify, options: {max_retries: 1}}]
""",
        )
        item = self.import_sample()  # a `mediterraneo` item

        self.assertEqual(self.app.run_process("markdown", workflow="a").done, 0)
        self.assertEqual(self.app.run_process("markdown", workflow="b").done, 1)
        self.assertIn("markdown", self.app.get_annotations(item))

    def test_other_options_for_a_key_on_shared_sources_are_a_warning(self) -> None:
        self.app.close()
        with self.assertLogs("newstool.catalog", "WARNING") as logs:
            self.app = self.make_app(
                workflows="workflows:\n  - name: a\n    sources: [mediterraneo]\n"
                "    process: [{processor: markdownify, options: {max_retries: 5}}]\n"
            )

        self.assertIn(
            "workflows.a.process.0: key 'markdown' is written with other options"
            " too (processors.0) on the same sources",
            logs.output[0],
        )

    def test_references_to_an_entry_share_its_run(self) -> None:
        self.app.close()
        self.app = self.make_app(
            catalog="processors: [{processor: markdownify, id: md}]\n",
            workflows="workflows:\n  - {name: a, sources: [mediterraneo], process: [md]}\n",
        )
        item = self.import_sample()  # a `mediterraneo` item

        self.assertIs(
            self.object_of("a", "markdown"), self.object_of("default", "markdown")
        )
        self.assertEqual(self.app.run_process("markdown", workflow="a").done, 1)
        # The same run: `default` finds it done.
        self.assertEqual(self.app.run_process("markdown").done, 0)
        self.assertIn("markdown", self.app.get_annotations(item))

    def test_default_uses_the_sources_not_skipped(self) -> None:
        config = Config.from_text(
            """
sources:
  - {id: a, name: A, url: 'https://a.test/', provider: plaza}
  - {id: b, name: B, url: 'https://b.test/', provider: plaza, skip_default: true}
workflows:
  - {name: only-b, sources: [b]}
"""
        )
        self.assertEqual(
            [(workflow.name, workflow.sources) for workflow in config.all_workflows()],
            [("default", ["a"]), ("only-b", ["b"])],
        )

    def test_process_entries_run_in_order_each_with_its_key(self) -> None:
        self.app.close()
        self.app = self.make_app(
            catalog="processors:\n  - markdownify\n"
            "  - {processor: markdownify, key: markdown/copy}\n"
        )
        item = self.import_sample()

        self.assertEqual(self.app.process_keys(), ["markdown", "markdown/copy"])
        self.assertEqual(self.app.process_keys("markdownify"), self.app.process_keys())
        self.assertEqual(self.app.run_process("markdown").done, 1)
        # Its own state: the first run being done does not skip it.
        self.assertEqual(self.app.run_process("markdown/copy").done, 1)
        annotations = self.app.get_annotations(item)
        self.assertEqual(annotations["markdown"], annotations["markdown/copy"])

    def test_invalid_process_entries_are_config_errors(self) -> None:
        for processors, message in (
            (
                "[grouping]",
                r"processors\.0: no plugin provides the processor 'grouping'",
            ),
            (
                "[{processor: markdownify, options: {model: m}}]",
                r"processors\.0\.options\.model: Extra inputs are not permitted",
            ),
            (
                "[{processor: markdownify, options: {key: copy}}]",
                r"processors\.0\.options\.key: Extra inputs are not permitted",
            ),
            (
                "[{processor: markdownify, key: Mark Down}]",
                r"processors\.0: invalid key 'Mark Down'",
            ),
            (
                "[markdownify, markdownify]",
                r"processors\.1: key 'markdown' is written by another entry",
            ),
        ):
            with (
                self.subTest(processors=processors),
                self.assertRaisesRegex(ConfigError, message),
            ):
                self.make_app(catalog=f"processors: {processors}\n")

    def test_invalid_plugin_sections_report_their_config_path(self) -> None:
        with self.assertRaisesRegex(
            ConfigError,
            r"plugins\.markdownify\.version: no such option\n"
            r"plugins\.markdownify\.max_retries: Input should be a valid integer",
        ):
            self.make_app("  markdownify: {version: '2', max_retries: many}\n")
        with self.assertRaisesRegex(
            ConfigError, r"plugins\.nonexistent: no plugin provides 'nonexistent'"
        ):
            self.make_app("  nonexistent:\n")

    def test_sections_hold_the_defaults_of_every_use(self) -> None:
        self.app.close()
        self.app = self.make_app(
            "  markdownify: {max_retries: 7}\n",
            catalog="processors:\n  - markdownify\n"
            "  - {processor: markdownify, key: copy, options: {max_retries: 1}}\n",
        )

        self.assertEqual(self.object_of("default", "markdown").options.max_retries, 7)
        self.assertEqual(self.object_of("default", "copy").options.max_retries, 1)

    def test_llm_consumers_get_the_llm_they_name(self) -> None:
        self.app.close()
        self.app = self.make_app(
            "  ollama: {chat_model: small}\n",
            catalog="""
llms:
  - ollama
  - {llm: ollama, id: big, options: {chat_model: big}}
processors:
  - markdownify
  - summarize
  - {processor: summarize, key: summary/big, options: {llm: big}}
  - {processor: tagger, options: {llm: ollama}}
""",
        )

        default = self.object_of("default", "summary").llm
        self.assertIsInstance(default, OllamaLLM)
        self.assertEqual(default.chat_model, "small")
        self.assertEqual(self.object_of("default", "summary/big").llm.chat_model, "big")
        # A type name: the type with its section's options, built once.
        by_type = self.object_of("default", "tags").llm
        self.assertEqual(by_type.chat_model, "small")
        self.assertIs(self.app._llm("ollama"), by_type)

    def test_a_missing_llm_is_a_config_error(self) -> None:
        for catalog, message in (
            (
                "processors: [markdownify, summarize]\n",
                r"processors\.1: uses an llm, and `llms` is empty",
            ),
            (
                (
                    "llms: [ollama]\nprocessors:\n  - markdownify\n"
                    "  - {processor: summarize, options: {llm: nope}}\n"
                ),
                r"processors\.1: no llm has the id or type 'nope'",
            ),
        ):
            with (
                self.subTest(catalog=catalog),
                self.assertRaisesRegex(ConfigError, message),
            ):
                self.make_app(catalog=catalog)

    def test_a_name_no_plugin_provides_is_a_config_error(self) -> None:
        for config, message in (
            (
                "sources:\n  - {id: a, name: A, url: 'https://a.test/', provider: nope}\n",
                r"sources\.a: no plugin provides the provider 'nope'",
            ),
            (
                "sources:\n  - {id: a, name: A, url: 'https://a.test/', provider: singlelink}\n",
                r"sources\.a: no plugin provides the provider 'singlelink'",
            ),
            (
                "processors: [nope]\n",
                r"processors\.0: no plugin provides the processor 'nope'",
            ),
        ):
            with (
                self.subTest(config=config),
                self.assertRaisesRegex(ConfigError, message),
            ):
                Application(Config.from_text(config))


class ClassRegisterTests(unittest.TestCase):
    def register(self, registered: list) -> ClassRegister:
        register = ClassRegister(PLUGINS_NAMESPACE, PLUGIN_ENTRY_POINT)
        with patch.object(markdownify, PLUGIN_ENTRY_POINT, return_value=registered):
            register.register("markdownify")
        return register

    def test_every_module_registers_conforming_classes(self) -> None:
        register = ClassRegister(PLUGINS_NAMESPACE, PLUGIN_ENTRY_POINT)
        register.register_found()

        self.assertEqual(
            sorted(register.classes(ProcessorType)),
            ["embed", "markdownify", "summarize", "tagger", "truncate"],
        )

    def test_entry_points_must_return_classes(self) -> None:
        instance = MarkdownifyProcessor(
            ProcessorOptions(), Services(db=Mock(), fetcher=Mock())
        )
        register = self.register([("markdownify", ProcessorType, instance)])

        with self.assertRaisesRegex(PluginError, "as an instance, not a class"):
            register.classes(ProcessorType)

    def test_classes_must_conform_to_their_protocol(self) -> None:
        register = self.register([("markdownify", ProcessorType, object)])

        with self.assertRaisesRegex(ProtocolConformanceError, "does not conform"):
            register.classes(ProcessorType)


if __name__ == "__main__":
    unittest.main()
