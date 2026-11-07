import os
import tempfile
import unittest
from datetime import time
from pathlib import Path
from unittest.mock import patch

import platformdirs

from newstool.config import ENV_ALIASES, Config, ConfigError, ollama_url

SOURCE = """
sources:
  - id: plaza
    name: Castellón Plaza
    provider: plaza
    url: https://castellonplaza.com/castellon9/
"""


class ConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        # Variables aliased to config keys must not leak in from the shell.
        patcher = patch.dict("os.environ")
        patcher.start()
        self.addCleanup(patcher.stop)
        for variable in ENV_ALIASES:
            os.environ.pop(variable, None)

    def test_expands_environment_variables(self) -> None:
        with patch.dict("os.environ", {"API_KEY": "secret"}):
            config = Config.from_text("plugins:\n  llm:\n    api_key: ${API_KEY}\n")

        self.assertEqual(config.plugins["llm"], {"api_key": "secret"})

    def test_missing_environment_variable_is_a_clear_error(self) -> None:
        with (
            patch.dict("os.environ", clear=True),
            self.assertRaisesRegex(
                ConfigError,
                r"^plugins\.x\.k: environment variable 'API_KEY' is not set$",
            ),
        ):
            Config.from_text("plugins:\n  x: {k: '${API_KEY}'}\n")

    def test_missing_variable_names_the_file_and_where_to_set_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.yaml"
            config_path.write_text("plugins:\n  x:\n    k: ${API_KEY}\n")

            with (
                patch.dict("os.environ", clear=True),
                self.assertRaises(ConfigError) as caught,
            ):
                Config.from_file(config_path)

        self.assertEqual(
            str(caught.exception),
            f"{config_path}: plugins.x.k: environment variable 'API_KEY' is not set\n"
            f"Set API_KEY in the environment or in {Path(directory) / '.env'}.",
        )

    def test_dotenv_next_to_the_config_fills_variables(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.yaml"
            config_path.write_text("plugins:\n  x: {k: '${API_KEY}', m: '${MODEL}'}\n")
            (Path(directory) / ".env").write_text("API_KEY=from-dotenv\nMODEL=small\n")

            with patch.dict("os.environ", {"MODEL": "from-environment"}, clear=True):
                config = Config.from_file(config_path)

        # The real environment wins over .env.
        self.assertEqual(
            config.plugins["x"], {"k": "from-dotenv", "m": "from-environment"}
        )

    def test_config_without_dotenv_uses_the_environment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.yaml"
            config_path.write_text("plugins:\n  x: {k: '${API_KEY}'}\n")

            with patch.dict("os.environ", {"API_KEY": "env"}, clear=True):
                config = Config.from_file(config_path)

        self.assertEqual(config.plugins["x"], {"k": "env"})

    def test_comments_are_not_expanded(self) -> None:
        with patch.dict("os.environ", clear=True):
            config = Config.from_text(
                "# needs ${API_KEY}\nplugins:\n  feedgenerator:\n"
            )

        self.assertEqual(config.plugins, {"feedgenerator": None})

    def test_double_dollar_is_a_literal_dollar(self) -> None:
        config = Config.from_text("plugins:\n  feedgenerator: {title: costs $$5}\n")

        self.assertEqual(config.plugins["feedgenerator"], {"title": "costs $5"})

    def test_sources_are_found_by_id(self) -> None:
        source = Config.from_text(SOURCE).get_source("plaza")

        self.assertEqual(source.provider, "plaza")

    def test_source_id_is_required(self) -> None:
        with self.assertRaises(ConfigError):
            Config.from_text(SOURCE.replace("  - id: plaza\n    name", "  - name"))

    def test_source_rejects_unknown_fields(self) -> None:
        with self.assertRaises(ConfigError):
            Config.from_text(SOURCE + "    uid: legacy\n")

    def test_source_ids_must_be_unique(self) -> None:
        duplicated = SOURCE + SOURCE.removeprefix("\nsources:\n")
        with self.assertRaisesRegex(ConfigError, "source ids must be unique"):
            Config.from_text(duplicated)

    def test_unknown_sections_are_rejected(self) -> None:
        # `process`, `remix` and `deliver` were the default workflow's runs;
        # `remixers` was replaced by `apps` (decision 0015).
        for section in (
            "pipelines: []\n",
            "process: []\n",
            "deliver: []\n",
            "remixers: []\n",
        ):
            with self.subTest(section=section), self.assertRaises(ConfigError):
                Config.from_text(section)

    def test_durations_are_seconds_or_take_a_unit_suffix(self) -> None:
        for text, seconds in (("90", 90), ("5m", 300), ("2h", 7200), ("3d", 259200)):
            with self.subTest(text=text):
                config = Config.from_text(f"cache:\n  expiration: {text}\n")
                self.assertEqual(config.cache.expiration, seconds)

    def test_invalid_durations_are_rejected(self) -> None:
        for text in ("soon", "-5m", "-1"):
            with self.subTest(text=text), self.assertRaises(ConfigError):
                Config.from_text(f"cache:\n  expiration: {text}\n")

    def test_empty_plugin_section_enables_the_plugin(self) -> None:
        config = Config.from_text("plugins:\n  markdownify:\n  feedgenerator: {}\n")

        self.assertEqual(config.plugins, {"markdownify": None, "feedgenerator": {}})

    def test_plugin_section_must_be_a_mapping(self) -> None:
        with self.assertRaises(ConfigError):
            Config.from_text("plugins:\n  feedgenerator: [title]\n")

    def test_catalog_entries_are_a_name_or_a_type_with_id_key_and_options(
        self,
    ) -> None:
        config = Config.from_text(
            "processors:\n  - markdownify\n"
            "  - {processor: summarize, id: summary-es, key: summary/es,"
            " options: {model: m}}\n"
        )

        self.assertEqual(
            [
                (entry.processor, entry.id, entry.key, entry.options)
                for entry in config.processors
            ],
            [
                ("markdownify", None, None, {}),
                ("summarize", "summary-es", "summary/es", {"model": "m"}),
            ],
        )

    def test_catalog_entries_reject_unknown_fields(self) -> None:
        with self.assertRaises(ConfigError):
            Config.from_text("processors:\n  - {enricher: summarize}\n")

    def test_catalog_ids_are_unique_per_section(self) -> None:
        with self.assertRaisesRegex(ConfigError, "processors: id.s. a used twice"):
            Config.from_text(
                "processors:\n  - {processor: summarize, id: a}\n"
                "  - {processor: tagger, id: a}\n"
                "apps:\n  - {app: digest, id: a}\n"
            )
        with self.assertRaisesRegex(ConfigError, "apps: id.s. d used twice"):
            Config.from_text(
                "apps:\n  - {app: digest, id: d}\n  - {app: feed, id: d}\n"
            )
        with self.assertRaisesRegex(ConfigError, "invalid id 'A b'"):
            Config.from_text("sinks:\n  - {sink: telegram, id: A b}\n")

    def test_apps_and_sinks_need_an_id(self) -> None:
        for section in ("apps:\n  - {app: feed}\n", "sinks:\n  - {sink: file}\n"):
            with self.subTest(section=section), self.assertRaises(ConfigError):
                Config.from_text(section)

    def test_app_schedule_and_routes(self) -> None:
        config = Config.from_text(
            "apps:\n  - {id: weekly, app: digest, every: 1d, at: '07:30',"
            " days: [mon, fri], routes: {digest: [tg]}}\n"
        )

        (entry,) = config.apps
        self.assertEqual(entry.every, 86400)
        self.assertEqual(entry.at, time(7, 30))
        self.assertEqual(entry.days, ["mon", "fri"])
        self.assertEqual(entry.routes, {"digest": ["tg"]})

    def test_app_takes_sink_or_routes_and_known_weekdays(self) -> None:
        for app in (
            "{id: a, app: feed, sink: s, routes: {feed: [s]}}",
            "{id: a, app: feed, days: [monday]}",
        ):
            with self.subTest(app=app), self.assertRaises(ConfigError):
                Config.from_text(f"apps:\n  - {app}\n")

    def test_workflow_entries_are_references_or_entries_of_its_own(self) -> None:
        config = Config.from_text(
            SOURCE + "workflows:\n  - name: w\n    sources: [plaza]\n"
            "    process: [markdownify, {processor: summarize, key: s}]\n"
        )

        (workflow,) = config.workflows
        reference, own = workflow.process
        self.assertEqual(reference, "markdownify")
        self.assertEqual((own.processor, own.key), ("summarize", "s"))

    def test_workflow_entries_have_no_id_nor_skip_default(self) -> None:
        for entry in (
            "{processor: summarize, id: s}",
            "{processor: summarize, skip_default: true}",
        ):
            with (
                self.subTest(entry=entry),
                self.assertRaisesRegex(ConfigError, "only catalog entries do"),
            ):
                Config.from_text(
                    SOURCE + f"workflows:\n  - name: w\n    sources: [plaza]\n"
                    f"    process: [{entry}]\n"
                )

    def test_workflows_have_no_remix_nor_deliver(self) -> None:
        for section in ("remix", "deliver"):
            with self.subTest(section=section), self.assertRaises(ConfigError):
                Config.from_text(
                    SOURCE + "workflows:\n  - name: w\n    sources: [plaza]\n"
                    f"    {section}: [feed]\n"
                )

    def test_default_workflow_has_the_sources_without_skip_default(self) -> None:
        config = Config.from_text(
            SOURCE + "  - {id: other, name: O, provider: plaza, url: 'https://o.test/',"
            " skip_default: true}\n"
        )

        (default,) = config.all_workflows()
        self.assertEqual((default.name, default.sources), ("default", ["plaza"]))
        self.assertEqual(default.process, [])

    def test_unconfigured_source_has_clear_error(self) -> None:
        with self.assertRaisesRegex(ConfigError, "source 'missing' is not configured"):
            Config().get_source("missing")


class EnvironmentOverrideTests(unittest.TestCase):
    def test_environment_overrides_the_file_key_by_key(self) -> None:
        with patch.dict("os.environ", {"NEWSTOOL_CACHE__EXPIRATION": "2h"}, clear=True):
            config = Config.from_text("log_level: info\ncache: {expiration: 5m}\n")

        self.assertEqual(config.cache.expiration, 2 * 60 * 60)
        self.assertEqual(config.log_level, "info")

    def test_environment_sets_arbitrary_plugin_options(self) -> None:
        environ = {
            "NEWSTOOL_PLUGINS__TAGGER__MODEL": "small",
            "NEWSTOOL_LOG_LEVEL": "debug",
        }
        with patch.dict("os.environ", environ, clear=True):
            config = Config.from_text("plugins:\n  tagger: {model: big, llm: x}\n")

        self.assertEqual(config.plugins["tagger"], {"model": "small", "llm": "x"})
        self.assertEqual(config.log_level, "debug")

    def test_dotenv_next_to_the_config_feeds_newstool_variables(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.yaml"
            config_path.write_text("log_level: info\n")
            (Path(directory) / ".env").write_text(
                "NEWSTOOL_LOG_LEVEL=error\nUNRELATED=1\n"
            )

            with patch.dict("os.environ", clear=True):
                config = Config.from_file(config_path)

        self.assertEqual(config.log_level, "error")

    def test_environment_wins_over_dotenv(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.yaml"
            config_path.write_text("")
            (Path(directory) / ".env").write_text("NEWSTOOL_LOG_LEVEL=error\n")

            with patch.dict("os.environ", {"NEWSTOOL_LOG_LEVEL": "debug"}, clear=True):
                config = Config.from_file(config_path)

        self.assertEqual(config.log_level, "debug")

    def test_the_environment_given_to_the_load_is_the_one_read(self) -> None:
        with patch.dict("os.environ", {"NEWSTOOL_LOG_LEVEL": "error"}, clear=True):
            config = Config.from_text("", environ={"NEWSTOOL_LOG_LEVEL": "debug"})

        self.assertEqual(config.log_level, "debug")

    def test_unknown_newstool_variables_are_ignored_everywhere(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.yaml"
            config_path.write_text("")
            (Path(directory) / ".env").write_text("NEWSTOOL_TYPO=1\n")

            with patch.dict("os.environ", {"NEWSTOOL_OTHER": "2"}, clear=True):
                Config.from_file(config_path)

    def test_values_are_not_template_expanded(self) -> None:
        with patch.dict("os.environ", {"NEWSTOOL_LOG_LEVEL": "a$b"}, clear=True):
            config = Config.from_text("")

        self.assertEqual(config.log_level, "a$b")


class AliasTests(unittest.TestCase):
    def test_ollama_host_reads_as_a_url(self) -> None:
        for host, expected in [
            ("box", "http://box:11434"),
            ("box:8080", "http://box:8080"),
            ("0.0.0.0", "http://localhost:11434"),
            ("0.0.0.0:8080", "http://localhost:8080"),
            ("[::]:8080", "http://localhost:8080"),
            ("[::1]:8080", "http://[::1]:8080"),
            ("https://box", "https://box"),
            ("http://box:8080/api", "http://box:8080/api"),
            ("box:notaport", "box:notaport"),
        ]:
            with self.subTest(host=host):
                self.assertEqual(ollama_url(host), expected)

    def test_empty_aliased_variables_are_unset(self) -> None:
        with patch.dict("os.environ", {"OLLAMA_HOST": ""}, clear=True):
            self.assertEqual(Config.from_text("").plugins, {})

    def test_external_variables_fill_plugin_options(self) -> None:
        environ = {"OLLAMA_HOST": "box:11434", "OLLAMA_API_KEY": "s$cret"}
        with patch.dict("os.environ", environ, clear=True):
            config = Config.from_text("plugins:\n  ollama: {chat_model: m}\n")

        self.assertEqual(
            config.plugins["ollama"],
            {"chat_model": "m", "api_base": "http://box:11434", "api_key": "s$cret"},
        )

    def test_the_file_wins_over_an_alias_and_newstool_wins_over_both(self) -> None:
        text = "plugins:\n  ollama: {api_base: from-file}\n"
        with patch.dict("os.environ", {"OLLAMA_HOST": "alias"}, clear=True):
            self.assertEqual(
                Config.from_text(text).plugins["ollama"], {"api_base": "from-file"}
            )

        environ = {
            "OLLAMA_HOST": "alias",
            "NEWSTOOL_PLUGINS__OLLAMA__API_BASE": "from-newstool",
        }
        with patch.dict("os.environ", environ, clear=True):
            self.assertEqual(
                Config.from_text(text).plugins["ollama"],
                {"api_base": "from-newstool"},
            )

    def test_alias_in_the_dotenv_next_to_the_config(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.yaml"
            config_path.write_text("")
            (Path(directory) / ".env").write_text("OLLAMA_API_KEY=from-dotenv\n")

            with patch.dict("os.environ", clear=True):
                config = Config.from_file(config_path)

        self.assertEqual(config.plugins["ollama"], {"api_key": "from-dotenv"})


class DirectoryTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="newstool-test-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name).resolve()
        self.config_dir = self.directory / "a" / "b"
        self.config_dir.mkdir(parents=True)
        self.config_path = self.config_dir / "config.yaml"

    def load(self, text: str, **environ: str) -> Config:
        self.config_path.write_text(text)
        with patch.dict("os.environ", environ, clear=True):
            return Config.from_file(self.config_path)

    def test_defaults_are_the_user_directories(self) -> None:
        with patch.dict("os.environ", clear=True):
            config = Config()
            data_dir = platformdirs.user_data_path("newstool")
            cache_dir = platformdirs.user_cache_path("newstool")

        self.assertEqual(config.storage_dir, data_dir)
        self.assertEqual(config.cache_dir, cache_dir)

    def test_storage_dir_holds_the_database_and_the_content(self) -> None:
        config = self.load(f"storage_dir: {self.directory}/store\n")

        self.assertEqual(
            config.database_uri, f"sqlite:///{self.directory}/store/data.db"
        )
        self.assertEqual(config.content_dir, self.directory / "store" / "content")

    def test_relative_paths_are_relative_to_the_config_file(self) -> None:
        for value, expected in [
            ("datadir", self.config_dir / "datadir"),
            ("./datadir", self.config_dir / "datadir"),
            ("../datadir", self.config_dir.parent / "datadir"),
            (f"{self.directory}/abs", self.directory / "abs"),
        ]:
            with self.subTest(value=value):
                config = self.load(f"storage_dir: {value}\ncache_dir: {value}\n")
                self.assertEqual(config.storage_dir, expected)
                self.assertEqual(config.cache_dir, expected)

    def test_home_is_expanded(self) -> None:
        config = self.load("storage_dir: ~/news\n", HOME=str(self.directory))

        self.assertEqual(config.storage_dir, self.directory / "news")

    def test_environment_paths_are_relative_to_the_config_file(self) -> None:
        config = self.load("", NEWSTOOL_STORAGE_DIR="../env-data")

        self.assertEqual(config.storage_dir, self.config_dir.parent / "env-data")

    def test_without_a_file_paths_are_relative_to_the_current_directory(self) -> None:
        with patch.dict("os.environ", {"NEWSTOOL_CACHE_DIR": "cache"}, clear=True):
            config = Config()

        self.assertEqual(config.cache_dir, Path.cwd().resolve() / "cache")

    def test_removed_keys_are_rejected(self) -> None:
        for text in ["db: {uri: 'sqlite://'}\n", "cache: {base_dir: x}\n"]:
            with self.subTest(text=text), self.assertRaises(ConfigError):
                self.load(text)


if __name__ == "__main__":
    unittest.main()
