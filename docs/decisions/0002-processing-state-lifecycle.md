# 0002: Processing state lifecycle

- **Status:** accepted
- **Date:** 2026-10-18
- **Revised:** 2026-10-27 (`enrich` renamed `process`; the key at entry
  level; keys per workflow, by 0009)

## Context

The technical definition allowed one annotation per `(item, processor)`,
treated a missing upstream annotation as a retryable failure, and said no
configuration change regenerates anything. The code writes several keys per
processor, waits for upstream processors, and reprocesses on a version bump.

## Decision

- **Runs and keys.** Each entry of the `process` section is a run of a
  processor with its own options, and writes exactly one annotation key (the
  processor's own unless the entry names one with `key`, next to
  `processor` and outside its `options`: `summary`, `summary/es`). A key is
  written by one entry per item: one within a workflow, and across
  workflows only if they share no source (decision 0009).
- **Annotations and state** are both keyed by `(item, key)`; the processor
  that wrote them is recorded, not part of the key. Two runs of one
  processor with different keys are independent: each has its own status,
  attempts and retries.
- **Dependencies:** a run names the key it reads (`requires`). Only items
  whose run of that key finished on their current content are picked up,
  even when forced. Items still waiting spend no attempts. A finished
  upstream that lacks the needed annotation is a retryable failure.
- **Outcomes:** done, ignored (permanent for that content), or error with
  exponential backoff and a retry limit (`max_retries`).
- **Reprocessing triggers**, and nothing else:
  - The item's content changes: every state becomes eligible with zero
    attempts.
  - The processor's `version` changes: done items are reprocessed.
    `version` is set in code only.
  - A forced regeneration, which resets attempts.
  - Deleting annotations, which also deletes the processing state.
- Changing a processor's or an entry's configuration never regenerates
  anything.

## Consequences

- Running processors out of order does not exhaust retries.
- Consumers (other processors, remixers, sinks) read annotations by key
  alone (`summary`, not `summarize.summary`); which processor wrote it does
  not matter to them.
- An item ignored upstream never reaches its dependants, and they keep no
  record of it.

## Revisions

- **2026-11-11 (0018).** Discarded: "the item's content changes: every
  state becomes eligible" by comparing the content each state recorded,
  which left the annotation of the old content readable. Remains: a content
  change reprocesses every key with zero attempts; it now deletes the
  item's annotations, which hold their run state.
- **2026-10-27 (0009).** Discarded: "a key is written by one entry only",
  across the whole configuration. Remains: one writer per `(item, key)`.
- **2026-10-26.** One key per run, keyed by `(item, key)`. Discarded:
  annotations keyed by `(item, processor, key)` with one state per
  `(item, processor)`, which let a processor write several keys per item
  but not run twice with different options (a second run found the item
  `done`), and the partial failure that saved some of a run's keys. `embed`
  now embeds one input per run, and its `tags_text` annotation is gone:
  `tags_text(tags)` recomputes it.
