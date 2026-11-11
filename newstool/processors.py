from __future__ import annotations

import dataclasses
import logging
import time
from abc import abstractmethod
from typing import Any, Protocol, runtime_checkable

import pydantic

from .db import ProcessingStatus
from .errors import PluginFailure, log_failure, reason
from .models import ProcessingScope, SourceItem
from .plugins import PluginOptions, Services

LOGGER = logging.getLogger(__name__)


class SkipItem(Exception):
    """Raise from `process_item` when the item doesn't apply to this processor
    (e.g. wrong language). Recorded as `ignored`: permanent for the item's
    current content, revisited only if it changes or the run is forced."""


@dataclasses.dataclass(slots=True)
class RunSummary:
    done: int = 0
    ignored: int = 0
    failed: int = 0


@runtime_checkable
class Processor(Protocol):
    """Annotates items. Each run writes one annotation key, which also keys
    its processing state."""

    def process(
        self,
        *,
        key: str,
        scope: ProcessingScope | None = None,
        force: bool = False,
    ) -> RunSummary: ...


@runtime_checkable
class ProcessorType(Protocol):
    """A Processor class, as plugins register it: each configured use builds
    one with its options, validated at startup with `options_model`."""

    options_model: type[pydantic.BaseModel]

    def __call__(self, options: Any, services: Services) -> Processor: ...

    def output_key(self, options: Any) -> str:
        """The key a run with `options` writes unless its entry names one."""
        ...

    def required_key(self, options: Any) -> str | None:
        """The key a run with `options` reads, if any."""
        ...


class ProcessorOptions(PluginOptions):
    """Options every processor takes."""

    max_retries: int = 3


class BaseProcessor:
    """A Processor that produces one annotation for each eligible item.

    `key` is the annotation it writes by default. Changing `version` makes
    items it finished eligible again. `requires` names the annotation key
    this one reads: only items whose run of it finished on their current
    content are picked up. `options_model` declares its options.
    """

    name: str
    key: str
    version: str | None = None
    requires: str | None = None
    options_model: type[ProcessorOptions] = ProcessorOptions

    def __init__(self, options: ProcessorOptions, services: Services) -> None:
        self.options = options
        self.db = services.db

    @classmethod
    def output_key(cls, options: Any) -> str:
        return cls.key

    @classmethod
    def required_key(cls, options: Any) -> str | None:
        return cls.requires

    def process(
        self,
        *,
        key: str,
        scope: ProcessingScope | None = None,
        force: bool = False,
    ) -> RunSummary:
        requires = self.required_key(self.options)
        items = self.db.get_unprocessed_items(
            key,
            version=self.version,
            max_retries=self.options.max_retries,
            force=force,
            scope=scope,
            requires=requires,
        )
        total = len(items)
        LOGGER.info(
            f"{key}: {total} item(s) to process with {self.name}"
            f" (version={self.version}, requires={requires}, force={force})"
        )

        summary = RunSummary()
        run_started = time.monotonic()
        for position, item in enumerate(items, start=1):
            LOGGER.info(f"{key}: [{position}/{total}] '{item.title}' ({item.uri})")
            item_started = time.monotonic()
            status, value, error = self._run_item(item)
            LOGGER.debug(
                f"{key}: '{item.uri}' {status.value}"
                f" in {time.monotonic() - item_started:.2f}s"
            )
            self.db.record_result(
                item,
                self.name,
                key,
                status,
                value=value,
                error=error,
                version=self.version,
                reset_attempts=force,
            )
            match status:
                case ProcessingStatus.DONE:
                    summary.done += 1
                case ProcessingStatus.IGNORED:
                    summary.ignored += 1
                case ProcessingStatus.ERROR:
                    summary.failed += 1

        LOGGER.info(
            f"{key}: finished in {time.monotonic() - run_started:.1f}s:"
            f" {summary.done} done, {summary.ignored} ignored, {summary.failed} failed"
        )
        return summary

    def _run_item(self, item: SourceItem) -> tuple[ProcessingStatus, Any, str | None]:
        """Run `process_item` and translate its outcome into a result."""
        try:
            return ProcessingStatus.DONE, self.process_item(item), None
        except SkipItem as e:
            LOGGER.info(f"{self.name} ignored '{item.uri}': {e}")
            return ProcessingStatus.IGNORED, None, None
        except Exception as e:  # noqa: BLE001
            log_failure(LOGGER, f"{self.name} failed on '{item.uri}'", e)
            return ProcessingStatus.ERROR, None, reason(e)

    def require_annotation(self, item: SourceItem, key: str) -> Any:
        """Return an upstream annotation, or raise if it is missing."""
        value = self.db.get_annotations(item, key=key).get(key)
        if not value:
            raise PluginFailure(f"{key} annotation is missing")
        return value

    @abstractmethod
    def process_item(self, item: SourceItem) -> Any:
        """Return the annotation's value.

        Raise `SkipItem` if the item doesn't apply. Any other exception marks
        the item `error`.
        """


def publisher_tags(item: SourceItem) -> list[str]:
    """The tags the item came with from its source (`data["tags"]`)."""
    tags = item.data.get("tags", [])
    if not isinstance(tags, list):
        return []
    return [tag for tag in tags if isinstance(tag, str)]


def embedding_key(input_key: str) -> str:
    """The key `embed` writes for `input_key`: `embedding` after its first
    part (`tags/embedding`, `summary/embedding/es`)."""
    first, _, rest = input_key.partition("/")
    return f"{first}/embedding/{rest}" if rest else f"{first}/embedding"
