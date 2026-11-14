# Architecture

How the current code implements [SPECIFICATION.md](SPECIFICATION.md). The
behavior rules (identity, change detection, retries, dependencies) are
defined there and not repeated here.

```
config.yaml ─► Config ─► Application (app.py) ◄── cli.py, external tools
                          │
        HTTPClient ◄──────┤ import
        (cached)          ▼
                     Provider ──► SourceItemData ──► SourceItem
                                                       │
                                                       ▼
                                          Database.upsert_source_items
                                           ├─ content ─► DiskStorage (content_dir)
                                           └─ row ─────► SQLite (source_items)
                                                       │
                     process                           ▼
                     Processor ◄── Database.get_unprocessed_items / get_content
                        └─► annotations + processing state
                     apps (when due)
                     Applet ◄── AppletReader (its workflow's sources):
                                items, annotations, documents
                        └─► AppletResult: state + emitted documents
                              └─► Database.commit_app_run: documents,
                                  a queued delivery per route, run record
                     deliver
                     Deliverer (per sink instance) ◄── the ledger
                        └─► Sink.send(document) ─► outside world
```

## Modules

| Module | Responsibility |
| :--- | :--- |
| `app.py` | `Application`, the single entry point: registers the plugin classes, resolves the configuration into a `Catalog`, wires config, HTTP cache and database, builds each profile's object on first use (`_object`), runs import and process one unit at a time on a workflow's sources (`import_source`, `run_process`; `workflows` lists the workflows in configuration order, `workflow(name)` gives one, `source_ids(workflows)` the sources of some workflows, each once, and `process_runs(workflows, processor=None)` their process runs as (workflow, key), each workflow's in its order, or one processor entry's by its `ref`), runs a workflow's applet instances (`run_app`, `reset_app`, `app_status`; `app_ids`, `workflow_apps(name)`) and deliveries (`deliver`, `plan_delivery`, `send_deliveries`, `mark_deliveries`; `sink_ids`, `workflow_sinks(workflows)`, the sinks some workflows' instances are routed to), answers queries and deletes. The database is private to it. `write_lock`, the exclusive lock every writing command takes. |
| `cli.py` | Click commands only: one per phase (`import`, `process`, `apps`, `deliver`) and `run` for the whole chain; each takes exactly one selection of workflows (`workflow_selection`: `-w/--workflow NAME`, repeatable, or `--all`, resolved by `selected_workflows`), and a bare one is a usage error; the phase commands narrow by id within it (`--source`, `--processor`, `--app`, `--sink`), an id outside it being an error; read-only `inspect items\|annotations\|documents\|apps\|content\|deliveries`, `delete items\|annotations\|documents\|deliveries\|apps`, `deliveries set-status\|send\|rename`; builds an `Application` per invocation, locked for the commands that write, and runs each unit through it with its own progress row; a unit that raises is logged and counted as failed, and the rest still run. `inspect` and `delete` share their selection options, so `inspect` is `delete`'s dry run. Results go to stdout and progress and logs to stderr, each rich only when it is a terminal (`RICH_STDOUT_*`/`RICH_STDERR_*` from `foundation.clilib`); summaries print after the progress ends. Global logging options and the log handler come from `foundation.clilib` and `foundation.loglib`. |
| `catalog.py` | `Catalog`: the configuration resolved against the registered classes, at start-up. Every use becomes a `Profile` (class, validated options), every workflow's process runs a `Run` (workflow, key, profile), every applet instance an `AppInstance` (profile, `Schedule`, routes, its `workflow`) and every sink instance a profile, with every check of decisions 0010, 0015 and 0019 (sections, ids, unique keys, one workflow per applet instance, routes and content types, what runs and applets read, LLMs, unused entities). Builds nothing. |
| `config.py` | Pydantic models for `config.yaml` (log level, `plugins` defaults per type, the catalog: `llms`, `sources`, `processors`, the instances `apps` and `sinks`; `workflows`, lists of ids; `cache`, `cache_dir`, `storage_dir`); `ProcessEntry.ref` is an entry's `id`, or else its type name. Removed shapes (`skip_default`, a workflow's own `process` entry) fail with what to write instead (decision 0019). `Duration`, a length of time as seconds or with a unit suffix (`5m`, `2h`, `3d`), parsed to seconds at load. `Config` is a pydantic-settings `BaseSettings`: `NEWSTOOL_*` variables, then a `.env` next to the config file, then the YAML, then the `ENV_ALIASES` variables (`OLLAMA_HOST`, `OLLAMA_API_KEY`), then defaults (`settings_customise_sources`). `ConfigPath`, a path relative to the config file's directory (the `LoadContext` of the load in progress); `storage_dir` holds `data.db` and `content/` (`database_uri`, `content_dir`). `${VAR}` expansion, in the YAML only, from the environment and a `.env` next to the config file, and the formatting of option errors with their config path. |
| `models.py` | Domain models: `SourceData` (a configured source), `SourceItemData` (provider output, validated), the DTOs `SourceItem`, `Annotation`, `Document`, `Delivery` and `AppletRun` (each with its database `id`), what applets return (`EmittedDocument`, `AppletResult`), and the selections `ProcessingScope` (`sources` holds a workflow's; publication and import bounds) and `DocumentFilter`. |
| `httpclient.py` | `requests` session with browser headers and a `foundation` cache, which `get(url, use_cache=False)` skips. |
| `errors.py` | How failures reach the user: `PluginFailure`, the exception a plugin raises, with a message written for the user, when it cannot do its job in an expected way; `EXPECTED_ERRORS`, that and the failures of the network, the LLM backend and the database; `describe` (the message of a `PluginFailure`, `Type: message` for any other exception) and `log_failure` (error-level log; the traceback only with debug logging or when the exception is unexpected). |
| `db.py` | SQLAlchemy models and `Database`, the only code that touches SQLite or the content storage. |
| `providers.py` | The `Provider`, `PreflightProvider` and `ProviderType` protocols, `BaseProvider` and `IndexSiteProvider`, optional base classes. |
| `processors.py` | The `Processor` and `ProcessorType` protocols, `ProcessorOptions`, `BaseProcessor`, `SkipItem` and `RunSummary`; `publisher_tags` (an item's `data["tags"]`) and `embedding_key` (the key `embed` writes for an input), shared by the bundles that need them. |
| `applets.py` | The `Applet` and `AppletType` protocols, `BaseApplet`, `Schedule` (when an instance is due), `required_keys` (the annotation keys an instance reads, which its workflow must write), `AppletReader` (what applets may read, scoped to the instance's workflow's sources), `check_result` and `run_key`. |
| `sinks.py` | The `Sink` and `SinkType` protocols, `SinkOptions`, `accepts`, and `Deliverer`, the delivery cycle of one sink instance over the ledger. |
| `llms.py` | The `LLM` and `LLMType` protocols, `LLMUnavailableError` and `strip_code_fence`, for answers wrapped in a code fence. |
| `plugins/` | The plugin bundles: one module per site provider (`telegram_channel` included), `markdownify`, the `ollama` LLM, `summarize`, `tagger`, `classify`, `embed`, `truncate` (a test stand-in for `summarize`), the applets `digest`, `feed` and `itemfeed`, and the sinks `telegram`, `googlechat`, `filesink` (`file`) and `stdout`. `PluginOptions`, `NoOptions`, `UsesLLMOptions`, `merge_options`, `PluginTypes`, `Services` and `ClassRegister` live in its `__init__`. |

## Plugins

Plugins register classes; the core builds one object per configured use
(decision 0010). The core knows only the protocols in `providers.py`,
`processors.py`, `applets.py`, `sinks.py` and `llms.py`, never a plugin's
code:

1. `Application.__init__` registers every module of the `newstool.plugins`
   namespace with `ClassRegister.register_found()`. Each module's
   `__newstool_plugin__()` returns `[(type name, type Protocol, class),
   ...]`, declared under `ProviderType`, `ProcessorType`, `AppletType`,
   `SinkType` or `LLMType`. `ClassRegister.classes(protocol)` indexes them
   by type name, checks that names are unique per protocol, that each is a
   class (an instance is a `PluginError`) and that it conforms
   (`isinstance(cls, protocol)`, else `ProtocolConformanceError`). A module
   that fails to import fails every command.
2. `Catalog` resolves the configuration (see *The catalog*): a `Profile`
   per use, with its options validated, a `Run` per workflow process unit
   and an `AppInstance` per applet instance. Every error is a `ConfigError`
   with its config path, before the database is opened.
3. A run builds its profile's object on first use, `cls(options,
   services)`, and keeps it for the other runs of the profile.

A type protocol declares `options_model` and `__call__(options, services)`;
`ProcessorType` adds `output_key(options)` and `required_key(options)`,
`AppletType` `outputs` (output name to content types) and
`requirements(options)` (the annotation keys it reads), and `SinkType`
`accepts` (content types), as class attributes or methods, so keys, routes
and requirements are checked without objects. An object keeps its options
(`self.options`) and what it takes from `services` (decision 0013):
providers the `HTTPClient` (`self.fetcher`), processors the `Database`
(`self.db`); applets and sinks take no database. Methods receive only what
each task needs: providers the source, processors the scope and the run's
key, applets the time, their run record and an `AppletReader`, sinks one
document. Each protocol has its own method (`retrieve_items` or
`iter_items`/`retrieve_item`, `process`, `is_due`/`run`, `send`).
Processors own their name, a class attribute that records who wrote an
annotation; entry points register each class under its name. Annotations
and processing state are keyed by the process run's key (see
*Workflows*), documents and run records by the applet instance's id, and
deliveries by the sink instance's id, never by the type name.

`services` is what the core shares with objects: `services.db`,
`services.fetcher`, and `services.llm(name)`, which returns the LLM `name` refers to (an `llms` id or an LLM type; `None`, the
first `llms` entry), built on first use by `Application._llm`. Objects that
use one take `UsesLLMOptions` and ask for it in their constructor.

A bundle may register several classes per protocol under different names.

### The catalog

`plugins.<type>` holds the defaults of a type's options for every use. It
builds nothing; `Catalog` checks its keys and each value against the
type's `options_model` (`check_section`), and rules across options when a
use is validated. The catalog lists the uses: `llms`, `sources` and
`processors`, each a type name or `{<type>, id, key, options}`; `apps` and
`sinks` list instances, each with a required `id`. Defining a use never
runs it: only workflows do. A use's options are
`merge_options(section, options)`, merged key by key in nested mappings,
any other value replacing, validated with `options_model`. A rejected
option is a `ConfigError` with its path
(`sinks.0.options.chat_id: Field required`).

An `id` lets workflows refer to a catalog entry; it cannot be another
type's name of its kind. A `processors` entry without one is referred to by
its type name (`ProcessEntry.ref`), so two entries of one type need
explicit ids. Every profile of the catalog is validated, whether a workflow
runs it or not; a source, processor or applet instance no workflow refers
to gets a warning. Sinks do not: rows queued by hand reach them.

## Workflows

Decision 0019. `config.workflows` is the list as written: each `Workflow`
holds ids (`sources`, `process`, `apps`); there is no implicit workflow.
`Catalog` resolves a workflow's `process` ids to the `processors` entries'
uses; each run is a `Run` (workflow, key, profile, location), and import
and process restrict the scope to its workflow's sources (`workflow_scope`,
`ProcessingScope.sources`). A workflow is the whole chain: its import,
process and applets, then the delivery to its sinks (see *Applets*).

Process runs are keyed `(workflow, key)`. A key is written by one
`processors` entry, so two entries with one key are a `ConfigError`, and
workflows that run a key share its profile: a key means the same on every
source. Annotations and processing state are per `(item, key)`. Every key a
process run reads (`required_key`) must be written by a process run on its
workflow's sources, in any workflow.

Bundles never import each other. `digest` reads the vectors `embed`
stores under `embedding_key(input)` (`tags/embedding`,
`summary/embedding/es`), the same way it reads `tags`.

## Providers

`Provider.retrieve_items(source)` yields `SourceItemData`. A
`PreflightProvider` imports in two stages instead: `iter_items(source)`
lists `PreflightSourceItemData` (the `uid`, a `ref` of the
plugin's own type to fetch the item with, and the `modified_at` the index
shows, if any), and the core calls `retrieve_item(preflight_item)`
only for items that are new, listed without a date, or listed newer than
the stored `modified_at`. An item that turns out no newer once retrieved is
dropped with a warning, and a uid other than the listed one is warned about.
Whichever the kind, what was fetched is stored even if the import fails
halfway. Each source builds its own provider object, with the source's
options. Most
sites are `IndexSiteProvider`s, which take no options: fetch `index_url(source)` (the source's URL unless the provider
overrides it), `parse_index` it into article URLs, fetch each article and
`parse_item` it.

A source's `options` override its provider's plugin section (see *The
catalog*):

```yaml
sources:
  - id: some-blog
    provider: feedreader
    options:
      fetch_article: true   # overrides plugins.feedreader.fetch_article
```

An unknown or invalid option fails every command at start-up as a
configuration error (`sources.<id>.options.<option>`). The options live in
the configuration only; the database does not store them.

HTML providers keep the article's cleaned HTML rather than converting it:
`foundation.scrapelib.prune_to_spine` keeps the main node and its ancestors,
and `drop_selectors` removes known cruft (ads, related links). Converting
to other formats is a processor's job.

Every item carries `content: bytes` and a `mimetype` without parameters.
`SourceItemData` rejects `text/*` content that isn't UTF-8, so text is
always UTF-8 and no charset is stored.

### Writing a plugin

A plugin is a module in `newstool/plugins/` that exposes
`__newstool_plugin__() -> PluginTypes`, the classes it provides under
their type names, which are what `plugins:` sections, sources and entries
name. A provider for a site with an index page (a section, an RSS feed)
that links to one article per item (a plugin reports an expected failure,
such as a page without the expected structure or an empty LLM response, by
raising `PluginFailure` from `..errors` with a message for the user; any
other exception is unexpected and shows its traceback):

```python
import hashlib
from collections.abc import Iterator

import bs4
from foundation.scrapelib import drop_selectors, prune_to_spine

from ..models import SourceData, SourceItemData
from ..providers import URI, IndexSiteProvider, ProviderType
from . import PluginTypes


class ExampleProvider(IndexSiteProvider):
    def index_url(self, source: SourceData) -> str:
        # Optional: defaults to the source's url.
        return str(source.url).rstrip("/") + "/feed/"

    def parse_index(self, content: bytes, source: SourceData) -> Iterator[URI]:
        """Yield the article URLs found in the index page."""
        ...

    def parse_item(self, content: bytes) -> SourceItemData:
        """Build one item from an article page."""
        soup = bs4.BeautifulSoup(content.decode("utf-8"), features="html5lib")
        if (article := soup.select_one("article")) is None:
            raise ValueError("Article not found")
        drop_selectors(article, [".ads", ".related"])
        url = ...
        return SourceItemData(
            uid=hashlib.sha256(url.encode()).hexdigest(),
            title=...,
            uri=url,
            content=str(prune_to_spine(article)).encode("utf-8"),
            mimetype="text/html",
            published_at=...,  # optional
            modified_at=...,  # optional
            data={"author": ..., "image": ...},  # any JSON-compatible extras
        )


def __newstool_plugin__() -> PluginTypes:
    return [("example", ProviderType, ExampleProvider)]
```

`retrieve_items` fetches the index and each article; a `ValueError` from
`parse_item` is logged and that article is skipped, so raise it for pages
that aren't articles. For anything else (several items in one page, binary
files), subclass `BaseProvider` and implement
`retrieve_items(source)` yourself, fetching with
`self.fetcher.get(url)`; `feedreader` and `telegram_channel` are examples with
options (`self.options`). When the index already gives each item's uid and
date and fetching an item is expensive, implement `iter_items` and
`retrieve_item` instead, so stored items are skipped undownloaded;
`csjuntasgobierno` and `prensaiberica` (with options) are examples.

A class with options sets `options_model` to a `PluginOptions` subclass
with defaults for the general case, so a use needs no options; its
constructor takes `(options, services)`. `feed` and `telegram` are
examples, and `summarize` an
LLM consumer (`UsesLLMOptions`). Use `pydantic.SecretStr` for secrets, so
they never show in a `repr` or a traceback. Processors usually subclass
`BaseProcessor` (`process_item(item)`, plus `key` and `requires` class
attributes, options from `ProcessorOptions`) and read the database through
`self.db`. Applets subclass `BaseApplet`: they declare `outputs` and
`requires`, and implement `run(now, run, reader)`, reading only through
the `AppletReader`, already scoped to their workflow's sources, and
returning an `AppletResult` (see *Applets*). Sinks declare `accepts` and
implement `send(document)`, with options from `SinkOptions`. Each sets
`name` and `options_model` as class attributes and is returned as
`(cls.name, <its type Protocol>, cls)`.

Rules every provider follows:

- `uid` is deterministic and stable across runs (decision 0001). The
  sha256 of the canonical article URL is the usual choice.
- Keep the site's cleaned HTML; never convert it (that is `markdownify`'s
  job). Text content must be UTF-8 and `mimetype` must have no parameters.
- Only report dates the site gives you; missing ones take the import time.
- `parse_item` works on bytes only, so it can be tested offline: save
  sample pages in `tests/samples/` and add a case to
  `tests/test_providers.py`.

Add the plugin to the README's tables.

## Persistence

SQLite tables:

- `sources`: one row per configured source, keyed by its configured `id`.
- `source_items`: metadata of each item (`uid`, `uri`, `title`, `mimetype`,
  `content_sha256`, `data`, `published_at`, `modified_at`, `imported_at`),
  unique per `(source_id, uid)`. `uri` is not unique; `imported_at` is set
  on creation and never changed.
- `item_annotations`: per item and annotation key (e.g. `markdown`,
  `summary`, `summary/es`), the state of its last run (processor, status
  `done`, `error` or `ignored`, attempts, last error, processor version,
  `attempted_at`) and, once a run finished, the `value_sha256` of its value
  and `updated_at` (decision 0018). A `done` row has a value (`CHECK`).
  The trigger `trg_source_items_content_changed` deletes an item's rows
  when its `content_sha256` changes; `Database` releases their values.
- `apps`: one row per applet instance that ever ran, keyed by its id:
  `last_started`, `last_success`, `last_error` and `state` (JSON).
- `documents`: what applet instances emitted, unique per `(app, output,
  key)`, with the content type, title, url, image url, `emitted_at` and the
  `content_sha256` of their content; never updated.
- `deliveries`: the ledger, one row per `(sink, document_id)`, `sink`
  being the sink instance's id, with status, attempts, last error and an
  `external_ref` (JSON).

Every table with an integer id uses `AUTOINCREMENT`, so a deleted id is
never reused: the CLI selects items and annotations by id (decision 0008).
The DTOs carry it; `upsert_source_items` sets it on the items it saves.
`import_source` stores each batch oldest first, so new item ids follow
publication order.

SQLAlchemy models never leave `db.py`: `Database` takes and returns DTOs.
Every SQLite connection gets `SQLITE_PRAGMAS` from a SQLAlchemy `connect`
listener: foreign keys on, WAL, `busy_timeout`, `synchronous=NORMAL`,
in-memory temp store. newstool does not use `foundation.dblib`, which is a
shortcut for code that uses `sqlite3` directly. Item and document foreign
keys are `ON DELETE CASCADE`, so `delete_items` and `delete_documents`
only delete the rows, then release their contents.
`Base.metadata.create_all` creates missing tables only; it never alters an
existing schema.

### Content storage

Item contents, annotation values (as JSON) and document contents are stored
outside SQLite, in one `foundation.storage.DiskStorage` in `content/` under `storage_dir`,
keyed by the sha256 of the bytes (decision 0004). The database is the only
record of which row uses which content.

- `SourceItem` and `Document` compute `content_sha256` when built with
  content. Items and documents read back have `content=None`; processors
  load an item's with `Database.get_content(item)`, applets read documents
  with their content through the `AppletReader`.
- Content is written **before** the row that references it, so a crash
  leaves an unused file, never a row pointing at nothing.
- After the commit, replaced hashes that no row (item, annotation or
  document) references any more are deleted. Identical contents are stored
  once and shared.
- Two writers running at the same time could delete a content the other
  one has just started to reference. `write_lock` prevents it: every
  command that writes takes an exclusive `flock` on `<database>.lock` and
  fails at once if another process holds it (POSIX only).

### Change detection

`upsert_source_items` applies the compared fields with `DBSourceItem.update`,
then asks `session.is_modified()` whether anything changed; only then does it
touch `modified_at` (spec §4.1).

## Processors

The eligibility and retry rules are in spec §4.2; this is where they live:

- A workflow's process runs are `processors` entries it refers to by
  `ref`: a processor, an optional `key` and its options. At start-up
  `Catalog` validates the options, asks the class for its
  `output_key(options)` when the entry names no key, and checks the keys
  (see *Workflows*). `run_process(key, workflow=...)` calls
  `processor.process(key=key, scope=..., force=...)`.
- `BaseProcessor.process_item(item)` returns the value of one
  annotation for one item, with its options in `self.options`.
  `Database.get_unprocessed_items(key, ...)` selects the eligible items
  (backoff in `backoff_seconds`, `max_retries` from `ProcessorOptions`,
  version in `version`). Raising `SkipItem` marks the item `ignored`; any
  other exception marks it `error`. `process()` returns a `RunSummary`
  (done, ignored, failed).
- `Database.record_result` saves a run's state and, when `done`, its
  annotation in one transaction, recording the item's `content_sha256`.
- `BaseProcessor.requires` (or `required_key(options)`, which `embed`
  overrides with its `input`) names the key the run reads;
  `require_annotation()` reads its value.
- Dependencies: `summarize`, `tagger` and `classify` read `markdown`;
  `embed` reads its `input` (`tags` by default).
- `Database.delete_annotations` removes annotations by id, each with the
  state of its run (one row), so their runs find the items pending. `delete annotations` passes what `find_annotations` selects.

## Applets

Decisions 0015 and 0019. `Catalog` builds an `AppInstance` per `apps`
entry: its profile, a `Schedule` (`every`, `at`, `days` as weekday
numbers), its routes, `routes` or the `sink` shorthand turned into
`{output: (sink ids)}`, and its `workflow`, the one that names it in its
`apps` (None if none does). At start-up it checks that every routed output
exists in the class's `outputs`, that every sink exists and `accepts` the
output's content types (`sinks.accepts`), that no instance is in two
workflows, and that every key of the class's `requirements(options)` is
written by a process run of the instance's workflow.

`Application.run_app(app_id, now, force, dry_run)` (an instance of no
workflow is a `ConfigError`):

1. reads the run record (`Database.get_app_run`, an empty `AppletRun` if it
   never ran) and asks `applet.is_due(now, run, schedule)`;
   `BaseApplet.is_due` defers to `Schedule.is_due(now, last_success)`.
   `force` skips it;
2. commits `last_started` on its own (`start_app_run`);
3. calls `applet.run(now, run, reader)`, `reader` an `AppletReader(db,
   sources)` over its workflow's sources and `run` the record read before
   the start, and validates the result with `check_result` (declared
   outputs and content types, no key twice);
4. stores it with `Database.commit_app_run`: in one transaction, each
   document whose `(output, key)` the instance has not stored, a `queued`
   delivery per sink its output is routed to that the document has none of
   (for a stored one too: a route added since, decision 0016), and the run
   record with the new state and `last_success = last_started`. It returns
   a `CommittedRun` (the new documents, and `routed`, the rows added for
   stored ones). Contents are written first.
   A failure (any exception, logged with `log_failure`) stores only
   `last_error` (`fail_app_run`).

`dry_run` runs the applet and reports which keys are new
(`existing_document_keys`), the rows it would add for stored ones
(`count_missing_routes`) and the state, writing nothing. `apps` runs the
selected workflows' instances and delivers nothing; `deliver -w` covers
`workflow_sinks`, `--all` every sink. `run` chains each selected
workflow's import, process and applets, then one delivery phase for the
union of their sinks (every sink with `--all`), as phases of one
`run_phases`, so a sink delivers once per call. Commands that write take
the write lock, so two of them never overlap. `reset_app` (`delete apps`)
deletes the run record, and with `with_documents` the instance's
documents (deliveries cascade); `app_status` gives each instance's record,
its workflow and
`Schedule.next_due`, which tries the moments where being due can change
(`last_success + every`, each day's start and `at`) over the next week.

`AppletReader` is what an applet reads, built per run with its instance's
workflow's sources: `items` (of those sources only, by publication and
import bounds, through `ProcessingScope`), `annotations(items, key)`
(by item key, one query), `content(item)` and `documents` (any instance's,
with content). It never exposes the `Database` or another instance's state.

The applets:

- `feed` builds an RSS feed of the newest `max_items` items it reads,
  keyed by the run's UTC time (`run_key`), so each run emits a new one.
- `itemfeed` emits a `text/plain` document per item imported since its
  cursor (its state, the last run's time) that has its `annotation`, keyed
  `item:<source>/<uid>`, with the item's title, link and `data["image"]`.
  The window starts `wait` before the cursor, so an item whose annotation
  came late is still emitted, but never before `start`, the first run's
  time minus `backfill` (none with `backfill: all`); keys already stored
  are ignored. A first run reads from `start`, so with the default
  `backfill` of 0 it emits nothing. It emits the
  oldest item first (`ItemFeedApplet.age`: publication time, or import time
  without one, then id), so its sinks deliver in that order.
- `digest` reads the items published in the `span_days` whole local days
  before the run's day (`period`) that have its `input` annotation and
  pass its `include`/`exclude` filters (`read_candidates`, giving frozen
  `Candidate`s with their text, tags, topics and vector), groups them into
  stories and keeps the `max_stories` best (`select_stories`): a pairwise
  `score_matrix` (Jaccard tag overlap, blended with the cosine similarity
  of the vectors with `algorithm: embeddings`, times a time decay with a
  `tau`) clustered by the function `CLUSTERERS` maps `algorithm` to
  (`single_link_clusters`, `average_link_clusters`), each `Story` scored by
  `story_score`. It emits `plan` (JSON) and, with `write`, `digest`
  (Markdown: one LLM call per story, one for the opening paragraph), both
  keyed `<from>_<to>`; no stories, no documents.

## Sinks

Decision 0015. A sink renders and sends one `Document` (`send(document)`,
returning its external reference); it knows nothing of items, annotations
or the ledger. `Deliverer(db, sink_id, sink, options, pacing)` runs the cycle of
one sink instance over its rows (`Database.deliveries_of(sink)`, oldest
document first: by `emitted_at`, then document id, which follows emission
order within a run):

1. `plan(now)`: warn about `sending` rows, keep `queued` ones and `error`
   ones with attempts left (`max_retries`) whose backoff
   (`backoff_seconds`, as processors) has passed, then `pace`: with an
   `interval`, only the first one, once the instance's last `done`
   delivery (`last_delivered_at`) is that old; then at most
   `max_per_run`. A `PacingOverride` (from `deliver`'s options) drops the
   interval, drops `max_per_run` or replaces it, for one run;
2. `send_rows(rows)`: for each, save it `sending`, load the document's
   content, call `send`, then save it `done` with the returned
   `external_ref`, or `error` with one more attempt. Errors are logged with
   their traceback, so `send` raises without chaining secrets.

Every state change is a `Database.save_delivery(delivery)` in its own
transaction. `Application.deliver(sink_id, now)` runs a cycle;
`plan_delivery` is its dry run. `send_deliveries` groups rows by sink and
sends them now with `send_rows`, skipping sinks no longer configured.
`set_delivery_status` rewrites the state of rows, and `mark_deliveries`
gives documents a row of a sink in a given state
(`Database.add_deliveries`): those a filter selects, routed or not, once
the sink `accepts` their content types (`selected_documents`), or without
filters those routed to it (`routed_documents`). `delete_documents` refuses documents
with rows that are not `done`.

A sink's options are a `SinkOptions` subclass (`interval`, `max_per_run`,
`max_retries`), plus its destination. `telegram` posts through
`post(bot_token, method, ...)`; each instance's `bot_token` and `chat_id`
default to its type's section, which is optional. A document whose whole
message fits in 4096 characters is posted with `sendMessage`, or
`sendPhoto` with its image under `images` (the caption cut to 1024); a
longer one goes as a file with `sendDocument`. `link_text` and
`link_preview` set the link's text and whether `sendMessage` shows its
preview, and `markdown` posts in Telegram's legacy `Markdown`, the text
unescaped, instead of HTML. It records `{"chat_id", "message_id"}`, since a
message id is only unique in its chat. `googlechat` posts each document to
its instance's webhook as one `cardsV2` card: the title and text in a
paragraph of Chat's HTML subset, the image under `images`, and a button
labelled `link_text` when the document has a link. Chat renders no image
from `blogger.googleusercontent.com`, so `chat_image_url` asks Blogger for
the full size and routes it through the `wsrv.nl` proxy. Request errors are
re-raised `from None` with their class only, since the URLs embed the
secrets. `file` writes the content to its `path` (`{app}`, `{output}`,
`{key}` substituted), through a partial file renamed over the target, and
records `{"path"}`.
