"""The `digest` applet (decision 0015) writes a Markdown digest of the
highlights of each of its sources with an LLM, from the `markdown` of the
items published in the last `lookback`. It emits one document per source on
its `digest` output, keyed `<source id>/<since>_<until>` (YYYY-MM-DD), so a
second run over the same period emits nothing new. Schedule it (`on`,
`at`) for the period it covers."""

import logging
from datetime import datetime, timedelta
from typing import ClassVar

from ..applets import AppletReader, AppletType, BaseApplet, Outputs, SourcesOptions
from ..config import Duration
from ..errors import PluginFailure
from ..llms import strip_code_fence
from ..models import (
    AppletResult,
    AppletRun,
    EmittedDocument,
    SourceData,
    SourceItem,
)
from . import PluginTypes, Services, UsesLLMOptions

LOGGER = logging.getLogger(__name__)

OUTPUT = "digest"

DIGEST_PROMPT = """You are the editor of a weekly news digest. Below are the articles
a news source published in the period, numbered, each with its title, date, link
and text. Write the digest in Markdown, in the same language as the articles:

- Open with one paragraph that sums up the period.
- Then pick the 5 to 10 most relevant stories, merging the articles about the
  same story into one entry.
- Give each story a `##` heading and a paragraph of 2 to 4 sentences, followed
  by the links of its articles as Markdown links.
- Return only the digest: no title, preface or closing remarks.

Articles:

"""


class DigestOptions(SourcesOptions, UsesLLMOptions):
    model: str | None = None
    lookback: Duration = 7 * 86400  # the period each run covers
    max_items: int = 50  # newest items per source
    max_article_chars: int = 3000  # each article's markdown is cut to this
    context_length: int = 32768  # the model's context window, in tokens


class DigestApplet(BaseApplet):
    """Items without the `markdown` annotation are left out."""

    name = "digest"
    outputs: ClassVar[Outputs] = {OUTPUT: frozenset({"text/markdown"})}
    requires = ("markdown",)
    options_model = DigestOptions
    options: DigestOptions

    def __init__(self, options: DigestOptions, services: Services) -> None:
        super().__init__(options, services)
        self.llm = services.llm(options.llm)

    def run(self, now: datetime, run: AppletRun, reader: AppletReader) -> AppletResult:
        options = self.options
        since = now - timedelta(seconds=options.lookback)
        items = reader.items(
            sources=options.sources,
            published_since=since,
            published_until=now,
            newest_first=True,
        )
        markdowns = reader.annotations(items, "markdown")

        items_by_source: dict[str, list[SourceItem]] = {}
        for item in items:
            if item.key in markdowns:
                items_by_source.setdefault(item.source.id, []).append(item)
        if not items_by_source:
            LOGGER.info(f"{self.name}: no items with markdown in the period")

        documents = []
        for source_id, source_items in items_by_source.items():
            articles = [
                (item, str(markdowns[item.key]))
                for item in reversed(source_items[: options.max_items])
            ]
            source = source_items[0].source
            documents.append(
                EmittedDocument(
                    output=OUTPUT,
                    key=f"{source_id}/{since:%Y-%m-%d}_{now:%Y-%m-%d}",
                    content=self._write(source, articles, since, now),
                    content_type="text/markdown",
                    title=f"{source.name}: {since:%Y-%m-%d} – {now:%Y-%m-%d}",
                )
            )
        return AppletResult(documents=tuple(documents))

    def _write(
        self,
        source: SourceData,
        articles: list[tuple[SourceItem, str]],
        since: datetime,
        until: datetime,
    ) -> str:
        options = self.options
        prompt = DIGEST_PROMPT + "\n\n".join(
            self._article_text(number, item, markdown, options.max_article_chars)
            for number, (item, markdown) in enumerate(articles, start=1)
        )
        response = self.llm.prompt(
            prompt, model=options.model, context_length=options.context_length
        )
        body = strip_code_fence(response)
        if not body:
            raise PluginFailure(f"LLM returned an empty digest for '{source.id}'")

        return f"# {source.name}: {since:%Y-%m-%d} – {until:%Y-%m-%d}\n\n{body}\n"

    def _article_text(
        self, number: int, item: SourceItem, markdown: str, max_chars: int
    ) -> str:
        published = f"{item.published_at:%Y-%m-%d}" if item.published_at else "-"
        return (
            f"### {number}. {item.title}\n"
            f"Date: {published}\n"
            f"Link: {item.uri}\n\n"
            f"{markdown[:max_chars].strip()}"
        )


def __newstool_plugin__() -> PluginTypes:
    return [(DigestApplet.name, AppletType, DigestApplet)]
