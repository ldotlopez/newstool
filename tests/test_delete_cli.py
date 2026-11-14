"""The delete commands end to end, on a temp database through the CLI."""

import shutil
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from click.testing import CliRunner

from newstool.cli import cli
from newstool.db import Database, DeliveryStatus, ProcessingStatus
from newstool.models import AppletResult, EmittedDocument, SourceData, SourceItem

SOURCE = SourceData(id="a", name="A", url="https://a.test/", provider="plaza")


class DeleteCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="newstool-test-"))
        self.config = self.tmp_dir / "config.yaml"
        self.config.write_text(
            f"storage_dir: {self.tmp_dir}\ncache_dir: {self.tmp_dir}/cache\n"
        )
        self.db = Database(
            f"sqlite:///{self.tmp_dir}/data.db", self.tmp_dir / "content"
        )
        self.items = [
            SourceItem(
                source=SOURCE,
                uid=uid,
                title=uid,
                uri=f"https://a.test/{uid}",
                content=uid.encode(),
                mimetype="text/html",
            )
            for uid in ("i1", "i2")
        ]
        self.db.upsert_source_items(self.items)
        # Two runs of one processor, each with its own key and state.
        for item in self.items:
            for key in ("tags/embedding", "markdown/embedding"):
                self.db.record_result(
                    item, "embed", key, ProcessingStatus.DONE, value=[0.5]
                )

    def tearDown(self) -> None:
        self.db.close()
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def run_cli(self, *args: str):
        return CliRunner().invoke(cli, ["-c", str(self.config), *args])

    def emit(self, *keys: str, app: str = "items", sinks=("telegram",)) -> None:
        result = AppletResult(
            documents=tuple(
                EmittedDocument("out", key, key, "text/plain") for key in keys
            )
        )
        self.db.commit_app_run(app, datetime.now(UTC), result, {"out": sinks})

    def test_items_are_deleted(self) -> None:
        result = self.run_cli("delete", "items", "--source", "a")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Deleted 2 item(s)", result.stdout)
        self.assertEqual(self.db.get_items(), [])

    def test_a_selection_without_filters_is_refused(self) -> None:
        for args in (
            ("items", "--limit", "1"),
            ("annotations", "--limit", "1"),
            ("documents", "--limit", "1"),
            ("deliveries", "--limit", "1"),
        ):
            with self.subTest(command=args[0]):
                result = self.run_cli("delete", *args)

                self.assertEqual(result.exit_code, 2)
                self.assertIn("name a filter or an id", result.output)
        self.assertEqual(len(self.db.get_items()), 2)

    def test_annotations_are_deleted_per_processor(self) -> None:
        args = ("annotations", "--processor", "embed", "--item", "1")
        listed = self.run_cli("inspect", *args)
        self.assertIn("embed.markdown/embedding", listed.output)

        result = self.run_cli("delete", *args)

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Deleted 2 annotation(s)", result.stdout)
        self.assertEqual([a.item_id for a in self.db.find_annotations()], [2, 2])
        for key in ("tags/embedding", "markdown/embedding"):
            pending = self.db.get_unprocessed_items(key, version=None, max_retries=3)
            self.assertEqual([item.uid for item in pending], ["i1"])

    def test_annotations_are_deleted_by_key_without_a_processor(self) -> None:
        args = ("annotations", "--key", "tags/embedding")
        listed = self.run_cli("inspect", *args)
        self.assertEqual(listed.output.count("embed.tags/embedding"), 2)

        result = self.run_cli("delete", *args)

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Deleted 2 annotation(s)", result.stdout)
        self.assertEqual(
            {a.key for a in self.db.find_annotations()}, {"markdown/embedding"}
        )
        for key, uids in (("tags/embedding", ["i1", "i2"]), ("markdown/embedding", [])):
            pending = self.db.get_unprocessed_items(key, version=None, max_retries=3)
            self.assertEqual([item.uid for item in pending], uids)

    def test_annotations_are_deleted_by_id_and_limit(self) -> None:
        by_id = self.run_cli("delete", "annotations", "--annotation", "1")
        missing = self.run_cli("delete", "annotations", "--annotation", "1")
        limited = self.run_cli(
            "delete", "annotations", "--processor", "embed", "--limit", "1"
        )

        self.assertIn("Deleted 1 annotation(s)", by_id.stdout)
        self.assertEqual(missing.exit_code, 1)
        self.assertIn("no annotation 1 in the selection", missing.output)
        self.assertIn("Deleted 1 annotation(s)", limited.stdout)
        self.assertEqual(len(self.db.find_annotations()), 2)

    def test_documents_with_pending_deliveries_are_refused(self) -> None:
        self.emit("k1")
        self.emit("k2", app="unrouted", sinks=())

        listed = self.run_cli("inspect", "documents")
        result = self.run_cli("delete", "documents", "--since", "2000-01-01")
        missing = self.run_cli("delete", "documents", "--document", "9")

        self.assertIn("unrouted", listed.output)
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Refused document 1", result.stderr)
        self.assertIn("Deleted 1 document(s)", result.stdout)
        self.assertEqual([d.key for d in self.db.find_documents()], ["k1"])
        self.assertEqual(missing.exit_code, 1)
        self.assertIn("no document 9 in the selection", missing.output)

    def test_deliveries_are_deleted_with_the_inspect_selection(self) -> None:
        self.emit("k1", "k2", sinks=("telegram", "other"))
        args = ("deliveries", "--sink", "telegram", "--key", "k1")
        listed = self.run_cli("inspect", *args)
        self.assertIn("items/out/k1", listed.output)
        self.assertNotIn("items/out/k2", listed.output)

        result = self.run_cli("delete", *args)

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Deleted 1 delivery(ies)", result.stdout)
        self.assertEqual(
            sorted((d.sink, d.document_label) for d in self.db.find_deliveries()),
            [
                ("other", "items/out/k1"),
                ("other", "items/out/k2"),
                ("telegram", "items/out/k2"),
            ],
        )
        self.assertEqual(len(self.db.find_documents()), 2)

    def test_deliveries_are_selected_by_id(self) -> None:
        self.emit("k1", "k2")

        listed = self.run_cli("inspect", "deliveries", "--delivery", "2")
        missing = self.run_cli("inspect", "deliveries", "--delivery", "9")
        result = self.run_cli("delete", "deliveries", "--delivery", "2")

        self.assertEqual(listed.exit_code, 0, listed.output)
        self.assertIn("items/out/k2", listed.output)
        self.assertNotIn("items/out/k1", listed.output)
        self.assertEqual(missing.exit_code, 1)
        self.assertIn("no delivery 9 in the selection", missing.output)
        self.assertIn("Deleted 1 delivery(ies)", result.stdout)
        self.assertEqual([d.id for d in self.db.find_deliveries()], [1])

    def test_deliveries_are_deleted_all_at_once(self) -> None:
        self.emit("k1", "k2")

        mixed = self.run_cli("delete", "deliveries", "--all", "--document", "1")
        other = self.run_cli("delete", "deliveries", "--sink", "x", "--all")
        everything = self.run_cli("delete", "deliveries", "--all")

        self.assertNotEqual(mixed.exit_code, 0)
        self.assertIn("Deleted 0 delivery(ies)", other.stdout)
        self.assertEqual(everything.exit_code, 0, everything.output)
        self.assertIn("Deleted 2 delivery(ies)", everything.stdout)
        self.assertEqual(self.db.find_deliveries(), [])

    def test_deliveries_are_marked_by_selection_or_all_at_once(self) -> None:
        self.emit("k1", "k2")
        (_, second) = self.db.find_deliveries()
        second.status = DeliveryStatus.ERROR
        second.attempts = 3
        second.last_error = "boom"
        self.db.save_delivery(second)

        set_status = ("deliveries", "set-status")
        refused = self.run_cli(*set_status, "--as", "done")
        mixed = self.run_cli(*set_status, "--as", "done", "--all", "--document", "1")
        sending = self.run_cli(*set_status, "--as", "sending", "--all")
        one = self.run_cli(*set_status, "--as", "queued", "--delivery", "2")
        dry = self.run_cli(*set_status, "--as", "done", "--all", "--dry-run")
        everything = self.run_cli(*set_status, "--as", "done", "--all")

        self.assertNotEqual(refused.exit_code, 0)
        self.assertNotEqual(mixed.exit_code, 0)
        self.assertNotEqual(sending.exit_code, 0)
        self.assertIn("Would mark 2 delivery(ies) as done", dry.stdout)
        self.assertEqual(one.exit_code, 0, one.output)
        (queued,) = self.db.find_deliveries(delivery_ids=[2])
        self.assertEqual((queued.attempts, queued.last_error), (0, None))
        self.assertIn("Marked 2 delivery(ies) as done", everything.stdout)
        self.assertEqual(
            {d.status for d in self.db.find_deliveries()}, {DeliveryStatus.DONE}
        )

    def test_send_needs_a_selection_and_skips_unconfigured_sinks(self) -> None:
        self.emit("k1")

        refused = self.run_cli("deliveries", "send")
        skipped = self.run_cli("deliveries", "send", "--delivery", "1")

        self.assertNotEqual(refused.exit_code, 0)
        self.assertEqual(skipped.exit_code, 0, skipped.output)
        self.assertEqual(self.db.find_deliveries()[0].status, DeliveryStatus.QUEUED)

    def test_reset_with_documents_works_for_an_unconfigured_instance(self) -> None:
        self.emit("k1")

        result = self.run_cli("delete", "apps", "--app", "items", "--with-documents")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Reset items; 1 document(s) deleted", result.stdout)
        self.assertEqual(self.db.find_documents(), [])


if __name__ == "__main__":
    unittest.main()
