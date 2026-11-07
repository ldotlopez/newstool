# 0014: Ledger rows by subject and the workflow in delivery commands

- **Status:** superseded by 0015
- **Date:** 2026-10-30
- **Revises:** 0012 (`set-status` only changes existing rows, `--sink`
  takes the ledger key, a subject without a row is delivered only by `run`)

## Context

Sinks are catalog entries and run only in the workflows that name them;
`default` imports and processes and delivers nothing (decision 0010). A
common setup imports and processes with `default` and delivers with another
workflow. After the first import the database holds many items within every
delivery's `lookback` and no ledger row for them, so the first run of the
delivering workflow posts them, `max_per_run` at a time. A person who wants
only the items of later imports delivered had no way to tell a delivery
"these are already sent": `deliveries set-status` changes existing rows,
`deliveries queue` creates them only as `queued` and respects `requires`,
and chaining both is two steps whose second one, without `--sink`, also
touches the queued rows of other deliveries.

`--sink` also took the full ledger key (`<workflow>/<key>`), a storage
format the person must know, while every other command names a workflow
with `-w`.

## Decision

- **The ledger stays per delivery.** A row belongs to `<workflow>/<key>`;
  two workflows that use the same catalog sink keep separate ledgers.
- **Selecting the delivery.** `--sink KEY` takes the delivery key (the part
  after `<workflow>/`: the catalog id, the type name of a workflow's own
  entry, or its `key`). `-w/--workflow` names the workflow and is required
  by `deliveries set-status`, `deliveries send` and `delete deliveries`:
  each acts on one workflow, `--sink` narrows it to one delivery. In
  `inspect deliveries` `-w` is optional: without it every workflow is
  listed, and `--sink KEY` shows that key in every workflow that uses it.
  Creating rows needs the delivery in the configuration: an unknown
  workflow or delivery key is an error. As filters, they match the rows
  stored under them, so the rows of a removed delivery can still be
  inspected, deleted or changed.
- **`set-status` creates rows.** With `--sink`, the standard filters
  (`--source`, `--item`, `--since`, `--until`, `--artifact`) select
  subjects, and every selected subject without a row gets one in the
  `--as` state: `queued`, `done` or `error`. A row created as `error` gets
  `last_error = "set by hand"`. `--all` with `--sink` selects every subject
  of the delivery (its items, or the artifacts of its remixers); without
  `--sink` it is every row of the workflow, as before. `--all` combines
  only with `-w`, `--sink`, `--as`, `--overwrite` and `--dry-run`.
- **Existing rows.**
  - Reached through subjects, they are left as they are unless
    `--overwrite` is given; the command reports how many it left and
    suggests `--overwrite`.
  - Selected as rows (`--delivery`, `--status`), they are always changed,
    as before.
  - `--overwrite` without `--sink` is an error: nothing is selected
    through subjects.
- **The person decides.** `set-status` ignores the delivery's `requires`:
  a subject is marked whatever its annotations. Queuing an item without
  the required annotation warns that it fails until the annotation exists
  and holds back its source (the per-source FIFO). A sink that finds the
  annotation missing raises `PluginFailure`, so the row goes `error` with
  a readable `last_error`. A filter of the wrong kind (`--artifact` for an
  item delivery, item filters for an artifact delivery) is an error; an
  artifact of a remixer the delivery does not name is marked like any
  other.
- **`--limit`** with `--sink` counts selected subjects, as in the item
  commands; without it, rows.
- **`--dry-run`** reports how many rows would be created, changed and left
  as they are, and writes nothing. `inspect deliveries` shows only existing
  rows, so it cannot preview a creation.
- **`deliveries queue` is removed.** `set-status --as queued` replaces it.

## Rejected options

- **A per-delivery watermark or start date** (an option, or a "since"
  stored with the delivery). Rejected in 0007 for hidden state; a date in
  the configuration filters by `published_at`, which back-dated feed items
  defeat.
- **A shorter `lookback`, or one counted from the import.** The first
  import is recent too when the delivering workflow first runs.
- **`run --mark-done`**, recording instead of sending. It inherits
  `lookback` and `max_per_run`, and a `run` that does not send is easy to
  run by mistake.
- **A ledger per catalog sink**, shared by the workflows that use it. It
  avoids posting an item twice to one destination, but reverses 0009/0010
  and needs a migration of every ledger key.
- **Resolving the workflow from `--sink` when only one uses the key.** A
  command that works stops working once a second workflow uses the key;
  an explicit `-w` also tells the person how the command is meant.
- **`--sink KEY` without `-w` meaning `default`.** `default` delivers
  nothing, so it would always fail.
- **Overwriting existing rows by default.** `--as queued --source X` would
  post again every item already delivered from X.
- **Respecting `requires` when creating rows**, or only for `queued`. Items
  still being processed would escape a `--as done` baseline and be posted
  later; the person who queues an incomplete item can see the warning.
- **`--as none` to delete rows.** It duplicates `delete deliveries`, hides
  a removal (whose subjects are queued again within `lookback`) behind a
  state change, and drops `external_ref`.

## Consequences

- A new delivery starts after a baseline:
  `deliveries set-status -w W --sink K --all --as done`.
- `--sink <workflow>/<key>` no longer works in any command; scripts that
  use it need `-w` and the bare key.
- Without `--sink`, nothing queues every subject in every delivery, as
  `deliveries queue --all` did; it takes one `set-status` per delivery.
- A subject without a row can be delivered outside `lookback`: create its
  row with `set-status`, then `deliveries send` it or let `run` pick it up.
