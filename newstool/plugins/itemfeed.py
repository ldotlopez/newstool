"""The `itemfeed` applet (decision 0015) emits one document per newly
imported item that has its `annotation` (the summary, by default): the
annotation is the text, with the item's title, link and image. Routed to a
chat sink, it posts each summarized item once.

Its state is a cursor, the time of its last run, and `start`: its first
run's time minus `backfill`. Nothing imported before `start` is ever
emitted, so with the default `backfill` of 0 the first run emits nothing
and only starts counting; `backfill: 1d` emits the last day's items on the
first run; `backfill: all` has no `start` and emits the whole history. An
item without the annotation yet is looked at again on later runs while it
was imported less than `wait` ago.

A run emits its documents oldest item first: by publication time, or import
time for an item without one, then by database id. Sinks deliver documents
in the order they were emitted, so a chat gets them in that order too.
"""

from datetime import UTC, datetime, timedelta
from typing import ClassVar, Literal

from ..applets import (
    AppletReader,
    AppletType,
    BaseApplet,
    Outputs,
)
from ..config import Duration
from ..models import AppletResult, AppletRun, EmittedDocument, SourceItem
from . import PluginOptions, PluginTypes

OUTPUT = "items"


class ItemFeedOptions(PluginOptions):
    annotation: str = "summary"  # the annotation key emitted as the text
    # How far before the first run to start: 0, nothing stored before it;
    # `all`, the whole history.
    backfill: Literal["all"] | Duration = 0
    wait: Duration = 86400  # how long an item may wait for its annotation


class ItemFeedApplet(BaseApplet):
    name = "itemfeed"
    outputs: ClassVar[Outputs] = {OUTPUT: frozenset({"text/plain"})}
    options_model = ItemFeedOptions
    options: ItemFeedOptions

    @classmethod
    def required_keys(cls, options: ItemFeedOptions) -> tuple[str, ...]:
        return (options.annotation,)

    def run(self, now: datetime, run: AppletRun, reader: AppletReader) -> AppletResult:
        options = self.options
        state = run.state if isinstance(run.state, dict) else {}
        cursor = state.get("cursor")
        start = state.get("start")
        if cursor is None:
            start = self.first_start(now)

        items = reader.items(
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

    def first_start(self, now: datetime) -> str | None:
        """`start` for a first run at `now`: `backfill` before it; None with
        `backfill: all`."""
        if self.options.backfill == "all":
            return None
        return (now - timedelta(seconds=self.options.backfill)).isoformat()

    def since(self, cursor: str | None, start: str | None) -> datetime | None:
        """The earliest import time to read: `wait` before the cursor (on a
        first run, none), but never before `start`; None, everything."""
        bounds = []
        if cursor is not None:
            wait = timedelta(seconds=self.options.wait)
            bounds.append(datetime.fromisoformat(cursor) - wait)
        if start is not None:
            bounds.append(datetime.fromisoformat(start))
        return max(bounds) if bounds else None

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
