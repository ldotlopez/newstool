"""Applets (decision 0015): plugin objects that decide when they run, read
what is stored, and return the documents they emit and their new state.
They have no side effects; the core stores what they return, and sinks
deliver the documents routed to them."""

from __future__ import annotations

import dataclasses
from abc import abstractmethod
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime, time, timedelta, tzinfo
from typing import Any, ClassVar, Protocol, runtime_checkable

import pydantic
from foundation.jsonlib import JsonCompatible

from .db import Database
from .errors import PluginFailure
from .models import (
    AppletResult,
    AppletRun,
    Document,
    DocumentFilter,
    ItemKey,
    ProcessingScope,
    SourceItem,
)
from .plugins import PluginOptions, Services

# An applet's outputs: each name with the content types it emits.
type Outputs = Mapping[str, frozenset[str]]

# Weekday names as `days` takes them, Monday first (`datetime.weekday()`).
WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
# How far ahead `Schedule.next_due` looks: past a week, every slot repeats.
SCHEDULE_HORIZON_DAYS = 8


@dataclasses.dataclass(frozen=True, slots=True)
class Schedule:
    """When an instance is due: `every` seconds after its last success, on
    the weekdays in `days` (Monday is 0; empty: every day), once a day from
    `at` local time when set. `tz` is the time zone of `at` and `days`; None
    is the system's."""

    every: float = 0
    at: time | None = None
    days: frozenset[int] = frozenset()
    tz: tzinfo | None = None

    def is_due(self, now: datetime, last_success: datetime | None) -> bool:
        if last_success is not None and now < last_success + timedelta(
            seconds=self.every
        ):
            return False
        local = now.astimezone(self.tz)
        if self.days and local.weekday() not in self.days:
            return False
        if self.at is not None:
            slot = local.replace(
                hour=self.at.hour, minute=self.at.minute, second=0, microsecond=0
            )
            if local < slot:
                return False
            if last_success is not None and last_success >= slot:
                return False
        return True

    def next_due(self, now: datetime, last_success: datetime | None) -> datetime:
        """The first moment from `now` when the instance is due. Due-ness
        changes only at these candidates: `last_success + every`, and each
        day's start and `at`."""
        if self.is_due(now, last_success):
            return now
        local = now.astimezone(self.tz)
        candidates = []
        if last_success is not None:
            candidates.append(last_success + timedelta(seconds=self.every))
        for days in range(SCHEDULE_HORIZON_DAYS):
            day = (local + timedelta(days=days)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            candidates.append(day)
            if self.at is not None:
                candidates.append(day.replace(hour=self.at.hour, minute=self.at.minute))
        for candidate in sorted(candidates):
            if candidate > now and self.is_due(candidate, last_success):
                return candidate
        raise ValueError("the schedule is never due")


@dataclasses.dataclass(frozen=True, slots=True)
class Requirements:
    """What an instance's runs read: its sources (None: every source) and the
    annotation keys, checked against the configuration at startup."""

    sources: tuple[str, ...] | None = None
    keys: tuple[str, ...] = ()


class AppletReader:
    """What an applet may read: items, their annotations and contents, and
    the documents of any instance. Not another instance's state."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def items(
        self,
        *,
        sources: Iterable[str] | None = None,
        published_since: datetime | None = None,
        published_until: datetime | None = None,
        imported_since: datetime | None = None,
        imported_until: datetime | None = None,
        limit: int | None = None,
        newest_first: bool = False,
    ) -> list[SourceItem]:
        """Items by publication date, oldest first unless `newest_first`,
        without their content. Since bounds are `>=`, until bounds `<`."""
        scope = ProcessingScope(
            sources=tuple(sources) if sources is not None else None,
            since=published_since,
            until=published_until,
            imported_since=imported_since,
            imported_until=imported_until,
            limit=limit,
        )
        return self._db.get_items(scope, newest_first=newest_first)

    def annotations(
        self, items: Iterable[SourceItem], key: str
    ) -> dict[ItemKey, JsonCompatible]:
        """The annotation `key` of each item, by item key; items without it
        are absent."""
        return self._db.get_annotation_values(items, key=key)

    def content(self, item: SourceItem) -> bytes:
        return self._db.get_content(item)

    def documents(
        self,
        *,
        app: str | None = None,
        output: str | None = None,
        emitted_since: datetime | None = None,
        emitted_until: datetime | None = None,
        limit: int | None = None,
        newest_first: bool = False,
    ) -> list[Document]:
        """Stored documents with their content, oldest first unless
        `newest_first`."""
        selection = DocumentFilter(
            app=app,
            output=output,
            since=emitted_since,
            until=emitted_until,
            limit=limit,
        )
        return self._db.find_documents(
            selection, newest_first=newest_first, with_content=True
        )


@runtime_checkable
class Applet(Protocol):
    """Decides whether it is due, and runs: returns its new state and the
    documents it emits. It never writes anything itself."""

    def is_due(self, now: datetime, run: AppletRun, schedule: Schedule) -> bool: ...

    def run(
        self, now: datetime, run: AppletRun, reader: AppletReader
    ) -> AppletResult: ...


@runtime_checkable
class AppletType(Protocol):
    """An Applet class, as plugins register it: each configured instance
    builds one with its options, validated at startup with
    `options_model`. `outputs` maps each output name to the content types
    it emits."""

    options_model: type[pydantic.BaseModel]
    outputs: Outputs

    def __call__(self, options: Any, services: Services) -> Applet: ...

    def requirements(self, options: Any) -> Requirements:
        """The sources and annotation keys a run with `options` reads."""
        ...


class SourcesOptions(PluginOptions):
    """Options of an applet that reads items: its sources, or every source
    when unset."""

    sources: list[str] | None = None


class BaseApplet:
    """An applet that is due by its instance's schedule and reads the items
    of `options.sources`; `requires` names the annotation keys it reads.
    Subclasses declare `name`, `outputs` and `options_model`, and implement
    `run`."""

    name: str
    outputs: ClassVar[Outputs]
    options_model: type[pydantic.BaseModel] = SourcesOptions
    requires: tuple[str, ...] = ()

    def __init__(self, options: Any, services: Services) -> None:
        self.options = options
        self.services = services

    @classmethod
    def requirements(cls, options: Any) -> Requirements:
        sources = getattr(options, "sources", None)
        return Requirements(
            sources=tuple(sources) if sources is not None else None,
            keys=cls.requires,
        )

    def is_due(self, now: datetime, run: AppletRun, schedule: Schedule) -> bool:
        return schedule.is_due(now, run.last_success)

    @abstractmethod
    def run(
        self, now: datetime, run: AppletRun, reader: AppletReader
    ) -> AppletResult: ...


def run_key(now: datetime) -> str:
    """The key of a document regenerated on every run: the run's UTC time."""
    return f"{now.astimezone(UTC):%Y-%m-%dT%H:%M:%SZ}"


def check_result(result: AppletResult, outputs: Outputs) -> None:
    """Fail a run that emits on an undeclared output, with an undeclared
    content type, or twice under one key."""
    seen: set[tuple[str, str]] = set()
    for document in result.documents:
        if (types := outputs.get(document.output)) is None:
            raise PluginFailure(f"emitted on undeclared output '{document.output}'")
        if document.content_type not in types:
            raise PluginFailure(
                f"emitted {document.content_type} on output '{document.output}',"
                f" which declares {', '.join(sorted(types))}"
            )
        if (document.output, document.key) in seen:
            raise PluginFailure(
                f"emitted key '{document.key}' twice on output '{document.output}'"
            )
        seen.add((document.output, document.key))
