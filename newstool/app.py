"""Application: the single entry point for front ends (CLI, scripts) and
external tools. It owns the wiring (config, HTTP cache, database, plugins),
runs the workflows' phases (import, process), the applets and the
deliveries, and answers queries.
"""

from __future__ import annotations

import dataclasses
import fcntl
import logging
from collections.abc import Iterable, Iterator
from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType
from typing import IO, Any, Self

from foundation.cache import UserCache
from foundation.jsonlib import JsonCompatible
from sqlalchemy import make_url

from .applets import AppletReader, check_result
from .catalog import AppInstance, Catalog, Profile
from .config import DEFAULT_WORKFLOW, Config, ConfigError, Workflow
from .consts import PACKAGE_NAME
from .db import Database, DeliveryStatus
from .errors import describe, log_failure, reason
from .httpclient import HTTPClient
from .llms import LLM
from .models import (
    Annotation,
    AppletRun,
    Delivery,
    Document,
    DocumentFilter,
    ItemKey,
    ProcessingScope,
    SourceData,
    SourceItem,
    SourceItemData,
)
from .plugins import ClassRegister, Services
from .processors import RunSummary
from .providers import PreflightProvider
from .sinks import Deliverer, PacingOverride, accepts

PLUGINS_NAMESPACE = "newstool.plugins"
PLUGIN_ENTRY_POINT = "__newstool_plugin__"

LOGGER = logging.getLogger(__name__)


# The `last_error` of a row created as `error`.
SET_BY_HAND = "set by hand"


class LockedError(RuntimeError):
    """Another newstool command holds the write lock."""


@dataclasses.dataclass(slots=True)
class MarkSummary:
    """What `mark_deliveries` did, or would do: rows created, existing rows
    changed, and existing rows left as they were."""

    created: int = 0
    changed: int = 0
    kept: int = 0


@dataclasses.dataclass(frozen=True, slots=True)
class DeleteSummary:
    """What `delete_documents` deleted, and the ids it refused."""

    deleted: int = 0
    refused: list[int] = dataclasses.field(default_factory=list)


@dataclasses.dataclass(frozen=True, slots=True)
class AppReport:
    """What a run of an applet instance did, or would do: whether it was
    due, its error, the `(output, key)` of the documents it emitted, new or
    already stored, and how many rows it queued for stored ones routed
    since they were emitted."""

    app: str
    due: bool
    error: str | None = None
    new: tuple[tuple[str, str], ...] = ()
    ignored: tuple[tuple[str, str], ...] = ()
    routed: int = 0
    state: JsonCompatible = None


@dataclasses.dataclass(frozen=True, slots=True)
class AppStatus:
    """An instance with its run record and when it is next due."""

    instance: AppInstance
    run: AppletRun
    next_due: datetime


class Application:
    def __init__(self, config: Config, *, create_schema: bool = True) -> None:
        self.config = config
        register = ClassRegister(PLUGINS_NAMESPACE, PLUGIN_ENTRY_POINT)
        register.register_found()
        self._catalog = Catalog(config, register)
        self._workflows = {
            workflow.name: workflow for workflow in config.all_workflows()
        }
        self._db = Database(
            config.database_uri, config.content_dir, create_schema=create_schema
        )
        self._reader = AppletReader(self._db)
        self._cache = UserCache(
            app=PACKAGE_NAME,
            expiration_time=config.cache.expiration,
            base_dir=config.cache_dir,
        )
        self._services = Services(
            db=self._db, fetcher=HTTPClient(cache=self._cache), llm_factory=self._llm
        )
        # Each profile's object, built when a run first needs it.
        self._objects: dict[Profile, Any] = {}
        self._lock_file: IO[str] | None = None

    @classmethod
    def from_config_file(
        cls, config_path: Path | None, *, create_schema: bool = True
    ) -> Self:
        """Build an Application from a config file, or from defaults when None."""
        config = Config.from_file(config_path) if config_path else Config()
        return cls(config, create_schema=create_schema)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        """Drop expired cache entries, then release the cache, the database
        and the write lock."""
        # UserCache never prunes on its own; once per run keeps it bounded.
        self._cache.prune()
        self._cache.close()
        self._db.close()
        if self._lock_file is not None:
            self._lock_file.close()
            self._lock_file = None

    def lock(self) -> None:
        """Take the write lock (see `write_lock`) until `close()`. Every
        command that writes takes it, so writers never overlap."""
        self._lock_file = write_lock(self.config.database_uri)

    def _object(self, profile: Profile) -> Any:
        """The profile's object, built on first use."""
        if profile not in self._objects:
            self._objects[profile] = profile.cls(profile.options, self._services)
        return self._objects[profile]

    def _llm(self, name: str | None) -> LLM:
        """The LLM `name` refers to (see `Services`)."""
        return self._object(self._catalog.llm_profile(name))

    @property
    def workflows(self) -> list[str]:
        """Workflow names, `default` first."""
        return list(self._workflows)

    def workflow(self, name: str = DEFAULT_WORKFLOW) -> Workflow:
        return lookup(self._workflows, name, "workflow")

    def sources(self, workflow: str = DEFAULT_WORKFLOW) -> list[SourceData]:
        """The workflow's sources, in configuration order."""
        ids = set(self.workflow(workflow).sources)
        return [source for source in self.config.sources if source.id in ids]

    def process_keys(
        self, processor: str | None = None, *, workflow: str = DEFAULT_WORKFLOW
    ) -> list[str]:
        """The keys of the workflow's process runs, in order; with
        `processor`, only its runs."""
        self.workflow(workflow)
        if processor is not None and processor not in self._catalog.processor_names:
            raise ConfigError(f"processor '{processor}' does not exist")
        return [
            key
            for (name, key), run in self._catalog.process.items()
            if name == workflow and processor in (None, run.profile.name)
        ]

    @property
    def app_ids(self) -> list[str]:
        """Every applet instance, in configuration order."""
        return list(self._catalog.apps)

    # --- Import ------------------------------------------------------------

    def import_source(self, source_id: str) -> list[SourceItem]:
        """Fetch the items of a configured source and store them, except the
        stored ones a preflight provider lists as unchanged."""
        source = self.config.get_source(source_id)
        provider = self._object(self._catalog.sources[source.id])
        checked: dict[str, datetime] = {}
        if isinstance(provider, PreflightProvider):
            item_datas = self._retrieve_preflight(source, provider, checked)
        else:
            item_datas = provider.retrieve_items(source)
        items = []
        try:
            for item_data in item_datas:
                item = SourceItem.from_data(source, item_data)
                LOGGER.info(f"{source.id}: {item.uri}")
                items.append(item)
        finally:
            # Oldest first, so new items get ids in publication order; undated
            # ones are stored as published now.
            now = datetime.now(UTC)
            items.sort(key=lambda item: item.published_at or now)
            # An error mid-run keeps what was fetched: the next run resumes.
            self._db.upsert_source_items(items)
            # Changed or not, a listed date once checked is not fetched again.
            self._db.advance_modified_times(source.id, checked)
        return items

    def _retrieve_preflight(
        self,
        source: SourceData,
        provider: PreflightProvider,
        checked: dict[str, datetime],
    ) -> Iterator[SourceItemData]:
        """The listed items that are new, or listed as modified since stored.
        Items listed without a date are always fetched. Fills `checked` with
        the listed date of each stored item retrieved."""
        stored_times = self._db.get_item_modified_times(source.id)
        for preflight_item in provider.iter_items(source):
            stored = stored_times.get(preflight_item.uid)
            listed = preflight_item.modified_at
            dated = stored is not None and listed is not None
            if dated and listed <= stored:
                continue
            try:
                item_data = provider.retrieve_item(preflight_item)
            except ValueError as e:
                LOGGER.error(f"{describe(e)} while retrieving '{preflight_item.ref}'")
                continue
            if dated:
                checked[preflight_item.uid] = listed
            if item_data.uid != preflight_item.uid:
                LOGGER.warning(
                    f"{source.id}: listed uid '{preflight_item.uid}' "
                    f"retrieved as '{item_data.uid}'"
                )
            if dated and (
                item_data.modified_at is None or item_data.modified_at <= stored
            ):
                LOGGER.warning(
                    f"{source.id}: '{item_data.uri}' listed as modified but not "
                    "newer once retrieved: not updated"
                )
                continue
            yield item_data

    # --- Process -----------------------------------------------------------

    def run_process(
        self,
        key: str,
        *,
        workflow: str = DEFAULT_WORKFLOW,
        scope: ProcessingScope | None = None,
        force: bool = False,
    ) -> RunSummary:
        """Run the workflow's process run that writes `key` on its
        sources. `force` also resets attempts."""
        if (run := self._catalog.process.get((workflow, key))) is None:
            raise ConfigError(
                f"no process run of workflow '{workflow}' writes the key '{key}'"
            )
        return self._object(run.profile).process(
            key=key,
            scope=workflow_scope(run.workflow, scope),
            force=force,
        )

    # --- Applets -----------------------------------------------------------

    def app_instance(self, app_id: str) -> AppInstance:
        return lookup(self._catalog.apps, app_id, "app")

    def app_status(self, now: datetime) -> list[AppStatus]:
        """Every instance's run record and next due time, in configuration
        order."""
        runs = self._db.get_app_runs()
        statuses = []
        for app in self._catalog.apps.values():
            run = runs.get(app.id, AppletRun(app=app.id))
            statuses.append(
                AppStatus(
                    instance=app,
                    run=run,
                    next_due=app.schedule.next_due(now, run.last_success),
                )
            )
        return statuses

    def run_app(
        self,
        app_id: str,
        now: datetime,
        *,
        force: bool = False,
        dry_run: bool = False,
    ) -> AppReport:
        """Run the instance if it is due (always with `force`) and store
        what it returns, or record its failure. With `dry_run`, report what
        it would emit and store nothing."""
        app = self.app_instance(app_id)
        applet = self._object(app.profile)
        run = self._db.get_app_run(app_id)
        if not force and not applet.is_due(now, run, app.schedule):
            return AppReport(app_id, due=False)
        if not dry_run:
            self._db.start_app_run(app_id, now)
        try:
            result = applet.run(now, run, self._reader)
            check_result(result, app.profile.cls.outputs)
        except Exception as e:  # noqa: BLE001
            # One failing applet must not stop the others; the run record and
            # the summary report it.
            log_failure(LOGGER, f"{app_id}: run failed", e)
            if not dry_run:
                self._db.fail_app_run(app_id, reason(e))
            return AppReport(app_id, due=True, error=describe(e))

        emitted = [(d.output, d.key) for d in result.documents]
        if dry_run:
            existing = self._db.existing_document_keys(app_id, emitted)
            return AppReport(
                app_id,
                due=True,
                new=tuple(pair for pair in emitted if pair not in existing),
                ignored=tuple(pair for pair in emitted if pair in existing),
                routed=self._db.count_missing_routes(app_id, existing, app.routes),
                state=result.state,
            )
        committed = self._db.commit_app_run(app_id, now, result, app.routes)
        new = {(d.output, d.key) for d in committed.documents}
        LOGGER.info(
            f"{app_id}: {len(new)} new document(s),"
            f" {len(emitted) - len(new)} already stored,"
            f" {committed.routed} delivery(ies) queued for stored ones"
        )
        return AppReport(
            app_id,
            due=True,
            new=tuple(pair for pair in emitted if pair in new),
            ignored=tuple(pair for pair in emitted if pair not in new),
            routed=committed.routed,
            state=result.state,
        )

    def reset_app(
        self, app_id: str, *, with_documents: bool = False, dry_run: bool = False
    ) -> int:
        """Delete the instance's run record; with `with_documents`, also its
        documents and their deliveries. Returns how many documents were (or
        would be) deleted. The instance need not be configured any more."""
        if dry_run:
            if not with_documents:
                return 0
            return len(self._db.find_documents(DocumentFilter(app=app_id)))
        return self._db.reset_app(app_id, with_documents=with_documents)

    # --- Deliver -----------------------------------------------------------

    def sink_profile(self, sink_id: str) -> Profile:
        return lookup(self._catalog.sinks, sink_id, "sink")

    def _deliverer(
        self, sink_id: str, pacing: PacingOverride | None = None
    ) -> Deliverer:
        profile = self.sink_profile(sink_id)
        return Deliverer(
            self._db, sink_id, self._object(profile), profile.options, pacing
        )

    def routed_sinks(self, app_ids: Iterable[str]) -> list[str]:
        """The sink instances the applet instances' outputs are routed to,
        in configuration order."""
        routed = {
            sink
            for app_id in app_ids
            for sinks in self.app_instance(app_id).routes.values()
            for sink in sinks
        }
        return [sink for sink in self._catalog.sinks if sink in routed]

    @property
    def sink_ids(self) -> list[str]:
        """Every sink instance, in configuration order."""
        return list(self._catalog.sinks)

    def plan_delivery(
        self, sink_id: str, now: datetime, pacing: PacingOverride | None = None
    ) -> list[Delivery]:
        """The rows a delivery run of the sink instance would send now."""
        return [delivery for delivery, _ in self._deliverer(sink_id, pacing).plan(now)]

    def deliver(
        self, sink_id: str, now: datetime, pacing: PacingOverride | None = None
    ) -> RunSummary:
        """Send the sink instance's pending rows, paced by its options or by
        `pacing`."""
        return self._deliverer(sink_id, pacing).deliver(now)

    def rename_sink(self, old: str, new: str, *, dry_run: bool = False) -> int:
        """Move the ledger of sink instance `old` to `new`, the name it now
        has in the configuration, so `new` does not deliver its documents
        again; return how many rows. `dry_run` only counts. `new` must be
        configured and have no rows yet."""
        lookup(self._catalog.sinks, new, "sink")
        if old == new:
            raise ConfigError(f"sink '{old}' cannot be renamed to itself")
        if existing := self._db.count_sink_deliveries(new):
            raise ConfigError(
                f"sink '{new}' already has {existing} delivery(ies); a rename"
                " needs an empty ledger"
            )
        if not (count := self._db.count_sink_deliveries(old)):
            raise ConfigError(f"sink '{old}' has no deliveries")
        return count if dry_run else self._db.rename_sink(old, new)

    def unconfigured_pending(self) -> dict[str, int]:
        """Pending rows of sinks no longer configured, counted by sink."""
        counts: dict[str, int] = {}
        for delivery, _ in self._db.deliveries_of(
            statuses=[DeliveryStatus.QUEUED, DeliveryStatus.ERROR]
        ):
            if delivery.sink not in self._catalog.sinks:
                counts[delivery.sink] = counts.get(delivery.sink, 0) + 1
        return counts

    # --- Queries -----------------------------------------------------------

    def get_items(
        self, scope: ProcessingScope | None = None, *, sort: str = "published"
    ) -> list[SourceItem]:
        """Items in scope by a `db.ITEM_SORTS` key, ascending, without their
        content."""
        return self._db.get_items(scope, sort=sort)

    def get_content(self, item: SourceItem) -> bytes:
        return self._db.get_content(item)

    def get_stored_content(self, sha256: str) -> bytes:
        return self._db.get_stored_content(sha256)

    def get_annotations(
        self, item: SourceItem, *, key: str | None = None
    ) -> dict[str, Any]:
        """An item's annotations as `{key: value}`; `{}` if none."""
        return self._db.get_annotations(item, key=key)

    def get_annotation_keys(
        self, item_ids: Iterable[int]
    ) -> dict[int, list[tuple[int, str, str]]]:
        """The `(id, processor, key)` of each item's annotations, by item id."""
        return self._db.get_annotation_keys(item_ids)

    def find_annotations(
        self,
        scope: ProcessingScope | None = None,
        *,
        processor: str | None = None,
        key: str | None = None,
        annotation_ids: Iterable[int] | None = None,
        sort: str = "item",
    ) -> list[Annotation]:
        """Annotations of the items in scope, with their values, by a
        `db.ANNOTATION_SORTS` key; filters combine and `limit` counts
        annotations."""
        return self._db.find_annotations(
            scope,
            processor=processor,
            key=key,
            annotation_ids=annotation_ids,
            sort=sort,
        )

    def get_annotation_values(
        self, items: Iterable[SourceItem], *, key: str
    ) -> dict[ItemKey, Any]:
        """One annotation's value per item; items without it are absent."""
        return self._db.get_annotation_values(items, key=key)

    # --- Documents ---------------------------------------------------------

    def find_documents(
        self,
        selection: DocumentFilter | None = None,
        *,
        sort: str = "emitted",
        with_content: bool = False,
    ) -> list[Document]:
        """Documents by a `db.DOCUMENT_SORTS` key, ascending; contents only
        `with_content`."""
        return self._db.find_documents(selection, sort=sort, with_content=with_content)

    def delete_documents(self, document_ids: Iterable[int]) -> DeleteSummary:
        """Delete these documents with their deliveries, except those with a
        delivery that is not `done`, which are refused."""
        document_ids = list(document_ids)
        undelivered = sorted(
            {
                delivery.document_id
                for delivery in self._db.find_deliveries(
                    DocumentFilter(document_ids=tuple(document_ids))
                )
                if delivery.status != DeliveryStatus.DONE
            }
        )
        deleted = self._db.delete_documents(
            document_id
            for document_id in document_ids
            if document_id not in undelivered
        )
        return DeleteSummary(deleted=deleted, refused=undelivered)

    # --- Deliveries --------------------------------------------------------

    def find_deliveries(
        self,
        documents: DocumentFilter | None = None,
        *,
        sink: str | None = None,
        status: DeliveryStatus | None = None,
        delivery_ids: Iterable[int] | None = None,
        limit: int | None = None,
        sort: str = "id",
    ) -> list[Delivery]:
        """Ledger rows by a `db.DELIVERY_SORTS` key, of the documents
        `documents` selects; filters combine and `limit` counts rows. `sink`
        is not checked against the configuration, so the rows of a removed
        sink can be found."""
        return self._db.find_deliveries(
            documents,
            sink=sink,
            status=status,
            delivery_ids=delivery_ids,
            limit=limit,
            sort=sort,
        )

    def set_delivery_status(
        self, deliveries: Iterable[Delivery], status: DeliveryStatus
    ) -> int:
        """Move these ledger rows to `queued`, `done` or `error`; return how
        many. `queued` also gives them fresh attempts, and `queued` and
        `done` clear the last error."""
        if status == DeliveryStatus.SENDING:
            raise ValueError("a delivery is only `sending` while it is sent")
        count = 0
        for delivery in deliveries:
            delivery.status = status
            if status == DeliveryStatus.QUEUED:
                delivery.attempts = 0
            if status != DeliveryStatus.ERROR:
                delivery.last_error = None
            self._db.save_delivery(delivery)
            count += 1
        return count

    def send_deliveries(self, deliveries: Iterable[Delivery]) -> dict[str, RunSummary]:
        """Send these ledger rows now, whatever their state, with no backoff
        and no pacing; one summary per sink. Rows of a sink that is no longer
        configured are skipped with a warning."""
        by_sink: dict[str, list[int]] = {}
        for delivery in deliveries:
            assert delivery.id is not None
            by_sink.setdefault(delivery.sink, []).append(delivery.id)

        summaries: dict[str, RunSummary] = {}
        for sink_id, delivery_ids in by_sink.items():
            if sink_id not in self._catalog.sinks:
                LOGGER.warning(
                    f"{sink_id}: not configured, skipped"
                    f" {len(delivery_ids)} delivery(ies)"
                )
                continue
            rows = self._db.deliveries_of(sink_id, delivery_ids=delivery_ids)
            summaries[sink_id] = self._deliverer(sink_id).send_rows(rows)
        return summaries

    def selected_documents(
        self, sink_id: str, selection: DocumentFilter
    ) -> list[Document]:
        """The documents `selection` names, whatever their routes; raise if
        the sink instance does not accept the content type of any."""
        profile = self.sink_profile(sink_id)
        documents = self._db.find_documents(selection)
        refused = sorted(
            {
                d.content_type
                for d in documents
                if not accepts(profile.cls, {d.content_type})
            }
        )
        if refused:
            raise ConfigError(
                f"sink '{sink_id}' ({profile.name}) does not accept"
                f" {', '.join(refused)}; narrow the selection"
            )
        return documents

    def routed_documents(
        self, sink_id: str, selection: DocumentFilter | None = None
    ) -> list[Document]:
        """The documents `selection` names among those of the outputs routed
        to the sink instance; `limit` counts them."""
        selection = selection or DocumentFilter()
        self.sink_profile(sink_id)
        routed = {
            (app.id, output)
            for app in self._catalog.apps.values()
            for output, sinks in app.routes.items()
            if sink_id in sinks
        }
        documents = [
            document
            for document in self._db.find_documents(
                dataclasses.replace(selection, limit=None)
            )
            if (document.app, document.output) in routed
        ]
        return documents[: selection.limit]

    def mark_deliveries(
        self,
        sink_id: str,
        status: DeliveryStatus,
        selection: DocumentFilter | None = None,
        *,
        overwrite: bool = False,
        dry_run: bool = False,
    ) -> MarkSummary:
        """Give the documents `selection` names a row of the sink instance
        in `status`, routed to it or not; without filters, every document
        routed to it. Existing rows are left as they are unless `overwrite`.
        `dry_run` only counts. A document whose content type the sink does
        not accept is a configuration error, and nothing is marked."""
        if status == DeliveryStatus.SENDING:
            raise ValueError("a delivery is only `sending` while it is sent")
        if selection is not None and selection.is_set():
            documents = self.selected_documents(sink_id, selection)
        else:
            documents = self.routed_documents(sink_id, selection)
        existing = {
            delivery.document_id: delivery
            for delivery in self._db.find_deliveries(
                DocumentFilter(document_ids=tuple(d.id for d in documents if d.id)),
                sink=sink_id,
            )
        }
        new = [d for d in documents if d.id not in existing]
        present = [existing[d.id] for d in documents if d.id in existing]
        summary = MarkSummary(created=len(new))
        if overwrite:
            summary.changed = len(present)
        else:
            summary.kept = len(present)
        if dry_run:
            return summary

        last_error = SET_BY_HAND if status == DeliveryStatus.ERROR else None
        self._db.add_deliveries(
            Delivery(
                sink=sink_id,
                document_id=document.id,
                status=status,
                last_error=last_error,
            )
            for document in new
            if document.id is not None
        )
        if overwrite:
            self.set_delivery_status(present, status)
        return summary

    def delete_deliveries(self, delivery_ids: Iterable[int]) -> int:
        """Delete these ledger rows; return how many. Their documents are
        not delivered again unless rows are created for them, by hand or by
        their applet emitting them again while routed to the sink."""
        return self._db.delete_deliveries(delivery_ids)

    # --- Deletion ----------------------------------------------------------

    def delete_annotations(self, annotation_ids: Iterable[int]) -> int:
        """Delete these annotations with the processing state of their
        (item, key): the items become pending again with fresh attempts.

        Returns the number of annotations deleted.
        """
        return self._db.delete_annotations(annotation_ids)

    def delete_items(self, item_ids: Iterable[int]) -> int:
        """Delete items with their state and annotations; return how many.
        One still in its source's index comes back on the next import, with
        a new id."""
        return self._db.delete_items(item_ids)


def write_lock(database_url: str) -> IO[str] | None:
    """Take the exclusive write lock, a file next to the database, held
    until the returned file is closed. Raise `LockedError` at once if another
    process holds it. In-memory databases are private to their process and
    need none (None).
    """
    url = make_url(database_url)
    if url.get_backend_name() != "sqlite" or url.database in (None, "", ":memory:"):
        return None
    lock_path = Path(f"{url.database}.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_file = lock_path.open("a")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock_file.close()
        raise LockedError(
            f"another newstool command is using the database ({lock_path})"
        ) from None
    return lock_file


def workflow_scope(
    workflow: Workflow, scope: ProcessingScope | None
) -> ProcessingScope:
    """`scope` restricted to the workflow's sources."""
    return dataclasses.replace(
        scope or ProcessingScope(), sources=tuple(workflow.sources)
    )


def lookup[T](objects: dict[str, T], name: str, kind: str) -> T:
    try:
        return objects[name]
    except KeyError:
        raise ConfigError(f"{kind} '{name}' is not configured") from None
