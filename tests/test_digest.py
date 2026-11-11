"""The digest applet with a stub LLM: no server needed."""

import json
import shutil
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock

from newstool.applets import AppletReader, AppletType
from newstool.db import Database, ProcessingStatus
from newstool.errors import PluginFailure
from newstool.llms import LLMUnavailableError
from newstool.models import AppletRun, EmittedDocument, SourceData, SourceItem
from newstool.plugins import Services, digest

SOURCE = SourceData(id="s", name="S", url="https://s.test/", provider="plaza")
OTHER_SOURCE = SourceData(id="o", name="O", url="https://o.test/", provider="plaza")
# Noon, so the local days are 2026-10-01 to 2026-10-07 in any nearby zone.
NOW = datetime(2026, 10, 8, 12, tzinfo=UTC)


class DigestTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="newstool-test-"))
        self.db = Database(
            f"sqlite:///{self.tmp_dir}/data.db", self.tmp_dir / "content"
        )
        self.reader = AppletReader(self.db)

    def tearDown(self) -> None:
        self.db.close()
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def add_item(
        self,
        uid: str,
        *,
        source: SourceData = SOURCE,
        day: int = 2,
        summary: str | None = "Summary",
        **annotations: object,
    ) -> SourceItem:
        """An item published on `day` with `summary` and `annotations`
        (keyword `about_spain` is the key `about/spain`)."""
        self.db.upsert_source_items(
            [
                SourceItem(
                    source=source,
                    uid=uid,
                    title=f"Title {uid}",
                    uri=f"https://{source.id}.test/{uid}",
                    content=b"<p></p>",
                    mimetype="text/html",
                    published_at=datetime(2026, 10, day, 12, tzinfo=UTC),
                )
            ]
        )
        (item,) = (i for i in self.db.get_items() if i.uid == uid)
        if summary is not None:
            annotations["summary"] = summary
        for key, value in annotations.items():
            self.db.record_result(
                item, "p", key.replace("_", "/"), ProcessingStatus.DONE, value=value
            )
        return item

    def run_digest(
        self, responses: list[str] | None = None, **options: object
    ) -> tuple[Mock, tuple[EmittedDocument, ...]]:
        llm = Mock()
        llm.prompt.side_effect = responses or []
        services = Services(db=self.db, fetcher=Mock(), llm_factory=lambda name: llm)
        applet = digest.DigestApplet(digest.DigestOptions(**options), services)
        return llm, applet.run(NOW, AppletRun(app="d"), self.reader).documents

    def stories(self, **options: object) -> list[list[str]]:
        """The plan's stories as sorted item titles, best first."""
        _, documents = self.run_digest(write=False, **options)
        (plan,) = documents
        return [
            sorted(entry["title"] for entry in story["items"])
            for story in json.loads(plan.content)["stories"]
        ]


class DigestAppletTests(DigestTestCase):
    def test_merges_a_story_across_sources_and_writes_it(self) -> None:
        self.add_item("a1", tags=["Pleno", "Grau"], summary="First")
        self.add_item("b1", source=OTHER_SOURCE, day=3, tags=["pleno", "grau"])
        self.add_item("a2", tags=["fiestas"])
        self.add_item("old", day=8, tags=["pleno"])  # after the period

        llm, documents = self.run_digest(
            ["## Pleno\n\nText.", "```markdown\n## Fiestas\n```", "Intro."],
            title="Castelló",
            model="writer",
        )

        plan, page = documents
        self.assertEqual(
            (plan.output, plan.key, page.output, page.key, page.content_type),
            (
                "plan",
                "2026-10-01_2026-10-07",
                "digest",
                "2026-10-01_2026-10-07",
                "text/markdown",
            ),
        )
        self.assertEqual(
            page.content,
            "# Castelló: 2026-10-01 – 2026-10-07\n\nIntro.\n\n"
            "## Pleno\n\nText.\n\n## Fiestas\n",
        )
        stories = json.loads(plan.content)["stories"]
        self.assertEqual([story["score"] for story in stories], [2.0, 1.0])
        self.assertEqual([entry["source"] for entry in stories[0]["items"]], ["s", "o"])
        first_prompt = llm.prompt.call_args_list[0]
        self.assertIn(
            "### Title a1\nSource: S\nLink: https://s.test/a1\n\nFirst",
            first_prompt.args[0],
        )
        self.assertEqual(
            first_prompt.kwargs, {"model": "writer", "context_length": 32768}
        )
        self.assertIn("## Pleno\n\nText.", llm.prompt.call_args_list[2].args[0])

    def test_write_false_emits_only_the_plan(self) -> None:
        self.add_item("a1", tags=["pleno"])

        llm, documents = self.run_digest(write=False)

        self.assertEqual([document.output for document in documents], ["plan"])
        llm.prompt.assert_not_called()

    def test_items_without_input_are_left_out(self) -> None:
        self.add_item("a1", tags=["pleno"])
        self.add_item("a2", tags=["pleno"], summary=None)

        self.assertEqual(self.stories(), [["Title a1"]])

    def test_include_and_exclude_filter_by_annotation(self) -> None:
        self.add_item("spain", about_spain=["yes"], topics=["Politics"])
        self.add_item("sports", about_spain=["yes"], topics=["Sports"])
        self.add_item("abroad", about_spain=["no"], topics=["Politics"])
        self.add_item("unlabelled", topics=["politics"])

        self.assertEqual(
            self.stories(
                include={"about/spain": ["yes"]}, exclude={"topics": ["sports"]}
            ),
            [["Title spain"]],
        )

    def test_topic_and_source_weights_rank_the_stories(self) -> None:
        self.add_item("plain", tags=["a"], topics=["cultura"])
        self.add_item("housing", tags=["b"], topics=["vivienda"])
        self.add_item("official", source=OTHER_SOURCE, tags=["c"])

        self.assertEqual(
            self.stories(topic_weights={"Vivienda": 2}, source_weights={"o": 1}),
            [["Title housing"], ["Title official"], ["Title plain"]],
        )
        self.assertEqual(
            len(self.stories(max_stories=1, topic_weights={"vivienda": 1})), 1
        )

    def test_nothing_in_the_period_emits_nothing(self) -> None:
        self.add_item("old", day=8)

        llm, documents = self.run_digest()

        self.assertEqual(documents, ())
        llm.prompt.assert_not_called()

    def test_an_empty_answer_is_an_error(self) -> None:
        self.add_item("a1")

        with self.assertRaises(PluginFailure):
            self.run_digest([" "])

    def test_requirements_follow_the_options(self) -> None:
        options = digest.DigestOptions(
            sources=["s"],
            input="summary/es",
            include={"about/spain": ["yes"]},
            exclude={"topics": ["sports"]},
            topic_weights={"vivienda": 1},
            algorithm="embeddings",
            embedding="summary/es",
        )

        requirements = digest.DigestApplet.requirements(options)

        self.assertEqual(requirements.sources, ("s",))
        self.assertEqual(
            requirements.keys,
            ("summary/es", "tags", "about/spain", "topics", "summary/embedding/es"),
        )
        self.assertEqual(
            digest.DigestApplet.requirements(digest.DigestOptions()).keys,
            ("summary", "tags"),
        )


class DigestGroupingTests(DigestTestCase):
    def test_single_link_chains_through_a_bridge_item_avglink_does_not(self) -> None:
        self.add_item("d1", tags=["a", "b"])
        self.add_item("d2", tags=["b", "c"])  # bridges d1 and d3
        self.add_item("d3", tags=["c", "d"])

        self.assertEqual(
            self.stories(algorithm="singlelink"), [["Title d1", "Title d2", "Title d3"]]
        )
        self.assertEqual(len(self.stories(algorithm="avglink")), 2)

    def test_embeddings_group_variants_without_shared_tags(self) -> None:
        for uid, tags, vector in (
            ("d1", ["BCE"], [1.0, 0.0]),
            ("d2", ["Banco Central Europeo"], [0.9, 0.1]),
            ("d3", ["pleno"], [0.0, 1.0]),
        ):
            self.add_item(uid, tags=tags, **{"tags/embedding": vector})

        self.assertEqual(
            self.stories(algorithm="embeddings"),
            [["Title d1", "Title d2"], ["Title d3"]],
        )
        self.assertEqual(
            self.stories(algorithm="embeddings", embedding_weight=0.0),
            [["Title d1"], ["Title d2"], ["Title d3"]],
        )


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
