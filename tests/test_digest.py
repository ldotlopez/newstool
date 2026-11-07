"""The digest applet with a stub LLM: no server needed."""

import shutil
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock

from newstool.applets import AppletReader, AppletType
from newstool.db import Database, ProcessingStatus
from newstool.llms import LLMUnavailableError
from newstool.models import AppletRun, EmittedDocument, SourceData, SourceItem
from newstool.plugins import Services, digest

SOURCE = SourceData(id="s", name="S", url="https://s.test/", provider="plaza")
OTHER_SOURCE = SourceData(id="o", name="O", url="https://o.test/", provider="plaza")
# A week after 2026-10-01.
NOW = datetime(2026, 10, 8, tzinfo=UTC)


class DigestAppletTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="newstool-test-"))
        self.db = Database(
            f"sqlite:///{self.tmp_dir}/data.db", self.tmp_dir / "content"
        )

    def tearDown(self) -> None:
        self.db.close()
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def add_item(self, source: SourceData, day: int, markdown: str | None) -> None:
        item = SourceItem(
            source=source,
            uid=f"d{day}",
            title=f"Day {day}",
            uri=f"https://{source.id}.test/{day}",
            content=b"<p></p>",
            mimetype="text/html",
            published_at=datetime(2026, 10, day, tzinfo=UTC),
        )
        self.db.upsert_source_items([item])
        if markdown is not None:
            self.db.record_result(
                item, "markdownify", "markdown", ProcessingStatus.DONE, value=markdown
            )

    def digest(
        self, now: datetime = NOW, response: str = "Week.", **options
    ) -> tuple[Mock, tuple[EmittedDocument, ...]]:
        llm = Mock()
        llm.prompt.return_value = response
        services = Services(db=self.db, fetcher=Mock(), llm_factory=lambda name: llm)
        applet = digest.DigestApplet(digest.DigestOptions(**options), services)
        result = applet.run(now, AppletRun(app="d"), AppletReader(self.db))
        return llm, result.documents

    def test_digests_newest_items_with_markdown_oldest_first(self) -> None:
        self.add_item(SOURCE, 1, "Body 1")
        self.add_item(SOURCE, 2, "Body 2 is long")
        self.add_item(SOURCE, 3, None)
        self.add_item(SOURCE, 4, "Body 4")

        llm, documents = self.digest(
            response="```markdown\nWeek.\n```",
            model="writer",
            max_items=2,
            max_article_chars=6,
        )

        (document,) = documents
        self.assertEqual(
            (document.output, document.key, document.content, document.content_type),
            (
                "digest",
                "s/2026-10-01_2026-10-08",
                "# S: 2026-10-01 – 2026-10-08\n\nWeek.\n",
                "text/markdown",
            ),
        )
        self.assertEqual(document.title, "S: 2026-10-01 – 2026-10-08")
        (prompt,), kwargs = llm.prompt.call_args
        self.assertEqual(kwargs, {"model": "writer", "context_length": 32768})
        self.assertTrue(
            prompt.endswith(
                "### 1. Day 2\nDate: 2026-10-02\nLink: https://s.test/2\n\nBody 2"
                "\n\n### 2. Day 4\nDate: 2026-10-04\nLink: https://s.test/4\n\nBody 4"
            )
        )

    def test_one_digest_per_source_unless_given_sources(self) -> None:
        self.add_item(SOURCE, 1, "Body")
        self.add_item(OTHER_SOURCE, 2, "Body")

        _, documents = self.digest()
        self.assertEqual(sorted(d.key.split("/")[0] for d in documents), ["o", "s"])

        _, documents = self.digest(sources=["o"])
        (document,) = documents
        self.assertEqual(document.key, "o/2026-10-01_2026-10-08")

    def test_nothing_in_the_period_emits_nothing(self) -> None:
        self.add_item(SOURCE, 1, "Body")

        llm, documents = self.digest(now=datetime(2026, 11, 1, tzinfo=UTC))

        self.assertEqual(documents, ())
        llm.prompt.assert_not_called()

    def test_empty_response_is_an_error(self) -> None:
        self.add_item(SOURCE, 1, "Body")

        with self.assertRaises(ValueError):
            self.digest(response=" ")


class DigestPluginTests(unittest.TestCase):
    def test_uses_the_requested_llm(self) -> None:
        llm = Mock()
        requested: list[str | None] = []

        def factory(name: str | None) -> Mock:
            requested.append(name)
            return llm

        ((name, protocol, cls),) = digest.__newstool_plugin__()
        applet = cls(
            digest.DigestOptions(llm="writer"),
            Services(db=Mock(), fetcher=Mock(), llm_factory=factory),
        )

        self.assertEqual((name, protocol), ("digest", AppletType))
        self.assertIs(applet.llm, llm)
        self.assertEqual(requested, ["writer"])

    def test_cannot_be_built_without_an_llm(self) -> None:
        with self.assertRaises(LLMUnavailableError):
            digest.DigestApplet(
                digest.DigestOptions(), Services(db=Mock(), fetcher=Mock())
            )


if __name__ == "__main__":
    unittest.main()
