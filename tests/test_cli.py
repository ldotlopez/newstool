import json
import logging
import re
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock, call, patch

import requests
from click.testing import CliRunner
from foundation.storage import EntryNotFoundError

from newstool.app import AppReport, DeleteSummary, MarkSummary
from newstool.cli import cli
from newstool.config import ConfigError
from newstool.db import DeliveryStatus
from newstool.errors import PluginFailure
from newstool.models import (
    Annotation,
    Delivery,
    Document,
    DocumentFilter,
    ProcessingScope,
    SourceData,
    SourceItem,
)
from newstool.processors import RunSummary
from newstool.sinks import PacingOverride

SOURCE = SourceData(
    id="plaza", name="Plaza", url="https://plaza.test/", provider="plaza"
)


def invoke(app: Mock, *args: str):
    with patch("newstool.cli.app_from_context", return_value=app):
        return CliRunner().invoke(cli, list(args))


class ExternalErrorTests(unittest.TestCase):
    """Failures outside the program show as a message; the traceback needs
    debug logging. Anything else keeps its traceback."""

    def setUp(self) -> None:
        logger = logging.getLogger("newstool")
        self.addCleanup(logger.setLevel, logger.level)
        logger.setLevel(logging.WARNING)

    def process_failing_with(self, error: Exception):
        # Outside `run_each`, which logs and summarizes a unit's failure.
        app = Mock()
        app.process_keys.side_effect = error
        return invoke(app, "process", "--default")

    def test_external_failure_is_a_message_without_traceback(self) -> None:
        result = self.process_failing_with(requests.ConnectionError("llm down"))

        self.assertEqual(result.exit_code, 1)
        self.assertIn("Error: ConnectionError: llm down", result.output)
        self.assertIsInstance(result.exception, SystemExit)

    def test_external_failure_keeps_its_traceback_with_debug(self) -> None:
        logging.getLogger("newstool").setLevel(logging.DEBUG)

        result = self.process_failing_with(requests.ConnectionError("llm down"))

        self.assertIsInstance(result.exception, requests.ConnectionError)

    def test_plugin_failure_is_a_message_without_traceback(self) -> None:
        result = self.process_failing_with(PluginFailure("empty digest"))

        self.assertEqual(result.exit_code, 1)
        self.assertIn("Error: empty digest", result.output)
        self.assertIsInstance(result.exception, SystemExit)

    def test_other_failures_keep_their_traceback(self) -> None:
        result = self.process_failing_with(ValueError("bug?"))

        self.assertIsInstance(result.exception, ValueError)


class CommandTests(unittest.TestCase):
    def test_execution_commands_need_exactly_one_selection(self) -> None:
        commands = [
            ["import"],
            ["process"],
            ["workflows"],
            ["run"],
            ["apps", "run"],
            ["deliver"],
            ["workflows", "--default", "--all"],
            ["workflows", "--all", "-w", "juntas"],
            ["apps", "run", "--app", "news", "--default"],
            ["deliver", "--sink", "chat", "--all"],
        ]
        for args in commands:
            with self.subTest(args=args):
                app = Mock()

                result = invoke(app, *args)

                self.assertEqual(result.exit_code, 2)
                self.assertIn("give exactly one of", result.output)
                app.import_source.assert_not_called()
                app.run_app.assert_not_called()
                app.deliver.assert_not_called()

    def test_run_takes_no_workflow(self) -> None:
        result = invoke(Mock(), "run", "-w", "juntas")

        self.assertEqual(result.exit_code, 2)
        self.assertIn("No such option", result.output)

    def test_import_reports_failed_sources_and_exits_with_error(self) -> None:
        app = Mock()
        app.source_ids.return_value = ["plaza"]
        app.import_source.side_effect = RuntimeError("site down")

        result = invoke(app, "import", "--default")

        self.assertEqual(result.exit_code, 1)
        app.source_ids.assert_called_once_with(["default"], None)
        self.assertIn("site down", result.output)
        self.assertIn("1 source(s) failed", result.output)

    def test_import_all_imports_every_workflow_sources_once(self) -> None:
        app = Mock()
        app.workflows = ["default", "juntas"]
        app.source_ids.return_value = ["plaza", "juntas"]
        app.import_source.return_value = []

        result = invoke(app, "import", "--all")

        self.assertEqual(result.exit_code, 0, result.output)
        app.source_ids.assert_called_once_with(["default", "juntas"], None)
        self.assertEqual(
            [c.args[0] for c in app.import_source.call_args_list], ["plaza", "juntas"]
        )

    def test_import_source_narrows_the_named_workflow(self) -> None:
        app = Mock()
        app.source_ids.return_value = ["juntas"]
        app.import_source.return_value = []

        result = invoke(app, "import", "juntas", "-w", "juntas")

        self.assertEqual(result.exit_code, 0, result.output)
        app.source_ids.assert_called_once_with(["juntas"], "juntas")
        app.import_source.assert_called_once_with("juntas")

    def test_process_all_runs_every_workflow_in_order(self) -> None:
        app = Mock()
        app.workflows = ["default", "juntas"]
        app.process_keys.return_value = ["summary"]
        app.run_process.return_value = RunSummary(done=1)

        result = invoke(app, "process", "summarize", "--all")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(
            app.process_keys.call_args_list,
            [
                call("summarize", workflow="default"),
                call("summarize", workflow="juntas"),
            ],
        )
        self.assertIn("Process (juntas)", result.stdout)

    def test_process_runs_every_entry_of_one_processor_with_scope_and_force(
        self,
    ) -> None:
        app = Mock()
        app.process_keys.return_value = ["summary/es", "summary/en"]
        app.run_process.return_value = RunSummary(done=2)

        result = invoke(
            app,
            "process",
            "summarize",
            "--default",
            "--source",
            "plaza",
            "--item",
            "3",
            "--item",
            "4",
            "--limit",
            "5",
            "--force",
        )

        self.assertEqual(result.exit_code, 0, result.output)
        app.process_keys.assert_called_once_with("summarize", workflow="default")
        scope = ProcessingScope(source="plaza", item_ids=(3, 4), limit=5)
        self.assertEqual(
            app.run_process.call_args_list,
            [
                call("summary/es", workflow="default", scope=scope, force=True),
                call("summary/en", workflow="default", scope=scope, force=True),
            ],
        )

    def test_process_goes_on_after_a_run_raises_and_exits_with_error(self) -> None:
        app = Mock()
        app.process_keys.return_value = ["summary", "tags"]
        app.run_process.side_effect = [RuntimeError("llm down"), RunSummary(done=3)]

        with self.assertLogs("newstool", "ERROR") as logs:
            result = invoke(app, "process", "--default")

        self.assertEqual(result.exit_code, 1)
        self.assertEqual(
            [c.args[0] for c in app.run_process.call_args_list], ["summary", "tags"]
        )
        self.assertIn("summary: failed", logs.output[0])
        self.assertIn("1 failure(s)", result.output)

    def test_process_without_processor_runs_every_entry(self) -> None:
        app = Mock()
        app.process_keys.return_value = ["markdown"]
        app.run_process.return_value = RunSummary(done=1)

        result = invoke(app, "process", "--default")

        self.assertEqual(result.exit_code, 0, result.output)
        app.process_keys.assert_called_once_with(None, workflow="default")
        app.run_process.assert_called_once_with(
            "markdown", workflow="default", scope=ProcessingScope(), force=False
        )
        self.assertIn("markdown", result.output)

    def test_apps_run_runs_every_instance_then_delivers(self) -> None:
        app = Mock()
        app.app_ids = ["news", "digest"]
        app.sink_ids = ["site"]
        app.run_app.side_effect = lambda app_id, now, **kwargs: AppReport(
            app_id, due=app_id == "news", new=(("feed", "k"),)
        )
        app.deliver.return_value = RunSummary(done=1)
        app.unconfigured_pending.return_value = {}

        result = invoke(app, "apps", "run", "--all", "--force")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(
            [(c.args[0], c.kwargs) for c in app.run_app.call_args_list],
            [
                ("news", {"force": True, "dry_run": False}),
                ("digest", {"force": True, "dry_run": False}),
            ],
        )
        app.deliver.assert_called_once()
        self.assertIn("news\tyes\t1\t0\t0", result.stdout)
        self.assertIn("digest\tno\t-\t-\t-", result.stdout)
        self.assertIn("site\t1\t0", result.stdout)

    def test_apps_run_with_app_delivers_to_its_sinks_only(self) -> None:
        app = Mock()
        app.sink_ids = ["chat", "site"]
        app.routed_sinks.return_value = ["site"]
        app.run_app.return_value = AppReport("news", due=True)
        app.deliver.return_value = RunSummary()
        app.unconfigured_pending.return_value = {}

        result = invoke(app, "apps", "run", "--app", "news")

        self.assertEqual(result.exit_code, 0, result.output)
        app.routed_sinks.assert_called_once_with(["news"])
        self.assertEqual([c.args[0] for c in app.deliver.call_args_list], ["site"])

    def test_apps_run_default_runs_the_unskipped_and_delivers_to_their_sinks(
        self,
    ) -> None:
        app = Mock()
        app.app_ids = ["news", "digest"]
        app.default_app_ids = ["news"]
        app.sink_ids = ["chat", "site"]
        app.routed_sinks.return_value = ["site"]
        app.run_app.return_value = AppReport("news", due=True)
        app.deliver.return_value = RunSummary()
        app.unconfigured_pending.return_value = {}

        result = invoke(app, "apps", "run", "--default")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual([c.args[0] for c in app.run_app.call_args_list], ["news"])
        app.routed_sinks.assert_called_once_with(["news"])
        self.assertEqual([c.args[0] for c in app.deliver.call_args_list], ["site"])

    def test_apps_run_no_deliver_stores_and_sends_nothing(self) -> None:
        app = Mock()
        app.app_ids = ["news"]
        app.run_app.return_value = AppReport(
            "news", due=True, ignored=(("feed", "k"),), routed=2
        )

        result = invoke(app, "apps", "run", "--all", "--no-deliver")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(app.run_app.call_args.kwargs["dry_run"], False)
        app.deliver.assert_not_called()
        self.assertIn("news\tyes\t0\t1\t2", result.stdout)
        self.assertNotIn("Deliver", result.stdout)

    def test_apps_run_dry_run_shows_documents_and_delivers_nothing(self) -> None:
        app = Mock()
        app.run_app.return_value = AppReport(
            "news",
            due=True,
            new=(("feed", "k1"),),
            ignored=(("feed", "k0"),),
            state={"cursor": "c"},
        )

        result = invoke(app, "apps", "run", "--app", "news", "--dry-run")

        self.assertEqual(result.exit_code, 0, result.output)
        app.app_instance.assert_called_once_with("news")
        self.assertEqual(app.run_app.call_args.kwargs["dry_run"], True)
        app.deliver.assert_not_called()
        self.assertIn("news\tfeed\tk1\tnew", result.stdout)
        self.assertIn("news\tfeed\tk0\talready stored", result.stdout)
        self.assertIn('news\t{"cursor": "c"}', result.stdout)

    def test_apps_run_exits_with_error_when_an_applet_failed(self) -> None:
        app = Mock()
        app.app_ids = ["news"]
        app.sink_ids = []
        app.run_app.return_value = AppReport("news", due=True, error="broken")
        app.unconfigured_pending.return_value = {}

        result = invoke(app, "apps", "run", "--all")

        self.assertEqual(result.exit_code, 1)
        self.assertIn("1 failure(s)", result.output)

    def test_apps_reset(self) -> None:
        app = Mock()
        app.reset_app.return_value = 3

        result = invoke(app, "apps", "reset", "--app", "news", "--with-documents")

        self.assertEqual(result.exit_code, 0, result.output)
        app.reset_app.assert_called_once_with(
            "news", with_documents=True, dry_run=False
        )
        self.assertIn("Reset news; 3 document(s) deleted", result.output)

    def test_deliver_sends_for_the_named_sinks(self) -> None:
        app = Mock()
        app.deliver.return_value = RunSummary(done=2, failed=1)
        app.unconfigured_pending.return_value = {"gone": 4}

        with self.assertLogs("newstool", "WARNING") as logs:
            result = invoke(app, "deliver", "--sink", "chat")

        self.assertEqual(result.exit_code, 1)
        self.assertEqual(app.deliver.call_args.args[0], "chat")
        self.assertIn("1 delivery(ies) failed", result.output)
        self.assertIn("gone: not configured, 4 pending", logs.output[0])

    def test_deliveries_rename_moves_the_ledger(self) -> None:
        app = Mock()
        app.rename_sink.return_value = 4

        result = invoke(app, "deliveries", "rename", "chat", "channel", "--dry-run")

        self.assertEqual(result.exit_code, 0, result.output)
        app.rename_sink.assert_called_once_with("chat", "channel", dry_run=True)
        self.assertIn("Would move 4 delivery(ies) from chat to channel", result.output)

    def test_deliver_goes_on_after_a_sink_raises(self) -> None:
        app = Mock()
        app.sink_ids = ["chat", "site"]
        app.deliver.side_effect = [RuntimeError("bot blocked"), RunSummary(done=1)]
        app.unconfigured_pending.return_value = {}

        with self.assertLogs("newstool", "ERROR") as logs:
            result = invoke(app, "deliver", "--all")

        self.assertEqual(result.exit_code, 1)
        self.assertEqual(
            [c.args[0] for c in app.deliver.call_args_list], ["chat", "site"]
        )
        self.assertIn("chat: failed", logs.output[0])
        self.assertIn("1 delivery(ies) failed", result.output)

    def test_deliver_passes_the_pacing_override(self) -> None:
        app = Mock()
        app.sink_ids = ["chat"]
        app.deliver.return_value = RunSummary(done=1)
        app.unconfigured_pending.return_value = {}

        result = invoke(
            app, "deliver", "--all", "--ignore-interval", "--ignore-max-per-run"
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(
            app.deliver.call_args.args[2],
            PacingOverride(ignore_interval=True, ignore_max_per_run=True),
        )
        result = invoke(
            app, "deliver", "--all", "--ignore-max-per-run", "--max-per-run", "3"
        )
        self.assertEqual(result.exit_code, 2)
        self.assertIn("exclude each other", result.output)

    def test_writing_commands_take_the_write_lock(self) -> None:
        app = Mock()
        app.process_keys.return_value = []

        with patch("newstool.cli.Application", return_value=app):
            result = CliRunner().invoke(cli, ["process", "--default"])

        self.assertEqual(result.exit_code, 0, result.output)
        app.lock.assert_called_once_with()

    def test_deliver_default_sends_for_the_sinks_of_unskipped_apps(self) -> None:
        app = Mock()
        app.default_app_ids = ["news"]
        app.routed_sinks.return_value = ["site"]
        app.deliver.return_value = RunSummary(done=1)
        app.unconfigured_pending.return_value = {}

        result = invoke(app, "deliver", "--default")

        self.assertEqual(result.exit_code, 0, result.output)
        app.routed_sinks.assert_called_once_with(["news"])
        self.assertEqual([c.args[0] for c in app.deliver.call_args_list], ["site"])

    def test_workflows_goes_on_after_a_failed_phase_and_exits_with_error(
        self,
    ) -> None:
        app = Mock()
        app.source_ids.return_value = ["plaza"]
        app.import_source.return_value = []
        app.process_keys.side_effect = RuntimeError("llm down")

        with self.assertLogs("newstool", "ERROR"):
            result = invoke(app, "workflows", "--default")

        self.assertEqual(result.exit_code, 1)
        self.assertIn("1 failure(s)", result.output)
        # Summaries are results: stdout only, after the progress rows.
        self.assertIn("Import", result.stdout)
        self.assertNotIn("Import", result.stderr)

    def test_workflows_runs_the_named_workflow(self) -> None:
        app = Mock()
        app.source_ids.return_value = ["juntas"]
        app.import_source.return_value = []
        app.process_keys.return_value = []

        result = invoke(app, "workflows", "--workflow", "juntas")

        self.assertEqual(result.exit_code, 0, result.output)
        app.source_ids.assert_called_once_with(["juntas"])
        app.process_keys.assert_called_once_with(None, workflow="juntas")
        app.run_app.assert_not_called()
        app.deliver.assert_not_called()

    def test_workflows_all_runs_every_workflow_in_order(self) -> None:
        app = Mock()
        app.workflows = ["default", "juntas"]
        app.source_ids.return_value = ["plaza"]
        app.import_source.return_value = []
        app.process_keys.return_value = []

        result = invoke(app, "workflows", "--all")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(
            [c.args for c in app.source_ids.call_args_list],
            [(["default"],), (["juntas"],)],
        )
        self.assertEqual(
            [c.kwargs for c in app.process_keys.call_args_list],
            [{"workflow": "default"}, {"workflow": "juntas"}],
        )
        self.assertIn("Import (juntas)", result.stdout)

    def test_run_default_runs_default_then_unskipped_apps_and_their_sinks(
        self,
    ) -> None:
        app = Mock()
        app.default_app_ids = ["news"]
        app.sink_ids = ["chat", "site"]
        app.routed_sinks.return_value = ["site"]
        app.source_ids.return_value = ["plaza"]
        app.import_source.return_value = []
        app.process_keys.return_value = []
        app.run_app.return_value = AppReport("news", due=True)
        app.deliver.return_value = RunSummary(done=1)
        app.unconfigured_pending.return_value = {}

        result = invoke(app, "run", "--default")

        self.assertEqual(result.exit_code, 0, result.output)
        app.source_ids.assert_called_once_with(["default"])
        app.process_keys.assert_called_once_with(None, workflow="default")
        self.assertEqual([c.args[0] for c in app.run_app.call_args_list], ["news"])
        app.routed_sinks.assert_called_once_with(["news"])
        self.assertEqual([c.args[0] for c in app.deliver.call_args_list], ["site"])
        self.assertIn("Apps", result.stdout)
        self.assertIn("site\t1\t0", result.stdout)

    def test_run_all_runs_every_workflow_app_and_sink(self) -> None:
        app = Mock()
        app.workflows = ["default", "juntas"]
        app.app_ids = ["news", "digest"]
        app.sink_ids = ["chat", "site"]
        app.source_ids.return_value = []
        app.process_keys.return_value = []
        app.run_app.side_effect = lambda app_id, now: AppReport(app_id, due=False)
        app.deliver.return_value = RunSummary()
        app.unconfigured_pending.return_value = {}

        result = invoke(app, "run", "--all")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(
            [c.kwargs for c in app.process_keys.call_args_list],
            [{"workflow": "default"}, {"workflow": "juntas"}],
        )
        self.assertEqual(
            [c.args[0] for c in app.run_app.call_args_list], ["news", "digest"]
        )
        app.routed_sinks.assert_not_called()
        self.assertEqual(
            [c.args[0] for c in app.deliver.call_args_list], ["chat", "site"]
        )

    def test_run_goes_on_to_the_apps_after_a_failed_workflow_phase(self) -> None:
        app = Mock()
        app.default_app_ids = ["news"]
        app.routed_sinks.return_value = []
        app.source_ids.side_effect = RuntimeError("bad source")
        app.process_keys.return_value = []
        app.run_app.return_value = AppReport("news", due=True)
        app.unconfigured_pending.return_value = {}

        with self.assertLogs("newstool", "ERROR"):
            result = invoke(app, "run", "--default")

        self.assertEqual(result.exit_code, 1)
        app.run_app.assert_called_once()
        self.assertIn("1 failure(s)", result.output)

    def test_user_errors_are_reported_without_traceback(self) -> None:
        app = Mock()
        app.process_keys.side_effect = ConfigError("processor 'nope' is not loaded")

        result = invoke(app, "process", "nope", "--default")

        self.assertEqual(result.exit_code, 1)
        self.assertIn("processor 'nope' is not loaded", result.output)
        self.assertNotIn("Traceback", result.output)


NOW = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)
ITEM = SourceItem(
    source=SOURCE,
    uid="abc",
    title="Title",
    uri="https://plaza.test/1",
    published_at=NOW,
    id=7,
)


def annotation(annotation_id: int, key: str, value: object) -> Annotation:
    return Annotation(
        item_id=7,
        processor="tagger",
        key=key,
        status="done",
        value=value,
        updated_at=NOW,
        id=annotation_id,
    )


class LogLevelTests(unittest.TestCase):
    """Precedence: --log-level and -v/-q, then NEWSTOOL_LOG_LEVEL, then the
    config's log_level, then warning."""

    def setUp(self) -> None:
        logging.getLogger("newstool").setLevel(logging.NOTSET)
        self.config_dir = Path(tempfile.mkdtemp(prefix="newstool-test-"))

    def level(self, *args: str, env: str | None = None, config: str = "") -> int:
        config_path = self.config_dir / "config.yaml"
        config_path.write_text(config)
        app = Mock()
        app.process_keys.return_value = []
        with patch("newstool.cli.Application", return_value=app):
            result = CliRunner().invoke(
                cli,
                ["-c", str(config_path), *args, "process", "--default"],
                env={"NEWSTOOL_LOG_LEVEL": env},
            )
        self.assertEqual(result.exit_code, 0, result.output)
        return logging.getLogger("newstool").level

    def test_defaults_to_warning(self) -> None:
        self.assertEqual(self.level(), logging.WARNING)

    def test_config_applies(self) -> None:
        self.assertEqual(self.level(config="log_level: info\n"), logging.INFO)

    def test_env_var_beats_config(self) -> None:
        level = self.level(env="error", config="log_level: info\n")
        self.assertEqual(level, logging.ERROR)

    def test_verbose_beats_env_var(self) -> None:
        self.assertEqual(self.level("-v", env="debug"), logging.INFO)

    def test_log_level_option_beats_env_var(self) -> None:
        self.assertEqual(self.level("--log-level", "error", env="info"), logging.ERROR)


class InspectCommandTests(unittest.TestCase):
    def test_items_lists_ids_and_annotation_keys(self) -> None:
        app = Mock()
        app.get_items.return_value = [ITEM]
        app.get_annotation_keys.return_value = {7: [(12, "summarize", "summary")]}

        result = invoke(app, "inspect", "items", "--source", "plaza")

        self.assertEqual(result.exit_code, 0, result.output)
        app.get_items.assert_called_once_with(
            ProcessingScope(source="plaza"), sort="updated"
        )
        self.assertEqual(list(app.get_annotation_keys.call_args.args[0]), [7])
        self.assertIn("Title", result.output)
        self.assertIn("12 summarize.summary", result.output)

    def test_one_item_shows_its_fields_and_a_row_per_annotation(self) -> None:
        app = Mock()
        app.get_items.return_value = [
            SourceItem(
                source=SOURCE,
                uid="abc",
                title="Title",
                uri="https://plaza.test/1",
                content=b"<p>hi</p>",
                data={"author": "Ana"},
                id=7,
            )
        ]
        app.get_annotation_keys.return_value = {
            7: [(12, "summarize", "summary"), (13, "tagger", "tags")]
        }

        result = invoke(app, "inspect", "items", "--item", "7")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Annotation #12", result.output)
        self.assertIn("summarize.summary", result.output)
        self.assertIn("Annotation #13", result.output)
        self.assertIn("Ana", result.output)
        sha256 = app.get_items.return_value[0].content_sha256
        self.assertIn("inspect content --sha256", result.output)
        # the hash folds across lines in a narrow terminal
        self.assertIn(sha256, re.sub(r"[\s│]", "", result.output))

    def test_content_prints_the_stored_bytes(self) -> None:
        app = Mock()
        app.get_stored_content.return_value = b"<p>hi</p>"

        result = invoke(app, "inspect", "content", "--sha256", "ab12")

        self.assertEqual(result.exit_code, 0, result.output)
        app.get_stored_content.assert_called_once_with("ab12")
        self.assertEqual(result.output, "<p>hi</p>")

    def test_missing_content_is_an_error(self) -> None:
        app = Mock()
        app.get_stored_content.side_effect = EntryNotFoundError("ab12")

        result = invoke(app, "inspect", "content", "--sha256", "ab12")

        self.assertEqual(result.exit_code, 1)
        self.assertIn("no content ab12", result.output)

    def test_items_as_json(self) -> None:
        app = Mock()
        app.get_items.return_value = [ITEM]
        app.get_annotation_keys.return_value = {7: [(12, "summarize", "summary")]}

        result = invoke(app, "inspect", "items", "--format", "json")

        self.assertEqual(result.exit_code, 0, result.output)
        (record,) = json.loads(result.output)
        self.assertEqual(record["id"], 7)
        self.assertEqual(record["uid"], "abc")
        self.assertEqual(record["published_at"], "2026-10-18T12:00:00+00:00")
        self.assertEqual(
            record["annotations"],
            [{"id": 12, "processor": "summarize", "key": "summary"}],
        )

    def test_sort_takes_a_key_of_the_entity(self) -> None:
        app = Mock()
        app.get_items.return_value = []
        app.get_annotation_keys.return_value = {}

        result = invoke(app, "inspect", "items", "--sort", "source", "--limit", "5")
        wrong = invoke(app, "inspect", "items", "--sort", "processor")

        self.assertEqual(result.exit_code, 0, result.output)
        app.get_items.assert_called_once_with(ProcessingScope(limit=5), sort="source")
        self.assertEqual(wrong.exit_code, 2)
        self.assertIn("'processor' is not one of", wrong.output)

    def test_missing_item_is_an_error(self) -> None:
        app = Mock()
        app.get_items.return_value = []

        result = invoke(app, "inspect", "items", "--item", "99")

        self.assertEqual(result.exit_code, 1)
        self.assertIn("no item 99 in the selection", result.output)

    def test_annotations_previews_long_values(self) -> None:
        app = Mock()
        app.find_annotations.return_value = [
            annotation(1, "markdown", "# Title\n\n" + "body " * 100),
            annotation(2, "tags", ["a", "b"]),
        ]

        result = invoke(
            app, "inspect", "annotations", "--item", "7", "--processor", "tagger"
        )

        self.assertEqual(result.exit_code, 0, result.output)
        app.find_annotations.assert_called_once_with(
            ProcessingScope(item_ids=(7,)),
            processor="tagger",
            key=None,
            annotation_ids=None,
            sort="updated",
        )
        self.assertIn("# Title…", result.output)
        self.assertNotIn("body body", result.output)
        self.assertIn('["a", "b"]', result.output)

    def test_one_annotation_prints_its_full_value(self) -> None:
        app = Mock()
        app.find_annotations.return_value = [annotation(2, "tags", ["a", "b"])]

        result = invoke(app, "inspect", "annotations", "--annotation", "2")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(result.stdout.strip(), '[\n  "a",\n  "b"\n]')
        self.assertIn("2 · item 7 · tagger.tags", result.stderr)

    def test_annotations_as_json_carry_full_values(self) -> None:
        app = Mock()
        app.find_annotations.return_value = [annotation(2, "tags", ["a", "b"])]

        result = invoke(app, "inspect", "annotations", "--format", "json")

        self.assertEqual(
            json.loads(result.output),
            [
                {
                    "id": 2,
                    "item_id": 7,
                    "processor": "tagger",
                    "key": "tags",
                    "status": "done",
                    "attempts": 0,
                    "last_error": None,
                    "processor_version": None,
                    "value_sha256": None,
                    "value": ["a", "b"],
                    "created_at": None,
                    "attempted_at": None,
                    "updated_at": "2026-10-18T12:00:00+00:00",
                }
            ],
        )

    def test_documents_lists_metadata(self) -> None:
        app = Mock()
        app.find_documents.return_value = [
            Document("news", "feed", "k1", "application/rss+xml", emitted_at=NOW, id=3)
        ]

        result = invoke(app, "inspect", "documents", "--app", "news")

        self.assertEqual(result.exit_code, 0, result.output)
        app.find_documents.assert_called_once_with(
            DocumentFilter(app="news"), sort="emitted", with_content=False
        )
        self.assertIn("3\tnews\tfeed\tk1\tapplication/rss+xml", result.output)

    def test_one_document_prints_content_to_stdout_and_metadata_to_stderr(
        self,
    ) -> None:
        app = Mock()
        app.find_documents.return_value = [
            Document(
                "weekly",
                "digest",
                "a/2026-10-01_2026-10-08",
                "text/markdown",
                "# Week",
                emitted_at=NOW,
                id=4,
            )
        ]

        result = invoke(app, "inspect", "documents", "--document", "4")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertTrue(app.find_documents.call_args.kwargs["with_content"])
        self.assertEqual(result.stdout, "# Week")
        self.assertIn(
            "4 · weekly/digest/a/2026-10-01_2026-10-08 · text/markdown", result.stderr
        )

    def test_missing_document_is_an_error(self) -> None:
        app = Mock()
        app.find_documents.return_value = []

        result = invoke(app, "inspect", "documents", "--document", "9")

        self.assertEqual(result.exit_code, 1)
        self.assertIn("no document 9 in the selection", result.output)

    def test_delete_documents_reports_the_refused(self) -> None:
        app = Mock()
        app.find_documents.return_value = [
            Document("news", "feed", "k", "text/plain", id=1),
            Document("news", "feed", "j", "text/plain", id=2),
        ]
        app.delete_documents.return_value = DeleteSummary(deleted=1, refused=[2])

        result = invoke(app, "delete", "documents", "--app", "news")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Refused document 2", result.stderr)
        self.assertIn("Deleted 1 document(s)", result.stdout)
        self.assertEqual(invoke(Mock(), "delete", "documents").exit_code, 2)

    def test_deliveries_show_their_document_and_state(self) -> None:
        app = Mock()
        app.find_deliveries.return_value = [
            Delivery(
                "chat",
                3,
                "error",
                attempts=2,
                updated_at=NOW,
                last_error="chat not found",
                document_label="items/items/item:a/1",
            ),
        ]

        result = invoke(
            app, "inspect", "deliveries", "--sink", "chat", "--status", "error"
        )

        self.assertEqual(result.exit_code, 0, result.output)
        app.find_deliveries.assert_called_once_with(
            DocumentFilter(),
            sink="chat",
            status=DeliveryStatus.ERROR,
            delivery_ids=None,
            limit=None,
            sort="updated",
        )
        self.assertIn("3 items/items/item:a/1", result.output)
        self.assertIn("chat not", result.output)

    def test_set_status_with_a_sink_marks_the_selected_documents(self) -> None:
        app = Mock()
        app.mark_deliveries.return_value = MarkSummary(created=3, kept=2)

        result = invoke(
            app,
            "deliveries",
            "set-status",
            "--sink",
            "chat",
            "--app",
            "items",
            "--as",
            "done",
        )

        self.assertEqual(result.exit_code, 0, result.output)
        app.mark_deliveries.assert_called_once_with(
            "chat",
            DeliveryStatus.DONE,
            DocumentFilter(app="items"),
            overwrite=False,
            dry_run=False,
        )
        self.assertIn("Marked 3 delivery(ies) as done: 3 new, 0 changed", result.stdout)
        self.assertIn("Left 2 existing delivery(ies)", result.stderr)

    def test_set_status_all_with_a_sink_marks_every_routed_document(self) -> None:
        app = Mock()
        app.mark_deliveries.return_value = MarkSummary(created=1)

        args = ("deliveries", "set-status", "--sink", "chat")
        result = invoke(app, *args, "--all", "--as", "queued", "--dry-run")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(
            app.mark_deliveries.call_args.kwargs,
            {"overwrite": False, "dry_run": True},
        )
        self.assertIn("Would mark 1 delivery(ies)", result.stdout)

    def test_set_status_with_a_sink_and_row_filters_changes_rows(self) -> None:
        app = Mock()
        app.find_deliveries.return_value = []
        app.set_delivery_status.return_value = 0
        args = ("deliveries", "set-status", "--sink", "chat")

        result = invoke(app, *args, "--status", "error", "--as", "queued")

        self.assertEqual(result.exit_code, 0, result.output)
        app.mark_deliveries.assert_not_called()
        self.assertEqual(app.find_deliveries.call_args.kwargs["sink"], "chat")

    def test_set_status_usage_errors(self) -> None:
        app = Mock()
        set_status = ("deliveries", "set-status", "--as", "done")
        for args in (
            ("--overwrite", "--document", "1"),  # no --sink
            ("--sink", "t", "--overwrite", "--delivery", "1"),
            ("--sink", "t", "--all", "--document", "1"),
            (),  # no selection
        ):
            with self.subTest(args=args):
                self.assertEqual(invoke(app, *set_status, *args).exit_code, 2)
        app.mark_deliveries.assert_not_called()
        app.set_delivery_status.assert_not_called()

    def test_send_needs_a_selection_and_exits_with_error_on_failure(self) -> None:
        app = Mock()
        app.find_deliveries.return_value = [Delivery("chat", 3, "done", id=5)]
        app.send_deliveries.return_value = {"chat": RunSummary(failed=1)}

        self.assertEqual(invoke(app, "deliveries", "send").exit_code, 2)
        result = invoke(app, "deliveries", "send", "--delivery", "5")

        self.assertEqual(result.exit_code, 1)
        app.send_deliveries.assert_called_once_with(app.find_deliveries.return_value)


if __name__ == "__main__":
    unittest.main()
