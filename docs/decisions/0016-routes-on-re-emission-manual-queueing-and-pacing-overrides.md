# 0016: Routes on re-emission, manual queueing and pacing overrides

- **Status:** accepted
- **Date:** 2026-11-10
- **Revises:** 0015 (when delivery rows are created, which documents
  `set-status --sink` marks, which sinks `apps run` delivers to, and how a
  delivery run may be paced)

## Context

Testing applets step by step (import and process, run an applet, then
deliver what it produced) showed four gaps in decision 0015:

- An applet run without a route stores documents with no delivery rows.
  Adding the route afterwards does nothing for them: rows are created only
  when a document is first stored, and emitting a stored key again is
  ignored.
- `deliveries set-status --sink X` only marks documents routed to X, so
  queueing documents for a sink by hand needs a configuration edit first.
- `apps run` always delivers, so running an applet and inspecting what it
  queued before anything is sent is not possible; with `--app`, it also
  delivers to every sink, including those of other applets.
- A sink's pacing (`interval`, `max_per_run`) cannot be lifted for one
  run, to drain a queue or test a sink.

## Decision

- **Routes reach re-emitted documents.** Each document a run emits, new
  or already stored, gets a `queued` row for each sink its output is routed
  to that it has none of, in the run's commit. A route added later thus
  reaches the stored documents the applet emits again (an `itemfeed`'s
  window), never its whole backlog. `apps run` reports these rows as
  `Routed`; `--dry-run` counts them.
- **Manual queueing ignores routes.** `deliveries set-status --sink X` with
  document filters gives every selected document a row of X, routed to it
  or not. The sink must accept the content types of all of them, or
  nothing is marked. `--all` still takes only the documents routed to X,
  so it cannot pour every applet's documents into one sink.
- **`apps run --no-deliver`** stores and queues what the applets emit and
  sends nothing; `deliver` sends it later.
- **`apps run --app ID`** delivers only to the sinks those instances are
  routed to. Without `--app`, it delivers to every sink, as before.
- **Pacing overrides, one flag per option.** `deliver --ignore-interval`
  drops the interval (its wait and its one row per run), so `max_per_run`
  alone limits the run; `--ignore-max-per-run` drops that limit;
  `--max-per-run N` replaces it (it excludes `--ignore-max-per-run`). A
  sink with an interval sends one row per run, so emptying its queue takes
  both ignore flags. Retries still wait for their backoff, and a failed
  delivery does not stop the others.

## Rejected options

- **A new route queueing every stored document of its output.** Still
  rejected (0015): it can flood its destination with the whole backlog.
- **Routes applied only to new documents** (0015 as it was). A route added
  after a test run could never reach what that run stored without
  marking by hand.
- **One rule for `set-status --sink`, routes never counted.** `--all` would
  mean every document of every applet.
- **Requiring `--app` to mark documents that are not routed.** A rule
  harder to explain for the same protection `--all` already gives.
- **`--ignore-interval` lifting the one row per run but not `max_per_run`
  separately, or a single `--no-limit`.** Two flags mirroring the two
  options read without the help.
- **Stopping a delivery run at its first failure.** Failures stay
  independent, as for processors; a broken sink fails each row once per
  run, up to `max_retries`.
- **`apps run --app` delivering only the rows of the documents it
  emitted.** A sink's pace would depend on who invoked it.

## Consequences

- A delivery row deleted by hand comes back if its applet emits the
  document again while routed to that sink.
- Re-emitting stored keys now costs a ledger lookup per document in each
  run's commit.
- `deliveries set-status --sink X --app A --as queued` is the way to send
  what `A` stored before any route, beyond what it emits again.
- A cron line with `apps run --app A` no longer drains sinks only other
  applets use; each needs its own `apps run` or `deliver`.
