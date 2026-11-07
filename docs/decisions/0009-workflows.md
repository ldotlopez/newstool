# 0009: Workflows and keyed entries

- **Status:** accepted
- **Date:** 2026-10-27
- **Revises:** 0002 (where an annotation key may be written), 0003
  (`remix` and `deliver` entries), 0007 (the ledger key, pacing)
- **Revised:** 2026-10-28, by 0010 (`default` is built from the catalog
  and delivers nothing; entries are catalog references or the workflow's
  own; `default: false` is `skip_default: true`; every ledger key is
  `<workflow>/<key>`; other options for a process key on shared sources
  are a warning, other processor types an error); 2026-11-06, by 0015
  (workflows keep only `sources` and `process`; `remix` and `deliver`
  entries and ledger keys are removed)

## Context

The configuration ran one pipeline over every source, and a sink was
configured once, in its plugin section: one chat, every source, an
`interval` counted per source. Some uses do not fit it, such as "post the
summarized items of source X to chat Y, one every 30 minutes, oldest first",
with the chat defined by that use, not by the plugin. The same holds for
remixers: one `digest` or feed per configuration.

`process` already had the shape needed: objects built once from
`plugins`, and entries that each run one with its own options under its
own key (decision 0002).

## Decision

- **Workflows.** A workflow names its sources and lists its own
  `process`, `remix` and `deliver` entries. The configuration's root keys
  are the `default` workflow, which uses every source except those with
  `default: false`; `workflows` adds more, as a list with `name` (YAML
  mappings drop duplicate keys silently). `default` is reserved.
- **Sources** stay global and are referenced by id. A workflow cannot
  change a source's options: two option sets for one item would flip its
  `content_sha256` between imports and break change detection (decision
  0001).
- **Entries.** `remix` and `deliver` entries have the shape of `process`
  ones: an object's name, or `{<object>, key, options}`. `key` defaults to
  the object's name.
- **Identity follows ownership.**
  - Annotations belong to items, so a process key is written by one entry
    within a workflow and across workflows that share a source; workflows
    with disjoint sources may write the same key, so a source outside
    `default` gets its own `markdown` and `summary`.
  - Artifacts belong to no source, so a remix key is unique across all
    workflows; it is stored as the artifact's `remixer`.
  - A delivery is marked by what it delivers and who asked for it: the
    ledger key is `<workflow>/<key>`, or the bare key in `default`, stored
    as the delivery's `sink`. A deliver key is unique within its workflow;
    `/` is not allowed in workflow names or keys.
- **No migration.** The bare keys of `default` are the object names used
  before, so existing artifacts and deliveries belong to its entries.
- **Scope.** Every phase of a workflow sees only its sources:
  `import` fetches them, and `process`, `remix` and `deliver` restrict
  their scope to them (`ProcessingScope.sources`).
- **Pacing** is per deliver entry (decision 0007): `interval` for the
  whole entry, oldest first, and `max_per_run` against flooding.
- **CLI.** `run` and the phase commands run `default` unless given
  `-w/--workflow NAME`; each workflow is its own cron line.

## Rejected options

- **Alternative pipelines only for delivery** (a `deliver` section without
  workflows). Some uses need their own sources and processing, such as a
  source summarized with another prompt for one channel.
- **Workflows that define or override sources.** Duplicated definitions,
  and the change-detection problem above.
- **Process keys unique across all workflows.** A source outside `default`
  could not get `markdown` or `summary`, which the consumers read by key,
  so the main use case would only work with the source also in `default`,
  delivered by it too.
- **Ledger key `<workflow>/<key>` in `default` too.** Every existing row
  would need a migration.
- **Separate `workflow`, `key` and `sink` columns in the ledger.** Cleaner
  queries by workflow, but a migration, for queries nothing needs yet.
- **One workflow, one delivery.** Today's `default` already delivers to
  several places.
- **`run` without `-w` running every workflow.** Rejected in favour of an
  explicit cron line per workflow.

## Consequences

- Configurations must list remixers and sinks in `remix` and `deliver`;
  the `telegram` subsections become deliver entries, and its chat an entry
  option.
- Renaming a workflow or a deliver key starts an empty ledger: its last
  `lookback` hours are delivered again, at most `max_per_run` per run.
  Renaming a remix key leaves its old artifacts behind.
- Changing a workflow's sources can make a valid configuration invalid,
  when it starts sharing a source with another workflow that writes the
  same key; the error names both.
- Data left by a removed workflow or key stays until deleted by hand; a
  cleanup command is pending (`PLAN.md`).
