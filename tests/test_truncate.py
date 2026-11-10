"""The `truncate` processor, over a database with one markdownified item."""

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

import pydantic

from newstool.db import Database, ProcessingStatus
from newstool.models import SourceData, SourceItem
from newstool.plugins import Services, truncate

SOURCE = SourceData(id="s", name="S", url="https://s.test/", provider="plaza")
MARKDOWN = "# Title\n\n" + "x" * 300


class TruncateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="newstool-test-"))
        self.addCleanup(shutil.rmtree, self.tmp_dir, ignore_errors=True)
        self.db = Database(
            f"sqlite:///{self.tmp_dir}/data.db", self.tmp_dir / "content"
        )
        self.addCleanup(self.db.close)
        self.db.upsert_source_items(
            [
                SourceItem(
                    source=SOURCE,
                    uid="1",
                    title="T",
                    uri="https://s.test/1",
                    content=b"<p></p>",
                    mimetype="text/html",
                )
            ]
        )
        (self.item,) = self.db.get_items()
        self.db.record_result(
            self.item, "markdownify", "markdown", ProcessingStatus.DONE, value=MARKDOWN
        )

    def summary(self, key: str = "summary", **options: object) -> object:
        processor = truncate.TruncateProcessor(
            truncate.TruncateOptions(**options),
            Services(db=self.db, fetcher=Mock()),
        )
        self.assertEqual(processor.process(key=key, force=True).done, 1)
        return self.db.get_annotations(self.item, key=key)[key]

    def test_keeps_the_first_200_characters_of_the_markdown(self) -> None:
        self.assertEqual(self.summary(), MARKDOWN[:200])

    def test_length_is_an_option_and_the_key_is_the_entrys(self) -> None:
        self.assertEqual(self.summary("summary/test", length=10), MARKDOWN[:10])

    def test_accepts_and_ignores_the_options_of_summarize(self) -> None:
        self.assertEqual(
            self.summary(
                llm="nonexistent",
                model="big",
                prompt="Resume: ",
                source_prompts={"s": "Resume: "},
            ),
            MARKDOWN[:200],
        )

    def test_shorter_markdown_is_kept_whole(self) -> None:
        self.assertEqual(self.summary(length=1000), MARKDOWN)

    def test_writes_summary_from_markdown_by_default(self) -> None:
        options = truncate.TruncateOptions()
        self.assertEqual(truncate.TruncateProcessor.output_key(options), "summary")
        self.assertEqual(truncate.TruncateProcessor.required_key(options), "markdown")
        with self.assertRaises(pydantic.ValidationError):
            truncate.TruncateOptions(length=0)


if __name__ == "__main__":
    unittest.main()
