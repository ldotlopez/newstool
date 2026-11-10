"""Cuts the article's markdown to its first characters: a fast, offline
stand-in for `summarize` in test workflows."""

import pydantic

from ..models import SourceItem
from ..processors import BaseProcessor, ProcessorOptions, ProcessorType
from . import PluginTypes


class TruncateOptions(ProcessorOptions):
    length: pydantic.PositiveInt = 200
    # `summarize`'s options, accepted and ignored so an entry can swap one
    # type for the other. Plain fields, not `UsesLLMOptions`: `llm` is not
    # checked against `llms`, so a test configuration needs none.
    llm: str | None = None
    model: str | None = None
    prompt: str | None = None
    source_prompts: dict[str, str] | None = None


class TruncateProcessor(BaseProcessor):
    name = "truncate"
    key = "summary"
    requires = "markdown"
    options_model = TruncateOptions
    options: TruncateOptions

    def process_item(self, item: SourceItem) -> str:
        markdown = self.require_annotation(item, "markdown")
        return markdown[: self.options.length]


def __newstool_plugin__() -> PluginTypes:
    return [(TruncateProcessor.name, ProcessorType, TruncateProcessor)]
