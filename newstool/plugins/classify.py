"""Labels the article's markdown with an LLM, from a closed list of labels
(topics, or the answers to a question such as "is it about Spain?"). The
publisher's tags go in the prompt as hints."""

import json

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

DEFAULT_QUESTION = "Which of these topics does the article cover?"

CLASSIFY_PROMPT = """{question}

Labels: {labels}

Answer only with the labels that apply, spelled as listed, as a JSON object:
{{"labels": ["label", ...]}}. Use an empty list when none applies.
{hints}
Article:

"""


class ClassifyOptions(ProcessorOptions, UsesLLMOptions):
    labels: list[str]
    question: str = DEFAULT_QUESTION
    model: str | None = None


class ClassifyProcessor(BaseProcessor):
    """Annotates the labels of `labels` the LLM picks; any other answer is
    left out."""

    name = "classify"
    key = "topics"
    requires = "markdown"
    options_model = ClassifyOptions
    options: ClassifyOptions

    def __init__(self, options: ClassifyOptions, services: Services) -> None:
        super().__init__(options, services)
        self.llm = services.llm(options.llm)

    def process_item(self, item: SourceItem) -> list[str]:
        markdown = self.require_annotation(item, "markdown")
        prompt = classify_prompt(self.options, publisher_tags(item)) + markdown

        response = self.llm.prompt(prompt, model=self.options.model, json_mode=True)

        try:
            answer = pydantic.TypeAdapter(list[str]).validate_python(
                json.loads(strip_code_fence(response))["labels"]
            )
        except (
            pydantic.ValidationError,
            KeyError,
            TypeError,
            json.JSONDecodeError,
        ) as e:
            raise PluginFailure(f"invalid labels response {response!r}: {e}") from e
        return known_labels(answer, self.options.labels)


def classify_prompt(options: ClassifyOptions, item_tags: list[str]) -> str:
    hints = (
        f"\nThe publisher tagged the article with: {', '.join(item_tags)}.\n"
        if item_tags
        else ""
    )
    return CLASSIFY_PROMPT.format(
        question=options.question, labels=", ".join(options.labels), hints=hints
    )


def known_labels(answer: list[str], labels: list[str]) -> list[str]:
    """The answered labels found in `labels` (ignoring case), in their
    configured spelling and order."""
    answered = {label.strip().lower() for label in answer}
    return [label for label in labels if label.lower() in answered]


def __newstool_plugin__() -> PluginTypes:
    return [(ClassifyProcessor.name, ProcessorType, ClassifyProcessor)]
