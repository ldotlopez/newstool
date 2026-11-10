"""The `itemfeed` applet (decision 0015) emits one document per newly
imported item that has its `annotation` (the summary, by default): the
annotation is the text, with the item's title, link and image. Routed to a
chat sink, it posts each summarized item once.

Its state is a cursor, the time of its last run. With `since_first_run`,
its first run only sets the cursor and records its time as `start`, so the
items stored before it are never emitted. An item without the annotation
yet is looked at again on later runs while it was imported less than `wait`
ago, but never if it was imported before `start`.

A run emits its documents oldest item first: by publication time, or import
time for an item without one, then by database id. Sinks deliver documents
in the order they were emitted, so a chat gets them in that order too.
"""

from datetime import UTC, datetime, timedelta
from typing import ClassVar

from ..applets import (
    AppletReader,
    AppletType,
    BaseApplet,
    Outputs,
    Requirements,
    SourcesOptions,
)
from ..config import Duration
from ..models import AppletResult, AppletRun, EmittedDocument, SourceItem
from . import PluginTypes

OUTPUT = "items"


class ItemFeedOptions(SourcesOptions):
    annotation: str = "summary"  # the annotation key emitted as the text
    since_first_run: bool = True  # the first run emits nothing
    wait: Duration = 86400  # how long an item may wait for its annotation


class ItemFeedApplet(BaseApplet):
    name = "itemfeed"
    outputs: ClassVar[Outputs] = {OUTPUT: frozenset({"text/plain"})}
    options_model = ItemFeedOptions
    options: ItemFeedOptions

    @classmethod
    def requirements(cls, options: ItemFeedOptions) -> Requirements:
        sources = tuple(options.sources) if options.sources is not None else None
        return Requirements(sources=sources, keys=(options.annotation,))

    def run(self, now: datetime, run: AppletRun, reader: AppletReader) -> AppletResult:
        options = self.options
        state = run.state if isinstance(run.state, dict) else {}
        cursor = state.get("cursor")
        start = state.get("start")
        if cursor is None and options.since_first_run:
            return AppletResult(
                state={"cursor": now.isoformat(), "start": now.isoformat()}
            )

        items = reader.items(
            sources=options.sources,
            imported_since=self.since(cursor, start),
            imported_until=now,
        )
        texts = reader.annotations(items, options.annotation)
        documents = tuple(
            self.document(item, str(texts[item.key]))
            for item in sorted(items, key=self.age)
            if item.key in texts
        )
        new_state: dict[str, str] = {"cursor": now.isoformat()}
        if start is not None:
            new_state["start"] = start
        return AppletResult(state=new_state, documents=documents)

    def since(self, cursor: str | None, start: str | None) -> datetime | None:
        """The earliest import time to read: `wait` before the cursor, but
        never before `start`; None, everything."""
        if cursor is None:
            return None
        since = datetime.fromisoformat(cursor) - timedelta(seconds=self.options.wait)
        if start is not None:
            since = max(since, datetime.fromisoformat(start))
        return since

    @staticmethod
    def age(item: SourceItem) -> tuple[datetime, int]:
        """The emission order: publication time, or import time without
        one, then database id."""
        when = item.published_at or item.imported_at or datetime.min.replace(tzinfo=UTC)
        return (when, item.id or 0)

    @staticmethod
    def document(item: SourceItem, text: str) -> EmittedDocument:
        image = item.data.get("image") if isinstance(item.data, dict) else None
        return EmittedDocument(
            output=OUTPUT,
            key=f"item:{item.source.id}/{item.uid}",
            content=text,
            content_type="text/plain",
            title=item.title,
            url=item.uri,
            image_url=image if isinstance(image, str) and image.strip() else None,
        )


def __newstool_plugin__() -> PluginTypes:
    return [(ItemFeedApplet.name, AppletType, ItemFeedApplet)]
