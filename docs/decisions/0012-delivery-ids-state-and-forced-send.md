# 0012: Delivery ids, changing their state and forced send

- **Status:** superseded by 0015
- **Date:** 2026-10-29
- **Revises:** 0007 (`deliver --requeue|--force`, `deliveries resolve`),
  0008 (deliveries "selected by their subject")
- **Revised:** 2026-10-30, by 0014 (`set-status` creates rows; `-w` and
  the delivery key)

## Context

Decisions 0007 and 0008 (rev. 2026-10-28) removed the `deliver` command and
`deliveries resolve`; `delete deliveries` and `run` remained. That left no
way to settle an interrupted `sending` row except deleting it, to requeue
failed rows, or to send one subject now. Rows had no handle a person could
type: `inspect deliveries` showed the subject and the ledger key, not the
row's `id`, and `delete deliveries` selected only by filters. The engine
(`BaseSink.deliver(requeue=, force=)`) still existed.

## Decision

- **Ids.** `inspect deliveries` shows the ledger row's numeric `id`, and
  `--delivery ID` (repeatable) selects rows in `inspect`, `delete` and the
  commands below. It combines with the other filters (AND); an explicit id
  the selection does not return is an error. Ids are never reused
  (`AUTOINCREMENT`, decision 0008).
- **`deliveries set-status --as queued|done|error`.** Moves the selected
  rows to that state. `sending` is never a target: it exists only while a
  send is in progress. `queued` resets `attempts`; `queued` and `done`
  clear `last_error`. `done` adds no `external_ref`: it records a delivery
  settled by hand. It replaces `deliveries resolve` and `deliver --requeue`.
  It needs a selection; `--all` changes every row and takes no other
  filter.
- **`deliveries send`.** Sends the selected rows now, whatever their state,
  with no backoff and no pacing (`deliver(force=True)`, once per ledger
  key). It only acts on existing rows: it needs a selection (no `--all`),
  and creates none. A row whose ledger key is no longer configured is
  skipped with a warning. It exits non-zero if a send fails.
- Both commands are non-interactive and take the write lock, like `delete`.

## Rejected options

- **Bringing back `deliver [KEY] --force --item X`.** It selected by
  subject and created rows; ids on existing rows are simpler and match
  `inspect`/`delete`.
- **`--all` on `send`.** It resends every delivered subject to the outside
  world; a selection must be explicit.
- **`sending` as a target of `set-status`.** A hand-set `sending` would
  never be retried.

## Consequences

- `inspect deliveries` is the dry run of `delete deliveries`,
  `deliveries set-status` and `deliveries send`.
- A subject without a row can only be delivered by the next `run`, within
  its `lookback`.
