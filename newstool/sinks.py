"""Sinks act on the outside world: each instance sends the documents routed
to it, and every delivery is recorded in the ledger, which is never
regenerated (decision 0015)."""

from __future__ import annotations

import dataclasses
import logging
import time
from collections.abc import Collection
from datetime import datetime, timedelta
from typing import Any, Protocol, runtime_checkable

import pydantic
from foundation.jsonlib import JsonCompatible

from .config import Duration
from .db import Database, DeliveryStatus, backoff_seconds
from .errors import log_failure, reason
from .models import Delivery, Document
from .plugins import PluginOptions, Services
from .processors import RunSummary

LOGGER = logging.getLogger(__name__)

# In `accepts`: every content type.
ANY_CONTENT_TYPE = "*/*"


class SinkOptions(PluginOptions):
    """Options every sink takes: its pacing and retries."""

    # Time between the instance's deliveries, oldest document first; 0: no
    # pacing.
    interval: Duration = 0
    # Deliveries per run at most, against flooding.
    max_per_run: pydantic.PositiveInt = 5
    max_retries: int = 3


@runtime_checkable
class Sink(Protocol):
    """Sends one document; returns its external reference. Raise on failure;
    the error is logged with its traceback, so it must not chain an exception
    that holds a secret (raise it `from None`)."""

    def send(self, document: Document) -> JsonCompatible: ...


@runtime_checkable
class SinkType(Protocol):
    """A Sink class, as plugins register it: each configured instance builds
    one with its options, validated at startup with `options_model`.
    `accepts` lists the content types it renders (`*/*`: any)."""

    options_model: type[pydantic.BaseModel]
    accepts: frozenset[str]

    def __call__(self, options: Any, services: Services) -> Sink: ...


@dataclasses.dataclass(frozen=True, slots=True)
class PacingOverride:
    """Pacing set for one delivery run, over the sink instance's options,
    one flag per option: `ignore_interval` drops the interval (its wait and
    its one row per run), so `max_per_run` alone limits the run;
    `ignore_max_per_run` drops that limit, and `max_per_run` replaces it."""

    ignore_interval: bool = False
    ignore_max_per_run: bool = False
    max_per_run: int | None = None

    def __post_init__(self) -> None:
        if self.max_per_run is not None and self.max_per_run < 1:
            raise ValueError("max_per_run must be at least 1")
        if self.ignore_max_per_run and self.max_per_run is not None:
            raise ValueError("ignore_max_per_run takes no max_per_run")


def accepts(sink_type: SinkType, content_types: Collection[str]) -> bool:
    """Whether the sink type renders every one of `content_types`."""
    return ANY_CONTENT_TYPE in sink_type.accepts or set(content_types) <= set(
        sink_type.accepts
    )


class Deliverer:
    """The delivery cycle of one sink instance over its ledger rows:

    1. the pending rows (queued, or failed with attempts left and their
       backoff elapsed), oldest document first;
    2. paced: one per `interval` since the instance's last delivery, at most
       `max_per_run`;
    3. each row is marked `sending`, sent, then `done` with the external
       reference, or `error`.

    Rows left `sending` by an interrupted run are never retried.
    """

    def __init__(
        self,
        db: Database,
        sink_id: str,
        sink: Sink,
        options: SinkOptions,
        pacing: PacingOverride | None = None,
    ) -> None:
        self.db = db
        self.sink_id = sink_id
        self.sink = sink
        self.options = options
        self.pacing = pacing or PacingOverride()

    def plan(self, now: datetime) -> list[tuple[Delivery, Document]]:
        """The rows a delivery run would send now."""
        rows = self.db.deliveries_of(
            self.sink_id,
            statuses=[
                DeliveryStatus.QUEUED,
                DeliveryStatus.ERROR,
                DeliveryStatus.SENDING,
            ],
        )
        if interrupted := sum(row.status == DeliveryStatus.SENDING for row, _ in rows):
            LOGGER.warning(
                f"{self.sink_id}: {interrupted} interrupted delivery(ies) stay"
                " `sending`; `deliveries set-status --status sending` settles them"
            )
        pending = [
            (delivery, document)
            for delivery, document in rows
            if self.is_due(delivery, now)
        ]
        return self.pace(pending, now)

    def deliver(self, now: datetime) -> RunSummary:
        """Send what `plan` selects."""
        return self.send_rows(self.plan(now))

    def is_due(self, delivery: Delivery, now: datetime) -> bool:
        """Queued rows are due; failed ones with attempts left, once their
        backoff has passed."""
        if delivery.status == DeliveryStatus.QUEUED:
            return True
        if delivery.status != DeliveryStatus.ERROR:
            return False
        if delivery.attempts >= self.options.max_retries:
            return False
        if delivery.updated_at is None:
            return True
        elapsed = (now - delivery.updated_at).total_seconds()
        return elapsed >= backoff_seconds(delivery.attempts)

    def pace(
        self, pending: list[tuple[Delivery, Document]], now: datetime
    ) -> list[tuple[Delivery, Document]]:
        """With an `interval`, the first pending row once the last delivery
        is that old; then at most `max_per_run` rows. `pacing` may drop
        either."""
        interval = 0 if self.pacing.ignore_interval else self.options.interval
        if interval:
            last = self.db.last_delivered_at(self.sink_id)
            if last is not None and now - last < timedelta(seconds=interval):
                return []
            pending = pending[:1]
        if self.pacing.ignore_max_per_run:
            return pending
        return pending[: self.pacing.max_per_run or self.options.max_per_run]

    def send_rows(self, rows: list[tuple[Delivery, Document]]) -> RunSummary:
        """Send these rows now, whatever their state."""
        LOGGER.info(f"{self.sink_id}: {len(rows)} to deliver")
        started = time.monotonic()
        summary = RunSummary()
        for delivery, document in rows:
            delivery.status = DeliveryStatus.SENDING
            self.db.save_delivery(delivery)
            try:
                document.content = self.db.load_document_content(document)
                external_ref = self.sink.send(document)
            except Exception as e:  # noqa: BLE001
                log_failure(
                    LOGGER, f"{self.sink_id}: could not deliver {document.label}", e
                )
                delivery.status = DeliveryStatus.ERROR
                delivery.attempts += 1
                delivery.last_error = reason(e)
                summary.failed += 1
            else:
                LOGGER.info(f"{self.sink_id}: delivered {document.label}")
                delivery.status = DeliveryStatus.DONE
                delivery.attempts = 0
                delivery.last_error = None
                delivery.external_ref = external_ref
                summary.done += 1
            self.db.save_delivery(delivery)
        LOGGER.info(
            f"{self.sink_id}: finished in {time.monotonic() - started:.1f}s:"
            f" {summary.done} delivered, {summary.failed} failed"
        )
        return summary
