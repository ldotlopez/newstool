# 0017: Explicit run selection

- **Status:** accepted
- **Date:** 2026-11-10
- **Revises:** 0009 (`run` and the phase commands running `default`
  without `-w`, one cron line per workflow) and 0015 (`run -w W` as import
  and process only, `apps run` as a second cron line, `apps reset ID`)

## Context

Every command that runs something did so when run bare: `import`,
`process` and `run` ran the `default` workflow, `apps run` every applet
instance and `deliver` every sink. A command typed by mistake, or a cron
line missing its flag, ran work nobody asked for, and `default` (what has
no `skip_default`) meant something different per command: applet
instances had no `skip_default` at all.

A setup of one workflow with its applets also needed two cron lines,
`run -w W` and `apps run`, though a single one, with each applet keeping
its schedule and each sink its pace, does the same.

`search` scanned every item's markdown from disk; `inspect` and the
applets cover its uses.

## Decision

- **Exactly one selection.** `import [SOURCE]`, `process [PROCESSOR]`,
  `workflows`, `apps run` and `deliver` each take a name option (`-w NAME`;
  `--app ID` and `--sink ID`, repeatable), `--default` or `--all`, and
  exactly one of them. A bare command, or one with two, is a usage error.
  `-w default` is the same as `--default`.
- **`--default` is what has no `skip_default`:** the `default` workflow
  (its sources and catalog processors without it), the applet instances
  without it, and the sinks those are routed to. Applet instances take
  `skip_default`.
- **`--all` is everything, skipped or not:** every workflow in turn,
  `default` first; every applet instance; every sink, so rows queued by
  hand for sinks no applet routes to go too. `import --all` fetches each
  source once.
- **`workflows`** runs import and process for the selected workflows; it
  replaces `run -w` and `run --all`.
- **`run --default | --all`** runs the workflow phases, then the applets
  that are due, then the delivery, all with the same selection. It takes no
  `-w`. A failing phase is logged and the next one still runs.
- **`import SOURCE`** narrows the selected workflows to one of their
  sources; one outside them is an error.
- **`apps reset --app ID`**, for uniformity with the other app commands. The
  instance still need not be configured.
- **`search` is removed**, with `Application.get_annotation_values`.
- `deliver`'s pacing overrides stay on `deliver` only; `run` and
  `apps run` keep each sink's configured pace. Rows of sinks no longer
  configured are reported whatever is selected.

## Rejected options

- **Bare commands running `default`.** The accident this decision removes.
- **`skip_default` on sinks.** A sink belongs to no workflow and is reached
  only through routes; a flag of its own could disagree with the applets
  that feed it (a skipped sink of a default applet would never deliver).
  `--default` derives the sinks from the routes instead.
- **`run --all` meaning the `default` set.** `--all` means everything in
  every command; `--default` names the default set.
- **A `workflows` group (`workflows run`, `workflows list`).** One command
  is enough; the workflows are in the configuration.
- **Moving `deliver` to `deliveries run`.** `import`, `process` and
  `deliver` are the phase verbs; `deliveries` holds the ledger tools.

## Consequences

- Every existing cron line breaks: `run -w W` becomes `workflows -w W`,
  `run` becomes `run --default` (now also running the applets and
  delivering), `apps run` and `deliver` need `--default` or `--all`, and
  `apps reset ID` becomes `apps reset --app ID`.
- One cron line, `run --default`, covers a setup with one workflow and its
  applets; it imports and processes on every call, so it runs at the pace
  imports should happen. Skipped workflows and applets get their own lines.
- `run` holds the write lock for the import, the processing, the applets
  and the delivery together.
