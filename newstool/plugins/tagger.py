"""Extracts entity tags from the article's markdown with an LLM, merged with
the tags the item came with."""

import json
import logging

import pydantic

from ..errors import PluginFailure
from ..llms import strip_code_fence
from ..models import SourceItem
from ..processors import (
    BaseProcessor,
    ProcessorOptions,
    ProcessorType,
    publisher_tags,
)
from . import PluginTypes, Services, UsesLLMOptions

LOGGER = logging.getLogger(__name__)

ResponseBaseModel = pydantic.RootModel[list[str]]

RESPONSE_JSON_SCHEMA = json.dumps(ResponseBaseModel.model_json_schema())


TAGS_PROMPT = f"""
You are an expert entity extraction and content tagging assistant. Your sole task is to analyze the provided text and extract relevant tags.

### Extraction Rules:

1.  **Tag Volume:** Extract between 3 and 10 tags maximum. Choose the most significant ones if the text is long.

2.  **Tag Categories:** Extract categories, locations, people, organizations, institutions, concepts, and themes.

3.  **Explicit Tags:** If the text explicitly mentions existing tags or keywords, prioritize and include them.

4.  **Language Matching:** Generate the tags in the exact same language as the source text.


### Output Formatting (Strict Constraint):

*   Return the output **ONLY** as a valid JSON array of strings.

*   Do **NOT** include any conversational filler, prefaces, introductions, or footnotes.

*   Do **NOT** wrap the JSON in markdown code blocks unless specifically requested. Output nothing but the raw JSON structure.

*  Respond with JSON matching this exact schema: {RESPONSE_JSON_SCHEMA}

### Example Output Format:

{{"items": ["Category", "Topic", "Persona Name", "Location Name", "Organization"]}}

"""

PUBLISHER_TAGS_PROMPT = """### Publisher's Tags:

The publisher tagged the article with: {tags}. Reuse their spelling for the
tags that apply.

"""

INPUT_PROMPT = """### Input Text:

"""


class TaggerOptions(ProcessorOptions, UsesLLMOptions):
    model: str | None = None


class TaggerProcessor(BaseProcessor):
    name = "tagger"
    key = "tags"
    requires = "markdown"
    options_model = TaggerOptions
    options: TaggerOptions

    def __init__(self, options: TaggerOptions, services: Services) -> None:
        super().__init__(options, services)
        self.llm = services.llm(options.llm)

    def process_item(self, item: SourceItem) -> list[str]:
        markdown = self.require_annotation(item, "markdown")
        item_tags = publisher_tags(item)

        response = self.llm.prompt(
            tags_prompt(markdown, item_tags), model=self.options.model, json_mode=True
        )

        try:
            parsed = json.loads(strip_code_fence(response))
            llm_tags = ResponseBaseModel(parsed["items"]).root
        except (
            pydantic.ValidationError,
            KeyError,
            TypeError,
            json.JSONDecodeError,
        ) as e:
            raise PluginFailure(f"invalid tags response {response!r}: {e}") from e

        tags = merge_tags(llm_tags, item_tags)
        LOGGER.debug(f"Tags for {item.title}: {tags!r}")
        return tags


def tags_prompt(markdown: str, item_tags: list[str]) -> str:
    """The prompt for `markdown`, with the publisher's tags when there are any."""
    hint = PUBLISHER_TAGS_PROMPT.format(tags=", ".join(item_tags)) if item_tags else ""
    return TAGS_PROMPT + hint + INPUT_PROMPT + markdown


def merge_tags(existing_tags: list[str], new_tags: list[str]) -> list[str]:
    """Merge two tag lists case-insensitively, keeping the first spelling and order."""
    merged: dict[str, str] = {}
    for tag in existing_tags + new_tags:
        merged.setdefault(tag.lower(), tag)
    return list(merged.values())


def __newstool_plugin__() -> PluginTypes:
    return [(TaggerProcessor.name, ProcessorType, TaggerProcessor)]
