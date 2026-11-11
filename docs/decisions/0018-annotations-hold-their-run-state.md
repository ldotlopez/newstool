# 0018: Annotations hold their run state; a content change deletes them

- **Status:** accepted
- **Date:** 2026-11-11
- **Revises:** 0002 (what a content change does to annotations), 0004 (the
  annotation's metadata)

## Context

Each `(item, key)` had two rows: its run state in `processing_state` and,
once a run finished, its annotation in `item_annotations`. Both had the same
key, recorded the processor, were written in the same transaction and were
deleted together. They could still disagree: when an item's content
changed, the state was made eligible again by comparing the content it
recorded with the item's, but the annotation of the old content stayed.
Processors that `require` a key were protected by the state; applets, which
read annotations directly, were not, so a digest could summarise the old
text until the item was processed again.

What counts as a change is unchanged (decision 0001): a different content.
A newer listed date only decides whether the item is fetched; a different
title, uri, MIME type or `data` updates the row but keeps its annotations.

## Decision

- **One row per `(item, key)`** in `item_annotations`: the state of its
  last run (processor, status, attempts, last error, processor version,
  `attempted_at`) and, once a run finished, its value (`value_sha256`,
  `updated_at`). No row means never attempted. `processing_state` is gone,
  and so is the `content_sha256` the state recorded.
- **The schema keeps it consistent:** a `done` row has a value
  (`CHECK`), `attempts >= 0`, and the statuses are checked as before.
- **A content change deletes the item's rows**, state and value: every key
  is processed again on the new content, with fresh attempts, and no
  reader sees a value of the old content. A SQLite trigger on
  `source_items` (`AFTER UPDATE OF content_sha256`, when it differs) does
  it, so no write path can skip it; `Database` reads the values before the
  update and releases their files after the commit.
- **A later run of the same content** that fails or is ignored (forced, or
  after a version bump) keeps the value it does not replace.
- Annotation ids stay the CLI's handles (decision 0008): runs without a
  value have ids too, and `inspect` and `delete annotations` only list the
  rows with a value.

## Consequences

- Eligibility and `requires` need no content comparison: a row is always of
  the item's current content.
- Annotations of an item disappear on a content change until it is
  processed again; `run` imports before it processes, so applets in the
  same run see the new ones.
- The production database is migrated once by a private one-shot
  script, kept out of the repository with its test (`private/`,
  git-ignored): it keeps each annotation's id, drops the runs of a previous
  content and `done` runs without annotation (pending again), and creates
  the trigger. The earlier one-shot scripts (`migrate_annotation_keys.sql`,
  `migrate_autoincrement.py`, `migrate_applets.py`) are retired: every
  database they were for has run them.
