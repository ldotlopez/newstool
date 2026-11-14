# 0019: Workflows as chains of global entities

- **Status:** accepted
- **Date:** 2026-11-14
- **Revises:** 0009 (the root keys as the `default` workflow, workflow
  entries of their own, the rejected unique process keys), 0010 (strings
  in `process:` as type names), 0015 (applet instances in no workflow,
  `apps run` delivering, `apps reset`), 0016 (`apps run --no-deliver`) and
  0017 (`workflows`, `--default`, `skip_default` on applet instances,
  `run --default|--all`)

## Context

What a configuration runs came from several places with their own rules:

- The root keys were the implicit `default` workflow: whatever had no
  `skip_default`. A workflow could also define processor entries of its
  own, and a string in its `process:` was a catalog id *or* a type name.
- Two workflows could write one annotation key with different options on
  shared sources, which needed a rule ("one processor type per key on
  shared sources") and a warning ("the first run to process an item writes
  it").
- `process PROCESSOR` named a type, ambiguous with several runs of it.
- Applet instances belonged to no workflow: a workflow's chain needed
  `workflows -w X` and then `apps run`, two cron lines whose order decided
  whether an applet read freshly processed items. An instance's `sources`
  option repeated, or contradicted, its workflow's.
- Selection had two models: `-w`/`--default`/`--all` over workflows,
  `--app`/`--sink`/`--default`/`--all` over instances, with `--default`
  meaning three different sets.

## Decision

### The catalog defines, workflows run

- The catalog only defines entities: `sources`, `processors`, `apps`,
  `sinks`, `llms` and the `plugins` sections. Defining an entity never runs
  it.
- Every source, processor, applet and sink entry has an `id`. A
  `processors` entry without one takes its type name (`markdownify`); two
  entries of one type need explicit ids. `llms` keep today's rule (an id,
  or the type name).
- There is no `skip_default` and no implicit `default` workflow; `default`
  is no longer a reserved name.
- A workflow is `name`, `sources`, `process` and `apps`, all lists of
  catalog ids: no entries of its own, no type names. Its sinks are those
  its instances are routed to.
- A process key is written by one catalog entry: a repeated key is a load
  error. Two workflows that run one key run the same entry, so conflicts
  on shared sources cannot happen. (0009 rejected unique keys because a
  source outside `default` could not get `markdown`; with global entries
  every workflow refers to the same `markdownify`.)
- An applet instance belongs to at most one workflow (a load error
  otherwise) and reads exactly its sources: the applets' `sources` option
  is removed. Every key an instance requires is written by a process entry
  of its own workflow (a load error otherwise), so a chain produces
  everything its applets read.
- A source, processor or applet instance no workflow refers to is a load
  warning. Sinks are not: rows queued by hand reach them through `deliver`.

### A workflow is the whole chain

Running a workflow imports its sources, runs its process entries in order
on them, runs its applet instances that are due, then delivers to its
sinks.

### CLI

- One command per phase: `import`, `process`, `apps` (no delivery) and
  `deliver`; `run`, the whole chain. `workflows` and `--no-deliver` are
  removed.
- Every one of them takes exactly one selection: `-w NAME` (repeatable) or
  `--all` (every workflow, in configuration order). A bare command is a
  usage error, as in 0017.
- The phase commands narrow by id within the selection: `--source`
  (`import`, `process`), `--processor` (`process`, a catalog id), `--app`
  (`apps`) and `--sink` (`deliver`); an id outside the selection is an
  error. `run` takes only the selection.
- `deliver -w X` delivers to X's sinks; `deliver --all` to every sink, so
  rows queued by hand for sinks no instance routes to go too.
- `run` runs each selected workflow's import, process and applets in turn,
  then one delivery phase for the union of their sinks (every sink with
  `--all`): a sink delivers once per call, so its `max_per_run` holds.
- `apps reset ID` becomes `delete apps --app ID [--with-documents]
  [--dry-run]`, next to `inspect apps`. The instance need not be
  configured, as before.

## Rejected options

- **Keeping `skip_default` and the implicit `default` workflow.** Every
  instance reading a subset of the sources would need a named workflow and
  `skip_default` on itself and its sources; with workflows as the only
  thing that runs, nothing needs marking out.
- **`--default` as an alias of `-w default`.** Without a `default`
  workflow there is nothing to alias.
- **Workflow entries of their own.** They made strings ambiguous and keys
  conflict across workflows; a catalog entry and a reference cost one line
  more.
- **One key written by several entries on disjoint sources.** A key's
  meaning would depend on the source, and editing a workflow's sources
  could create a conflict.
- **An applet instance in several workflows.** Instances that emit anew on
  every run (`feed`, the grouping applets) would run once per chain, and
  their sources could not follow a workflow.
- **An applet `sources` option narrowing the workflow's.** A second place
  saying what an instance reads; a workflow of its own costs a few lines,
  and importing a source again is cheap (preflight, HTTP cache, process
  runs skip what is done).
- **The applet schedule in the workflow.** With one workflow per instance
  it only moves the data, away from the run record that decides when the
  instance is due.
- **Narrowing options on `run`.** `run` is the cron line; step-by-step
  debugging happens with the phase commands.
- **One command with phase options (`run --only process`).** It would
  gather every phase's options in one help, with meaningless combinations.
- **`apps` keeping its `run`/`reset` group, or a `reset-app` command.**
  Resetting deletes an instance's run record: it belongs with `delete`,
  next to `inspect apps`.

## Consequences

- Every configuration file breaks: the root keys' implicit workflow becomes
  a named workflow; workflow entries move to `processors` with an `id`;
  workflows gain `apps`; applet instances lose `sources`; `skip_default`
  goes. The old shapes fail with errors that say what to write instead.
- Stored data does not change: the database stores no workflow names, and
  source, applet and sink ids and process keys keep their meaning.
- Every cron line breaks: one `run -w X` per workflow, several `-w` on one
  line, or `run --all`.
- A minimal configuration needs an explicit workflow, and adding a source
  or a processor to a single-chain setup touches the catalog and the
  workflow.
- Processing a source without feeding a workflow's applets, or an applet
  over several workflows' sources, needs a workflow of its own; the
  sources it shares are imported again, cheaply.
- An instance with no schedule runs on every `run` of its workflow.
