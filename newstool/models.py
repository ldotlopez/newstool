from __future__ import annotations

import dataclasses
import hashlib
from datetime import datetime
from typing import Self

from foundation.jsonlib import JsonCompatible
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

# (source id, uid): an item's identity. Each source is its own uid space.
type ItemKey = tuple[str, str]


class SourceData(BaseModel):
    """A configured source. `id` is its identity and must stay stable."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    name: str
    url: HttpUrl
    provider: str
    # Over the provider's `plugins` section, the options its provider is
    # built with. Config only, like `skip_default`: the database stores
    # neither.
    options: dict[str, JsonCompatible] = Field(default_factory=dict)
    # Left out of the `default` workflow; workflows that name it use it.
    skip_default: bool = False

    def __hash__(self) -> int:
        # The id is the identity (decision 0001), and the options are a dict.
        return hash(self.id)


class SourceItemData(BaseModel):
    """A provider's output for one item, validated at the scraping boundary.

    `uid` is derived by the provider; it only has to be deterministic and
    stable within its source.
    """

    uid: str
    title: str
    uri: str
    content: bytes
    mimetype: str
    data: JsonCompatible = {}
    published_at: datetime | None = None
    modified_at: datetime | None = None

    @model_validator(mode="after")
    def text_is_utf8(self) -> Self:
        # Text is always stored as UTF-8, so the mimetype carries no charset.
        if ";" in self.mimetype:
            raise ValueError(f"mimetype must not have parameters: {self.mimetype!r}")
        if self.mimetype.startswith("text/"):
            try:
                self.content.decode("utf-8")
            except UnicodeDecodeError as e:
                raise ValueError(f"{self.mimetype} content is not UTF-8") from e
        return self


@dataclasses.dataclass(frozen=True, slots=True)
class PreflightSourceItemData[T]:
    """An item as its source's index lists it, before fetching it."""

    uid: str
    ref: T  # what the plugin needs to fetch it; opaque to the core
    # As the index shows it, when it does: lets the core skip unchanged items.
    modified_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.modified_at is not None and self.modified_at.tzinfo is None:
            raise ValueError(
                f"modified_at must be timezone-aware: {self.modified_at!r}"
            )


@dataclasses.dataclass
class SourceItem:
    source: SourceData
    uid: str
    title: str
    uri: str
    # None when read back from the database: load it with Application.get_content().
    content: bytes | None = None
    mimetype: str = "application/octet-stream"
    content_sha256: str | None = None
    data: JsonCompatible = dataclasses.field(default_factory=dict)
    published_at: datetime | None = None
    modified_at: datetime | None = None
    # Set by the database on the item's first import, never changed.
    imported_at: datetime | None = None
    # The database id: None until saved. A local handle, not the identity.
    id: int | None = None

    def __post_init__(self) -> None:
        if self.content is not None:
            self.content_sha256 = hashlib.sha256(self.content).hexdigest()

    @classmethod
    def from_data(cls, source: SourceData, data: SourceItemData) -> SourceItem:
        return cls(source=source, **data.model_dump())

    @property
    def key(self) -> ItemKey:
        return (self.source.id, self.uid)

    def __hash__(self) -> int:
        return hash(self.key)


@dataclasses.dataclass(frozen=True, slots=True)
class EmittedDocument:
    """What an applet emits on one of its outputs (decision 0015). `key` is
    the applet's and deterministic, so emitting it again is ignored;
    `title`, `url` and `image_url` are for the sinks that use them."""

    output: str
    key: str
    content: str
    content_type: str
    title: str | None = None
    url: str | None = None
    image_url: str | None = None


@dataclasses.dataclass(slots=True)
class Document:
    """A stored emitted document, never rewritten: unique per (app, output,
    key), where `app` is the applet instance's id. `content` is None unless
    loaded; `emitted_at` is set by the database."""

    app: str
    output: str
    key: str
    content_type: str
    content: str | None = None
    content_sha256: str | None = None
    title: str | None = None
    url: str | None = None
    image_url: str | None = None
    emitted_at: datetime | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        if self.content is not None:
            self.content_sha256 = hashlib.sha256(self.content.encode()).hexdigest()

    @classmethod
    def from_emitted(cls, app: str, emitted: EmittedDocument) -> Document:
        return cls(
            app=app,
            output=emitted.output,
            key=emitted.key,
            content_type=emitted.content_type,
            content=emitted.content,
            title=emitted.title,
            url=emitted.url,
            image_url=emitted.image_url,
        )

    @property
    def label(self) -> str:
        """How logs and tables name it."""
        return f"{self.app}/{self.output}/{self.key}"


@dataclasses.dataclass(slots=True)
class Delivery:
    """A record of delivering one document to one sink instance (decision
    0015). `status` is a `db.DeliveryStatus`."""

    sink: str  # the sink instance's id
    document_id: int
    status: str
    attempts: int = 0
    last_error: str | None = None
    external_ref: JsonCompatible = None  # e.g. {"message_id": ...}
    created_at: datetime | None = None
    updated_at: datetime | None = None
    document_label: str | None = None  # "<app>/<output>/<key>", read back only
    id: int | None = None


@dataclasses.dataclass(slots=True)
class AppletRun:
    """An applet instance's run record: when it last started and succeeded,
    its last error, and its opaque state. Never run: all None."""

    app: str
    last_started: datetime | None = None
    last_success: datetime | None = None
    last_error: str | None = None
    state: JsonCompatible = None


@dataclasses.dataclass(frozen=True, slots=True)
class AppletResult:
    """What a successful applet run returns: its new state and what it
    emits."""

    state: JsonCompatible = None
    documents: tuple[EmittedDocument, ...] = ()


@dataclasses.dataclass(frozen=True, slots=True)
class DocumentFilter:
    """Which documents an operation applies to; unset fields do not
    restrict, and they combine. Times bound `emitted_at`."""

    app: str | None = None
    output: str | None = None
    key: str | None = None
    since: datetime | None = None  # emitted_at >=
    until: datetime | None = None  # emitted_at <
    document_ids: tuple[int, ...] | None = None
    limit: int | None = None

    def is_set(self) -> bool:
        """Whether it names anything but a limit."""
        return any(
            (
                self.app,
                self.output,
                self.key,
                self.since,
                self.until,
                self.document_ids,
            )
        )


@dataclasses.dataclass(slots=True)
class Annotation:
    """The run of one key on one item (decision 0018): the state of its last
    run and, once a run finished, its value. `status` is a
    `db.ProcessingStatus`; `processor` is the one that ran last."""

    item_id: int
    processor: str
    key: str
    status: str
    attempts: int = 0
    last_error: str | None = None
    processor_version: str | None = None
    value_sha256: str | None = None  # None until a run finished
    value: JsonCompatible = None  # loaded only by the reads that return values
    created_at: datetime | None = None
    attempted_at: datetime | None = None  # the last run; retries back off from it
    updated_at: datetime | None = None  # when the value last changed
    id: int | None = None


@dataclasses.dataclass(frozen=True, slots=True)
class ProcessingScope:
    """Which items an operation applies to. Every field is optional and they
    combine; an unset field means no restriction on that axis."""

    source: str | None = None  # source id
    sources: tuple[str, ...] | None = None  # source ids: a workflow's
    since: datetime | None = None  # published_at >=
    until: datetime | None = None  # published_at <
    imported_since: datetime | None = None  # imported_at >=
    imported_until: datetime | None = None  # imported_at <
    item_ids: tuple[int, ...] | None = None  # database ids
    limit: int | None = None
