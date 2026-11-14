"""The `feed` applet (decision 0015) builds an RSS feed of the newest items
of its sources, newest first, capped at `max_items`. Every run emits it
anew on its `feed` output, keyed by the run's time; a `file` sink
publishes it.
"""

from datetime import UTC, datetime
from typing import ClassVar
from xml.sax.saxutils import escape

from ..applets import (
    AppletReader,
    AppletType,
    BaseApplet,
    Outputs,
    run_key,
)
from ..models import AppletResult, AppletRun, EmittedDocument, SourceItem
from . import PluginOptions, PluginTypes

RFC822 = "%a, %d %b %Y %H:%M:%S %z"
OUTPUT = "feed"
CONTENT_TYPE = "application/rss+xml"


class Options(PluginOptions):
    title: str = "newstool feed"
    link: str | None = None
    description: str | None = None  # the title when unset
    max_items: int = 100


class FeedApplet(BaseApplet):
    name = "feed"
    outputs: ClassVar[Outputs] = {OUTPUT: frozenset({CONTENT_TYPE})}
    options_model = Options
    options: Options

    def run(self, now: datetime, run: AppletRun, reader: AppletReader) -> AppletResult:
        items = reader.items(limit=self.options.max_items, newest_first=True)
        document = EmittedDocument(
            output=OUTPUT,
            key=run_key(now),
            content=self._build_feed(items, now),
            content_type=CONTENT_TYPE,
            title=self.options.title,
        )
        return AppletResult(documents=(document,))

    def _build_feed(self, items: list[SourceItem], now: datetime) -> str:
        options = self.options
        entries = "\n".join(self._build_entry(item) for item in items)
        description = options.description or options.title
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<rss version="2.0"><channel>\n'
            f"<title>{escape(options.title)}</title>\n"
            + (f"<link>{escape(options.link)}</link>\n" if options.link else "")
            + f"<description>{escape(description)}</description>\n"
            + f"<lastBuildDate>{now.astimezone(UTC).strftime(RFC822)}</lastBuildDate>\n"
            + f"{entries}\n"
            + "</channel></rss>\n"
        )

    def _build_entry(self, item: SourceItem) -> str:
        pub_date = ""
        if item.published_at is not None:
            pub_date = f"<pubDate>{item.published_at.astimezone(UTC).strftime(RFC822)}</pubDate>\n"

        return (
            "<item>\n"
            f"<title>{escape(item.title)}</title>\n"
            f"<link>{escape(item.uri)}</link>\n"
            f'<guid isPermaLink="false">{escape(item.source.id)}/{escape(item.uid)}</guid>\n'
            f"{pub_date}"
            "</item>"
        )


def __newstool_plugin__() -> PluginTypes:
    return [(FeedApplet.name, AppletType, FeedApplet)]
