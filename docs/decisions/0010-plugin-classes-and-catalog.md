# 0010: Plugin classes and the configuration catalog

- **Status:** accepted
- **Date:** 2026-10-28
- **Revises:** 0003 (loading, enabling, options, objects), 0006 (LLMs and
  `services`), 0007 (sinks built per use), 0009 (the `default` workflow,
  entries and keys)
- **Revised:** 2026-11-06, by 0015 (`remixers` and `sinks` leave the
  catalog; applet and sink instances are global)

## Context

Every plugin object was built once, from its `plugins` section, and each
use (a source, a `process`, `remix` or `deliver` entry) passed its own
options to every call. Each plugin split its options into two models: the
section's (`Options`, with what only the instance holds: `llm`,
`max_retries`, `bot_token`) and the per-use one (`use_options`). An option
was either per instance or per use, never both, so two uses could not pick
different LLMs. Bundles with several objects needed subsections
(`grouping`), LLM plugins had to be listed before their consumers, and a
consumer without its LLM became an `Unavailable*` stand-in.

## Decision

- **Classes, not instances.** An entry point,
  `__newstool_plugin__()`, takes no arguments and returns
  `(type name, type Protocol, class)` triples. A bundle may register any
  number of classes per protocol; type names are unique per protocol. The
  type protocols (`ProviderType`, `ProcessorType`, `RemixerType`,
  `SinkType`, `LLMType`) declare `options_model` and
  `__call__(options, services)`, plus the keys a run writes or reads
  (`output_key`, `required_key`) as class methods, so the core works them
  out without an object. `ClassRegister` (in `newstool.plugins`, on
  foundation's `BaseRegister`, to move to foundation later) imports every
  module of the namespace and checks conformance with `isinstance(cls,
  protocol)`.
- **One object per use.** An object is built with the options of its use
  and keeps them (`self.options`); the phase methods take no options. Its
  options are one model; the per-instance/per-use split and `use_options`
  are gone.
- **`plugins` holds defaults per type.** `plugins.<type>` sets defaults for
  every use of the type (`telegram` and `telegram_artifacts` are separate
  sections). It builds nothing. Its options are checked at startup against
  the type's model, each value on its own; rules across options (model
  validators) are checked in each use.
- **The catalog.** `llms`, `sources`, `processors`, `remixers` and `sinks`
  list uses: a type name, or `{<type>, id, key, options}`. `id` names a use
  so workflows can refer to it; it is not a type's name. `key` names what
  the use writes (an annotation, artifacts, ledger rows) and keeps its
  current defaults. Precedence: the type's defaults, then
  `plugins.<type>`, then the entry's `options`, merged key by key in nested
  mappings; any other value, lists included, replaces.
- **Workflows refer or define.** A workflow entry is a catalog id, a type
  name (the type with its section's options, one profile per type), or an
  entry of its own, which has no `id` or `skip_default`. A reference cannot
  override options: one id is one run.
- **`default`** is built from the catalog: the sources, processors and
  remixers without `skip_default: true`, in catalog order. It delivers
  nothing; delivering always takes a named workflow. A workflow may deliver
  without processing, relying on what others write on its sources.
- **LLMs** are a catalog too. An object names one by id or type
  (`llm:` in `UsesLLMOptions`); none is the first `llms` entry. `Services`
  builds each on first use. A name that resolves to no LLM is a
  configuration error, so the `Unavailable*` objects are gone.
- **Startup checks.** The whole catalog is validated when `Application` is
  built, whatever the workflow; objects are built when a run first needs
  them. Process keys: one run per key within a workflow; on shared sources
  two processor types cannot write one key, and other options for it only
  get a warning (the first run to process an item writes it). A remix key
  belongs to one workflow. Every key a process or delivery run reads must
  be written by a process run on its workflow's sources, in any workflow.
- **Ledger keys** are `<workflow>/<key>` for every workflow.

## Rejected options

- **One registration per protocol and bundle.** `telegram` and `grouping`
  provide several types.
- **Factory functions next to the classes.** A class with `options_model`
  is the factory.
- **Sections per bundle (module).** A second namespace beside the type
  names, and options whose meaning depends on which class reads them.
- **References that override options.** One id would stand for several
  runs, and the "same id, same run" rule would need its own checks.
- **Validating only what the running workflow uses.** Each workflow runs
  from its own cron line, so an error in another one would surface hours
  later; validating everything is cheap.
- **Building every object at startup.** A workflow without LLMs would still
  build them.
- **Two processor types writing one key, with a warning.** Each would see
  the other's `processor_version` and process every item again on every
  run.
- **`default` delivering.** A sink catalogued for one workflow would post
  every source of `default` too.
- **Shallow merging.** Chosen deep: nested defaults survive partial
  overrides, at the cost of not being able to unset an inherited key.
- **Deleting what the configuration no longer names.** Several
  configurations may share a database; a listing of orphans is in
  `PLAN.md`.

## Consequences

- Configuration files must be rewritten: `process`, `remix` and `deliver`
  move to the catalog (`processors`, `remixers`, `sinks`) or to workflows;
  `default: false` is `skip_default: true`; `plugins.telegram` splits into
  `telegram` and `telegram_artifacts`; LLMs are listed in `llms`.
- Databases start afresh: `default` no longer has ledger rows of its own.
- Every plugin module is imported on every command; a broken one fails all
  of them.
- In the catalog, what persists is a source's `id` and a run's `key`;
  renaming another `id` changes nothing stored.
- Configurations that share a database are not checked against each other:
  their runs on shared sources must agree on keys.
- A plugin option holds its value for every call of its object; a value
  that changes per call is a method argument.
