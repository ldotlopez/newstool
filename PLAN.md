# newstool — Working Plan

Ordered smallest-and-most-necessary → biggest-and-least-necessary.
Update statuses as we progress: `[ ]` todo, `[x]` done, `[~]` in progress.
Ideas and plans not scheduled yet go to the backlog at the end.

## Plugin classes and the configuration catalog (decision 0010)

Agreed 2026-10-28. Entry points register classes; the core builds one
object per configured use, with its options. `plugins.<type>` holds
defaults per type; `llms`, `sources`, `processors`, `remixers` and `sinks`
are the catalog, with `id`s workflows refer to; `default` is the catalog
without `skip_default` and delivers nothing. Needs a new database and a
rewritten configuration.

- [x] **`ClassRegister`** in `newstool.plugins`, on foundation's
  `BaseRegister`: every module registered, classes by type Protocol
  (`ProviderType`, `ProcessorType`, `RemixerType`, `SinkType`, `LLMType`),
  several per bundle under different names.
- [x] **One object per use**: constructors take `(options, services)`;
  `use_options`, the `Options`/per-use split, the phase methods' `options`
  and the `Unavailable*` objects go. `ProcessorOptions` (`max_retries`),
  `UsesLLMOptions` (`llm`), `BaseProvider`.
- [x] **Config**: catalog entries with `id`, `key`, `options`,
  `skip_default`; workflow entries as ids, type names or their own entries
  (no `id`); `default: false` → `skip_default: true`; deep `merge_options`.
- [x] **`Catalog`** (`catalog.py`): profiles and runs resolved and checked
  at startup (sections, ids vs type names, keys, what runs read, LLMs);
  objects built on first use; every ledger key `<workflow>/<key>`.
- [x] **Tests, docs** (decision 0010, 0003/0006/0007/0009 revised,
  ARCHITECTURE, SPECIFICATION, README) and **configs**
  (`config.example.yaml`, the user's `config.yaml`).
- [ ] **Move `ClassRegister` to foundation.**

## Workflows, delivery entries and per-use options as pydantic models

Agreed 2026-10-27. A workflow selects sources and runs its own `process`,
`remix` and `deliver` entries; the root keys are the `default` workflow.
A delivery is marked by what it delivers and who asked for it (the
workflow), so one sink (e.g. `telegram`) serves several instances, each with
its own chat and pacing.

```yaml
sources:
  - id: x
    provider: feedreader
    url: ...
  - id: y
    provider: plaza
    url: ...
    default: false             # only workflows use it
process: [markdownify, summarize]
deliver:
  - sink: telegram             # key: telegram
workflows:
  - name: channel-y
    sources: [y]
    process: [...]
    deliver:
      - sink: telegram
        key: channel-y
        options: {chat_id: "-100…", requires: summary, interval: 30, max_per_run: 1}
```

Rules:

- **Sources** stay global and are referenced by id; workflows cannot
  override their options (two option sets for one item would flip its
  `content_sha256` and break change detection, decision 0001). `default`
  uses every source except those with `default: false`.
- **Process keys** are unique within a workflow and across workflows that
  share a source (annotations are per item); workflows with disjoint
  sources may write the same key, so a `default: false` source gets its
  own `markdown` and `summary` (revised 2026-10-27).
- **Remix entries** are `{remixer, key, options}` like the other phases;
  `key` defaults to the remixer's name and is unique across all workflows
  (artifacts are not per source). No schema change: the `artifacts.remixer`
  column holds the key, so existing artifacts stay valid (revised
  2026-10-27).
- **Delivery identity** is `(workflow, key, subject)`. `key` is optional,
  defaults to the sink name and is unique within its workflow. No schema
  change: the `sink` column holds `workflow/key`, and `default` writes the
  bare `key`, so existing rows stay valid with no migration. `/` is
  forbidden in workflow names and keys. Renaming a workflow or key is a new
  requester: it delivers its `lookback` again.
- **Workflows** are a list with `name` (YAML mappings drop duplicate keys
  silently); `default` is reserved.
- **Pacing** per delivery entry, in `BaseSink`/`BaseItemSink`: `interval`
  is one item per interval for the whole entry, oldest first across its
  sources (the per-source mode goes); `max_per_run` caps every run against
  flooding (a new key starts with an empty ledger). `--force` needs an
  explicit selection and skips both.
- **CLI:** `run` and every phase command run `default` without `-w NAME`;
  `deliver KEY --force --item N` resends.

- [x] **1. Per-use options as pydantic models** for providers, processors
  and sinks (was a backlog item): each plugin splits its `Options` by
  inheritance, a model with the per-use options and `Options(<it>)` adding
  the instance-only ones; the core validates each use at startup and merges
  it over the section defaults (`merge_options` in `plugins/__init__`)
  instead of `inspect.signature(...).bind`. Shared delivery options
  (`interval`, `max_per_run`, `lookback`, `max_retries`) in a
  `DeliveryOptions` in `sinks.py`; sink-specific ones (`chat_id`,
  `artifacts`, the webhook) in subclasses; `requires` stays a class
  attribute. Remixers too (`feedgenerator`, `digest`, `grouping`). Tests.
- [x] **2. Config:** `Workflow` (`name`, `sources`, `process`, `remix`,
  `deliver`), `RemixEntry` and `DeliveryEntry` (`<plugin>`, `key`,
  `options`), `SourceData.default`; the root keys build `default`. Startup
  checks: names, source ids, process keys per shared source, global remix
  keys, delivery keys per workflow, no `/`.
- [x] **3. Sinks as entries:** objects built once from `plugins:` (the
  `telegram` bundle subsections go); `deliver` takes the entry's ledger
  key and options. `interval` per entry and `max_per_run` in the base
  classes; `TelegramSink.select` and `last_delivery_by_source` go or
  become per key. `external_ref` records the destination
  (`{"chat_id", "message_id"}`).
- [x] **4. Application and phases** scoped to a workflow: import, process
  and remix over its sources; remixers listed per workflow.
- [x] **5. CLI:** `-w/--workflow` on `run` and the phase commands
  (default `default`); `deliver [KEY]`; `inspect deliveries` and
  `deliveries resolve` by ledger key.
- [x] **6. Docs**, each edit approved first: rewrite decisions 0003
  (per-use options) and 0007 (ledger identity, entries, pacing), a new
  decision for workflows; ARCHITECTURE, README, SPECIFICATION,
  `config.example.yaml`.

## `enrich` section: processor runs keyed by annotation key

Agreed 2026-10-26 (decision 0002). `enrich:` lists processor runs in order;
each writes one annotation key, and state and annotations are unique per
`(item, key)`. Objects are built once from `plugins:`; non-essential options
go to the verb, as with providers.

```yaml
enrich:
  - markdownify
  - processor: summarize
    options: {key: summary/es, prompt: "...", model: modelB}
```

- [x] **1. Config:** `Config.enrich: list[EnrichEntry]` (`processor`,
  `options`), a bare name for defaults.
- [x] **2. Processors:** `Processor.output_key(**options)` and
  `enrich(db, *, key, scope, force, **options)`; `process_item` returns one
  value and declares its run options (`summarize`: `prompt`, `model`;
  `tagger`: `model`; `embed`: `input`, `model`). `PartialFailure` and
  `tags_text` removed; `embed` one input per entry.
- [x] **3. Startup checks** in `Application`: processor loaded, options
  accepted, key format, no key written twice.
- [x] **4. Database:** `processing_state.key`, unique `(item, key)` in
  `processing_state` and `item_annotations`; reads by key only.
  `scripts/migrate_annotation_keys.sql` migrates existing databases.
- [x] **5. Consumers** read by key (`telegram`, `grouping`, `digest`,
  `search`); `requires` names a key.
- [x] **6. CLI:** `enrich [PROCESSOR]` runs every entry (of that processor);
  the summary lists keys. `delete annotations` stays per processor.
- [x] **7. Docs and configs:** README, ARCHITECTURE, SPECIFICATION,
  decisions 0002, 0003, 0007 and 0008, `config.example.yaml`.

## Per-source provider options (`provider_options`)

Agreed 2026-10-26. A source passes options to its provider:

```yaml
- id: some-blog
  provider: rssparser
  provider_options:
    article_selector: .article
```

Convention for every plugin: its `plugins.<name>` section holds defaults,
and each use overrides only what its verb declares. `import-url` goes for
now; it comes back later on a model that fits (an ad hoc source).
External pipelines go too: they will be replaced, not kept as scripts.

- [x] **1. Remove `import-url`:** the command and its CLI test,
  `Application.import_url`, `URLProvider` and `UnsupportedProviderError`
  (the plugins register as `Provider`), `scripts/pipeline_url.py` (the
  only pipeline).
  `import_sample()` in `tests/test_app.py` imports another way.
- [x] **2. Remove the pickle cache** (`NEWSTOOL_PICKLE_CACHE`) from
  `Application.import_source`.
- [x] **3. `provider_options` on sources**, from the config only: not stored
  in the database (`DBSource` unchanged). `import_source` passes them to
  `retrieve_items(source, fetcher, **provider_options)`.
- [x] **4. Validate at startup:** `Application` binds each source's options
  against its provider's `retrieve_items` signature; a failed bind is a
  `ConfigError` naming `sources.<id>.provider_options`. Providers declare
  their options explicitly, never `**kwargs` (it would accept anything).
- [x] **5. `rssparser`:** `article_selector` becomes a `retrieve_items`
  keyword, defaulting to the plugin section's `article_selector`; the
  `article_selectors` map goes. Tests.
- [x] **6. Docs**, each edit approved first: rewrite decision 0003 (options
  convention; the pipelines point goes); 0001 (the single-URL import line);
  SPECIFICATION (§4.1 and the external pipelines note); ARCHITECTURE (the
  `scripts/` row and the Pipelines section); README (`import-url` and
  `pipeline_url.py`); `config.example.yaml`; the backlog's *Pipeline
  dependency graph* entry.
- [x] **7. Naming review:** `provider`/`provider_options` stay. `rssparser`
  is now `feedreader` and the `rssfeed` remixer `feedgenerator`;
  `scripts/migrate_feed_names.py` renames the stored artifacts (run once).
- [x] **8. Docs for the renames.**

## P1 — Plain logging and the `<APP>_LOG_LEVEL` fix

Precedence: CLI (`--log-level`, `-v`/`-q`) > `NEWSTOOL_LOG_LEVEL` >
config `log_level` > `warning`. With `-v`/`-q` and no `--log-level`, they
step from `warning`, ignoring the env var: `-v` is always info, `-vv` debug.

Bug (confirmed 2026-10-24): `click_logging_options` gives `--log-level` a
`"warning"` default, so `setup_logger` never reads the env var, which it only
looks up when `log_level is None`.

foundation (`../foundation`, separate commits; its push is manual):

- [x] **1. `click_logging_options`:** `--log-level` defaults to `None`; the
  help names the `warning` default and the `<APP>_LOG_LEVEL` variable.
- [x] **2. `setup_logger` / `setup_logger_from_click`:** a
  `default_log_level` parameter (defaults to `DEFAULT_LOG_LEVEL`) for the
  app's config value; `-v`/`-q` without `--log-level` ignore the env var.
  Fix the stale `configure_handler` docstrings.
- [x] **3. `tests/test_loglib.py`:** nothing gives warning; the env var
  applies; `--log-level` and `-v` beat it; the app default applies when
  neither CLI nor env set a level.

newstool:

- [x] **4.** `uv lock --upgrade-package foundation` (foundation `main` at
  `96d6929`).
- [x] **5. `log_level: str = "warning"` in `Config`.** Low value (the level
  is a per-run concern; cron can pass `-v`); droppable without affecting the
  rest.
- [x] **6. Logger setup moves to `app_from_context`**, after the config is
  loaded: one `setup_logger_from_click(..., default_log_level=cfg.log_level)`
  call, with the logging options in `ctx.obj` like `config_path`. Without
  step 5, only pass the CLI values through.
- [x] **7. INFO logs per phase**, as `"{name}: …"`:
  - import: `"{source.id}: {uri}"` per item in `app.import_source`, for every
    provider, no source header (`db.py`'s `N new, M updated` closes it);
  - remix: start and end (duration, artifact count) in `BaseRemixer.remix`,
    like `BaseProcessor.enrich`;
  - deliver: `N to deliver` and `done/failed` with duration in `_send_all`;
  - enrich: already complete.
- [x] **8. Precedence tests** in `test_cli.py`: env var applies, `-v` beats
  it, config applies (with step 5).
- [x] **Docs, when done:** `README.md` (env var, config key, precedence),
  `ARCHITECTURE.md` (`config.py`) and `config.example.yaml`.

## P2 — Rich progress across the app

Progress bars complement the logs, never replace them. Each stream is rich
only when it is a terminal: stdout carries results (tables, `inspect`,
contents, `--help`, and the `run`/`import`/`enrich`/`remix`/`deliver`
summaries), stderr carries diagnostics (progress, logs).

| | stdout terminal | stdout redirected |
| :--- | :--- | :--- |
| **stderr terminal** | all rich | rich progress and logs, plain tables |
| **stderr redirected** | rich tables, no progress, plain logs | all plain (cron) |

Progress goes per phase and unit only, driven from `cli.py`: plugin
contracts stay untouched (per-item progress is in the backlog).

foundation:

- [x] **1. Per-stream rich in `clilib`.** `RICH_STDOUT_ENABLED` /
  `RICH_STDOUT_DISABLED` and `RICH_STDERR_ENABLED` / `RICH_STDERR_DISABLED`,
  computed at import from each stream's TTY; `DISABLE_RICH`,
  `RICH_DISABLED` and `TERM=dumb` disable both. `RICH_ENABLED` /
  `RICH_DISABLED` are removed, to avoid two ways of asking. `NO_COLOR` no
  longer disables rich: it only drops colors, which rich already honors.
- [x] **2. `setup_logger` picks the handler.** With `infect=True`, a
  `RichHandler` when stderr is rich, otherwise a plain `StreamHandler`
  (`%(asctime)s %(levelname)s %(name)s: %(message)s`), on the root logger,
  once. `infect=False` still attaches nothing.
- [x] **3. Tests**, reloading `clilib` with a patched environment and
  streams (computed at import), and both handler choices. Branch
  `p2-rich-per-stream` (`efc073c`), not merged yet.

newstool:

- [x] **4.** `uv lock --upgrade-package foundation`; the README test command
  becomes `DISABLE_RICH=1 uv run python -m unittest discover -s tests`, so
  the mode is fixed whoever runs it (unittest keeps the caller's stderr).
- [x] **5. Per-stream switches in `cli.py`.** `rich_click` vs `click` and
  `print_table` follow stdout; `print_content` uses `RICH_STDOUT_ENABLED`
  instead of its own `isatty`. `setup_logging` drops its plain-handler
  branch and the `infect` argument (it was on the package logger, so
  third-party logs fell to `logging.lastResort` in plain mode).
- [x] **6. `Application` exposes processor, remixer and sink names**, like
  `sources`; `app.enrich`/`remix`/`deliver` are deleted and `test_app.py`
  moves to `run_*` and the name lists (configuration order).
- [x] **7. One `Progress` in `cli.py`** on `get_stderr_console()`, with
  `disable=RICH_STDERR_DISABLED`, replacing `track`; the CLI calls `run_*`
  one unit at a time. `run` keeps a phase row (`n/4`); unit rows (spinner,
  elapsed) are removed when done (`remove_task`). `redirect_stdout=False`,
  so a redirected stdout keeps the tables, printed after the rows end.
- [x] **Docs, when done:** propose `ARCHITECTURE.md` (names on
  `Application`, no `enrich`/`remix`/`deliver`; output per stream) and
  `README.md` (terminal detection per stream, `NO_COLOR`, test command).

- [x] **Other foundation consumers** (karasync, intelligence, gvavivenda,
  photolib-tools' `immichtool`), workspace members on the editable
  foundation: migrated in their working copies, left uncommitted for the
  owner. Progress moves to the stderr console with `RICH_STDERR_*`;
  intelligence's plain `echo` lines become `LOGGER.info`/`LOGGER.error`.
  Checked against the branch: same test failures as before. gvavivenda
  already fails to import on foundation `main` (`StatValidator` is gone from
  `foundation.cache`), unrelated to P2.

Out of scope: `inspect`, `delete` and `scripts/` (fast, tables already rich).

## Numeric ids and `inspect` (decision 0008)

- [x] **1. `AUTOINCREMENT` and `scripts/migrate_autoincrement.py`.**
  `sqlite_autoincrement=True` on every table with an integer id; a
  one-shot script recreates the existing tables with it, keeping rows and
  ids, with a test on a copy of a populated database. Run on
  `~/.local/share/newstool/data.db` on 2026-10-23 (backup at
  `data.db.bak-20261023`); it had no `telegram/state` to migrate.
- [x] **2. Ids in the DTOs.** `id: int | None` on `SourceItem` and
  `Artifact`; an `Annotation` DTO (`id`, item id, `processor`, `key`,
  `updated_at`, `value`).
- [x] **3. `--item` replaces `--uid`.** `ProcessingScope` takes item ids;
  `scope_options` drops `--uid` and adds a repeatable `--item`, in
  `enrich`, `remix` and `inspect`.
- [x] **4. Shared selection queries** in `Database` and `Application`:
  `get_items(scope)` as it was, `find_annotations(scope, processor, key,
  annotation_ids)`, `list_artifacts(remixer, names=, limit=)`, plus
  `get_annotation_keys(items)`, the annotation ids and keys of many items
  in one query for the items listing.
- [x] **5. `inspect items|annotations|artifacts`** with `--format
  table|json`; remove `items`, `annotations`, `artifacts` and `artifact`.
  Tests for id parsing, JSON output and missing ids.
- [x] **Docs, when done:** propose the `README.md` (usage) and
  `ARCHITECTURE.md` (`cli.py`, `models.py`) updates.

## Sinks and the delivery ledger (decision 0007)

- [x] **1. `deliveries` table and its `db.py` API**, with tests. DTOs, as
  in the rest of the module:
  - `queue_item_deliveries(sink, scope, requires)` (reuses the `requires`
    join of `get_unprocessed_items`) and `queue_artifact_deliveries(sink,
    remixers, since, names)`: rows for the candidates without one.
  - `get_item_deliveries(sink, scope, statuses)` and
    `get_artifact_deliveries(sink, statuses, names)`: rows with their
    subjects, in FIFO order. Eligibility, backoff and every state change
    (`sending`, `done`, `error`, requeue, resolve) live in the sinks and
    `Application`, saved with `save_delivery(delivery)`.
  - `find_deliveries(scope, sink, status, artifact_names)`, for `inspect
    deliveries`, `deliveries resolve` and `delete`.
  - `last_delivery_by_source(sink)`: time of the last `done` delivery per
    source (replaces `last_post`).
- [x] **2. `sinks.py`, `Application` and CLI.** `Sink`, `BaseItemSink`,
  `BaseArtifactSink`, `UnavailableSink`; `Application.run_sink` and
  `Application.deliver`, in configuration order; `deliver [SINK]` with
  `--requeue`, `--force` (requires `--item` or `--artifact`) and the scope
  options; `inspect deliveries` and `deliveries resolve`; `run` (all four phases, non-zero
  exit on failures); the exclusive lock file for writing commands.
- [x] **3. `telegram` item sink and `scripts/migrate_telegram_state.py`**
  (`posted` → `done` rows with `message_id`, `queue` → `queued` rows;
  `watermark` and `last_post` dropped). Run it before the first
  `deliver telegram`.
- [x] **4. Dated `digest` names** (`<source>/<since>_<until>`) **and the
  `telegram_artifacts` sink** (`sendDocument`, option `artifacts`).
- [x] **Docs, when done:** propose the `ARCHITECTURE.md`, `README.md` and
  `SPECIFICATION.md` updates.

- [x] **5. `delete items|annotations|artifacts`** (decision 0008), with the
  `inspect` selection: non-interactive, cascading, items and artifacts with
  deliveries skipped with a warning unless `--force`, annotations per
  processor; takes the write lock.

Risks:

- If the migration fails, the chat gets the last `lookback` hours again.
- `migrate_autoincrement.py` rewrites every table of the real database:
  back it up first, with the SQLite backup API (README, *Data and backups*).
- An existing `telegram:` section with `interval` at the top level is now
  rejected: it moves to the `telegram:` subsection (`config.example.yaml`).

---

## Done

- [x] **Plugin bundles with `foundation.plugin.Register`** (decision 0003, revised):
  one `plugins` namespace and config section; entry points validate their
  own options (pydantic, with defaults) and return objects declared under
  the `Provider`/`URLProvider`/`Processor`/`Remixer` protocols. `llm`
  bundles `summarize`, `tagger` and the new `embed`; `grouping` bundles
  `singlelink`, `avglink` and `embeddings`, which now reads stored
  embeddings.
- [x] **LLM plugins** (decision 0006): the `LLM` protocol (`prompt`,
  `embed`) and the `ollama` backend; `llm` split into the `summarize`,
  `tagger` and `embed` plugins, which pick an LLM by name and get it from
  the `services` every entry point receives.
- [x] **Secrets**: no rotation needed (never committed; owner's call).
- [x] **External scripts**: none existed outside `scripts/`. The embeddings
  experiment became the `grouping_embeddings` remixer (single-link over tag
  overlap blended with tag embeddings), sharing `single_link_groups` with
  `grouping_singlelink`; the script is gone.
- [x] **`.env` support** (`python-dotenv`): `${VAR}` reads the environment,
  then a `.env` next to the config file.
- [x] **No database rebuild needed** (owner's call).
- [x] **CLI inspection commands**: `items` (scope options), `annotations`
  (preview table; `--key` prints full values), `artifacts` (metadata, via
  the new `Application.list_artifacts`) and `artifact` (content to stdout,
  metadata to stderr; missing is an error). Plain under `DISABLE_RICH`,
  syntax-highlighted on a terminal otherwise.
- [x] **Tests updated** to the reworked core, plus `Application`, remixer and
  identity coverage (73 tests).
- [x] **`foundation.dblib` and `foundation.plugin` declare `__all__`.** The
  shared `configure_connection` was tried and dropped: `dblib` is a shortcut
  for direct `sqlite3` use, and newstool, on SQLAlchemy, keeps its own
  `SQLITE_PRAGMAS`.
- [x] **`rssfeed`** takes the newest `max_items` items, newest first, and
  emits the required channel `<description>` (plus `<link>` when configured).
- [x] **TECH-DOC reconciliation** (decisions 0001–0004): source `id` required
  and items keyed by `(source id, uid)`, `uri` not unique; `${VAR}`
  expansion for secrets in `config.yaml`; plugins loaded with
  `foundation.plugin.ClassLoader`; remixers as their own plugin type and
  config section (`rssfeed`, `grouping_*`, sharing `GroupingRemixer`);
  `Application` as the single entry point with a private database, query
  facade, `enrich`/`remix` phases in config order and annotation deletion
  (which also deletes the state); `--force` resets attempts; `version` no
  longer accepted from config, and unknown plugin params rejected;
  annotation and artifact contents in the shared `DiskStorage`; pipelines
  moved to `scripts/pipeline_url.py`.
- [x] **One output rule**: `summarize` no longer writes artifacts and
  `markdownify` emits only `markdown`.
- [x] **CLI**: `import`, `import-url --source`, `enrich [PROCESSOR]`,
  `remix [REMIXER]`; `--log-level`/`-v`; `DISABLE_RICH` plain output;
  import progress and per-source error summary; run summaries as tables.
- [x] **Cleanup**: removed `ipdb.set_trace()` from `theguardian`, unused
  provider `NAME`s and constants, dead commented code, the `markdownify`
  docstring copied from `rssfeed`, `_get_or_create_source(_bulk)`, unused
  HTTP exceptions and the env-var fallbacks in processors; one Ollama client
  helper (`llm.py`, default port 11434); `castelloninformacion` no longer
  mutates its source; the `group_events*.py` scripts duplicated by the
  grouping remixers are gone.
- [x] **Application core (`newstool/app.py`).** `App` moved out of the CLI:
  wiring plus `import_source`, `import_url`, `run_processor`, `run_pipeline`;
  reads go through `App.db`. `cli.py` and the `group_events*` scripts use it.
- [x] **Reprocess changed content.** `processing_state.content_sha256` records
  the content each run used; a different one makes the item eligible again
  with fresh retries.
- [x] **Processor dependencies (`REQUIRES`).** `summarize`/`tagger` need
  `markdownify`, `telegram` needs `summarize`; only items the upstream
  finished on current content are picked up, so upstream skips no longer
  become downstream errors. Full failures raise plain exceptions.
- [x] **One transaction per processor result** (`Database.record_result`).
- [x] **`summarize` and `tagger` read `markdownify.markdown`.**
- [x] **SQLite connection settings** match `foundation.dblib.SQLite3DB`
  (foreign keys, WAL, ...); item foreign keys are `ON DELETE CASCADE` in the
  models.
- [x] **Bulk annotation reads** (`Database.get_annotation_values`); the three
  scripts share `load_tagged_items` from `_grouping_scoring`.
- [x] **Artifacts.** `Artifact` DTO, `DBArtifact.from_dto/to_dto/update`,
  `Database.get_artifact`. `telegram` stores `message_id` as an annotation
  and never posts an item twice.
- [x] **Re-imported `csjuntasgobierno`.** Fixed the HTTP client advertising
  `br`/`zstd` without decoders (castello.es answered with raw brotli); 1246
  items now hold their PDFs.
- [x] **Content storage.** Item contents moved out of SQLite into a
  `foundation.storage.DiskStorage` keyed by sha256 (`db.content_dir`).
  `source_items.content` replaced by `mimetype` + `content_sha256`; text is
  always UTF-8; processors load content on demand via `Database.get_content`.
- [x] **Removed `save_source_items`** and its tests; `upsert_source_items` is
  the only write path. The commented-out block in `_get_or_create_source_bulk`
  is gone too.
- [x] **Removed `newstool/filestore.py`** (`BufferedStore`), superseded by
  `foundation.storage`.
- [x] **Keep cleaned HTML at ingestion instead of markdown.** Providers keep
  `main_node` and its ancestors with `prune_to_spine`, drop cruft with
  `drop_selectors`, and store the HTML. Markdown is the `markdownify`
  processor's job.
- [x] **Use `SourceItem.from_data()`** in `App.import_source`.
- [x] **Swap `save_source_items` → `upsert_source_items`** in `App.import_source`.
- [x] **Gate the debug pickle dump behind `NEWSTOOL_PICKLE_CACHE`.**
- [x] **Configuration-defined pipelines.** `pipeline-url` runs an ordered list
  of configured processor steps; step params override processor defaults.
- [x] **Telegram message formatting.** `sendPhoto` with an escaped HTML caption
  (title, summary, link) when the item has an image, `sendMessage` otherwise.

---

## Backlog: ideas and pending plans (flagged, not scheduled)

- **Force rich without a terminal** (e.g. for `watch` or `ssh` without a
  pty), in foundation. Only if P2's TTY detection gets in the way.
- **Per-item progress** inside processors, sinks and imports. P2 left it
  out to keep the plugin contracts as they are (a callback would change
  `Processor.process` and `Sink.deliver`); revisit if unit rows fall short.
- **Concurrent imports.** Releasing replaced contents can race with another
  process starting to reference the same content. Add a lock if imports ever
  run in parallel.
- **HTTP client through `Services`.** Plugins outside providers fetch with
  bare `requests` (e.g. `telegram` downloads item images to upload them),
  without the shared `HTTPClient`'s headers and cache. Share one in
  `Services` so every plugin uses it.
- **Forcing a workflow's process runs** (2026-10-28, idea): find a mechanism
  to force reprocessing from a workflow. Today `process -w NAME [PROCESSOR]
  --force` selects by processor, so it forces every entry of that processor
  (e.g. both `summary` and `summary/ca`), not one key.
- **PDF text extraction.** `markdownify` skips non-HTML items; PDF items need
  their own extraction step before `summarize`/`tagger` can use them.
- **Alembic.** Not needed while the database can be rebuilt from the
  sources.
- **Generalizing `BaseProvider`/`IndexSiteProvider`** for non-news sources:
  wait for a second concrete use case.
- **Save annotations and artifacts as soon as possible**: they stay in
  memory until the loop finishes.
- **Per-source `process` overrides** (`sources>process`): the `process`
  section exists (see the plan above); per-source runs or options are next.
  Proposed shape (2026-10-27, not agreed): the same list format as `process`; an entry
  whose key matches a default entry replaces it, a new key adds a run.
- **Ledger per destination** (2026-10-27, idea; named deliveries came
  with the catalog's `sinks`, decision 0010): the ledger and pacing are per
  workflow, so two workflows referring to one sink entry each deliver to its
  channel. A record and an `interval` per destination would revise 0009.
  Wait until two workflows share a destination.
- **`inspect orphans`** (2026-10-28, agreed shape): list the ledger rows,
  annotations and artifacts of keys, remixers and sources the configuration
  no longer names, and delete them with the existing `delete` commands.
  Never delete from the configuration alone: several configurations may
  share a database.
- **`deliveries rename OLD NEW`**: renaming a workflow or delivery key
  redelivers its `lookback`; a rename keeps the ledger.
- **Ledger columns `workflow`, `key`, `sink`** instead of `workflow/key`
  in `sink`: when querying by workflow or knowing the plugin per row
  matters. Needs a migration.
- **Configurable input keys for consumers**: `summarize`/`tagger` read
  `markdown`, `telegram` `summary`, `grouping` `tags`; an option naming
  another key when a run writes, e.g., `summary/es`.
- **summary plugin: per-source prompt**: the prompt is configurable
  globally and per `process` entry; per source is pending.
- **google chat deliver plugin**
- **Backend-specific LLM options per use**: each use picks its LLM
  (`llm`, decision 0010) and `model`; `json_mode`/`context_length` stay
  explicit in the `LLM` protocol. An `llms` entry with other options covers
  most needs; revisit when a consumer needs a backend option per call.
- **`pyproject.toml` cleanup** (2026-10-28): the distribution is still
  named `news-aggregator` with the placeholder description, the `tagging`
  (ollama) and `feeds` (feedparser) groups duplicate main dependencies, and
  a stale `news_aggregator.egg-info/` remains. Do it with the `newstool`
  rename.
- **`run_each` stops a phase on the first failure** (2026-10-28, bug):
  `cli.py` wraps each run in `try/finally` without `except`, so one failing
  run skips the rest of its phase.
- **Delivery order options** (2026-11-10, idea): today the order is fixed,
  oldest first. Sinks deliver by `emitted_at`, then document id (emission
  order within a run), and `itemfeed` emits its items by publication time,
  or import time without one. Options to control it: a per-sink `order:
  oldest|newest` for its pending rows; per-applet emission order (e.g.
  `itemfeed` by publication or by import time); and a "newest only" mode
  that skips a backlog (e.g. after downtime, deliver the latest N and mark
  the rest `done`, instead of draining it at the `interval`).
- **Database layer audit** (2026-11-10, plan): review `db.py` code and
  schema, simplify and formalize where possible. It has gone through many
  architecture changes (decisions 0001, 0002, 0004, 0007, 0012, 0014, 0015,
  0016) and may carry leftovers or debt. Today: 7 tables (`sources`,
  `source_items`, `processing_state`, `item_annotations`, `apps`,
  `documents`, `deliveries`), ~1500 lines and ~67 methods in one
  `Database` class; the schema is created, never migrated, with one-shot
  scripts in `scripts/` (`migrate_applets.py`, `migrate_autoincrement.py`,
  the older `migrate_annotation_keys.sql`). Things to look at:
  - overlapping queries: `deliveries_of` vs `find_deliveries`;
    `existing_document_keys` vs `count_missing_routes`; filters applied in
    Python after the query (`Application.routed_documents` filters by
    route, then applies `limit`);
  - the DTO/ORM conventions (`from_dto`/`to_dto`/`update` on every model,
    `.claude/rules/database.md`) applied evenly, and no ORM row leaking;
  - which rules live in the schema (`UniqueConstraint`, `CheckConstraint`,
    cascades) and which only in Python, e.g. delivery states, the
    one-row-per-(sink, document) rule, document immutability;
  - the split between `processing_state` and `item_annotations`, and
    whether `sources` still earns its table;
  - the custom column types (`CustomJSON`, `UTCDateTime`) and index
    coverage for the queries actually run;
  - whether to adopt real migrations (e.g. a schema version) instead of
    one-shot scripts, and whether to split `Database` by aggregate (items,
    applets, ledger).
  Plan vs apply: audit first, as a written list of findings, before
  changing anything; any schema change needs a script with a test.
- **Configuration keys review** (2026-11-10, plan): review the names of
  the configuration file's keys, look for names that say better what they
  stand for, and make them consistent across subsystems. Seen so far, to
  confirm:
  - instance names: workflows use `name`, everything else `id`;
  - the type field changes per section (`provider`, `processor`, `llm`,
    `sink`, `app`); the `apps` section holds *applet* instances under
    `app:`, and `sink:` means the sink type in `sinks` but the route
    shorthand in `apps`;
  - one concept, two names: a processor entry's `key` vs `itemfeed`'s
    `annotation` for the same annotation key;
  - durations named differently: `every` (apps), `interval` (sinks),
    `wait` (`itemfeed`), `lookback` (`digest`, `grouping`),
    `cache.expiration`;
  - `plugins` holds defaults per *type*, not per plugin module (a module
    such as `telegram` may register several types);
  - `skip_default` and the implicit `default` workflow; `days` (renamed
    from `on`, a YAML 1.1 boolean); `storage_dir` / `cache_dir`.
  Renames break existing configuration files (and `${NEWSTOOL_*}`
  overrides), so batch them in one change with a decision record, an
  update of `config.example.yaml` and the docs, and clear errors for the
  old names. Stored data keyed by config values (source `id`s, process
  `key`s, applet and sink `id`s) must not change meaning.

---

*Last updated: 2026-11-10*
