"""The LLM plugins: the ollama backend with a stubbed client, and its
consumers with a stub LLM. No server needed."""

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pydantic

from newstool.db import Database, ProcessingStatus
from newstool.llms import LLMType, LLMUnavailableError
from newstool.models import SourceData, SourceItem
from newstool.plugins import Services, classify, embed, ollama, summarize, tagger
from newstool.processors import Processor, ProcessorType

SOURCE = SourceData(id="s", name="S", url="https://s.test/", provider="plaza")


class StubLLM:
    def __init__(self, response: str = "") -> None:
        self.response = response
        self.calls: list[tuple[str, object, dict]] = []

    def prompt(
        self,
        prompt: str,
        *,
        model: str | None = None,
        json_mode: bool = False,
        context_length: int | None = None,
    ) -> str:
        self.calls.append(("prompt", prompt, {"model": model, "json_mode": json_mode}))
        return self.response

    def embed(self, texts: list[str], *, model: str | None = None) -> list[list[float]]:
        self.calls.append(("embed", texts, {"model": model}))
        return [[float(i)] for i, _ in enumerate(texts)]


class ServicesTests(unittest.TestCase):
    def test_asks_the_factory_for_the_named_llm(self) -> None:
        llm = StubLLM()
        names: list[str | None] = []

        def factory(name: str | None) -> StubLLM:
            names.append(name)
            return llm

        services = Services(db=Mock(), fetcher=Mock(), llm_factory=factory)

        self.assertIs(services.llm(), llm)
        self.assertIs(services.llm("b"), llm)
        self.assertEqual(names, [None, "b"])

    def test_without_llms_it_raises(self) -> None:
        with self.assertRaisesRegex(LLMUnavailableError, "no llm is configured"):
            Services(db=Mock(), fetcher=Mock()).llm()


class ProcessorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="newstool-test-"))
        self.db = Database(
            f"sqlite:///{self.tmp_dir}/data.db", self.tmp_dir / "content"
        )
        self.db.upsert_source_items(
            [
                SourceItem(
                    source=SOURCE,
                    uid="1",
                    title="T",
                    uri="https://s.test/1",
                    content=b"<p></p>",
                    mimetype="text/html",
                    data={"tags": ["bce"]},
                )
            ]
        )
        (self.item,) = self.db.get_items()
        for processor, key, value in (
            ("markdownify", "markdown", "# T\n\nBody"),
            ("tagger", "tags", ["pleno", "BCE"]),
        ):
            self.db.record_result(
                self.item, processor, key, ProcessingStatus.DONE, value=value
            )

    def tearDown(self) -> None:
        self.db.close()
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def build(self, cls: type, llm: StubLLM, **options: object) -> Processor:
        """A processor of `cls` with `options`, using `llm`."""
        services = Services(db=self.db, fetcher=Mock(), llm_factory=lambda name: llm)
        return cls(cls.options_model(**options), services)

    def annotation(self, processor: Processor, key: str) -> object:
        """Run `processor`, writing `key`; return its value."""
        summary = processor.process(key=key, force=True)
        self.assertEqual(summary.done, 1)
        return self.db.get_annotations(self.item, key=key)[key]


class SummarizeTests(ProcessorTestCase):
    def test_summarizes_with_the_backend_model_unless_overridden(self) -> None:
        llm = StubLLM(" A summary. ")
        processor = self.build(summarize.SummarizeProcessor, llm)

        self.assertEqual(self.annotation(processor, "summary"), "A summary.")
        self.assertEqual(llm.calls[0][2], {"model": None, "json_mode": False})

        self.annotation(
            self.build(summarize.SummarizeProcessor, llm, model="small"), "summary"
        )
        self.assertEqual(llm.calls[1][2]["model"], "small")

    def test_an_empty_response_is_an_error_without_traceback(self) -> None:
        processor = self.build(summarize.SummarizeProcessor, StubLLM("  "))

        with self.assertLogs("newstool.processors", "ERROR") as logs:
            summary = processor.process(key="summary", force=True)

        self.assertEqual(summary.failed, 1)
        self.assertIsNone(logs.records[0].exc_info)
        self.assertIn("LLM returned an empty summary", logs.records[0].getMessage())

    def test_each_use_writes_its_key_with_its_options(self) -> None:
        llm = StubLLM("Resumen.")
        default = self.build(
            summarize.SummarizeProcessor, llm, model="small", prompt="Summarize: "
        )
        spanish = self.build(
            summarize.SummarizeProcessor, llm, model="big", prompt="Resume: "
        )

        self.annotation(default, "summary")
        self.annotation(spanish, "summary/es")

        self.assertEqual(
            [(call[1], call[2]["model"]) for call in llm.calls],
            [("Summarize: # T\n\nBody", "small"), ("Resume: # T\n\nBody", "big")],
        )
        self.assertEqual(
            self.db.get_annotations(self.item).keys() & {"summary", "summary/es"},
            {"summary", "summary/es"},
        )

    def test_a_source_prompt_replaces_the_prompt_for_its_items(self) -> None:
        llm = StubLLM("Resumen.")
        own = self.build(
            summarize.SummarizeProcessor,
            llm,
            prompt="Summarize: ",
            source_prompts={SOURCE.id: "Resume: "},
        )
        other = self.build(
            summarize.SummarizeProcessor,
            llm,
            prompt="Summarize: ",
            source_prompts={"elsewhere": "Resume: "},
        )

        self.annotation(own, "summary")
        self.annotation(other, "summary")

        self.assertEqual(
            [call[1] for call in llm.calls],
            ["Resume: # T\n\nBody", "Summarize: # T\n\nBody"],
        )

    def test_rejects_options_the_processor_does_not_take(self) -> None:
        options = summarize.SummarizeOptions()
        self.assertEqual(summarize.SummarizeProcessor.output_key(options), "summary")
        with self.assertRaises(pydantic.ValidationError):
            summarize.SummarizeOptions.model_validate({"temperature": 1})

    def test_an_interrupted_run_keeps_the_summaries_already_made(self) -> None:
        self.db.upsert_source_items(
            [
                SourceItem(
                    source=SOURCE,
                    uid=uid,
                    title="T",
                    uri=f"https://s.test/{uid}",
                    content=b"<p></p>",
                    mimetype="text/html",
                )
                for uid in ("2", "3")
            ]
        )
        items = self.db.get_items()
        for item in items[1:]:
            self.db.record_result(
                item, "markdownify", "markdown", ProcessingStatus.DONE, value="# T"
            )

        class InterruptedLLM(StubLLM):
            def prompt(self, prompt: str, **options: object) -> str:
                if len(self.calls) == 2:
                    raise KeyboardInterrupt
                return super().prompt(prompt, **options)

        processor = self.build(summarize.SummarizeProcessor, InterruptedLLM("Summary."))
        with self.assertRaises(KeyboardInterrupt):
            processor.process(key="summary")

        # A fresh connection sees only committed rows.
        reopened = Database(
            f"sqlite:///{self.tmp_dir}/data.db", self.tmp_dir / "content"
        )
        self.addCleanup(reopened.close)
        summaries = reopened.get_annotation_values(items, key="summary")
        self.assertEqual(len(summaries), 2)
        self.assertEqual(set(summaries.values()), {"Summary."})
        unprocessed = reopened.get_unprocessed_items(
            "summary", version=None, max_retries=3, requires="markdown"
        )
        self.assertEqual(len(unprocessed), 1)


class TaggerTests(ProcessorTestCase):
    def test_merges_json_tags_with_the_item_tags(self) -> None:
        llm = StubLLM('```json\n{"items": ["BCE", "Pleno"]}\n```')
        processor = self.build(tagger.TaggerProcessor, llm, model="small")

        self.assertEqual(self.annotation(processor, "tags"), ["BCE", "Pleno"])
        self.assertEqual(llm.calls[0][2], {"model": "small", "json_mode": True})

    def test_the_prompt_carries_the_publisher_tags(self) -> None:
        self.assertIn(
            "tagged the article with: bce, Pleno.",
            tagger.tags_prompt("Body", ["bce", "Pleno"]),
        )
        self.assertNotIn("Publisher's Tags", tagger.tags_prompt("Body", []))
        llm = StubLLM('{"items": ["Pleno"]}')

        tags = self.annotation(self.build(tagger.TaggerProcessor, llm), "tags")

        self.assertIn("tagged the article with: bce.", llm.calls[0][1])
        self.assertEqual(tags, ["Pleno", "bce"])


class ClassifyTests(ProcessorTestCase):
    def test_keeps_only_the_configured_labels(self) -> None:
        llm = StubLLM('{"labels": ["Vivienda", "astrology", "cultura"]}')
        processor = self.build(
            classify.ClassifyProcessor,
            llm,
            labels=["cultura", "vivienda", "deportes"],
            question="Which topics?",
        )

        self.assertEqual(self.annotation(processor, "topics"), ["cultura", "vivienda"])
        prompt = llm.calls[0][1]
        self.assertTrue(prompt.startswith("Which topics?"))
        self.assertIn("Labels: cultura, vivienda, deportes", prompt)
        self.assertIn("tagged the article with: bce.", prompt)
        self.assertTrue(prompt.endswith("# T\n\nBody"))

    def test_an_invalid_answer_fails_the_item(self) -> None:
        processor = self.build(classify.ClassifyProcessor, StubLLM("[]"), labels=["a"])

        self.assertEqual(processor.process(key="topics", force=True).failed, 1)


class EmbedTests(ProcessorTestCase):
    def test_embeds_the_tags_text_by_default(self) -> None:
        llm = StubLLM()
        processor = self.build(embed.EmbedProcessor, llm, model="embedder")

        self.assertEqual(self.annotation(processor, "tags/embedding"), [0.0])
        self.assertEqual(llm.calls, [("embed", ["BCE, pleno"], {"model": "embedder"})])

    def test_embeds_the_input_its_options_name(self) -> None:
        llm = StubLLM()
        processor = self.build(embed.EmbedProcessor, llm, input="markdown")

        self.annotation(processor, "markdown/embedding")

        self.assertEqual(llm.calls, [("embed", ["# T\n\nBody"], {"model": None})])
        options = embed.EmbedOptions(input="markdown")
        self.assertEqual(embed.EmbedProcessor.required_key(options), "markdown")

    def test_output_key_follows_the_input(self) -> None:
        for overrides, key in (
            ({}, "tags/embedding"),
            ({"input": "markdown"}, "markdown/embedding"),
            ({"input": "summary/es"}, "summary/embedding/es"),
        ):
            options = embed.EmbedOptions.model_validate(overrides)
            self.assertEqual(embed.EmbedProcessor.output_key(options), key)

    def test_embeds_a_text_annotation_of_any_key(self) -> None:
        self.db.record_result(
            self.item, "summarize", "summary/es", ProcessingStatus.DONE, value="Resumen"
        )
        llm = StubLLM()
        processor = self.build(embed.EmbedProcessor, llm, input="summary/es")

        self.annotation(processor, "summary/embedding/es")

        self.assertEqual(llm.calls, [("embed", ["Resumen"], {"model": None})])


class ConsumerPluginTests(unittest.TestCase):
    def test_consumers_use_the_requested_llm(self) -> None:
        llm = StubLLM()
        for plugin, options, expected in (
            (summarize, {}, None),
            (tagger, {"llm": "b"}, "b"),
            (embed, {"llm": "a", "model": "e"}, "a"),
        ):
            with self.subTest(plugin=plugin.__name__):
                factory = Mock(return_value=llm)

                ((_, protocol, cls),) = plugin.__newstool_plugin__()
                processor = cls(
                    cls.options_model(**options),
                    Services(db=Mock(), fetcher=Mock(), llm_factory=factory),
                )

                self.assertIs(protocol, ProcessorType)
                self.assertIs(processor.llm, llm)
                factory.assert_called_once_with(expected)

    def test_consumers_cannot_be_built_without_an_llm(self) -> None:
        for plugin in (summarize, tagger, embed):
            with self.subTest(plugin=plugin.__name__):
                ((_, _, cls),) = plugin.__newstool_plugin__()
                with self.assertRaises(LLMUnavailableError):
                    cls(cls.options_model(), Services(db=Mock(), fetcher=Mock()))


class OllamaTests(unittest.TestCase):
    def test_uses_the_default_models_unless_overridden(self) -> None:
        client = Mock()
        client.generate.return_value = Mock(response="ok")
        client.embed.return_value = Mock(embeddings=[(1.0, 2.0)])
        options = ollama.Options(chat_model="chat", embed_model="embedder")
        with patch.object(ollama, "ollama_client", return_value=client):
            llm = ollama.OllamaLLM(options, Services(db=Mock(), fetcher=Mock()))

        self.assertEqual(llm.prompt("hi"), "ok")
        llm.prompt("hi", model="other", json_mode=True, context_length=8192)
        self.assertEqual(llm.embed(["text"]), [[1.0, 2.0]])

        self.assertEqual(
            [call.kwargs for call in client.generate.call_args_list],
            [
                {
                    "model": "chat",
                    "prompt": "hi",
                    "stream": False,
                    "format": None,
                    "options": None,
                },
                {
                    "model": "other",
                    "prompt": "hi",
                    "stream": False,
                    "format": "json",
                    "options": {"num_ctx": 8192},
                },
            ],
        )
        client.embed.assert_called_once_with(model="embedder", input=["text"])

    def test_registers_one_llm_class_named_ollama(self) -> None:
        ((name, protocol, cls),) = ollama.__newstool_plugin__()
        llm = cls(
            ollama.Options(chat_model="chat"), Services(db=Mock(), fetcher=Mock())
        )

        self.assertEqual((name, protocol, cls), ("ollama", LLMType, ollama.OllamaLLM))
        self.assertEqual(
            (llm.chat_model, llm.embed_model), ("chat", ollama.DEFAULT_EMBED_MODEL)
        )

    def test_api_key_is_not_shown(self) -> None:
        cfg = ollama.Options(api_key="secret")

        self.assertNotIn("secret", repr(cfg))


if __name__ == "__main__":
    unittest.main()
