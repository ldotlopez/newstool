# 0007: Sinks and the delivery ledger

- **Status:** superseded by 0015
- **Date:** 2026-10-20
- **Supersedes:** 0005
- **Amends:** 0003 (a fourth plugin type and phase)
- **Revised:** 2026-10-23, by 0008; 2026-10-27, by 0009; 2026-10-27, the
  bot per entry (see *Revisions*); 2026-10-28, by 0010 (one sink object
  per use, built with its options)

## Context

Decision 0005 made `telegram` a remixer so it could rate-limit across
items. Since then, `remix` mixes two kinds of work: building artifacts,
which is pure and can be regenerated, and acting on the outside world,
which cannot be undone. Its record of what it posted lives in an artifact
(`telegram/state`), a table meant to be regenerated; as an annotation it
would be lost to `--force` or `delete_annotations`. The core cannot tell
what was delivered, what is pending or what failed, and running it as
`remix telegram` hides delivery inside another phase.

What matters is not item versus collection but derived versus recorded:

| | Annotations | Artifacts | Sink data |
| :--- | :--- | :--- | :--- |
| Subject | item | collection | item or artifact |
| Nature | derived | derived | record of an external fact |
| Regenerable | yes (`--force`) | yes (every `remix`) | no |
| Safe to delete | yes | yes | no: it causes duplicate posts |

## Decision

- **Type.** `Sink` is a fourth plugin type, defined by a `typing.Protocol`
  in `sinks.py` with its own method: `deliver(db, *, key, options, scope,
  artifacts, requeue, force) -> RunSummary`. Sinks act on the outside
  world; remixers no longer do. A sink is used by `deliver` entries
  (decision 0009), each with its own options, where it delivers among
  them, and its own ledger key.
- **Data.** Annotations and artifacts stay as they are. Sink data goes to
  a new `deliveries` table, the ledger: one row per (ledger key, subject),
  the ledger key naming who asked for the delivery (the deliver entry's
  key, prefixed by its workflow outside `default`: `<workflow>/<key>`,
  decision 0009; the column keeps the name `sink`), with
  the subject as two nullable foreign keys (`source_item_id`,
  `artifact_id`, both `ON DELETE CASCADE`, a `CHECK` that exactly one is
  set, `UNIQUE (sink, source_item_id)` and `UNIQUE (sink, artifact_id)`),
  the status, attempts, the last error, the subject's `content_sha256` at
  delivery, an external reference (JSON, e.g. `{"chat_id": …,
  "message_id": …}`) and
  timestamps. It never references `DiskStorage` contents. `--force` on
  other phases, annotation deletion and artifact rebuilds never touch it;
  `save_artifact` keeps an artifact's id, so its rows stay valid.
- **States.** `queued`, `sending`, `done`, `error`.
  - The queue is stored, so a first run with `--since` keeps the rest of
    its window and the queue can be inspected.
  - `sending` is committed on its own before the external call. A row
    still `sending` when a run starts was interrupted and its outcome is
    unknown: it is never retried automatically.
  - `error` rows are retried with the processors' backoff and
    `max_retries` (an entry option, default 3).
- **Candidates.** Without `--since` or `--item`, an entry queues the subjects
  of the last `lookback` hours (an option, default 24; items by
  `published_at`, artifacts by `created_at`) that have no row. There is no
  watermark. A sink with `redeliver_on_change` (a class attribute) also
  requeues `done` rows whose subject's hash changed.
- **Bases.** `BaseItemSink` (with `requires`, as in processors) and
  `BaseArtifactSink` share one cycle:
  1. queue the candidates;
  2. `select(pending, now)` picks what is due, and `pace` limits it, which
     is where rate limits live; nothing sleeps;
  3. for each selected subject, begin (`sending`), `send(db, subject,
     options) -> external_ref`, then finish (`done`) or fail (`error`).
- **Pacing.** Options of every entry: `interval` (minutes; default 0, no
  pacing) delivers one subject, the oldest due, once the entry's last
  `done` delivery is that old, whatever its source; `max_per_run` (default
  5) caps every run, so a new or renamed entry, whose ledger is empty, does
  not flood its destination with its whole `lookback`.
- **Order.** Oldest first, strict FIFO per source. An `error` row at the head of a
  source's queue holds it back until it is delivered or exhausts
  `max_retries`; then it stays `error`, visible, and the queue moves on.
  `deliver --requeue` requeues the `error` rows in scope with fresh
  attempts; nothing requeues `done` or `sending` rows.
- **Forced send.** `deliver KEY --force` sends every subject in scope now,
  whatever its state (`done`, `error`, `sending`), with no backoff and no
  pacing. It names one entry, and requires an explicit selection,
  `--item <id>` for item sinks or `--artifact <remix key>/<name>` for
  artifact sinks; it is an error without either. A forced send updates its
  row (`done` with the new `external_ref`, or `error`), and counts as the
  entry's last delivery.
- **CLI.** `deliver [KEY]` runs a workflow's deliver entries in
  configuration order (`-w`, default `default`), with the scope options,
  `--requeue` and `--force`. It is a phase of its
  own, after `remix`, so sinks see freshly built artifacts. `run` runs
  `import`, `process`, `remix` and `deliver` in turn; failures inside a
  phase are logged and do not stop the next one, and `run` exits non-zero
  if any occurred. `inspect deliveries [--sink] [--status]` inspects the
  ledger (decision 0008); `deliveries resolve LEDGER_KEY --as done|queued`
  settles interrupted (`sending`) rows.
- **Scheduling.** External (cron, jobs); there is no long-running process.
  Commands that write take an exclusive lock on a file next to the
  database and fail at once if another holds it.
- **`telegram`.** A bundle of two sinks; `bot_token` and `chat_id` are
  entry options, whose defaults are the section's (optional), so entries
  can post with different bots:
  - `telegram` (items): `requires = "summary"` (an annotation key,
    decision 0002), no redelivery. Its state artifact is no longer
    produced.
  - `telegram_artifacts`: delivers every artifact of the remix keys listed
    in `artifacts` (e.g. `[digest]`), no redelivery, as a document
    (`sendDocument`) with a short caption, which avoids the 4096-character
    message limit.
- **`digest`.** Artifacts are named `<source>/<since>_<until>`
  (`YYYY-MM-DD`): each digest is a new artifact, delivered once, and
  rebuilding the same range overwrites it without posting it again.

## Rejected options

- **Remixers with side effects** (decision 0005). `remix` cannot be re-run
  safely, and the record of what was posted lives with regenerable data.
- **Sink data as annotations.** `--force` and `delete_annotations` would
  erase it, and posted items would be posted again.
- **Merging annotations and artifacts into one `outputs` table.** It needs
  a subject id without a real foreign key, or nullable columns with
  partial indexes, loses the cascades and rewrites every annotation query.
  Contents are already stored the same way in `DiskStorage`.
- **One table with a `kind` column (derived or recorded).** A mistaken
  `--force` or deletion would erase delivery records.
- **A per-sink watermark.** It only told a new sink where to start;
  `lookback` does that without hidden state.
- **A pending set computed on every run.** An item that leaves the
  `lookback` window while waiting for its `interval` turn would be lost
  silently.
- **Retrying `sending` rows automatically, or only through a flag.** The
  first turns every crash into a possible duplicate post; the second
  cannot record that a delivery did happen.
- **`--force` as requeue.** In a sink, *force* reads as *send now*;
  requeuing has its own flag, `--requeue`.
- **External apps on `Application` with a generic store.** That store
  would be artifacts under another name, and the core could not compute
  or show what is pending. Apps stay an option for long-running or
  interactive uses, built on the same ledger.
- **A per-item sink method.** Rate limits need the whole batch; that is
  why 0005 moved `telegram` out of the processors.
- **Pacing per source** (the first `telegram` sink: one post per source
  every `interval`). A channel fed by several sources got one post per
  source at once; per entry, the destination sees one post per interval.
- **The sink's name as the ledger key.** One sink could deliver to one
  place only, its chat or webhook fixed in the plugin section.
- **Locking left to cron (`flock`).** It depends on every installation
  getting the cron line right.

## Consequences

- No database rebuild: `create_all` adds `deliveries` and alters nothing.
- `scripts/migrate_telegram_state.py` runs once, before the first `deliver
  telegram`. It turns `posted` into `done` rows with their `message_id`
  and `queue` into `queued` rows, and drops `watermark` and `last_post`.
  Without it, the last `lookback` hours are posted again. The old artifact
  is left in place.
- `remix` becomes free of side effects and safe to re-run.
- If cron stops for longer than `lookback`, the gap is delivered only with
  `--since`.
- Cron runs `run` or `deliver` more often than the shortest entry interval.
  Two writing commands can no longer run at once; the second fails with a
  clear error. This also closes the content-deletion race of decision
  0004. The lock is POSIX-only.
- Delivery happens at most once, unless an interrupted row is resolved
  as `queued` or a send is forced.
- Reposting an item (`deliver telegram --force --item X`) creates a new
  message; the previous `message_id` is replaced in the ledger, and the
  old message is not deleted.
- Renaming a deliver entry's key, or its workflow, starts an empty ledger:
  its last `lookback` hours are delivered again, at most `max_per_run` per
  run. Rows written before 0009 belong to the `default` entries keyed by
  the sink's name.
- `remix telegram` and the `telegram/state` artifact go away.
- `digest` artifacts accumulate, and `inspect artifacts --artifact
  digest/...` takes the dated name. The old undated `digest/<source>`
  artifacts fall outside `lookback` once they are more than 24 hours old.
- A file-export sink (RSS to a file to be served) is out of scope; the
  feed is still written with
  `inspect artifacts --artifact feedgenerator/feed > feed.xml`.

## Revisions

- **2026-10-28 (0008).** Discarded: the `deliver` command (with
  `--requeue` and `--force`) and `deliveries resolve`; delivery runs only
  as a phase of `run`, and `delete deliveries` drops ledger rows so their
  subjects are queued again within `lookback`. Remains: the ledger, its
  states, the delivery cycle, and requeue and forced delivery in
  `Application.run_delivery`.
- **2026-10-27.** Discarded: one bot per configuration, its token required
  in the `telegram` section. Remains: the section, now optional, as the
  entries' defaults.
- **2026-10-27 (0009).** Discarded: the ledger keyed by the sink's name,
  `telegram`'s per-source `interval`, the chat and webhook fixed in the
  plugin section, the `telegram` subsections, sinks enabled by their
  section, and `UnavailableSink` (no sink needed it). Remains: the ledger,
  its states and the delivery cycle, now per deliver entry, plus
  `max_per_run`.
- **2026-10-23 (0008).** Discarded: selecting items with `--uid` (now
  `--item <id>`, the item's numeric id) and the `deliveries list` command
  (now `inspect deliveries`). Remains: everything else, including
  `--artifact <remixer>/<name>` and `deliveries resolve`.
- **2026-10-23 (implementation).** Discarded: `deliver --force` across
  every sink (it now names one SINK, so a forced resend reaches one place).
  Not implemented yet: `redeliver_on_change`, which no sink uses. Remains:
  everything else.
