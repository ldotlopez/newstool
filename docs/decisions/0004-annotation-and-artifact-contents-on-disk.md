# 0004: Annotation and artifact contents on disk

- **Status:** accepted
- **Date:** 2026-10-18
- **Revised:** 2026-11-06, by 0015 (artifacts are removed; document
  contents are stored the same way)

## Context

Item contents already live in a `foundation.storage.DiskStorage`. Annotation
values and artifact contents are still stored in SQLite, as JSON and text.

## Decision

Annotation and artifact contents are stored through
`foundation.storage.DiskStorage`. The database keeps only the reference it
returns, plus metadata:

- Annotation: processor, item, key, `created_at` and `updated_at`.
- Artifact: remixer, name, content type, `created_at` and `updated_at`.

## Consequences

- All bulky content follows the same storage path, and the database stays
  small.
- Backups must cover the content directory as well as the database.

## Revisions

- **2026-11-11 (0018).** The annotation's metadata also holds the state of
  its last run (status, attempts, last error, processor version,
  `attempted_at`); `updated_at` is when its value last changed. Remains:
  the value on disk, its reference in the database.
