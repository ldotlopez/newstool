# newstool: specification

Consolidated version · 23 October 2026

This document defines what newstool does, independently of how it is
implemented. It is self-contained: it is the reference for rebuilding the
application. [ARCHITECTURE.md](ARCHITECTURE.md) describes the current
implementation and [decisions/](decisions/) records why it is that way.

## 1. Purpose and scope

newstool is a pipeline for **acquiring, enriching, remixing (with
applets) and delivering** content,
built for news and meant to grow into a personal collector of generic
information. External tools that consume its results are outside the project
and reach it only through the `Application` class.


## 2. Glossary

| Term | Definition |
| --- | --- |
| **Source** | An entry of the `sources` configuration section, with `id`, `name`, `provider` and `url`. Its identity is its `id`. |
| **Workflow** | Which sources to import and the process runs on them. `default` is built from the catalog; `workflows` adds more. |
| **Plugin** | A bundle of plugin types: named classes of providers, processors, applets, sinks and LLMs. Every bundle is loaded; nothing is built until a run needs it. |
| **Catalog** | The configured uses of the plugin types (`llms`, `sources`, `processors`), each with its options; an `id` lets workflows refer to one. Applet and sink instances (`apps`, `sinks`) are global and always have an `id`. |
| **Provider** | Object that knows how to handle one kind of site. One implementation serves every URL with the same structure. |
| **Item** | A unit of acquired content. Key: `(source id, uid)`. Its `uri` is just another field and is not unique. It also has a numeric id, a local handle to select it that is never reused but changes if the database is rebuilt. |
| **uid** | The item's identifier within its source, produced by the provider. It must be deterministic and stable across runs; how it is computed is up to the provider. |
| **Annotation** | Data derived from an item by a processor run. Key: `(item, key)`; the processor that wrote it is recorded but is not part of the key. |
| **Processor** | Object that produces annotations for one item at a time. Each process run uses a processor with its own options, and writes one key. |
| **Applet** | Object that decides when it runs, reads what is stored, and emits documents on its named outputs, keeping a state of its own. Each instance (`apps`) uses an applet type with its own options and schedule. |
| **Document** | What an applet instance emitted on one of its outputs (newsletter, RSS, a message per item...). Key: `(instance, output, key)`, the key chosen by the applet. Never rewritten. |
| **Route** | Which sink instances receive the documents of an instance's output, declared in the configuration. |
| **Sink** | Object that delivers documents to the outside world (e.g. posts them to a chat, writes a file). Each instance (`sinks`) has its own destination and pacing. |
| **Delivery** | The record of delivering one document through one sink instance. Key: `(sink instance, document)`. It records an external fact and is never regenerated. |

## 3. Configuration

A single YAML file with the sections `plugins`, `llms`, `sources`,
`processors`, `workflows`, `apps`, `sinks`, `cache` and `db`. All of
them are optional. Each source names its provider explicitly:

```yaml
plugins:
  <type>: {...}            # defaults of the type's options in every use
llms:
  - <llm type>             # the first serves the uses that name none, or
  - {llm: <type>, id: <id>, options: {...}}
sources:
  - id: <stable id>        # required
    name: <readable name>
    provider: <provider type>
    url: <url>
    options: {...}         # over the provider's plugin section
    skip_default: false    # true: only the workflows that name it use it
processors:
  - <processor type>       # a run with the section's options, or
  - processor: <processor type>
    id: <id>               # lets workflows refer to it
    key: <annotation key>  # default: the processor's own
    options: {...}         # over the processor's plugin section
    skip_default: false    # true: left out of `default`
workflows:
  - name: <name>
    sources: [<source id>, ...]
    process: [...]         # catalog ids, type names or entries without id
sinks:
  - id: <id>               # required
    sink: <sink type>
    options: {...}         # destination, interval, max_per_run, max_retries
apps:
  - id: <id>               # required
    app: <applet type>
    every: <duration>      # due this long after its last success
    at: "HH:MM"            # local time: once a day from then
    days: [mon, ...]       # only on these weekdays
    options: {...}         # over the applet's plugin section
    sink: <sink id>        # an applet with one output, or
    routes: {<output>: [<sink id>, ...]}
cache:
  expiration: <duration>   # HTTP cache lifetime: seconds, or 5m, 2h, 3d
db:
  uri: <sqlalchemy uri>    # default: <user data dir>/newstool/data.db
  content_dir: <path>      # default: <user data dir>/newstool/content
```

`${VAR}` references in values are replaced with environment variables when
the file is loaded; comments and keys are not expanded. Secrets (API keys,
tokens) are always passed this way.

Every plugin is loaded; its types are named, uniquely per kind, and
`plugins.<type>` sets the defaults of the type's options for every use. A
use's options are the type's defaults, then its section, then its own
`options`, merged key by key in nested mappings (any other value, lists
included, replaces). Every section and use is checked at start-up, whatever
the workflow, so a bad option fails every command with its path
(`plugins.<type>.<option>`, `sources.<id>.options.<option>`,
`apps.<n>.options.<option>`). An object is built only when a run needs it.

An `id` names a catalog entry so that workflows can refer to it; it cannot
be a type's name. A workflow entry is a catalog id, a type name (the type
with its section's options) or an entry of its own, without `id`; a
reference cannot change the entry's options. An object that uses an LLM
names it by id or type (`llm:`), or takes the first of `llms`; a name that
resolves to none is a configuration error.

### 3.1 Workflows

`default` uses every source without `skip_default: true` and runs, in
order, every catalog processor without it. Each entry of `workflows` names
its sources and its process runs. A command runs one workflow, `default`
unless another is named (`run --all` runs each in turn, `default` first),
and each phase only touches that workflow's sources. Applets and sinks belong to no workflow (§4.3).

- A process key is written by one run within a workflow. On sources shared
  by workflows, one processor type writes it; other options for it are a
  warning (the first run to process an item writes it). Workflows with
  disjoint sources may write the same key, since annotations belong to
  items.
- Every key a process run reads must be written by a process run on its
  workflow's sources, in any workflow.
- Ids, workflow names and output names are lowercase letters, digits, `_`
  and `-`; `default` is reserved.

A source's `id` is part of its items' key, so it must be stable; its `url`
and `provider` can change without losing items.

## 4. Phases

### 4.1 Import

Each source is queried through its provider's plugin, which lists the
articles, extracts their content and creates or updates one item per
article.

- **Dates:** each item stores `published_at`, `modified_at` and
  `imported_at`.
  - New item: the first two come from the provider; a missing one takes the
    current time. `imported_at` is the time of its first import, and never
    changes.
  - Changed item: `modified_at` takes the provider's value if it is newer
    than the stored one (it never moves backwards); if the provider does not
    emit it, it takes the current time. `published_at` is set once and never
    overwritten.
- **Listed dates:** a provider may list its items before fetching them, each
  with the date its index shows. A stored item listed with a date that is not
  newer than its `modified_at` is not fetched. One listed as newer is
  fetched; once it has been checked, its `modified_at` takes the listed date
  whether or not it changed, so it is not fetched again until a later date is
  listed. If its fetched date is not newer than the stored one, it is not
  updated. Items listed without a date are always fetched.
- **Change detection:** an item is changed if any of `title`, `uri`,
  `mimetype`, content (`content_sha256`) or `data` differs. Dates do not
  count. Re-importing an identical item writes nothing but a listed date
  (above).
- **Interrupted import:** the items fetched before an error are stored.
- **Changed item:** it is overwritten. Its annotations are kept, but if its
  content changed, all its processing states become eligible again with
  attempts reset to zero. Documents are not invalidated.
- **Duplicates:** the same article in two sources is two items, even if both
  sources use the same provider. Deduplication, if wanted, is the applets'
  job.
- **Source removed from the YAML:** its items are kept and stop being
  updated. Applets still see them.

### 4.2 Processing

Processors create annotations on items. `process` runs the workflow's
process runs in order; each run writes one key, by default the processor's
own, and keeps its own processing state per item under that key (§3.1). A
run's options override those of the processor's plugin section.

- **Dependencies:** a run declares the key it reads. It only picks up items
  whose run of that key finished successfully on their current content; the
  rest wait without spending attempts, also under forced regeneration. If
  the upstream run finished but the needed annotation is missing, the
  result is a retryable failure.
- **Possible results:**
  - **Success:** the annotation is saved.
  - **Skip:** the item does not apply to this processor. It is permanent for
    that content: it is only re-evaluated if the item's content changes or
    regeneration is forced.
  - **Retryable failure:** no annotation.
- **Retries:** at most 3 attempts by default, configurable with
  `max_retries`. Attempts are spaced by an exponential backoff of
  `60 s · 2^(n-1)`, capped at 24 h.
- **Attempt counter:** reset to zero on success or skip, when the item's
  content changes, when its annotations are deleted and when regeneration is
  forced from `Application`.
- **Cardinality:** one annotation per `(item, key)`; regenerating overwrites
  it.
- **Processor version:** each processor can declare a version in its code.
  When it changes, the items it had finished successfully are processed
  again without forcing; skipped items and exhausted failures are not.
- Changing a processor's or an entry's configuration regenerates
  **nothing**. Annotations are kept until the item changes, the processor's
  version is bumped, or they are regenerated or deleted from `Application`.
- A processor that no workflow runs is never built.

### 4.3 Applets

Applets are a plugin type of their own. Each configured instance decides
when it runs, reads items, annotations and the documents of any instance,
and returns its new state and the documents it emits. `apps run` runs the
instances that are due, then delivers.

- **When it runs:** an instance is due when its schedule allows it:
  `every` after its last success, on its `days`, once a day from `at`
  (local time). Without a schedule it is due on every `apps run`. An
  applet may decide otherwise. A forced run ignores the schedule.
- **Run record:** per instance, the start of its last run, the start of its
  last successful one, its last error, and an opaque state only that
  applet reads. The applet computes what each run covers (since its last
  success, a calendar week, a cursor of its own) from them.
- **Reading:** items filter by publication date and by import date; an
  incremental window uses the import date, so an item imported late with
  an old publication date is still new. Another instance's state is not
  readable.
- **Documents:** each has an output, a key, content and a content type,
  and optionally a title, a link and an image for the sinks. A key emitted
  again by the same instance and output is ignored, so a rerun emits
  nothing twice. Documents are never rewritten. An output without a route
  still stores them, for other applets to read.
- **Atomic commit:** a successful run stores its documents, their delivery
  rows and its new state at once. A failed run stores only its error; its
  state stays as it was, so the next run covers the same window again.
- Applets have **no external side effects**: they never send anything.
- **Requirements:** an applet declares the sources and annotation keys it
  reads; an unknown source, or a key no process run writes on any of those
  sources, is a configuration error.
- **Reset** deletes an instance's run record, so it starts from scratch.
  Its documents stay unless asked otherwise, so what it emits again under
  their keys is not delivered again.

### 4.4 Deliver

Sinks deliver the documents routed to them and record every delivery.

- **Routes:** each document a run emits, new or already stored, gets a
  `queued` delivery for each sink its output is routed to that it has none
  of (decision 0016). A route added later reaches the stored documents its
  applet emits again; older ones are queued by hand. Documents carry no
  delivery parameters: the destination and the pacing are the sink
  instance's. A route between an output and a sink that does not accept
  its content types is a configuration error.
- **States:** `queued`, `sending`, `done`, `error`. A delivery is marked
  `sending` before the external call; one still `sending` when a run starts
  was interrupted, its outcome is unknown, and it is never retried
  automatically: it is settled by hand as `done` or `queued`.
- **Retries:** failures are retried with the processors' backoff and
  `max_retries` (3 by default). Requeuing gives failures fresh attempts. A
  failure does not hold back other deliveries.
- **Order and pacing** are the sink instance's, over every document routed
  to it, oldest first: by emission time, then emission order within a run
  (document id). An applet that emits several documents in one run emits
  them oldest first; `itemfeed` orders its items by publication time, or
  import time for an item without one, then id. With an `interval`, one
  delivery once its last one is that old; and never more than `max_per_run`
  in a run. Two instances routed to one sink share its pacing. One
  delivery run may drop the interval, drop `max_per_run`, or replace it;
  retries still wait for their backoff.
- **Forced delivery** sends explicitly selected deliveries now, whatever
  their state, with no backoff and no pacing.
- **Marking by hand** gives the documents selected by filters a row of one
  sink in a chosen state (`queued`, `done` or `error`), routed to it or
  not, if the sink accepts their content types; without filters, every
  document routed to it. Existing rows change only when asked.
- A document is delivered at most once per sink instance, unless a
  delivery is forced or its row is deleted and created again.

## 5. API: the `Application` class

The single entry point for external tools: a Python API used in the same
process, not a network service. It offers:

- **Queries** of items, annotations, documents, applet runs and
  deliveries.
- **Running** import and process per workflow, applet instances (due,
  forced, or as a dry run) and the deliveries of each sink instance.
- **Forced regeneration** of annotations, which resets the attempt counter.
- **Deletion** of annotations, by processor, by item or both. Deleting also
  removes the processing state, so the item becomes pending again with
  attempts at zero.
- **Deletion** of items, with their processing state and annotations, and
  of documents with their deliveries; a document with a delivery that is
  not `done` is refused.
- **Resetting** an applet instance, optionally with its documents.
- **Changing the state** of ledger rows (`queued`, `done` or `error`, which
  also settles interrupted deliveries), **marking** the selected documents
  routed to one sink (rows created in a chosen state), **deleting** rows
  and **sending** them now, selected by id or by the filters of
  `inspect deliveries`.
- A **write lock**: commands that write take it, so two of them never run
  at the same time; the second fails at once.

The database is not exposed: every query goes through `Application`.

## 6. Storage

- **Items:** content on disk through `foundation.storage.DiskStorage`, keyed
  by its sha256. Metadata goes in the database (title, URI, MIME type,
  `content_sha256`, `data`, `published_at`, `modified_at`, `imported_at`).
- **Processing state:** in the database, per `(item, key)`: the processor
  that ran, status, attempts, last error, processor version and the
  `content_sha256` used.
- **Annotations and documents:** content is stored on disk through
  `foundation.storage.DiskStorage` and the database keeps the reference it
  returns. Their metadata:
  - Annotation: producer, referenced item, key, `created_at` and
    `updated_at`.
  - Document: instance, output, key, content type, title, link, image and
    `emitted_at`.
- **Applet runs:** in the database, per instance: last start, last success,
  last error and its state (JSON).
- **Deliveries:** in the database, per `(sink instance, document)`: status,
  attempts, last error, an external reference (e.g. a message id) and
  timestamps. Deleting the document deletes its deliveries.

## 7. Known limitations

1. Duplicates across sources are processed twice, with the cost that implies
   for expensive processors.
2. Renaming a source's `id` orphans its previous items and re-imports
   everything under another key.
3. Documents can lag behind their items between two runs of their applet.
4. Items of a removed source keep appearing in documents unless the applet
   filters them out.
5. An item skipped by an upstream processor never reaches the processors
   that depend on it, and those processors keep no record of it.
6. A deleted item that is still in its source's index comes back on the
   next import, with a new id.
7. Renaming an applet instance's `id` starts it from scratch: its run
   record and the keys of its documents are under the old one.
8. Deleting a document frees its key: an applet that emits it again stores
   it anew, and it is delivered again.

## 8. Confirmed assumptions

1. `Application` is a Python API used in the same process, not a network
   service.
2. Deleting an annotation removes the processing state and, with it, the
   attempt counter.
