"""Embeds one of the item's annotations with an LLM, for `digest`'s
`embeddings` grouping."""

from ..errors import PluginFailure
from ..models import SourceItem
from ..processors import (
    BaseProcessor,
    ProcessorOptions,
    ProcessorType,
    embedding_key,
)
from . import PluginTypes, Services, UsesLLMOptions


class EmbedOptions(ProcessorOptions, UsesLLMOptions):
    input: str = "tags"  # the annotation embedded
    model: str | None = None


class EmbedProcessor(BaseProcessor):
    """Annotates `embedding_key(input)` (`tags/embedding`,
    `summary/embedding/es`): the embedding of the `input` annotation
    (default `tags`), a list as `tags_text`, a string as it is."""

    name = "embed"
    key = "tags/embedding"
    options_model = EmbedOptions
    options: EmbedOptions

    def __init__(self, options: EmbedOptions, services: Services) -> None:
        super().__init__(options, services)
        self.llm = services.llm(options.llm)

    @classmethod
    def output_key(cls, options: EmbedOptions) -> str:
        return embedding_key(options.input)

    @classmethod
    def required_key(cls, options: EmbedOptions) -> str | None:
        return options.input

    def process_item(self, item: SourceItem) -> list[float]:
        value = self.require_annotation(item, self.options.input)
        match value:
            case list():
                text = tags_text(value)
            case str():
                text = value
            case _:
                raise PluginFailure(f"{self.options.input} is not text or a list")
        return self.llm.embed([text], model=self.options.model)[0]


def tags_text(tags: list[str]) -> str:
    """The text embedded for an item's tags: sorted and comma-separated."""
    return ", ".join(sorted(tags, key=str.lower))


def __newstool_plugin__() -> PluginTypes:
    return [(EmbedProcessor.name, ProcessorType, EmbedProcessor)]
