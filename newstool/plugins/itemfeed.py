"""The `itemfeed` applet (decision 0015) emits one document per newly
imported item that has its `annotation` (the summary, by default): the
annotation is the text, with the item's title, link and image. Routed to a
chat sink, it posts each summarized item once.

Its state is a cursor, the time of its last run. With `since_first_run`,
its first run only sets the cursor, so the items stored before it are not
emitted. An item without the annotation yet is looked at again on later
runs while it was imported less than `wait` ago.
"""

from datetime import datetime, timedelta
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
        if cursor is None and options.since_first_run:
            return AppletResult(state={"cursor": now.isoformat()})

        since = (
            datetime.fromisoformat(cursor) - timedelta(seconds=options.wait)
            if cursor is not None
            else None
        )
        items = reader.items(
            sources=options.sources, imported_since=since, imported_until=now
        )
        texts = reader.annotations(items, options.annotation)
        documents = tuple(
            self.document(item, str(texts[item.key]))
            for item in items
            if item.key in texts
        )
        return AppletResult(state={"cursor": now.isoformat()}, documents=documents)

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
