from __future__ import annotations

import dataclasses
import functools
import json
import logging
import sys
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import click as plain_click
import rich_click
from click.core import ParameterSource
from foundation.clilib import (
    RICH_STDERR_DISABLED,
    RICH_STDOUT_DISABLED,
    RICH_STDOUT_ENABLED,
    click_logging_options,
    get_stderr_console,
    get_stdout_console,
)
from foundation.loglib import setup_logger_from_click
from foundation.plugin import PluginError
from foundation.storage import EntryNotFoundError
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.syntax import Syntax
from rich.table import Table

from .app import Application, AppReport, LockedError
from .applets import WEEKDAYS, Schedule
from .config import DEFAULT_WORKFLOW, Config, ConfigError
from .consts import PACKAGE_NAME
from .db import (
    ANNOTATION_SORTS,
    DELIVERY_SORTS,
    DOCUMENT_SORTS,
    ITEM_SORTS,
    DeliveryStatus,
)
from .errors import EXPECTED_ERRORS, describe, log_failure
from .models import Delivery, DocumentFilter, ProcessingScope, SourceItem
from .processors import RunSummary
from .sinks import PacingOverride

# Help goes to stdout: rich only when stdout is a terminal.
click = plain_click if RICH_STDOUT_DISABLED else rich_click

LOGGER = logging.getLogger(PACKAGE_NAME)

# Errors a user can fix (bad config, unknown plugin...): reported without a traceback.
USER_ERRORS = (ConfigError, PluginError, LockedError)


def report_user_errors[**P, R](command: Callable[P, R]) -> Callable[P, R]:
    @functools.wraps(command)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return command(*args, **kwargs)
        except USER_ERRORS as e:
            raise click.ClickException(str(e)) from e
        except EXPECTED_ERRORS as e:
            if LOGGER.isEnabledFor(logging.DEBUG):
                raise
            raise click.ClickException(describe(e)) from e

    return wrapper


def setup_logging(log_options: dict[str, Any], default_log_level: str) -> None:
    """Configure the package logger from the global options, falling back to
    NEWSTOOL_LOG_LEVEL, then to `default_log_level`."""
    # Logs go through foundation's shared stderr console, the same one the
    # progress bars use, so live progress redraws around log records; plain
    # lines when stderr is not a terminal.
    setup_logger_from_click(
        PACKAGE_NAME, **log_options, default_log_level=default_log_level
    )


def app_from_context(ctx: click.Context, *, write: bool = False) -> Application:
    """Build the Application for this invocation and close it when the command
    ends. Commands that `write` hold the write lock until then.

    Logging is set up here, between loading the config, which may set its
    level, and building the Application, which already logs."""
    config_path = ctx.obj["config_path"]
    config = Config.from_file(config_path) if config_path else Config()
    setup_logging(ctx.obj["log_options"], config.log_level)
    app = Application(config)
    ctx.call_on_close(app.close)
    if write:
        app.lock()
    return app


@contextmanager
def progress_rows() -> Iterator[Progress]:
    """Phase and unit rows on stderr, off when stderr is not a terminal.

    stdout is not redirected through the live display, so tables still reach
    a redirected stdout; print them after the rows end, or they would break
    the redraw on a shared terminal."""
    progress = Progress(
        SpinnerColumn(finished_text="✔"),
        TextColumn("{task.description}"),
        TimeElapsedColumn(),
        console=get_stderr_console(),
        disable=RICH_STDERR_DISABLED,
        redirect_stdout=False,
    )
    with progress:
        yield progress


def run_each[T](
    progress: Progress,
    names: Iterable[str],
    run: Callable[[str], T],
    on_error: Callable[[str, Exception], T],
) -> dict[str, T]:
    """Run each unit by name with its own row, removed when it ends. A unit
    that raises is logged and gets `on_error`'s result, so the summary
    reports it and the units after it still run."""
    results = {}
    for name in names:
        row = progress.add_task(name, total=None)
        try:
            results[name] = run(name)
        except Exception as e:  # noqa: BLE001
            log_failure(LOGGER, f"{name}: failed", e)
            results[name] = on_error(name, e)
        finally:
            progress.remove_task(row)
    return results


def failed_summary(name: str, exc: Exception) -> RunSummary:
    """The summary of a process or delivery run that raised: one failure."""
    return RunSummary(failed=1)


def print_table(title: str, headers: list[str], rows: list[list[Any]]) -> None:
    if RICH_STDOUT_DISABLED:
        print(title)
        for row in rows:
            print("\t".join(str(cell) for cell in row))
        return

    table = Table(title=title)
    for header in headers:
        table.add_column(header, overflow="fold")  # ids and URIs stay whole
    for row in rows:
        table.add_row(*(str(cell) for cell in row))
    get_stdout_console().print(table)


def scope_options[**P, R](command: Callable[P, R]) -> Callable[P, R]:
    """Add --source/--since/--until/--item/--limit, passed to the command as `scope`."""

    @click.option("--source", default=None, help="Limit to one source id")
    @click.option(
        "--since",
        type=click.DateTime(),
        default=None,
        help="Published at or after (UTC)",
    )
    @click.option(
        "--until", type=click.DateTime(), default=None, help="Published before (UTC)"
    )
    @click.option(
        "--item", "item_ids", type=int, multiple=True, help="Item id (repeatable)"
    )
    @click.option("--limit", type=int, default=None, help="At most this many items")
    @functools.wraps(command)
    def wrapper(
        *args: Any,
        source: str | None,
        since: datetime | None,
        until: datetime | None,
        item_ids: tuple[int, ...],
        limit: int | None,
        **kwargs: Any,
    ) -> R:
        scope = ProcessingScope(
            source=source,
            since=since.replace(tzinfo=UTC) if since else None,
            until=until.replace(tzinfo=UTC) if until else None,
            item_ids=item_ids or None,
            limit=limit,
        )
        return command(*args, scope=scope, **kwargs)

    return wrapper


def document_options[**P, R](command: Callable[P, R]) -> Callable[P, R]:
    """Add --app/--output/--key/--since/--until/--document/--limit, passed to
    the command as `documents`."""

    @click.option("--app", "app_id", default=None, help="Only this applet instance's")
    @click.option("--output", default=None, help="Only this output's")
    @click.option("--key", default=None, help="Only the documents with this key")
    @click.option(
        "--since", type=click.DateTime(), default=None, help="Emitted at or after (UTC)"
    )
    @click.option(
        "--until", type=click.DateTime(), default=None, help="Emitted before (UTC)"
    )
    @click.option(
        "--document",
        "document_ids",
        type=int,
        multiple=True,
        help="Document id (repeatable)",
    )
    @click.option("--limit", type=int, default=None, help="At most this many")
    @functools.wraps(command)
    def wrapper(
        *args: Any,
        app_id: str | None,
        output: str | None,
        key: str | None,
        since: datetime | None,
        until: datetime | None,
        document_ids: tuple[int, ...],
        limit: int | None,
        **kwargs: Any,
    ) -> R:
        documents = DocumentFilter(
            app=app_id,
            output=output,
            key=key,
            since=since.replace(tzinfo=UTC) if since else None,
            until=until.replace(tzinfo=UTC) if until else None,
            document_ids=document_ids or None,
            limit=limit,
        )
        return command(*args, documents=documents, **kwargs)

    return wrapper


workflow_option = click.option(
    "-w",
    "--workflow",
    default=DEFAULT_WORKFLOW,
    show_default=True,
    help="The workflow to run",
)

dry_run_option = click.option(
    "--dry-run", is_flag=True, help="Show what would be done, changing nothing"
)


@click.group()
@click.option("-c", "--config", "config_path", type=Path, default=None)
@click_logging_options
@click.pass_context
def cli(
    ctx: click.Context,
    config_path: Path | None,
    log_level: str | None,
    verbose: int,
    quiet: int,
) -> None:
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config_path
    ctx.obj["log_options"] = {
        "log_level": log_level,
        "verbose": verbose,
        "quiet": quiet,
    }


def import_sources(
    app: Application, progress: Progress, workflow: str
) -> list[list[Any]]:
    """Import every source of the workflow, a row each; return the summary
    rows (source, items, error)."""

    def import_one(source_id: str) -> list[Any]:
        return [source_id, len(app.import_source(source_id)), ""]

    def import_failed(source_id: str, exc: Exception) -> list[Any]:
        return [source_id, "-", describe(exc)]

    sources = [source.id for source in app.sources(workflow)]
    return list(run_each(progress, sources, import_one, import_failed).values())


def print_import(rows: list[list[Any]], title: str = "Import") -> int:
    """Print the import summary; return how many sources failed."""
    print_table(title, ["Source", "Items", "Error"], rows)
    return sum(1 for _, _, error in rows if error)


def print_process(summaries: dict[str, RunSummary], title: str = "Process") -> int:
    """Print the process summary; return how many items failed."""
    print_table(
        title,
        ["Key", "Done", "Ignored", "Failed"],
        [[name, s.done, s.ignored, s.failed] for name, s in summaries.items()],
    )
    return sum(s.failed for s in summaries.values())


def print_apps(reports: dict[str, AppReport]) -> int:
    """Print the applet runs' summary; return how many failed."""
    print_table(
        "Apps",
        ["App", "Due", "New", "Already stored", "Routed", "Error"],
        [
            [
                name,
                "yes" if r.due else "no",
                len(r.new) if r.due else "-",
                len(r.ignored) if r.due else "-",
                r.routed if r.due else "-",
                r.error or "",
            ]
            for name, r in reports.items()
        ],
    )
    return sum(1 for r in reports.values() if r.error)


def print_deliver(summaries: dict[str, RunSummary]) -> int:
    """Print the deliver summary; return how many deliveries failed."""
    print_table(
        "Deliver",
        ["Sink", "Delivered", "Failed"],
        [[name, s.done, s.failed] for name, s in summaries.items()],
    )
    return sum(s.failed for s in summaries.values())


@cli.command("import")
@workflow_option
@click.pass_context
@report_user_errors
def import_cmd(ctx: click.Context, workflow: str) -> None:
    """Import every source of the workflow."""
    app = app_from_context(ctx, write=True)
    with progress_rows() as progress:
        rows = import_sources(app, progress, workflow)
    if failed := print_import(rows):
        raise click.ClickException(f"{failed} source(s) failed")


@cli.command("process")
@click.argument("processor", required=False)
@workflow_option
@scope_options
@click.option(
    "--force",
    is_flag=True,
    help="Reprocess everything in scope, ignored items included, with fresh attempts",
)
@click.pass_context
@report_user_errors
def process_cmd(
    ctx: click.Context,
    processor: str | None,
    workflow: str,
    scope: ProcessingScope,
    force: bool,
) -> None:
    """Run every process run of the workflow in order, or only
    PROCESSOR's."""
    app = app_from_context(ctx, write=True)
    with progress_rows() as progress:
        summaries = run_each(
            progress,
            app.process_keys(processor, workflow=workflow),
            lambda key: app.run_process(
                key, workflow=workflow, scope=scope, force=force
            ),
            failed_summary,
        )
    if failed := print_process(summaries):
        raise click.ClickException(f"{failed} failure(s); see the log above")


# (phase, run under the progress rows, print its summary and count failures)
type Phase = tuple[str, Callable[[Progress], Any], Callable[[Any], int]]


def workflow_phases(app: Application, workflow: str, labelled: bool) -> list[Phase]:
    """The import and process phases of `run` for one workflow; labelled
    phases and summaries name the workflow."""
    prefix = f"{workflow}: " if labelled else ""
    suffix = f" ({workflow})" if labelled else ""
    return [
        (
            f"{prefix}import",
            lambda progress: import_sources(app, progress, workflow),
            lambda rows: print_import(rows, title=f"Import{suffix}"),
        ),
        (
            f"{prefix}process",
            lambda progress: run_each(
                progress,
                app.process_keys(workflow=workflow),
                lambda key: app.run_process(key, workflow=workflow),
                failed_summary,
            ),
            lambda summaries: print_process(summaries, title=f"Process{suffix}"),
        ),
    ]


@cli.command("run")
@workflow_option
@click.option(
    "--all",
    "all_workflows",
    is_flag=True,
    help="Run every workflow, `default` first",
)
@click.pass_context
@report_user_errors
def run_cmd(ctx: click.Context, workflow: str, all_workflows: bool) -> None:
    """Run the workflow's import and process in turn, or every workflow's
    with --all; `apps run` runs the applets and delivers.

    A failure is logged and the next phase still runs; the exit status is
    non-zero if anything failed.
    """
    if all_workflows and (
        ctx.get_parameter_source("workflow") is not ParameterSource.DEFAULT
    ):
        raise click.UsageError("--all and --workflow exclude each other")
    app = app_from_context(ctx, write=True)
    failures = 0

    workflows = app.workflows if all_workflows else [workflow]
    phases = [
        phase
        for name in workflows
        for phase in workflow_phases(app, name, labelled=all_workflows)
    ]
    results = []
    with progress_rows() as progress:
        for number, (phase, run_phase, print_summary) in enumerate(phases, start=1):
            description = f"{phase} ({number}/{len(phases)})"
            row = progress.add_task(description, total=1)
            try:
                results.append((print_summary, run_phase(progress)))
            except Exception as e:  # noqa: BLE001
                log_failure(LOGGER, f"{phase} failed", e)
                failures += 1
                progress.update(row, description=f"{description} failed")
            progress.update(row, completed=1)

    for print_summary, result in results:
        failures += print_summary(result)
    if failures:
        raise click.ClickException(f"{failures} failure(s); see the log above")


def match_snippet(text: str, query: str, width: int = 60) -> str | None:
    """The text around the first case-insensitive match, on one line."""
    start = text.casefold().find(query.casefold())
    if start < 0:
        return None
    snippet = text[max(start - width, 0) : start + len(query) + width]
    return " ".join(snippet.split())


@cli.command("search")
@click.argument("query")
@scope_options
@click.pass_context
@report_user_errors
def search_cmd(ctx: click.Context, query: str, scope: ProcessingScope) -> None:
    """Items whose markdownify text contains QUERY (case-insensitive).

    --limit counts the items searched, not the matches.
    """
    app = app_from_context(ctx)
    items = app.get_items(scope)
    # shortcut: loads every markdown from disk, add an index if it gets slow
    markdowns = app.get_annotation_values(items, key="markdown")
    rows = []
    for item in items:
        snippet = match_snippet(markdowns.get(item.key, ""), query)
        if snippet is not None:
            rows.append([item.id, item.source.id, item.title, snippet])
    print_table("Matches", ["ID", "Source", "Title", "Match"], rows)


# --- Inspection -------------------------------------------------------------

PREVIEW_LENGTH = 80


def format_value(value: Any) -> str:
    """An annotation value as text: strings as they are, the rest as JSON."""
    if isinstance(value, str):
        return value
    return json.dumps(value, indent=2, ensure_ascii=False, default=str)


def preview(value: Any) -> str:
    """One line of the value: the first line of text, or compact JSON."""
    if isinstance(value, str):
        lines = value.splitlines()
    else:
        lines = [json.dumps(value, ensure_ascii=False, default=str)]
    first = lines[0] if lines else ""
    if len(lines) > 1 or len(first) > PREVIEW_LENGTH:
        return first[: PREVIEW_LENGTH - 1] + "…"
    return first


def lexer_for(content_type: str) -> str | None:
    for marker in ("json", "xml", "html"):
        if marker in content_type:
            return marker
    return None


def json_default(value: Any) -> str:
    return value.isoformat() if isinstance(value, datetime) else str(value)


def print_json(records: list[dict[str, Any]]) -> None:
    click.echo(json.dumps(records, indent=2, ensure_ascii=False, default=json_default))


def check_found(kind: str, requested: Iterable[Any], found: Iterable[Any]) -> None:
    """Fail on explicitly requested ids the selection did not return."""
    if missing := set(requested) - set(found):
        listed = ", ".join(sorted(str(id_) for id_ in missing))
        raise click.ClickException(f"no {kind} {listed} in the selection")


def annotation_options[**P, R](command: Callable[P, R]) -> Callable[P, R]:
    """Add --processor/--key/--annotation, which narrow an item selection."""
    command = click.option(
        "--annotation",
        "annotation_ids",
        type=int,
        multiple=True,
        help="Annotation id (repeatable)",
    )(command)
    command = click.option("--key", default=None, help="Only this key")(command)
    return click.option(
        "--processor", default=None, help="Only this processor's annotations"
    )(command)


def delivery_options[**P, R](command: Callable[P, R]) -> Callable[P, R]:
    """Add the document filters, --delivery, --sink and --status, which
    select ledger rows."""
    command = click.option(
        "--status",
        type=click.Choice([status.value for status in DeliveryStatus]),
        default=None,
        help="Only deliveries in this state",
    )(command)
    command = click.option(
        "--sink", default=None, help="Only this sink instance's deliveries"
    )(command)
    command = click.option(
        "--delivery",
        "delivery_ids",
        type=int,
        multiple=True,
        help="Delivery id (repeatable)",
    )(command)
    return document_options(command)


def select_deliveries(
    app: Application,
    documents: DocumentFilter,
    delivery_ids: tuple[int, ...],
    sink: str | None,
    status: str | None,
    sort: str,
) -> list[Delivery]:
    """The ledger rows the `delivery_options` select, `--limit` counting
    rows; an explicit delivery id outside the selection is an error."""
    deliveries = app.find_deliveries(
        dataclasses.replace(documents, limit=None),
        sink=sink,
        status=DeliveryStatus(status) if status else None,
        delivery_ids=delivery_ids or None,
        limit=documents.limit,
        sort=sort,
    )
    if documents.limit is None:
        check_found("delivery", delivery_ids, (d.id for d in deliveries))
    return deliveries


def sort_option(
    keys: Iterable[str], default: str = "updated"
) -> Callable[[Callable], Callable]:
    """--sort among `keys`, oldest (or smallest) first; `default` when not
    given. It also decides which rows --limit keeps."""
    return click.option(
        "--sort",
        type=click.Choice(sorted(keys)),
        default=default,
        show_default=True,
        help="Sort key, ascending (oldest first for dates)",
    )


format_option = click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)


def print_content(content: str, content_type: str) -> None:
    """Content to stdout as is, highlighted on a terminal."""
    lexer = lexer_for(content_type)
    if RICH_STDOUT_ENABLED and lexer:
        get_stdout_console().print(Syntax(content, lexer))
    else:
        sys.stdout.write(content)


@cli.group("inspect")
def inspect_group() -> None:
    """Show what is stored (read-only)."""


def print_item(item: SourceItem, annotations: list[tuple[int, str, str]]) -> None:
    """One item as field/value rows, one row per annotation."""
    dates = (item.published_at, item.modified_at, item.imported_at)
    published, modified, imported = (f"{d:%Y-%m-%d %H:%M}" if d else "" for d in dates)
    print_table(
        f"Item {item.id}",
        ["Field", "Value"],
        [
            ["Source", item.source.id],
            ["UID", item.uid],
            ["Title", item.title],
            ["URI", item.uri],
            ["Published", published],
            ["Modified", modified],
            ["Imported", imported],
            ["Mimetype", item.mimetype],
            ["Content", f"inspect content --sha256 {item.content_sha256}"],
            ["Data", format_value(item.data)],
            *(
                [f"Annotation #{annotation_id}", f"{processor}.{key}"]
                for annotation_id, processor, key in annotations
            ),
        ],
    )


@inspect_group.command("items")
@scope_options
@sort_option(ITEM_SORTS)
@format_option
@click.pass_context
@report_user_errors
def inspect_items_cmd(
    ctx: click.Context, scope: ProcessingScope, sort: str, output_format: str
) -> None:
    """Items in scope, with the ids and keys of their annotations.

    One --item in table format shows all its fields, one row per annotation.
    """
    app = app_from_context(ctx)
    items = app.get_items(scope, sort=sort)
    if scope.limit is None:  # with a limit, a requested item may just be cut off
        check_found("item", scope.item_ids or (), (item.id for item in items))
    annotations = app.get_annotation_keys(item.id for item in items)

    if output_format == "json":
        print_json(
            [
                {
                    "id": item.id,
                    "source": item.source.id,
                    "uid": item.uid,
                    "title": item.title,
                    "uri": item.uri,
                    "mimetype": item.mimetype,
                    "content_sha256": item.content_sha256,
                    "data": item.data,
                    "published_at": item.published_at,
                    "modified_at": item.modified_at,
                    "imported_at": item.imported_at,
                    "annotations": [
                        {"id": annotation_id, "processor": processor, "key": key}
                        for annotation_id, processor, key in annotations.get(
                            item.id, []
                        )
                    ],
                }
                for item in items
            ]
        )
        return

    if len(scope.item_ids or ()) == 1 and items:
        print_item(items[0], annotations.get(items[0].id, []))
        return

    print_table(
        "Items",
        ["ID", "Source", "Published", "Title", "Annotations"],
        [
            [
                item.id,
                item.source.id,
                f"{item.published_at:%Y-%m-%d %H:%M}",
                item.title,
                "\n".join(
                    f"{annotation_id} {processor}.{key}"
                    for annotation_id, processor, key in annotations.get(item.id, [])
                ),
            ]
            for item in items
        ],
    )


@inspect_group.command("annotations")
@scope_options
@annotation_options
@sort_option(ANNOTATION_SORTS)
@format_option
@click.pass_context
@report_user_errors
def inspect_annotations_cmd(
    ctx: click.Context,
    scope: ProcessingScope,
    processor: str | None,
    key: str | None,
    annotation_ids: tuple[int, ...],
    sort: str,
    output_format: str,
) -> None:
    """Annotations of the items in scope; --limit counts annotations.

    One --annotation in table format prints its full value (text as is, the
    rest as JSON) to stdout and its metadata to stderr.
    """
    annotations = app_from_context(ctx).find_annotations(
        scope,
        processor=processor,
        key=key,
        annotation_ids=annotation_ids or None,
        sort=sort,
    )
    if scope.limit is None:
        check_found("annotation", annotation_ids, (a.id for a in annotations))

    if output_format == "json":
        print_json([dataclasses.asdict(annotation) for annotation in annotations])
    elif len(annotation_ids) == 1:
        (annotation,) = annotations
        click.echo(
            f"{annotation.id} · item {annotation.item_id} · "
            f"{annotation.processor}.{annotation.key} · "
            f"updated {annotation.updated_at:%Y-%m-%d %H:%M}",
            err=True,
        )
        click.echo(format_value(annotation.value))
    else:
        print_table(
            "Annotations",
            ["ID", "Item", "Processor.Key", "Updated", "Value"],
            [
                [
                    a.id,
                    a.item_id,
                    f"{a.processor}.{a.key}",
                    f"{a.updated_at:%Y-%m-%d %H:%M}",
                    preview(a.value),
                ]
                for a in annotations
            ],
        )


@inspect_group.command("documents")
@document_options
@sort_option(DOCUMENT_SORTS, "emitted")
@format_option
@click.pass_context
@report_user_errors
def inspect_documents_cmd(
    ctx: click.Context, documents: DocumentFilter, sort: str, output_format: str
) -> None:
    """Documents the applet instances emitted. Contents are loaded only for
    --document.

    One --document in table format prints its content to stdout and its
    metadata to stderr, so it can be redirected.
    """
    app = app_from_context(ctx)
    with_content = bool(documents.document_ids)
    found = app.find_documents(documents, sort=sort, with_content=with_content)
    if documents.limit is None:
        check_found("document", documents.document_ids or (), (d.id for d in found))

    if output_format == "json":
        records = []
        for document in found:
            record = dataclasses.asdict(document)
            if not with_content:
                del record["content"]
            records.append(record)
        print_json(records)
    elif len(documents.document_ids or ()) == 1 and found:
        (document,) = found
        click.echo(
            f"{document.id} · {document.label} · {document.content_type} · "
            f"emitted {document.emitted_at:%Y-%m-%d %H:%M}",
            err=True,
        )
        print_content(document.content or "", document.content_type)
    else:
        print_table(
            "Documents",
            ["ID", "App", "Output", "Key", "Type", "Emitted", "Title"],
            [
                [
                    d.id,
                    d.app,
                    d.output,
                    d.key,
                    d.content_type,
                    f"{d.emitted_at:%Y-%m-%d %H:%M}",
                    d.title or "",
                ]
                for d in found
            ],
        )


def format_seconds(seconds: float) -> str:
    """A duration as the config writes it: `3d`, `2h`, `5m` or `90s`."""
    for unit, size in (("d", 86400), ("h", 3600), ("m", 60)):
        if seconds and seconds % size == 0:
            return f"{int(seconds // size)}{unit}"
    return f"{seconds:g}s"


def describe_schedule(schedule: Schedule) -> str:
    """The schedule as the config writes it; `always` when unrestricted."""
    parts = []
    if schedule.every:
        parts.append(f"every {format_seconds(schedule.every)}")
    if schedule.days:
        parts.append("days " + ",".join(WEEKDAYS[day] for day in sorted(schedule.days)))
    if schedule.at is not None:
        parts.append(f"at {schedule.at:%H:%M}")
    return " ".join(parts) or "always"


def format_time(moment: datetime | None) -> str:
    return f"{moment.astimezone():%Y-%m-%d %H:%M}" if moment else ""


@inspect_group.command("apps")
@format_option
@click.pass_context
@report_user_errors
def inspect_apps_cmd(ctx: click.Context, output_format: str) -> None:
    """The applet instances: their schedule, last runs and next due time,
    in local time."""
    statuses = app_from_context(ctx).app_status(datetime.now(UTC))
    if output_format == "json":
        print_json(
            [
                {
                    "id": status.instance.id,
                    "app": status.instance.profile.name,
                    "schedule": describe_schedule(status.instance.schedule),
                    "routes": dict(status.instance.routes),
                    "last_started": status.run.last_started,
                    "last_success": status.run.last_success,
                    "last_error": status.run.last_error,
                    "next_due": status.next_due,
                    "state": status.run.state,
                }
                for status in statuses
            ]
        )
        return
    print_table(
        "Apps",
        ["ID", "App", "Schedule", "Last started", "Last success", "Next due", "Error"],
        [
            [
                status.instance.id,
                status.instance.profile.name,
                describe_schedule(status.instance.schedule),
                format_time(status.run.last_started),
                format_time(status.run.last_success),
                format_time(status.next_due),
                preview(status.run.last_error or ""),
            ]
            for status in statuses
        ],
    )


@inspect_group.command("content")
@click.option("--sha256", required=True, help="The content's sha256")
@click.pass_context
@report_user_errors
def inspect_content_cmd(ctx: click.Context, sha256: str) -> None:
    """Stored content (of an item, annotation or document) as is, to stdout."""
    try:
        content = app_from_context(ctx).get_stored_content(sha256)
    except EntryNotFoundError as e:
        raise click.ClickException(f"no content {sha256}") from e
    click.echo(content, nl=False)


@inspect_group.command("deliveries")
@delivery_options
@sort_option(DELIVERY_SORTS)
@format_option
@click.pass_context
@report_user_errors
def inspect_deliveries_cmd(
    ctx: click.Context,
    documents: DocumentFilter,
    delivery_ids: tuple[int, ...],
    sink: str | None,
    status: str | None,
    sort: str,
    output_format: str,
) -> None:
    """The delivery ledger; --limit counts rows."""
    deliveries = select_deliveries(
        app_from_context(ctx), documents, delivery_ids, sink, status, sort
    )

    if output_format == "json":
        print_json([dataclasses.asdict(delivery) for delivery in deliveries])
        return

    print_table(
        "Deliveries",
        ["ID", "Sink", "Document", "Status", "Attempts", "Updated", "Error"],
        [
            [
                d.id,
                d.sink,
                f"{d.document_id} {d.document_label}",
                d.status,
                d.attempts,
                f"{d.updated_at:%Y-%m-%d %H:%M}",
                preview(d.last_error or ""),
            ]
            for d in deliveries
        ],
    )


# --- Deletion ---------------------------------------------------------------


def require_selection(*filters: object, action: str = "delete") -> None:
    """Refuse a selection that names no filter or id: it would match all."""
    if not any(filters):
        raise click.UsageError(f"name a filter or an id to select what to {action}")


def delivery_filters(
    documents: DocumentFilter,
    delivery_ids: tuple[int, ...],
    sink: str | None,
    status: str | None,
) -> tuple[object, ...]:
    """What a `delivery_options` selection names, for `require_selection`."""
    return (documents.is_set(), delivery_ids, sink, status)


def check_all_rows(
    all_rows: bool,
    documents: DocumentFilter,
    delivery_ids: tuple[int, ...],
    status: str | None,
) -> None:
    """`--all` takes --sink only."""
    if all_rows and (documents.is_set() or delivery_ids or status):
        raise click.UsageError("--all takes no filter or id but --sink")


@cli.group("delete")
def delete_group() -> None:
    """Delete stored data, without asking. `inspect` with the same options
    lists what would be deleted."""


@delete_group.command("items")
@scope_options
@sort_option(ITEM_SORTS)
@click.pass_context
@report_user_errors
def delete_items_cmd(ctx: click.Context, scope: ProcessingScope, sort: str) -> None:
    """Delete items with their processing state and annotations.

    An item still in its source's index comes back on the next import, with
    a new id. Documents built from them stay.
    """
    require_selection(scope.source, scope.since, scope.until, scope.item_ids)
    app = app_from_context(ctx, write=True)
    items = app.get_items(scope, sort=sort)
    if scope.limit is None:
        check_found("item", scope.item_ids or (), (item.id for item in items))
    deleted = app.delete_items(item.id for item in items)
    click.echo(f"Deleted {deleted} item(s)")


@delete_group.command("annotations")
@scope_options
@annotation_options
@sort_option(ANNOTATION_SORTS)
@click.pass_context
@report_user_errors
def delete_annotations_cmd(
    ctx: click.Context,
    scope: ProcessingScope,
    processor: str | None,
    key: str | None,
    annotation_ids: tuple[int, ...],
    sort: str,
) -> None:
    """Delete annotations with their processing state, so the run that
    wrote each key finds its item pending again; --limit counts annotations.
    """
    require_selection(
        scope.source,
        scope.since,
        scope.until,
        scope.item_ids,
        processor,
        key,
        annotation_ids,
    )
    app = app_from_context(ctx, write=True)
    annotations = app.find_annotations(
        scope,
        processor=processor,
        key=key,
        annotation_ids=annotation_ids or None,
        sort=sort,
    )
    if scope.limit is None:
        check_found("annotation", annotation_ids, (a.id for a in annotations))

    deleted = app.delete_annotations(a.id for a in annotations)
    click.echo(f"Deleted {deleted} annotation(s); their items are pending again")


@delete_group.command("documents")
@document_options
@sort_option(DOCUMENT_SORTS, "emitted")
@click.pass_context
@report_user_errors
def delete_documents_cmd(
    ctx: click.Context, documents: DocumentFilter, sort: str
) -> None:
    """Delete documents with their deliveries.

    A document with a delivery that is not `done` is refused. Deleting a
    document frees its key: an applet that emits it again stores it anew.
    """
    require_selection(documents.is_set())
    app = app_from_context(ctx, write=True)
    found = app.find_documents(documents, sort=sort)
    if documents.limit is None:
        check_found("document", documents.document_ids or (), (d.id for d in found))
    summary = app.delete_documents(d.id for d in found if d.id is not None)
    for document_id in summary.refused:
        click.echo(
            f"Refused document {document_id}: it has deliveries not `done`",
            err=True,
        )
    click.echo(f"Deleted {summary.deleted} document(s)")


@delete_group.command("deliveries")
@delivery_options
@sort_option(DELIVERY_SORTS)
@click.option(
    "--all",
    "all_rows",
    is_flag=True,
    help="Every row, or every row of --sink; takes no other filter",
)
@click.pass_context
@report_user_errors
def delete_deliveries_cmd(
    ctx: click.Context,
    documents: DocumentFilter,
    delivery_ids: tuple[int, ...],
    sink: str | None,
    status: str | None,
    sort: str,
    all_rows: bool,
) -> None:
    """Delete ledger rows; --limit counts rows.

    Their documents are not delivered again unless `deliveries set-status`
    creates rows for them.
    """
    check_all_rows(all_rows, documents, delivery_ids, status)
    if not all_rows:
        require_selection(*delivery_filters(documents, delivery_ids, sink, status))
    app = app_from_context(ctx, write=True)
    deliveries = select_deliveries(app, documents, delivery_ids, sink, status, sort)
    deleted = app.delete_deliveries(d.id for d in deliveries if d.id is not None)
    click.echo(f"Deleted {deleted} delivery(ies)")


# --- Deliveries -------------------------------------------------------------


@cli.group("deliveries")
def deliveries_group() -> None:
    """Change the state of ledger rows, or send them now."""


@deliveries_group.command("set-status")
@delivery_options
@sort_option(DELIVERY_SORTS)
@click.option(
    "--as",
    "target",
    type=click.Choice(
        [s.value for s in DeliveryStatus if s is not DeliveryStatus.SENDING]
    ),
    required=True,
    help="The new state; `queued` also gives fresh attempts",
)
@click.option(
    "--all",
    "all_rows",
    is_flag=True,
    help="With --sink, every document routed to it; without it, every row."
    " Takes no other filter",
)
@click.option(
    "--overwrite",
    is_flag=True,
    help="With --sink, also change the documents' existing rows",
)
@click.option("--dry-run", is_flag=True, help="Count, without changing anything")
@click.pass_context
@report_user_errors
def deliveries_set_status_cmd(
    ctx: click.Context,
    documents: DocumentFilter,
    delivery_ids: tuple[int, ...],
    sink: str | None,
    status: str | None,
    sort: str,
    target: str,
    all_rows: bool,
    overwrite: bool,
    dry_run: bool,
) -> None:
    """Set the state of deliveries.

    With --sink and document filters, every selected document gets a row of
    that sink, routed to it or not (its content type must be one the sink
    accepts); with --sink and --all, every document routed to it. --limit
    counts documents. Existing rows are left as they are unless --overwrite.
    That queues documents for a sink by hand (`--as queued`).

    Otherwise, or with --delivery or --status, it changes the selected rows;
    --limit counts rows. That settles an interrupted `sending` row (`--as
    done` or `--as queued`), or requeues failed ones (`--as queued`).
    """
    check_all_rows(all_rows, documents, delivery_ids, status)
    by_document = (
        sink is not None
        and not (delivery_ids or status)
        and (all_rows or documents.is_set())
    )
    if overwrite and not by_document:
        raise click.UsageError(
            "--overwrite needs --sink and document filters (or --all), and no"
            " --delivery or --status"
        )
    verb = "Would mark" if dry_run else "Marked"
    app = app_from_context(ctx, write=not dry_run)

    if by_document:
        assert sink is not None
        summary = app.mark_deliveries(
            sink,
            DeliveryStatus(target),
            documents,
            overwrite=overwrite,
            dry_run=dry_run,
        )
        click.echo(
            f"{verb} {summary.created + summary.changed} delivery(ies) as"
            f" {target}: {summary.created} new, {summary.changed} changed"
        )
        if summary.kept:
            click.echo(
                f"Left {summary.kept} existing delivery(ies) as they were;"
                " --overwrite changes them",
                err=True,
            )
        return

    if not all_rows:
        require_selection(
            *delivery_filters(documents, delivery_ids, sink, status),
            action="change",
        )
    deliveries = select_deliveries(app, documents, delivery_ids, sink, status, sort)
    if dry_run:
        changed = len(deliveries)
    else:
        changed = app.set_delivery_status(deliveries, DeliveryStatus(target))
    click.echo(f"{verb} {changed} delivery(ies) as {target}")


@deliveries_group.command("rename")
@click.argument("old")
@click.argument("new")
@click.option("--dry-run", is_flag=True, help="Count, without changing anything")
@click.pass_context
@report_user_errors
def deliveries_rename_cmd(
    ctx: click.Context, old: str, new: str, dry_run: bool
) -> None:
    """Move the ledger of sink instance OLD to NEW, after renaming it in the
    configuration, so NEW does not deliver its documents again.

    NEW must be configured and have no deliveries yet.
    """
    app = app_from_context(ctx, write=not dry_run)
    count = app.rename_sink(old, new, dry_run=dry_run)
    verb = "Would move" if dry_run else "Moved"
    click.echo(f"{verb} {count} delivery(ies) from {old} to {new}")


@deliveries_group.command("send")
@delivery_options
@sort_option(DELIVERY_SORTS)
@click.pass_context
@report_user_errors
def deliveries_send_cmd(
    ctx: click.Context,
    documents: DocumentFilter,
    delivery_ids: tuple[int, ...],
    sink: str | None,
    status: str | None,
    sort: str,
) -> None:
    """Send ledger rows now, whatever their state, with no backoff or
    pacing.

    A row is sent again even if it is `done`. Exits non-zero if any fails.
    """
    require_selection(
        *delivery_filters(documents, delivery_ids, sink, status), action="send"
    )
    app = app_from_context(ctx, write=True)
    deliveries = select_deliveries(app, documents, delivery_ids, sink, status, sort)
    if print_deliver(app.send_deliveries(deliveries)):
        ctx.exit(1)


@cli.command("deliver")
@click.option(
    "--sink", "sink_ids", multiple=True, help="Only this sink instance (repeatable)"
)
@click.option(
    "--ignore-interval",
    is_flag=True,
    help="Send now even if the interval has not passed, up to max_per_run",
)
@click.option(
    "--ignore-max-per-run",
    is_flag=True,
    help="Every due row; on a sink with an interval, with --ignore-interval",
)
@click.option(
    "--max-per-run",
    type=click.IntRange(min=1),
    help="At most this many per sink instance, instead of its max_per_run",
)
@dry_run_option
@click.pass_context
@report_user_errors
def deliver_cmd(
    ctx: click.Context,
    sink_ids: tuple[str, ...],
    ignore_interval: bool,
    ignore_max_per_run: bool,
    max_per_run: int | None,
    dry_run: bool,
) -> None:
    """Send every sink instance's pending deliveries, paced; `apps run`
    does this after running the applets.

    --ignore-interval and --ignore-max-per-run each drop one of the sinks'
    pacing options for this run, and --max-per-run replaces one. A sink
    with an interval sends one row per run, so emptying its queue takes
    both --ignore-interval and --ignore-max-per-run. Retries still wait for
    their backoff, and a failed delivery does not stop the others.
    """
    if ignore_max_per_run and max_per_run is not None:
        raise click.UsageError(
            "--ignore-max-per-run and --max-per-run exclude each other"
        )
    pacing = PacingOverride(
        ignore_interval=ignore_interval,
        ignore_max_per_run=ignore_max_per_run,
        max_per_run=max_per_run,
    )
    app = app_from_context(ctx, write=not dry_run)
    now = datetime.now(UTC)
    selected = list(sink_ids) or app.sink_ids
    if dry_run:
        rows = [
            [d.id, d.sink, f"{d.document_id} {d.document_label}", d.status]
            for sink_id in selected
            for d in app.plan_delivery(sink_id, now, pacing)
        ]
        print_table("Would deliver", ["ID", "Sink", "Document", "Status"], rows)
        return
    if failed := run_delivery(app, selected, now, pacing):
        raise click.ClickException(f"{failed} delivery(ies) failed")


def run_delivery(
    app: Application,
    sink_ids: list[str],
    now: datetime,
    pacing: PacingOverride | None = None,
) -> int:
    """Deliver for each sink instance and print the summary; return how many
    deliveries failed."""
    with progress_rows() as progress:
        summaries = run_each(
            progress,
            sink_ids,
            lambda sink: app.deliver(sink, now, pacing),
            failed_summary,
        )
    for sink, count in app.unconfigured_pending().items():
        LOGGER.warning(
            f"{sink}: not configured, {count} pending delivery(ies) left as they are"
        )
    return print_deliver(summaries)


# --- Applets ----------------------------------------------------------------


@cli.group("apps")
def apps_group() -> None:
    """Run applet instances, or reset them."""


@apps_group.command("run")
@click.option(
    "--app", "app_ids", multiple=True, help="Only this applet instance (repeatable)"
)
@click.option("--force", is_flag=True, help="Run even if not due")
@click.option(
    "--no-deliver",
    is_flag=True,
    help="Store and queue what they emit, but send nothing; `deliver` sends it",
)
@dry_run_option
@click.pass_context
@report_user_errors
def apps_run_cmd(
    ctx: click.Context,
    app_ids: tuple[str, ...],
    force: bool,
    no_deliver: bool,
    dry_run: bool,
) -> None:
    """Run the applet instances that are due, then deliver: with --app,
    for the sink instances those are routed to; without it, for all.

    Each emitted document gets a queued delivery per sink its output is
    routed to, including one already stored that has no row of a sink
    routed since (the Routed column). --no-deliver stops there.

    --dry-run runs them and shows the documents they would emit, storing and
    delivering nothing. Exits non-zero if anything failed.
    """
    app = app_from_context(ctx, write=not dry_run)
    now = datetime.now(UTC)
    selected = list(app_ids) or app.app_ids
    for app_id in selected:
        app.app_instance(app_id)
    with progress_rows() as progress:
        reports = run_each(
            progress,
            selected,
            lambda app_id: app.run_app(app_id, now, force=force, dry_run=dry_run),
            lambda app_id, exc: AppReport(app_id, due=True, error=describe(exc)),
        )
    failures = print_apps(reports)
    if dry_run:
        print_emitted(reports)
    elif not no_deliver:
        sinks = app.routed_sinks(selected) if app_ids else app.sink_ids
        failures += run_delivery(app, sinks, now)
    if failures:
        raise click.ClickException(f"{failures} failure(s); see the log above")


def print_emitted(reports: dict[str, AppReport]) -> None:
    """The documents a dry run would emit, and each instance's new state."""
    rows = [
        [name, output, key, label]
        for name, report in reports.items()
        for pairs, label in ((report.new, "new"), (report.ignored, "already stored"))
        for output, key in pairs
    ]
    print_table("Documents", ["App", "Output", "Key", "Status"], rows)
    print_table(
        "States",
        ["App", "State"],
        [
            [name, preview(report.state)]
            for name, report in reports.items()
            if report.due and report.error is None
        ],
    )


@apps_group.command("reset")
@click.argument("app_id")
@click.option(
    "--with-documents",
    is_flag=True,
    help="Also delete its documents and their deliveries",
)
@dry_run_option
@click.pass_context
@report_user_errors
def apps_reset_cmd(
    ctx: click.Context, app_id: str, with_documents: bool, dry_run: bool
) -> None:
    """Delete APP_ID's state and run times, so it starts from scratch.

    Its documents stay unless --with-documents, so what it emits again under
    their keys is not delivered again. The instance need not be configured.
    """
    app = app_from_context(ctx, write=not dry_run)
    deleted = app.reset_app(app_id, with_documents=with_documents, dry_run=dry_run)
    verb = "Would reset" if dry_run else "Reset"
    click.echo(f"{verb} {app_id}; {deleted} document(s) deleted")
