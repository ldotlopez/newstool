"""Persistence: SQLite metadata plus a content-addressed DiskStorage.

Item, annotation and document contents live in one `DiskStorage`, keyed by
the sha256 of their bytes; rows only hold that key. SQLAlchemy models never
leave this module: `Database` takes and returns DTOs.
"""

from __future__ import annotations

import contextlib
import dataclasses
import enum
import hashlib
import logging
import sqlite3
from collections.abc import Iterable, Iterator, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Self

from foundation.jsonlib import dump_json_compatible, load_json_compatible
from foundation.storage import DiskStorage
from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    event,
    tuple_,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Query,
    Session,
    aliased,
    mapped_column,
    relationship,
    sessionmaker,
)
from sqlalchemy.types import TypeDecorator

from .models import (
    Annotation,
    AppletResult,
    AppletRun,
    Delivery,
    Document,
    DocumentFilter,
    ItemKey,
    ProcessingScope,
    SourceData,
    SourceItem,
)

LOGGER = logging.getLogger(__name__)

SQLITE_PRAGMAS = (
    "foreign_keys = ON",
    "busy_timeout = 5000",
    "journal_mode = WAL",
    "synchronous = NORMAL",
    "temp_store = MEMORY",
)


def _configure_sqlite_connection(
    dbapi_connection: sqlite3.Connection, connection_record: Any
) -> None:
    for pragma in SQLITE_PRAGMAS:
        dbapi_connection.execute(f"PRAGMA {pragma}")


class Base(DeclarativeBase):
    pass


class CustomJSON(TypeDecorator):
    """JSON column with pluggable encode/decode for non-standard Python types."""

    impl = JSON
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        return dump_json_compatible(value)

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        return load_json_compatible(value)


class UTCDateTime(TypeDecorator):
    """DateTime column that round-trips tz-aware UTC datetimes.

    The sqlite3 driver returns naive datetimes, and `DateTime(timezone=True)`
    does not change that. This normalizes to UTC on write, re-attaches UTC on
    read, and rejects naive datetimes rather than guessing their timezone.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Any) -> Any:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError(f"naive datetime not allowed: {value!r}")
        return value.astimezone(UTC)

    def process_result_value(self, value: Any, dialect: Any) -> datetime | None:
        if value is None:
            return None
        return value if value.tzinfo else value.replace(tzinfo=UTC)


# Ids are handles the CLI selects rows by (decision 0008): never reuse a
# deleted one.
AUTOINCREMENT = {"sqlite_autoincrement": True}


def _sha256_column() -> Mapped[str]:
    return mapped_column(String(64), index=True)


class DBSource(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String(255))

    items: Mapped[list[DBSourceItem]] = relationship(
        back_populates="source", cascade="all, delete-orphan", passive_deletes=True
    )

    @classmethod
    def from_dto(cls, dto: SourceData) -> Self:
        return cls(id=dto.id, name=dto.name, url=str(dto.url), provider=dto.provider)

    def to_dto(self) -> SourceData:
        return SourceData(
            id=self.id, name=self.name, url=self.url, provider=self.provider
        )

    def update(self, dto: SourceData) -> None:
        self.name = dto.name
        self.url = str(dto.url)
        self.provider = dto.provider


class DBSourceItem(Base):
    __tablename__ = "source_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"))
    uid: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(Text)
    uri: Mapped[str] = mapped_column(Text)
    mimetype: Mapped[str] = mapped_column(String(255))
    content_sha256: Mapped[str] = _sha256_column()
    data: Mapped[dict] = mapped_column(CustomJSON, default=dict)
    # From the provider when it gives them, else the import time (see
    # Database._upsert_source_items).
    published_at: Mapped[datetime] = mapped_column(UTCDateTime)
    modified_at: Mapped[datetime] = mapped_column(UTCDateTime)
    # The first import; never moved (decision 0015).
    imported_at: Mapped[datetime] = mapped_column(UTCDateTime)

    source: Mapped[DBSource] = relationship(back_populates="items")

    __table_args__ = (
        UniqueConstraint("source_id", "uid"),
        Index("ix_source_items_source_id_published_at", "source_id", "published_at"),
        Index("ix_source_items_source_id_imported_at", "source_id", "imported_at"),
        CheckConstraint(
            "length(content_sha256) = 64", name="ck_source_items_content_sha256"
        ),
        AUTOINCREMENT,
    )

    @classmethod
    def from_dto(cls, dto: SourceItem) -> Self:
        return cls(
            source_id=dto.source.id,
            uid=dto.uid,
            title=dto.title,
            uri=dto.uri,
            mimetype=dto.mimetype,
            content_sha256=dto.content_sha256,
            data=dto.data,
            published_at=dto.published_at,
            modified_at=dto.modified_at,
            imported_at=dto.imported_at,
        )

    def to_dto(self) -> SourceItem:
        return SourceItem(
            source=self.source.to_dto(),
            uid=self.uid,
            title=self.title,
            uri=self.uri,
            mimetype=self.mimetype,
            content_sha256=self.content_sha256,
            data=self.data,
            published_at=self.published_at,
            modified_at=self.modified_at,
            imported_at=self.imported_at,
            id=self.id,
        )

    def update(self, dto: SourceItem) -> None:
        """Assign every field but the identity and the timestamps, whose
        no-regression rules live in Database._apply_source_item_changes."""
        self.title = dto.title
        self.uri = dto.uri
        self.mimetype = dto.mimetype
        self.content_sha256 = dto.content_sha256
        self.data = dto.data


class ProcessingStatus(enum.StrEnum):
    DONE = "done"
    ERROR = "error"
    IGNORED = "ignored"


def backoff_seconds(
    attempts: int,
    base: float = 60.0,
    factor: float = 2.0,
    max_seconds: float = 24 * 3600,
) -> float:
    """Exponential backoff between retries: base * factor**(attempts-1), capped."""
    return min(base * (factor ** max(attempts - 1, 0)), max_seconds)


class DBProcessingState(Base):
    """Per-(item, key) run state; no row means never attempted. `key` is the
    annotation the run writes; `processor` is the one that ran it.

    `ignored` is the processor's own permanent skip for that content.
    `error` rows count attempts for retries with backoff.
    """

    __tablename__ = "processing_state"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_item_id: Mapped[int] = mapped_column(
        ForeignKey("source_items.id", ondelete="CASCADE")
    )
    processor: Mapped[str] = mapped_column(String(255))
    key: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50))
    attempts: Mapped[int] = mapped_column(default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    # A different VERSION on the processor makes `done` items eligible again.
    processor_version: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Item content this state was computed from; a different one on the item
    # makes it eligible again.
    content_sha256: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime)

    __table_args__ = (
        UniqueConstraint("source_item_id", "key"),
        Index("ix_processing_state_processor_status", "processor", "status"),
        CheckConstraint(
            "status IN ('done', 'error', 'ignored')", name="ck_processing_state_status"
        ),
        AUTOINCREMENT,
    )


class DBItemAnnotation(Base):
    """One key a processor produced for an item; the value lives in storage.
    A key is unique per item, whichever processor wrote it."""

    __tablename__ = "item_annotations"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_item_id: Mapped[int] = mapped_column(
        ForeignKey("source_items.id", ondelete="CASCADE")
    )
    processor: Mapped[str] = mapped_column(String(255))
    key: Mapped[str] = mapped_column(String(255))
    content_sha256: Mapped[str] = _sha256_column()
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime)

    __table_args__ = (
        UniqueConstraint("source_item_id", "key"),
        Index("ix_item_annotations_processor", "processor"),
        AUTOINCREMENT,
    )


class DBApp(Base):
    """An applet instance's run record (decision 0015). No row: it never
    ran. `state` is the applet's own, opaque to the core."""

    __tablename__ = "apps"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    last_started: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    last_success: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    state: Mapped[Any] = mapped_column(CustomJSON, nullable=True)

    @classmethod
    def from_dto(cls, dto: AppletRun) -> Self:
        return cls(
            id=dto.app,
            last_started=dto.last_started,
            last_success=dto.last_success,
            last_error=dto.last_error,
            state=dto.state,
        )

    def to_dto(self) -> AppletRun:
        return AppletRun(
            app=self.id,
            last_started=self.last_started,
            last_success=self.last_success,
            last_error=self.last_error,
            state=self.state,
        )

    def update(self, dto: AppletRun) -> None:
        self.last_started = dto.last_started
        self.last_success = dto.last_success
        self.last_error = dto.last_error
        self.state = dto.state


class DBDocument(Base):
    """A document an applet instance emitted; never rewritten (decision
    0015). Its content lives in storage."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    app: Mapped[str] = mapped_column(String(255))
    output: Mapped[str] = mapped_column(String(255))
    key: Mapped[str] = mapped_column(String(512))
    content_type: Mapped[str] = mapped_column(String(255))
    content_sha256: Mapped[str] = _sha256_column()
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    emitted_at: Mapped[datetime] = mapped_column(UTCDateTime)

    __table_args__ = (
        UniqueConstraint("app", "output", "key"),
        Index("ix_documents_app_emitted_at", "app", "emitted_at"),
        CheckConstraint(
            "length(content_sha256) = 64", name="ck_documents_content_sha256"
        ),
        AUTOINCREMENT,
    )

    @classmethod
    def from_dto(cls, dto: Document) -> Self:
        return cls(
            app=dto.app,
            output=dto.output,
            key=dto.key,
            content_type=dto.content_type,
            content_sha256=dto.content_sha256,
            title=dto.title,
            url=dto.url,
            image_url=dto.image_url,
            emitted_at=dto.emitted_at,
        )

    def to_dto(self) -> Document:
        return Document(
            app=self.app,
            output=self.output,
            key=self.key,
            content_type=self.content_type,
            content_sha256=self.content_sha256,
            title=self.title,
            url=self.url,
            image_url=self.image_url,
            emitted_at=self.emitted_at,
            id=self.id,
        )

    def update(self, dto: Document) -> None:
        """Documents are immutable once stored; this exists for the DTO
        contract and is used by no write path."""
        self.app = dto.app
        self.output = dto.output
        self.key = dto.key
        self.content_type = dto.content_type
        self.content_sha256 = dto.content_sha256
        self.title = dto.title
        self.url = dto.url
        self.image_url = dto.image_url
        self.emitted_at = dto.emitted_at


@dataclasses.dataclass(slots=True)
class CommittedRun:
    """What `commit_app_run` stored: the new documents, and how many rows it
    added for documents already stored, routed since they were emitted."""

    documents: list[Document] = dataclasses.field(default_factory=list)
    routed: int = 0


class DeliveryStatus(enum.StrEnum):
    QUEUED = "queued"
    SENDING = "sending"  # committed before the external call
    DONE = "done"
    ERROR = "error"


class DBDelivery(Base):
    """The delivery ledger: one row per (sink instance, document), the record
    of an external fact (decision 0015)."""

    __tablename__ = "deliveries"

    id: Mapped[int] = mapped_column(primary_key=True)
    sink: Mapped[str] = mapped_column(String(255))
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE")
    )
    status: Mapped[str] = mapped_column(String(50))
    attempts: Mapped[int] = mapped_column(default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_ref: Mapped[Any] = mapped_column(CustomJSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime)

    document: Mapped[DBDocument] = relationship()

    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'sending', 'done', 'error')",
            name="ck_deliveries_status",
        ),
        UniqueConstraint("sink", "document_id"),
        Index("ix_deliveries_sink_status", "sink", "status"),
        AUTOINCREMENT,
    )

    @classmethod
    def from_dto(cls, dto: Delivery) -> Self:
        return cls(
            sink=dto.sink,
            document_id=dto.document_id,
            status=dto.status,
            attempts=dto.attempts,
            last_error=dto.last_error,
            external_ref=dto.external_ref,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )

    def to_dto(self) -> Delivery:
        return Delivery(
            sink=self.sink,
            document_id=self.document_id,
            status=self.status,
            attempts=self.attempts,
            last_error=self.last_error,
            external_ref=self.external_ref,
            created_at=self.created_at,
            updated_at=self.updated_at,
            document_label=(
                f"{self.document.app}/{self.document.output}/{self.document.key}"
            ),
            id=self.id,
        )

    def update(self, dto: Delivery) -> None:
        self.sink = dto.sink
        self.document_id = dto.document_id
        self.status = dto.status
        self.attempts = dto.attempts
        self.last_error = dto.last_error
        self.external_ref = dto.external_ref
        self.created_at = dto.created_at
        self.updated_at = dto.updated_at


# Sort keys of the selection queries, by entity: the columns to sort by,
# ascending (oldest first for dates). The row id breaks ties.
ITEM_SORTS = {
    "id": [DBSourceItem.id],
    "source": [DBSourceItem.source_id],
    "published": [DBSourceItem.published_at],
    "imported": [DBSourceItem.imported_at],
    "updated": [DBSourceItem.modified_at],
    "title": [DBSourceItem.title],
}
ANNOTATION_SORTS = {
    "id": [DBItemAnnotation.id],
    "item": [
        DBItemAnnotation.source_item_id,
        DBItemAnnotation.processor,
        DBItemAnnotation.key,
    ],
    "processor": [DBItemAnnotation.processor, DBItemAnnotation.key],
    "updated": [DBItemAnnotation.updated_at],
}
DOCUMENT_SORTS = {
    "id": [DBDocument.id],
    "app": [DBDocument.app, DBDocument.output, DBDocument.key],
    "type": [DBDocument.content_type],
    "emitted": [DBDocument.emitted_at],
}
DELIVERY_SORTS = {
    "id": [DBDelivery.id],
    "sink": [DBDelivery.sink],
    "status": [DBDelivery.status],
    "updated": [DBDelivery.updated_at],
}


def _encode_value(value: Any) -> tuple[str, bytes]:
    """An annotation value as stored: its JSON bytes and their sha256."""
    encoded = dump_json_compatible(value).encode()
    return hashlib.sha256(encoded).hexdigest(), encoded


class Database:
    def __init__(
        self, database_url: str, content_dir: Path, *, create_schema: bool = True
    ) -> None:
        """Open the database and the content storage.

        `create_schema` creates missing tables only; it never alters an
        existing schema.
        """
        self._ensure_sqlite_directory(database_url)
        self.engine = create_engine(database_url)
        if self.engine.dialect.name == "sqlite":
            event.listen(self.engine, "connect", _configure_sqlite_connection)
        if create_schema:
            Base.metadata.create_all(self.engine)

        self._sessionmaker = sessionmaker(bind=self.engine)
        self.contents = DiskStorage(content_dir)
        LOGGER.info(f"Using database at '{database_url}'")

    @staticmethod
    def _ensure_sqlite_directory(database_url: str) -> None:
        """Create the parent directory of a file-based SQLite URL."""
        prefix = "sqlite:///"
        if not database_url.startswith(prefix):
            return
        db_path = database_url.removeprefix(prefix)
        if db_path == "" or db_path.startswith(":memory:"):
            return
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    def close(self) -> None:
        self.engine.dispose()
        self.contents.close()

    @contextlib.contextmanager
    def session_scope(self) -> Iterator[Session]:
        """One transaction: commit on success, roll back on any error."""
        session = self._sessionmaker()
        try:
            yield session
            session.commit()
        except BaseException:
            session.rollback()
            raise
        finally:
            session.close()

    # --- Contents --------------------------------------------------------

    def get_content(self, item: SourceItem) -> bytes:
        """Return the item's stored content.

        Raise foundation.storage.EntryNotFoundError if the storage lost it.
        """
        if item.content_sha256 is None:
            raise ValueError(f"item {item.key} has no content reference")
        return self.get_stored_content(item.content_sha256)

    def get_stored_content(self, sha256: str) -> bytes:
        """Return the stored content with this sha256, whatever references it.

        Raise foundation.storage.EntryNotFoundError if there is none.
        """
        return self.contents.get(sha256)

    def _release_contents(self, sha256s: set[str]) -> None:
        """Delete the contents no row references any more.

        An upsert in another process that started referencing one of these
        between the check and the delete would lose its content: writers take
        `Application.lock()` (decision 0007) so that they never overlap.
        """
        if not sha256s:
            return
        referenced: set[str] = set()
        with self.session_scope() as sess:
            for column in (
                DBSourceItem.content_sha256,
                DBItemAnnotation.content_sha256,
                DBDocument.content_sha256,
            ):
                referenced.update(
                    sha256
                    for (sha256,) in sess.query(column).filter(column.in_(sha256s))
                )
        for sha256 in sha256s - referenced:
            self.contents.delete(sha256)

    # --- Import ----------------------------------------------------------

    def upsert_source_items(self, items: list[SourceItem]) -> None:
        """Create or update items, and the sources they belong to, and set
        each item's `id`.

        Contents are written before the rows that reference them, so a crash
        leaves an unused file, never a row pointing at nothing. Contents the
        updated rows stopped using are released after the commit.
        """
        items_by_source: dict[SourceData, list[SourceItem]] = {}
        for item in items:
            items_by_source.setdefault(item.source, []).append(item)

        replaced: set[str] = set()
        with self.session_scope() as sess:
            for source, source_items in items_by_source.items():
                self._sync_source(sess, source)
                replaced |= self._upsert_source_items(sess, source, source_items)

        self._release_contents(replaced)

    def _sync_source(self, session: Session, source: SourceData) -> None:
        db_source = session.get(DBSource, source.id)
        if db_source is None:
            session.add(DBSource.from_dto(source))
        else:
            db_source.update(source)
        session.flush()

    def _upsert_source_items(
        self, session: Session, source: SourceData, items: list[SourceItem]
    ) -> set[str]:
        """Returns the sha256 of the contents the updated items stopped using."""
        items_by_uid = {item.uid: item for item in items}
        existing_by_uid = {
            db_item.uid: db_item
            for db_item in session.query(DBSourceItem).filter(
                DBSourceItem.source_id == source.id,
                DBSourceItem.uid.in_(items_by_uid),
            )
        }

        now = datetime.now(UTC)
        replaced: set[str] = set()
        rows: list[tuple[SourceItem, DBSourceItem]] = []
        created = updated = 0

        for uid, item in items_by_uid.items():
            if item.content is None or item.content_sha256 is None:
                raise ValueError(f"item {item.key} has no content to store")

            db_item = existing_by_uid.get(uid)
            if db_item is None:
                self.contents.set(item.content_sha256, item.content)
                db_item = DBSourceItem.from_dto(
                    dataclasses.replace(
                        item,
                        published_at=item.published_at or now,
                        modified_at=item.modified_at or now,
                        imported_at=now,
                    )
                )
                session.add(db_item)
                rows.append((item, db_item))
                created += 1
                continue

            rows.append((item, db_item))

            if db_item.content_sha256 != item.content_sha256:
                self.contents.set(item.content_sha256, item.content)
                replaced.add(db_item.content_sha256)

            if self._apply_source_item_changes(session, db_item, item, now=now):
                updated += 1

        session.flush()
        for item, db_item in rows:
            item.id = db_item.id
        LOGGER.info(f"{source.id}: {created} new, {updated} updated item(s)")
        return replaced

    def _apply_source_item_changes(
        self, session: Session, db_item: DBSourceItem, dto: SourceItem, *, now: datetime
    ) -> bool:
        """Apply `dto` to `db_item`; return whether anything changed.

        Ordering is load-bearing: `update()` must run before
        `session.is_modified()` and the timestamps after it, or the
        timestamps themselves would count as changes.
        """
        db_item.update(dto)
        if not session.is_modified(db_item, include_collections=False):
            return False

        if dto.modified_at is None:
            db_item.modified_at = now
        elif dto.modified_at > db_item.modified_at:
            db_item.modified_at = dto.modified_at
        # published_at is set once, on creation, and never moved.
        return True

    # --- Items -------------------------------------------------------------

    def get_items(
        self,
        scope: ProcessingScope | None = None,
        *,
        newest_first: bool = False,
        sort: str = "published",
    ) -> list[SourceItem]:
        """Items in scope, by an `ITEM_SORTS` key, ascending unless
        `newest_first`; `limit` keeps the first ones in that order."""
        scope = scope or ProcessingScope()
        columns = [*ITEM_SORTS[sort], DBSourceItem.id]
        with self.session_scope() as sess:
            query = self._apply_scope(sess.query(DBSourceItem), scope)
            query = query.order_by(
                *(column.desc() if newest_first else column for column in columns)
            )
            if scope.limit:
                query = query.limit(scope.limit)
            return [db_item.to_dto() for db_item in query]

    def get_item_modified_times(self, source_id: str) -> dict[str, datetime]:
        """The `modified_at` of each uid stored for a source."""
        with self.session_scope() as sess:
            query = sess.query(DBSourceItem.uid, DBSourceItem.modified_at).filter(
                DBSourceItem.source_id == source_id
            )
            return dict(query.all())

    def advance_modified_times(
        self, source_id: str, modified_times: dict[str, datetime]
    ) -> None:
        """Move each uid's `modified_at` forward to the given time, never
        backwards, whether or not its content changed."""
        if not modified_times:
            return
        with self.session_scope() as sess:
            query = sess.query(DBSourceItem).filter(
                DBSourceItem.source_id == source_id,
                DBSourceItem.uid.in_(modified_times),
            )
            for db_item in query:
                db_item.modified_at = max(
                    db_item.modified_at, modified_times[db_item.uid]
                )

    @staticmethod
    def _apply_scope(query: Query, scope: ProcessingScope) -> Query:
        if scope.source:
            query = query.filter(DBSourceItem.source_id == scope.source)
        if scope.sources is not None:
            query = query.filter(DBSourceItem.source_id.in_(scope.sources))
        if scope.since:
            query = query.filter(DBSourceItem.published_at >= scope.since)
        if scope.until:
            query = query.filter(DBSourceItem.published_at < scope.until)
        if scope.imported_since:
            query = query.filter(DBSourceItem.imported_at >= scope.imported_since)
        if scope.imported_until:
            query = query.filter(DBSourceItem.imported_at < scope.imported_until)
        if scope.item_ids:
            query = query.filter(DBSourceItem.id.in_(scope.item_ids))
        return query

    @staticmethod
    def _get_item_row(session: Session, item: SourceItem) -> DBSourceItem:
        return (
            session.query(DBSourceItem)
            .filter_by(source_id=item.source.id, uid=item.uid)
            .one()
        )

    # --- Processing state --------------------------------------------------

    def get_unprocessed_items(
        self,
        key: str,
        *,
        version: str | None,
        max_retries: int,
        force: bool = False,
        scope: ProcessingScope | None = None,
        requires: str | None = None,
    ) -> list[SourceItem]:
        """Items a run writing `key` should process, oldest first.

        With `requires`, only items whose run of that key finished on their
        current content are candidates, even with `force`: the rest wait
        instead of failing here. `force` skips eligibility, including
        `ignored` items.
        """
        scope = scope or ProcessingScope()
        now = datetime.now(UTC)

        with self.session_scope() as sess:
            query = sess.query(DBSourceItem, DBProcessingState).outerjoin(
                DBProcessingState,
                (DBProcessingState.source_item_id == DBSourceItem.id)
                & (DBProcessingState.key == key),
            )
            if requires is not None:
                query = self._join_finished(query, requires)
            query = self._apply_scope(query, scope).order_by(DBSourceItem.published_at)

            result = []
            for db_item, state in query:
                if not force and not self._is_eligible(
                    state, db_item.content_sha256, version, max_retries, now
                ):
                    continue
                result.append(db_item.to_dto())
                if scope.limit and len(result) >= scope.limit:
                    break
            return result

    @staticmethod
    def _join_finished(query: Query, key: str) -> Query:
        """Keep the items whose run of `key` finished on their current content."""
        upstream = aliased(DBProcessingState)
        return query.join(
            upstream,
            (upstream.source_item_id == DBSourceItem.id)
            & (upstream.key == key)
            & (upstream.status == ProcessingStatus.DONE)
            & (upstream.content_sha256 == DBSourceItem.content_sha256),
        )

    @staticmethod
    def _is_eligible(
        state: DBProcessingState | None,
        content_sha256: str,
        version: str | None,
        max_retries: int,
        now: datetime,
    ) -> bool:
        if state is None:
            return True  # never attempted
        if state.content_sha256 != content_sha256:
            return True  # the item's content changed since the last run
        if state.status == ProcessingStatus.IGNORED:
            return False  # permanent for this content; only force revisits it
        if state.status == ProcessingStatus.DONE:
            return state.processor_version != version
        if state.attempts >= max_retries:
            return False
        elapsed = (now - state.updated_at).total_seconds()
        return elapsed >= backoff_seconds(state.attempts)

    def record_result(
        self,
        item: SourceItem,
        processor: str,
        key: str,
        status: ProcessingStatus,
        *,
        value: Any = None,
        error: str | None = None,
        version: str | None = None,
        reset_attempts: bool = False,
    ) -> None:
        """Save a run's state and, when `done`, its annotation `key` with
        `value`, in one transaction.

        The state records `item.content_sha256`, the content the run used.
        `reset_attempts` starts the retry count afresh (forced runs).
        """
        replaced: set[str] = set()
        with self.session_scope() as sess:
            db_item = self._get_item_row(sess, item)
            now = datetime.now(UTC)
            if status == ProcessingStatus.DONE:
                replaced = self._save_annotation(
                    sess, db_item.id, processor, key, value, now
                )
            self._save_state(
                sess,
                db_item,
                processor,
                key,
                status,
                error,
                version,
                reset_attempts,
                now,
            )
        self._release_contents(replaced)

    @staticmethod
    def _save_state(
        session: Session,
        db_item: DBSourceItem,
        processor: str,
        key: str,
        status: ProcessingStatus,
        error: str | None,
        version: str | None,
        reset_attempts: bool,
        now: datetime,
    ) -> None:
        state = (
            session.query(DBProcessingState)
            .filter_by(source_item_id=db_item.id, key=key)
            .one_or_none()
        )
        if state is None:
            state = DBProcessingState(
                source_item_id=db_item.id,
                key=key,
                attempts=0,
                created_at=now,
            )
            session.add(state)
        elif reset_attempts or state.content_sha256 != db_item.content_sha256:
            state.attempts = 0

        state.processor = processor
        state.status = status
        state.content_sha256 = db_item.content_sha256
        state.processor_version = version
        state.updated_at = now
        if status == ProcessingStatus.ERROR:
            state.attempts += 1
            state.last_error = error
        else:
            state.attempts = 0
            state.last_error = None

    # --- Annotations -------------------------------------------------------

    def _save_annotation(
        self,
        session: Session,
        source_item_id: int,
        processor: str,
        key: str,
        value: Any,
        now: datetime,
    ) -> set[str]:
        """Store the value, then upsert its row; returns the replaced content."""
        sha256, encoded = _encode_value(value)
        self.contents.set(sha256, encoded)

        row = (
            session.query(DBItemAnnotation)
            .filter_by(source_item_id=source_item_id, key=key)
            .one_or_none()
        )
        if row is None:
            session.add(
                DBItemAnnotation(
                    source_item_id=source_item_id,
                    processor=processor,
                    key=key,
                    content_sha256=sha256,
                    created_at=now,
                    updated_at=now,
                )
            )
            return set()
        row.processor = processor
        if row.content_sha256 == sha256:
            return set()
        replaced = {row.content_sha256}
        row.content_sha256 = sha256
        row.updated_at = now
        return replaced

    def _load_value(self, sha256: str) -> Any:
        return load_json_compatible(self.contents.get(sha256).decode())

    def get_annotations(
        self, item: SourceItem, *, key: str | None = None
    ) -> dict[str, Any]:
        """An item's annotations as `{key: value}`; `key` narrows the result.
        Nothing found is `{}`."""
        with self.session_scope() as sess:
            query = (
                sess.query(
                    DBItemAnnotation.key,
                    DBItemAnnotation.content_sha256,
                )
                .join(DBSourceItem, DBItemAnnotation.source_item_id == DBSourceItem.id)
                .filter(
                    DBSourceItem.source_id == item.source.id,
                    DBSourceItem.uid == item.uid,
                )
            )
            if key is not None:
                query = query.filter(DBItemAnnotation.key == key)
            rows = query.all()

        return {row_key: self._load_value(sha256) for row_key, sha256 in rows}

    def get_annotation_keys(
        self, item_ids: Iterable[int]
    ) -> dict[int, list[tuple[int, str, str]]]:
        """The `(id, processor, key)` of each item's annotations, by item id,
        read in a single query. Items without annotations are absent."""
        item_ids = list(item_ids)
        if not item_ids:
            return {}
        with self.session_scope() as sess:
            rows = (
                sess.query(
                    DBItemAnnotation.source_item_id,
                    DBItemAnnotation.id,
                    DBItemAnnotation.processor,
                    DBItemAnnotation.key,
                )
                .filter(DBItemAnnotation.source_item_id.in_(item_ids))
                .order_by(DBItemAnnotation.processor, DBItemAnnotation.key)
                .all()
            )
        result: dict[int, list[tuple[int, str, str]]] = {}
        for item_id, annotation_id, processor, key in rows:
            result.setdefault(item_id, []).append((annotation_id, processor, key))
        return result

    def find_annotations(
        self,
        scope: ProcessingScope | None = None,
        *,
        processor: str | None = None,
        key: str | None = None,
        annotation_ids: Iterable[int] | None = None,
        sort: str = "item",
    ) -> list[Annotation]:
        """Annotations of the items in scope, with their values, by an
        `ANNOTATION_SORTS` key. Every filter combines; `limit` counts
        annotations."""
        scope = scope or ProcessingScope()
        with self.session_scope() as sess:
            query = sess.query(DBItemAnnotation).join(
                DBSourceItem, DBItemAnnotation.source_item_id == DBSourceItem.id
            )
            query = self._apply_scope(query, scope)
            if processor is not None:
                query = query.filter(DBItemAnnotation.processor == processor)
            if key is not None:
                query = query.filter(DBItemAnnotation.key == key)
            if annotation_ids is not None:
                query = query.filter(DBItemAnnotation.id.in_(annotation_ids))
            query = query.order_by(*ANNOTATION_SORTS[sort], DBItemAnnotation.id)
            if scope.limit:
                query = query.limit(scope.limit)
            rows = [
                (
                    row.id,
                    row.source_item_id,
                    row.processor,
                    row.key,
                    row.updated_at,
                    row.content_sha256,
                )
                for row in query
            ]
        return [
            Annotation(
                id=annotation_id,
                item_id=item_id,
                processor=row_processor,
                key=row_key,
                updated_at=updated_at,
                value=self._load_value(sha256),
            )
            for annotation_id, item_id, row_processor, row_key, updated_at, sha256 in rows
        ]

    def get_annotation_values(
        self, items: Iterable[SourceItem], *, key: str
    ) -> dict[ItemKey, Any]:
        """One annotation's value per item, read in a single query.

        Items without that annotation are absent from the result.
        """
        keys = [item.key for item in items]
        if not keys:
            return {}
        with self.session_scope() as sess:
            rows = (
                sess.query(
                    DBSourceItem.source_id,
                    DBSourceItem.uid,
                    DBItemAnnotation.content_sha256,
                )
                .join(
                    DBItemAnnotation, DBItemAnnotation.source_item_id == DBSourceItem.id
                )
                .filter(
                    tuple_(DBSourceItem.source_id, DBSourceItem.uid).in_(keys),
                    DBItemAnnotation.key == key,
                )
                .all()
            )
        return {
            (source_id, uid): self._load_value(sha256)
            for source_id, uid, sha256 in rows
        }

    def delete_annotations(self, annotation_ids: Iterable[int]) -> int:
        """Delete the annotations with these ids, each with the processing
        state of its (item, key), so its run finds the item pending again.

        Returns the number of annotations deleted.
        """
        annotation_ids = list(annotation_ids)
        if not annotation_ids:
            return 0
        with self.session_scope() as sess:
            annotations = sess.query(DBItemAnnotation).filter(
                DBItemAnnotation.id.in_(annotation_ids)
            )
            rows = [
                (row.source_item_id, row.key, row.content_sha256) for row in annotations
            ]
            deleted = annotations.delete(synchronize_session=False)
            sess.query(DBProcessingState).filter(
                tuple_(DBProcessingState.source_item_id, DBProcessingState.key).in_(
                    [(item_id, key) for item_id, key, _ in rows]
                )
            ).delete(synchronize_session=False)

        self._release_contents({sha256 for _, _, sha256 in rows})
        return deleted

    def delete_items(self, item_ids: Iterable[int]) -> int:
        """Delete items with everything that references them (processing
        state, annotations) and release their contents; return how many were
        deleted. Documents built from them stay."""
        item_ids = list(item_ids)
        if not item_ids:
            return 0
        with self.session_scope() as sess:
            released = {
                sha256
                for (sha256,) in sess.query(DBSourceItem.content_sha256).filter(
                    DBSourceItem.id.in_(item_ids)
                )
            }
            released |= {
                sha256
                for (sha256,) in sess.query(DBItemAnnotation.content_sha256).filter(
                    DBItemAnnotation.source_item_id.in_(item_ids)
                )
            }
            # The foreign keys cascade to state and annotations.
            deleted = (
                sess.query(DBSourceItem)
                .filter(DBSourceItem.id.in_(item_ids))
                .delete(synchronize_session=False)
            )
        self._release_contents(released)
        return deleted

    # --- Applet runs -------------------------------------------------------

    def get_app_run(self, app: str) -> AppletRun:
        """The instance's run record; an empty one if it never ran."""
        with self.session_scope() as sess:
            row = sess.get(DBApp, app)
            return row.to_dto() if row is not None else AppletRun(app=app)

    def get_app_runs(self) -> dict[str, AppletRun]:
        """Every stored run record, by instance id."""
        with self.session_scope() as sess:
            return {row.id: row.to_dto() for row in sess.query(DBApp)}

    def start_app_run(self, app: str, started: datetime) -> None:
        """Record that a run of the instance started, in its own
        transaction."""
        with self.session_scope() as sess:
            row = sess.get(DBApp, app)
            if row is None:
                sess.add(DBApp.from_dto(AppletRun(app=app, last_started=started)))
            else:
                row.last_started = started

    def fail_app_run(self, app: str, error: str) -> None:
        """Record a failed run: only its error; state and times stay."""
        with self.session_scope() as sess:
            row = sess.get(DBApp, app)
            if row is None:
                sess.add(DBApp.from_dto(AppletRun(app=app, last_error=error)))
            else:
                row.last_error = error

    def existing_document_keys(
        self, app: str, keys: Iterable[tuple[str, str]]
    ) -> set[tuple[str, str]]:
        """The `(output, key)` pairs among `keys` the instance already
        stored."""
        keys = list(keys)
        if not keys:
            return set()
        with self.session_scope() as sess:
            rows = sess.query(DBDocument.output, DBDocument.key).filter(
                DBDocument.app == app,
                tuple_(DBDocument.output, DBDocument.key).in_(keys),
            )
            return {(output, key) for output, key in rows}

    @staticmethod
    def _missing_routes(
        sess: Session, document_id: int, sinks: Sequence[str]
    ) -> tuple[str, ...]:
        """The sinks among `sinks` the document has no row of."""
        present = {
            sink
            for (sink,) in sess.query(DBDelivery.sink).filter(
                DBDelivery.document_id == document_id
            )
        }
        return tuple(sink for sink in sinks if sink not in present)

    def count_missing_routes(
        self,
        app: str,
        keys: Iterable[tuple[str, str]],
        routes: Mapping[str, Sequence[str]],
    ) -> int:
        """How many rows `commit_app_run` would add for the documents among
        `keys` (`(output, key)`) the instance already stored."""
        keys = list(keys)
        if not keys:
            return 0
        with self.session_scope() as sess:
            rows = sess.query(DBDocument.id, DBDocument.output).filter(
                DBDocument.app == app,
                tuple_(DBDocument.output, DBDocument.key).in_(keys),
            )
            return sum(
                len(self._missing_routes(sess, document_id, routes.get(output, ())))
                for document_id, output in rows
            )

    def commit_app_run(
        self,
        app: str,
        started: datetime,
        result: AppletResult,
        routes: Mapping[str, Sequence[str]],
    ) -> CommittedRun:
        """Store a successful run in one transaction: its new documents, a
        `queued` delivery per route of each emitted document's output, its
        state, and `last_success = started`. A document whose key the
        instance already stored is not stored again; it only gets a row for
        each route it has none of (a route added since it was emitted).

        Contents are written first, so a failed commit leaves unused files,
        never rows pointing at nothing.
        """
        documents = [
            Document.from_emitted(app, emitted) for emitted in result.documents
        ]
        for document in documents:
            assert document.content is not None and document.content_sha256
            self.contents.set(document.content_sha256, document.content.encode())

        now = datetime.now(UTC)
        committed = CommittedRun()
        with self.session_scope() as sess:
            existing = {
                (output, key): document_id
                for document_id, output, key in sess.query(
                    DBDocument.id, DBDocument.output, DBDocument.key
                ).filter(DBDocument.app == app)
            }
            for document in documents:
                sinks = routes.get(document.output, ())
                document_id = existing.get((document.output, document.key))
                if document_id is None:
                    row = DBDocument.from_dto(
                        dataclasses.replace(document, emitted_at=now)
                    )
                    sess.add(row)
                    sess.flush()
                    document_id = row.id
                    existing[(document.output, document.key)] = document_id
                    committed.documents.append(
                        dataclasses.replace(document, emitted_at=now, id=row.id)
                    )
                else:
                    sinks = self._missing_routes(sess, document_id, sinks)
                    committed.routed += len(sinks)
                sess.add_all(
                    DBDelivery.from_dto(
                        Delivery(
                            sink=sink,
                            document_id=document_id,
                            status=DeliveryStatus.QUEUED,
                            created_at=now,
                            updated_at=now,
                        )
                    )
                    for sink in sinks
                )

            run = AppletRun(
                app=app,
                last_started=started,
                last_success=started,
                last_error=None,
                state=result.state,
            )
            row = sess.get(DBApp, app)
            if row is None:
                sess.add(DBApp.from_dto(run))
            else:
                row.update(run)
        return committed

    def reset_app(self, app: str, *, with_documents: bool = False) -> int:
        """Delete the instance's run record; with `with_documents`, also its
        documents with their deliveries. Returns how many documents were
        deleted."""
        with self.session_scope() as sess:
            sess.query(DBApp).filter(DBApp.id == app).delete(synchronize_session=False)
            if not with_documents:
                return 0
            ids = [
                document_id
                for (document_id,) in sess.query(DBDocument.id).filter(
                    DBDocument.app == app
                )
            ]
        return self.delete_documents(ids)

    # --- Documents ---------------------------------------------------------

    @staticmethod
    def _apply_document_filter(query: Query, selection: DocumentFilter) -> Query:
        if selection.app is not None:
            query = query.filter(DBDocument.app == selection.app)
        if selection.output is not None:
            query = query.filter(DBDocument.output == selection.output)
        if selection.key is not None:
            query = query.filter(DBDocument.key == selection.key)
        if selection.since is not None:
            query = query.filter(DBDocument.emitted_at >= selection.since)
        if selection.until is not None:
            query = query.filter(DBDocument.emitted_at < selection.until)
        if selection.document_ids is not None:
            query = query.filter(DBDocument.id.in_(selection.document_ids))
        return query

    def find_documents(
        self,
        selection: DocumentFilter | None = None,
        *,
        sort: str = "emitted",
        newest_first: bool = False,
        with_content: bool = False,
    ) -> list[Document]:
        """Documents by a `DOCUMENT_SORTS` key, ascending unless
        `newest_first`; `limit` keeps the first ones in that order. Contents
        only `with_content`."""
        selection = selection or DocumentFilter()
        columns = [*DOCUMENT_SORTS[sort], DBDocument.id]
        with self.session_scope() as sess:
            query = self._apply_document_filter(sess.query(DBDocument), selection)
            query = query.order_by(
                *(column.desc() if newest_first else column for column in columns)
            )
            if selection.limit:
                query = query.limit(selection.limit)
            documents = [row.to_dto() for row in query]
        if with_content:
            for document in documents:
                document.content = self.load_document_content(document)
        return documents

    def load_document_content(self, document: Document) -> str:
        """The document's stored content."""
        if document.content_sha256 is None:
            raise ValueError(f"document {document.label} has no content reference")
        return self.contents.get(document.content_sha256).decode()

    def delete_documents(self, document_ids: Iterable[int]) -> int:
        """Delete these documents with their deliveries and release their
        contents; return how many."""
        document_ids = list(document_ids)
        if not document_ids:
            return 0
        with self.session_scope() as sess:
            query = sess.query(DBDocument).filter(DBDocument.id.in_(document_ids))
            released = {row.content_sha256 for row in query}
            # The foreign key cascades to the deliveries.
            deleted = query.delete(synchronize_session=False)
        self._release_contents(released)
        return deleted

    # --- Deliveries --------------------------------------------------------

    def deliveries_of(
        self,
        sink: str | None = None,
        *,
        statuses: Iterable[DeliveryStatus] | None = None,
        delivery_ids: Iterable[int] | None = None,
    ) -> list[tuple[Delivery, Document]]:
        """Rows with their documents (no content), oldest document first:
        the delivery order."""
        with self.session_scope() as sess:
            query = sess.query(DBDelivery, DBDocument).join(
                DBDocument, DBDelivery.document_id == DBDocument.id
            )
            if sink is not None:
                query = query.filter(DBDelivery.sink == sink)
            if statuses is not None:
                query = query.filter(DBDelivery.status.in_(list(statuses)))
            if delivery_ids is not None:
                query = query.filter(DBDelivery.id.in_(list(delivery_ids)))
            query = query.order_by(DBDocument.emitted_at, DBDocument.id)
            return [(row.to_dto(), document.to_dto()) for row, document in query]

    def add_deliveries(self, deliveries: Iterable[Delivery]) -> int:
        """Store these new rows, stamped now; return how many."""
        now = datetime.now(UTC)
        rows = [
            DBDelivery.from_dto(
                dataclasses.replace(delivery, created_at=now, updated_at=now)
            )
            for delivery in deliveries
        ]
        with self.session_scope() as sess:
            sess.add_all(rows)
        return len(rows)

    def save_delivery(self, delivery: Delivery) -> None:
        """Store a row's new state, stamped now, in its own transaction."""
        if delivery.id is None:
            raise ValueError("only stored deliveries can be saved")
        delivery.updated_at = datetime.now(UTC)
        with self.session_scope() as sess:
            sess.get_one(DBDelivery, delivery.id).update(delivery)

    def last_delivered_at(self, sink: str) -> datetime | None:
        """When the sink instance last delivered anything, if ever."""
        with self.session_scope() as sess:
            # order_by, not func.max(), which would bypass UTCDateTime.
            row = (
                sess.query(DBDelivery.updated_at)
                .filter(
                    DBDelivery.sink == sink,
                    DBDelivery.status == DeliveryStatus.DONE,
                )
                .order_by(DBDelivery.updated_at.desc())
                .first()
            )
        return None if row is None else row[0]

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
        """Rows by a `DELIVERY_SORTS` key (`id` is creation order), of the
        documents `documents` selects; filters combine and `limit` counts
        rows."""
        documents = documents or DocumentFilter()
        with self.session_scope() as sess:
            query = sess.query(DBDelivery).join(
                DBDocument, DBDelivery.document_id == DBDocument.id
            )
            query = self._apply_document_filter(query, documents)
            if sink is not None:
                query = query.filter(DBDelivery.sink == sink)
            if status is not None:
                query = query.filter(DBDelivery.status == status)
            if delivery_ids is not None:
                query = query.filter(DBDelivery.id.in_(list(delivery_ids)))
            query = query.order_by(*DELIVERY_SORTS[sort], DBDelivery.id)
            if limit:
                query = query.limit(limit)
            return [row.to_dto() for row in query]

    def delete_deliveries(self, delivery_ids: Iterable[int]) -> int:
        """Delete the rows with these ids; return how many."""
        delivery_ids = list(delivery_ids)
        if not delivery_ids:
            return 0
        with self.session_scope() as sess:
            return (
                sess.query(DBDelivery)
                .filter(DBDelivery.id.in_(delivery_ids))
                .delete(synchronize_session=False)
            )

    def count_sink_deliveries(self, sink: str) -> int:
        """How many ledger rows the sink instance has."""
        with self.session_scope() as sess:
            return sess.query(DBDelivery).filter(DBDelivery.sink == sink).count()

    def rename_sink(self, old: str, new: str) -> int:
        """Move the ledger rows of sink instance `old` to `new`; return how
        many. The unique (sink, document) rule rejects it if `new` already
        has a row for one of the documents."""
        with self.session_scope() as sess:
            return (
                sess.query(DBDelivery)
                .filter(DBDelivery.sink == old)
                .update({DBDelivery.sink: new}, synchronize_session=False)
            )
