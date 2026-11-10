import contextlib
import io
import json
import shutil
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock

import pydantic
from sqlalchemy.exc import IntegrityError

from newstool.db import Database, DeliveryStatus
from newstool.models import AppletResult, Delivery, Document, EmittedDocument
from newstool.plugins import Services, filesink, googlechat, stdout, telegram
from newstool.sinks import Deliverer, PacingOverride, SinkOptions, accepts

NOW = datetime(2026, 11, 6, 12, 0, tzinfo=UTC)


class RecordingSink:
    """Records what it sends; fails for the keys in `failing`."""

    def __init__(self, failing: set[str] | None = None) -> None:
        self.failing = failing or set()
        self.sent: list[str] = []

    def send(self, document: Document) -> dict:
        if document.key in self.failing:
            raise RuntimeError(f"{document.key} rejected")
        self.sent.append(document.key)
        return {"message_id": len(self.sent)}


def emitted(*keys: str, output: str = "out") -> AppletResult:
    return AppletResult(
        documents=tuple(
            EmittedDocument(output, key, f"text {key}", "text/plain") for key in keys
        )
    )


class LedgerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="newstool-test-"))
        self.db = Database(
            f"sqlite:///{self.tmp_dir}/data.db", self.tmp_dir / "content"
        )

    def tearDown(self) -> None:
        self.db.close()
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def emit(self, *keys: str, app: str = "a", sinks: tuple[str, ...] = ("chat",)):
        return self.db.commit_app_run(
            app, NOW, emitted(*keys), {"out": sinks}
        ).documents

    def statuses(self, sink: str = "chat") -> dict[str, str]:
        return {
            delivery.document_label.rsplit("/", 1)[1]: delivery.status
            for delivery in self.db.find_deliveries(sink=sink)
        }

    def deliverer(self, sink: RecordingSink, **options) -> Deliverer:
        return Deliverer(self.db, "chat", sink, SinkOptions(**options))


class CommitTests(LedgerTestCase):
    def test_stores_documents_their_deliveries_and_the_run(self) -> None:
        committed = self.db.commit_app_run(
            "a",
            NOW,
            AppletResult(state={"n": 1}, documents=emitted("k1").documents),
            {"out": ("chat", "file")},
        )

        (document,) = committed.documents
        self.assertEqual(committed.routed, 0)
        self.assertEqual(
            (document.app, document.output, document.key), ("a", "out", "k1")
        )
        self.assertEqual(
            {d.sink: d.status for d in self.db.find_deliveries()},
            {"chat": "queued", "file": "queued"},
        )
        run = self.db.get_app_run("a")
        self.assertEqual((run.last_success, run.state), (NOW, {"n": 1}))

    def test_a_key_emitted_again_is_ignored(self) -> None:
        self.emit("k1")

        stored = self.emit("k1", "k2")

        self.assertEqual([d.key for d in stored], ["k2"])
        self.assertEqual(len(self.db.find_deliveries()), 2)

    def test_a_route_added_later_queues_the_documents_emitted_again(self) -> None:
        self.emit("k1", "k2", sinks=())

        committed = self.db.commit_app_run(
            "a", NOW, emitted("k1"), {"out": ("chat", "file")}
        )

        self.assertEqual((committed.documents, committed.routed), ([], 2))
        self.assertEqual(self.statuses("chat"), {"k1": "queued"})
        self.assertEqual(self.statuses("file"), {"k1": "queued"})
        # Emitted again with its rows in place: nothing more.
        again = self.db.commit_app_run("a", NOW, emitted("k1"), {"out": ("chat",)})
        self.assertEqual(again.routed, 0)
        self.assertEqual(
            self.db.count_missing_routes(
                "a", [("out", "k1"), ("out", "k2")], {"out": ("chat",)}
            ),
            1,
        )

    def test_an_output_without_route_stores_its_documents_only(self) -> None:
        self.emit("k1", sinks=())

        self.assertEqual(len(self.db.find_documents()), 1)
        self.assertEqual(self.db.find_deliveries(), [])

    def test_a_failed_run_keeps_state_and_success(self) -> None:
        self.db.commit_app_run("a", NOW, AppletResult(state="kept"), {})
        later = NOW + timedelta(hours=1)
        self.db.start_app_run("a", later)

        self.db.fail_app_run("a", "boom")

        run = self.db.get_app_run("a")
        self.assertEqual(
            (run.last_started, run.last_success, run.last_error, run.state),
            (later, NOW, "boom", "kept"),
        )

    def test_reset_keeps_documents_unless_asked(self) -> None:
        self.emit("k1")

        self.assertEqual(self.db.reset_app("a"), 0)
        self.assertEqual(self.db.get_app_run("a").last_success, None)
        self.assertEqual(self.emit("k1"), [])  # still stored: ignored

        self.assertEqual(self.db.reset_app("a", with_documents=True), 1)
        self.assertEqual(self.db.find_deliveries(), [])
        self.assertEqual([d.key for d in self.emit("k1")], ["k1"])


class DelivererTests(LedgerTestCase):
    def test_sends_queued_rows_oldest_first_once(self) -> None:
        self.emit("k1")
        self.emit("k2", "k3")
        sink = RecordingSink()

        summary = self.deliverer(sink).deliver(NOW)
        again = self.deliverer(sink).deliver(NOW)

        self.assertEqual(sink.sent, ["k1", "k2", "k3"])
        self.assertEqual((summary.done, again.done), (3, 0))
        (first, *_) = self.db.find_deliveries(sink="chat")
        self.assertEqual(first.external_ref, {"message_id": 1})

    def test_max_per_run_and_interval_pace_the_sink(self) -> None:
        self.emit("k1", "k2", "k3")
        sink = RecordingSink()

        self.deliverer(sink, max_per_run=2).deliver(NOW)
        self.assertEqual(sink.sent, ["k1", "k2"])

        paced = self.deliverer(sink, interval="30m")
        paced.deliver(datetime.now(UTC))
        self.assertEqual(sink.sent, ["k1", "k2"])  # the last one was just now
        paced.deliver(datetime.now(UTC) + timedelta(minutes=31))
        self.assertEqual(sink.sent, ["k1", "k2", "k3"])

    def test_a_pacing_override_replaces_the_options_for_one_run(self) -> None:
        self.emit("k1", "k2", "k3", "k4")
        sink = RecordingSink()
        options = SinkOptions(interval="1h", max_per_run=1)

        def run(pacing: PacingOverride) -> None:
            Deliverer(self.db, "chat", sink, options, pacing).deliver(NOW)

        run(PacingOverride())
        run(PacingOverride())  # the interval has not passed
        self.assertEqual(sink.sent, ["k1"])
        run(PacingOverride(ignore_interval=True))
        self.assertEqual(sink.sent, ["k1", "k2"])  # max_per_run still holds
        run(PacingOverride(ignore_interval=True, max_per_run=5))
        self.assertEqual(sink.sent, ["k1", "k2", "k3", "k4"])

    def test_ignore_max_per_run_sends_every_due_row(self) -> None:
        self.emit("k1", "k2", "k3")
        sink = RecordingSink()

        Deliverer(
            self.db,
            "chat",
            sink,
            SinkOptions(max_per_run=1),
            PacingOverride(ignore_max_per_run=True),
        ).deliver(NOW)

        self.assertEqual(sink.sent, ["k1", "k2", "k3"])
        with self.assertRaises(ValueError):
            PacingOverride(ignore_max_per_run=True, max_per_run=2)

    def test_two_applets_share_the_sink_pacing(self) -> None:
        self.emit("k1", app="a")
        self.emit("k2", app="b")
        sink = RecordingSink()

        self.deliverer(sink, interval="1h").deliver(NOW)

        self.assertEqual(sink.sent, ["k1"])

    def test_failures_retry_with_backoff_and_hold_nothing_back(self) -> None:
        self.emit("bad", "good")
        sink = RecordingSink(failing={"bad"})

        with self.assertLogs("newstool.sinks", "ERROR"):
            summary = self.deliverer(sink).deliver(NOW)

        self.assertEqual((summary.done, summary.failed), (1, 1))
        self.assertEqual(self.statuses(), {"bad": "error", "good": "done"})
        (failed,) = self.db.find_deliveries(status=DeliveryStatus.ERROR)
        self.assertEqual((failed.attempts, failed.last_error), (1, "bad rejected"))

        self.assertEqual(self.deliverer(sink).plan(datetime.now(UTC)), [])
        later = datetime.now(UTC) + timedelta(hours=1)
        self.assertEqual(len(self.deliverer(sink).plan(later)), 1)
        self.assertEqual(self.deliverer(sink, max_retries=1).plan(later), [])

    def test_sending_rows_are_never_retried(self) -> None:
        self.emit("k1")
        (delivery,) = self.db.find_deliveries()
        delivery.status = DeliveryStatus.SENDING
        self.db.save_delivery(delivery)

        with self.assertLogs("newstool.sinks", "WARNING"):
            self.assertEqual(self.deliverer(RecordingSink()).plan(NOW), [])

    def test_send_rows_sends_whatever_the_state(self) -> None:
        self.emit("k1")
        sink = RecordingSink()
        self.deliverer(sink).deliver(NOW)

        rows = self.db.deliveries_of("chat")
        summary = self.deliverer(sink).send_rows(rows)

        self.assertEqual((summary.done, sink.sent), (1, ["k1", "k1"]))

    def test_rows_reach_the_sink_with_their_content(self) -> None:
        self.emit("k1")
        received: list[Document] = []
        sink = Mock()
        sink.send.side_effect = lambda document: received.append(document)

        self.deliverer(sink).deliver(NOW)

        self.assertEqual(received[0].content, "text k1")

    def test_one_row_per_sink_and_document(self) -> None:
        (document,) = self.emit("k1")

        with self.assertRaises(IntegrityError):
            self.db.add_deliveries(
                [Delivery(sink="chat", document_id=document.id, status="queued")]
            )


class DeliveryOrderTests(LedgerTestCase):
    def test_documents_go_out_oldest_emitted_first(self) -> None:
        # Two runs: each run's documents in emission order, the earlier run's
        # before the later one's, whatever their keys.
        self.emit("z", "m")
        self.emit("a")
        sink = RecordingSink()

        self.deliverer(sink, max_per_run=10).deliver(NOW)

        self.assertEqual(sink.sent, ["z", "m", "a"])


class AcceptsTests(unittest.TestCase):
    def test_content_types_must_all_be_accepted(self) -> None:
        self.assertTrue(accepts(telegram.TelegramSink, {"text/plain"}))
        self.assertFalse(
            accepts(googlechat.GoogleChatSink, {"text/plain", "application/json"})
        )
        self.assertTrue(accepts(filesink.FileSink, {"application/rss+xml"}))


class FileSinkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="newstool-test-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def sink(self, path: str) -> filesink.FileSink:
        options = filesink.FileOptions(path=path)
        return filesink.FileSink(options, Services(db=Mock(), fetcher=Mock()))

    def test_writes_and_replaces_the_file(self) -> None:
        sink = self.sink(str(self.tmp_dir / "out" / "{app}-{output}.xml"))
        document = Document("news", "feed", "k", "application/rss+xml", "<rss/>")

        sink.send(document)
        reference = sink.send(
            Document("news", "feed", "j", "application/rss+xml", "<new/>")
        )

        target = self.tmp_dir / "out" / "news-feed.xml"
        self.assertEqual(target.read_text(), "<new/>")
        self.assertEqual(reference, {"path": str(target)})
        self.assertEqual(
            sorted(p.name for p in target.parent.iterdir()), ["news-feed.xml"]
        )

    def test_key_slashes_become_underscores(self) -> None:
        sink = self.sink(str(self.tmp_dir / "{key}.md"))

        sink.send(Document("d", "digest", "s/2026-10-01", "text/markdown", "# S"))

        self.assertTrue((self.tmp_dir / "s_2026-10-01.md").exists())

    def test_path_must_be_absolute_and_use_known_fields(self) -> None:
        for path in ("relative.xml", "/x/{name}.xml"):
            with self.subTest(path=path), self.assertRaises(pydantic.ValidationError):
                filesink.FileOptions(path=path)


class StdoutSinkTests(unittest.TestCase):
    def test_prints_each_document_as_a_json_line(self) -> None:
        sink = stdout.StdoutSink(SinkOptions(), Services(db=Mock(), fetcher=Mock()))
        documents = [
            Document(
                "news",
                "items",
                "s/1",
                "text/plain",
                "Resumen ñ",
                title="T",
                url="https://s.test/1",
                emitted_at=NOW,
                id=7,
            ),
            Document("news", "items", "s/2", "text/plain", "Otro"),
        ]

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            references = [sink.send(document) for document in documents]

        self.assertEqual(references, [None, None])
        lines = output.getvalue().splitlines()
        self.assertIn("Resumen ñ", lines[0])
        first = json.loads(lines[0])
        self.assertEqual(first["emitted_at"], NOW.isoformat())
        self.assertEqual(
            {name: first[name] for name in ("app", "output", "key", "id", "title")},
            {"app": "news", "output": "items", "key": "s/1", "id": 7, "title": "T"},
        )
        self.assertEqual(json.loads(lines[1])["content"], "Otro")
        self.assertTrue(accepts(stdout.StdoutSink, {"application/rss+xml"}))


if __name__ == "__main__":
    unittest.main()
