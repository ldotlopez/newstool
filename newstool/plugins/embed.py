"""Embeds the item's tags or markdown with an LLM, for the `embeddings`
grouping applet."""

from typing import Literal

from ..models import SourceItem
from ..processors import BaseProcessor, ProcessorOptions, ProcessorType
from . import PluginTypes, Services, UsesLLMOptions


class EmbedOptions(ProcessorOptions, UsesLLMOptions):
    input: Literal["tags", "markdown"] = "tags"  # the annotation embedded
    model: str | None = None


class EmbedProcessor(BaseProcessor):
    """Annotates `<input>_embedding`: the embedding of the `tags` (as
    `tags_text`) or the `markdown` annotation, as the run's `input` option
    says (default `tags`)."""

    name = "embed"
    key = "tags_embedding"
    options_model = EmbedOptions
    options: EmbedOptions

    def __init__(self, options: EmbedOptions, services: Services) -> None:
        super().__init__(options, services)
        self.llm = services.llm(options.llm)

    @classmethod
    def output_key(cls, options: EmbedOptions) -> str:
        return f"{options.input}_embedding"

    @classmethod
    def required_key(cls, options: EmbedOptions) -> str | None:
        return options.input

    def process_item(self, item: SourceItem) -> list[float]:
        value = self.require_annotation(item, self.options.input)
        text = tags_text(value) if self.options.input == "tags" else value
        return self.llm.embed([text], model=self.options.model)[0]


def tags_text(tags: list[str]) -> str:
    """The text embedded for an item's tags: sorted and comma-separated."""
    return ", ".join(sorted(tags, key=str.lower))


def __newstool_plugin__() -> PluginTypes:
    return [(EmbedProcessor.name, ProcessorType, EmbedProcessor)]
