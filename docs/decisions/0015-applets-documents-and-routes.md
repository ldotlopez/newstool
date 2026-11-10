# 0015: Applets, emitted documents and routes

- **Status:** accepted
- **Date:** 2026-11-06
- **Supersedes:** 0007 (sinks and the delivery ledger), 0012 (delivery ids,
  state and forced send), 0014 (ledger rows by subject)
- **Revises:** 0003 (the remixer type is removed; applets are a plugin
  type), 0004 (artifacts are removed; document contents follow the same
  storage path), 0009 (workflows keep only `sources` and `process`), 0010
  (`remixers` and `sinks` leave the workflows; applets and sinks are
  global instances)
- **Revised:** 2026-11-10, by 0016 (routes reach re-emitted documents;
  `set-status --sink` with filters ignores routes; `apps run --no-deliver`
  and `--app` delivering to its own sinks; pacing overrides on `deliver`)

## Context

A remixer produces artifacts from the items in a `ProcessingScope` that its
workflow or the CLI hands it, every time its workflow runs. The outputs
that motivate it do not fit that shape:

- a weekly summary, a daily feed, an hourly digest of a subreddit under
  specific conditions: each one decides *when* it runs, not the workflow's
  cron line;
- "what is new since the last run" cannot be expressed: a remixer keeps no
  state, so `digest` approximates it with `lookback` and periods in the
  artifact name;
- its inputs vary: a source, several, the output of another remixer, a
  window of 24 hours or of a calendar week.

Delivery is tied to the same structure: sinks are entries of a workflow and
deliver its items or the artifacts of named remixers, so the sink knows
about items, annotation keys (`summary`), `requires` and per-source FIFOs.
Building the message is the sink's job, though only the producer knows what
it wants to say.

## Decision

### Configuration

```yaml
sinks:
  - id: tg-main
    sink: telegram
    options: {chat_id: ${TELEGRAM_CHAT_ID}, interval: 30m}
  - id: feed-file
    sink: file
    options: {path: /srv/www/{app}.xml}

apps:
  - id: castellon-items
    app: itemfeed
    options: {sources: [castellonplaza], annotation: summary}
    sink: tg-main                     # the applet has one output
  - id: weekly-digest
    app: digest
    days: [mon]
    at: "07:00"
    options: {sources: [castellonplaza]}
    routes:
      digest: [tg-main]
  - id: headlines
    app: feed
    every: 1h
    options: {sources: [castellonplaza], max_items: 10}
    sink: feed-file
```

- `sinks` and `apps` are root sections. Ids are unique within each section,
  and `/` is not allowed in them. `plugins` keeps the defaults per type
  (decision 0010) for applets and sinks too.
- Workflows (the root and `workflows`) keep `sources` and `process`; their
  `remix` and `deliver` entries and the `remixers` section are removed.

### Applets

- **Type.** `Applet` and `AppletType` are `typing.Protocol`s in
  `applets.py`. An applet class declares `options_model` and `outputs`: a
  mapping of output name to the content types it emits. It is built once
  per instance with its options and `Services` (decisions 0010, 0013).
- **Methods.**
  - `is_due(now, run, schedule) -> bool`: whether the instance runs now.
    `BaseApplet` defers to the instance's `schedule`; an applet may
    override it.
  - `run(now, run, reader) -> AppletResult`: `run` is the instance's
    `AppletRun` (below), `reader` the read interface. It returns the new
    state and the documents it emits. Raising `PluginFailure` fails the
    run.
- **Requirements.** `AppletType.requirements(options)` returns the source
  ids (None: every source) and annotation keys a run reads. At startup an
  unknown source is a configuration error, and so is an annotation key
  that no process run writes on any of those sources, the rule process
  runs already follow (decision 0009).
- **No external side effects.** An applet never sends anything and never
  writes to the database; the core stores what it returns.

### Schedule

- An instance takes `every` (a duration, default `0`), `at` (local
  `HH:MM`, optional) and `days` (weekdays `mon`…`sun`, optional), next to
  `app`, not in `options`. Local time is the system's time zone. The key is
  `days`, not `on`: YAML 1.1, which PyYAML reads, takes `on` for `true`.
- An instance is due when all hold:
  - it has never succeeded, or `now >= last_success + every`;
  - with `days`, today is one of those days;
  - with `at`, the local time is at or past `at` today and `last_success`
    is before today's `at`.
- Without any of them, the instance is due on every `apps run`.
- A failed run leaves `last_success` unchanged, so the instance is due
  again on the next `apps run`.

### Runs and state

- **Run record.** Table `apps`, one row per instance id: `last_started`,
  `last_success`, `last_error`, `state` (JSON, opaque, read only by that
  applet). `AppletRun` is its DTO; an instance without a row gets an empty
  one (no times, `state = None`).
- **Windows belong to the applet.** It computes its window or cursor from
  `now`, `last_started`, `last_success` and its state, and keeps the
  cursor in its state.
- **One run at a time.** `apps run` takes the write lock every writing
  command takes (an OS file lock next to the database, released if the
  process dies), so two runs never overlap: the second fails at once.
- **Atomic commit.**
  - `last_started` is committed on its own when the run starts.
  - A successful run stores, in one transaction: its documents (contents
    written to `DiskStorage` first), their delivery rows, its state, and
    `last_success = last_started`, clearing `last_error`. Content files
    left by a failed commit are unreferenced, and harmless since storage
    is content-addressed.
  - A failed run stores only `last_error`; its state and window stay as
    they were.
- **Emitting on an undeclared output**, with an undeclared content type,
  or twice under one key in one run, fails the run.

### Reading

The `reader` passed to `run` is an `AppletReader` over the database:

- `items(*, sources, published_since, published_until, imported_since,
  imported_until, limit, newest_first) -> list[SourceItem]`;
- `annotations(items, key) -> dict[ItemKey, JsonCompatible]`, by item key,
  only for items that have the key;
- `content(item) -> bytes`;
- `documents(*, app, output, emitted_since, emitted_until, limit,
  newest_first) -> list[Document]`, with their content.

Every filter is optional; time bounds are `>=` since and `<` until. Another
instance's state is not readable.

- **`imported_at`.** `source_items` gets `imported_at`, set on an item's
  first import and never changed. An incremental window filters by it: an
  item imported late with an old `published_at` is still new. A changed
  item keeps its `imported_at`; its new annotations do not bring it back
  into an incremental window.

### Documents

- **Emitted document** (`EmittedDocument`): output, key, content
  (`str`), content type, and optional `title`, `url`, `image_url` that
  sinks may use.
- **Stored document** (`Document`, table `documents`): the above plus `id`,
  `app` (the instance id), `emitted_at` and the content's `sha256`; the
  content goes through `DiskStorage` (decision 0004).
- **Immutable.** `UNIQUE (app, output, key)`. A document emitted again
  under an existing key is ignored, with no delivery rows. Keys are
  deterministic (`2026-W45`, `item:1234`), so a rerun emits nothing twice.
- **An output without a route** still stores its documents for other
  applets to read.

### Sinks

- **Type.** `Sink` and `SinkType` stay in `sinks.py`: a sink type
  declares `options_model` and `accepts`, the content types it renders; a
  sink has `send(document) -> JsonCompatible`, the external reference.
  Raising `PluginFailure` fails that delivery.
- **Instances are global** (`sinks`): `id`, `sink`, `options`. Every sink's
  options include `interval` (default `0`), `max_per_run` (default 5) and
  `max_retries` (default 3); the destination (`chat_id`, `path`) and
  presentation choices (`markdown`, `link_preview`) are the type's own.
- **A sink renders documents only.** It knows nothing of items or
  annotations. `telegram` sends text with the document's image and link
  when present, or the document as a file when it does not fit in a
  message; `googlechat` sends a card; `file` writes the content to its
  `path` (absolute), replacing it, where `{app}`, `{output}` and `{key}`
  are substituted (`/` in a key becomes `_`).

### Routes

- `routes: {<output>: [<sink id>, …]}` routes an instance's outputs.
  `sink: <sink id>` is shorthand for an applet with exactly one output.
- Configuration errors at startup: both keys in one instance; `sink` on an
  applet with several outputs; a route to an unknown output or sink; an
  output whose content types are not all in the sink's `accepts`.

### Deliveries

- **Rows.** Table `deliveries`: `id` (`AUTOINCREMENT`), `sink` (sink
  instance id), `document_id` (`ON DELETE CASCADE`), `status`, `attempts`,
  `last_error`, `external_ref`, `created_at`, `updated_at`;
  `UNIQUE (sink, document_id)`.
- **Created when a document is stored**, one per route of its output, as
  `queued`. Adding a route delivers only documents emitted afterwards;
  older ones are queued by hand (`deliveries set-status`).
- **States** as before: `queued`, `sending`, `done`, `error`. `sending` is
  committed on its own before `send`; a row left `sending` is never retried
  automatically. `error` rows are retried with the processors' backoff
  while `attempts < max_retries`.
- **Pacing per sink instance**, over every row of that sink: pending rows
  (queued, or error with attempts left and backoff elapsed), oldest
  document first, one per `interval` since the sink's last `done`, at most
  `max_per_run`. A failing row does not hold back others.
- **A row whose sink is no longer configured** is left as is and reported
  by `deliver`.

### CLI

- `run -w W`, `import`, `process`: import and process only. `remix` is
  removed.
- `apps run [--app ID]… [--force] [--dry-run]`: runs the due instances
  (all selected ones with `--force`), then a delivery pass over every
  sink. `--dry-run` runs the applets and shows, per instance, whether it
  is due, the documents it would emit (new or ignored) and its new state;
  it writes nothing and delivers nothing.
- `deliver [--sink ID]… [--dry-run]`: the delivery pass alone.
- `apps reset ID [--with-documents] [--dry-run]`: deletes the run record.
  `--with-documents` also deletes the instance's documents and, by cascade,
  their delivery rows, so what it emits again is delivered again.
- `inspect apps`: instance, type, schedule, last started, last success,
  last error, next due time when computable from the schedule.
- `inspect documents`, `delete documents`: filters `--app`, `--output`,
  `--key`, `--since`/`--until` (on `emitted_at`), `--document ID`.
  `delete documents` refuses documents with rows that are not `done`,
  naming them. `inspect content` shows a document's content by sha256.
- `inspect deliveries`, `delete deliveries`, `deliveries send`,
  `deliveries set-status`: filters `--sink`, `--delivery ID`, `--status`
  and the document filters above. `-w` is gone from them. `set-status`
  with `--sink` creates rows for the selected documents routed to that
  sink that have none (`--all`: every one routed to it), in the `--as`
  state, under the rules of 0014 (`--overwrite`, `--dry-run`).
- `inspect artifacts`, `delete artifacts` and every `--artifact` filter
  are removed.

### Plugins

- `feedgenerator` → applet `feed`, output `feed`
  (`application/rss+xml`); `digest` → applet `digest`, output `digest`
  (`text/markdown`), keys `<source>/<since>_<until>`; `singlelink`,
  `avglink`, `embeddings` → applets with one output, `groups`
  (`application/json`). `feed` and the grouping applets emit anew on every
  run, keyed by the run's UTC time.
- `telegram` and `googlechat` as item sinks → applet `itemfeed`: options
  `sources`, `annotation` (the key whose value is the text) and
  `since_first_run` (default `true`); on its first run it stores the
  current time as its cursor and emits nothing, then emits one document
  per item imported since the cursor that has the annotation, key
  `item:<source>/<uid>`, with the item's title, URL and image. An item
  whose annotation is missing is left for a later run while it stays
  within `wait` (default `1d`) of its import.
- `telegram` and `telegram_artifacts` become one document sink `telegram`;
  `googlechat` becomes a document sink; `file` is new.

### Migration

`scripts/migrate_applets.py` (with a test):

- adds `source_items.imported_at`, filled with `published_at`;
- drops `artifacts` and the old `deliveries`, and deletes from
  `DiskStorage` the artifact contents no item or annotation references;
- creates `apps`, `documents` and the new `deliveries`.

`scripts/migrate_telegram_state.py` and `scripts/migrate_feed_names.py`
are removed: they read or renamed artifacts and the old ledger, which no
longer exist. `config.example.yaml` is rewritten to the shape above.

## Rejected options

- **Applets that call sinks directly.** Every applet would reimplement the
  ledger, pacing and retries, and a crash between a send and saving the
  state would send again: the problem of decision 0005.
- **Delivery rows that copy the content per route.** A document routed to
  two sinks would be stored twice, and an output without a route would be
  stored nowhere for other applets to read.
- **Delivery rows that reference a regenerable artifact.** Regenerating it
  changes what a pending delivery sends.
- **Delivery parameters in the document** (`chat_id` and the like).
  Destinations are declared once per sink instance and routed in the
  configuration; a document with its own destination breaks the pacing of
  its sink.
- **Pacing per applet or per document.** Two applets routed to one chat
  would ignore each other.
- **Routing a whole instance to sinks, with no named outputs.** An applet
  with two kinds of output needs two instances, each with its own state
  and its own reads of the same items.
- **A window computed and advanced by the core.** Calendar periods and
  external cursors do not fit `[previous end, now)`.
- **No run record in the core.** Nobody could tell when an applet last ran
  or why it failed.
- **Cron expressions for the schedule.** They need a dependency;
  `every`/`at`/`on` cover the cases at hand, and `is_due` covers the rest.
- **Schedules only in code.** Each applet would invent its own format.
- **`run -w` running the applets.** Every workflow's cron line would
  trigger every applet; applets are not tied to workflows.
- **Delivering a new route's backlog**, whole or limited. A new route can
  flood its destination; `set-status --as queued` queues what is wanted.
- **Automatic document retention.** Deletes on every run; `delete
  documents` is explicit.
- **Filtering only by `published_at`.** Incremental applets miss items
  imported late with an old publication date.
- **Reading other instances' state.** Couples applets to each other's
  private formats; emitted documents serve that purpose.
- **Visible artifacts next to emitted documents.** Two output mechanisms;
  a `file` sink publishes and documents are readable.
- **Keeping the old tables as `legacy_*`**, or converting the item ledger
  into `done` documents. Nothing would read the first; the second is a
  complex script for what `since_first_run` gives.
- **A lock row in `apps`.** A crash leaves it held; a file lock is released
  by the OS.
- **A file lock per instance.** The write lock already keeps writers from
  overlapping, and two locks would only let `apps run` overlap with
  commands it must not.
- **`on` for the weekdays.** PyYAML reads the key as `true`.
- **A daemon that schedules applets.** A frequent cron line and the due
  check give the same result with no long-running process.

## Consequences

- Two cron lines: `run -w W` per workflow, and `apps run` every few
  minutes.
- Sinks are simpler: `ArtifactDeliveryOptions`, `SubjectKindError`,
  `lookback`, `requires` on sinks and the per-source FIFO disappear.
  Ordering is oldest document first across the sink.
- Existing artifacts and the delivery history are lost; item applets start
  from their first run, so nothing already posted is sent again.
- `imported_at` of items imported before the migration is their
  publication date: a calendar-window applet over import time sees them as
  imported when published.
- An applet's state format is its own: an incompatible change needs
  `apps reset`.
- An instance's `id` is part of its documents' identity and its run record:
  renaming it starts it from scratch, as renaming a source does.
- Deleting a document frees its key: an applet that emits it again creates
  it anew. Applets with a cursor do not go back.
- `apps reset --with-documents` also removes what other applets read from
  that instance.
- An applet that emits anew on every run (`feed`, the grouping applets)
  stores a document per run until `delete documents` removes old ones.
- `apps run` holds the write lock for the whole run, LLM calls included, so
  a `run -w W` that starts meanwhile fails at once; cron lines should not
  overlap.
