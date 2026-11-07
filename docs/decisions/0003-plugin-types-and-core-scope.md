# 0003: Plugin types and core scope

- **Status:** accepted
- **Date:** 2026-10-18
- **Revised:** 2026-10-20 (plugin bundles loaded with `Register`);
  2026-10-26 (per-use options); 2026-10-27 (autoloading, `process`;
  per-use options as models, `remix` and `deliver` entries; see
  *Revisions*); 2026-10-28, by 0010 (entry points register classes, one
  object per use, `plugins` holds defaults per type; *Loading*,
  *Enabling*, *Options*, *Per-use options*, *Objects* and *Bundles* below
  are superseded); 2026-11-06, by 0015 (the remixer type is replaced by
  applets)
- **Amended by:** 0006 (LLM plugins and the `services` argument), 0007
  (sinks and the `deliver` phase)

## Context

Artifact generators (`rssfeed`, `grouping_*`) lived among the processors as
`ArtifactProcessor`s, the core ran configured pipelines, and plugins were
loaded by hand-written `importlib` factories.

A first revision split them into three types, each loaded from its own
package with `foundation.plugin.ClassLoader` and built on every use with its
constructor arguments. That made every new plugin type a new package and
loader, kept related plugins apart (`summarize`, `tagger` and
`grouping_embeddings` each built an Ollama client from the same options and
declared the same option models) and left each plugin's options unchecked
until it was first used.

## Decision

- **Types.** There are three plugin types: provider, processor and remixer,
  each defined by a `typing.Protocol` the core consumes (`Provider`,
  `Processor`, `Remixer`). Remixers read items, annotations
  and other remixers' artifacts, and produce artifacts; they run on demand
  from the CLI.
- **Loading.** Plugins live in one namespace, `newstool.plugins`, and are
  loaded with `foundation.plugin.Register`, unmodified. A module is a bundle:
  it can provide any number of objects of any type.
- **Enabling.** The `plugins` config section lists plugins with their
  options, in order. The `process`, `remix` and `deliver` sections (and
  those of each workflow, decision 0009) list the runs of each phase, in
  order; an object that no entry names never runs. After the listed
  plugins, a provider that a source names, or a processor, remixer or sink
  that an entry names, if no loaded plugin provides it, loads the plugin of
  the same name with its defaults; a name no plugin provides is a
  configuration error with its path (`sources.<id>.provider`,
  `process.<n>.processor`). A plugin neither listed nor named is never
  imported. All of them are loaded when `Application` is built, before the
  database is opened.
- **Options.** The entry point, `__newstool_plugin__(**options)`, receives
  its section as keyword arguments, validates it with its own pydantic model
  (unknown keys rejected, defaults for the general case, so an empty section
  is enough), builds its objects and returns `(name, Protocol, object)`
  triples. Objects are instances, never classes: the core rejects a class as
  a plugin error. Every provider and processor builds with no options, since
  it can be loaded by name alone. The core never sees a plugin's models; it reports a
  `ValidationError` raised by an entry point as a configuration error with
  the options' path (`plugins.<plugin>.<option>`).
- **Per-use options.** A plugin's section holds its defaults; each use (a
  source of a provider, an entry of a processor, remixer or sink) overrides
  only the options its object declares per use. Every object implements
  `use_options(overrides)`, which validates them over its section with a
  pydantic model of its own and returns that model, and the phase method
  takes it (`retrieve_items(source, fetcher, options)`, `process(db, *,
  key, options, ...)`). A plugin declares the per-use model and its
  section's `Options`, usually a subclass adding the instance-only options,
  so each option is declared once; `merge_options` and the base classes'
  `options_model` do the merge. When `Application` is built, the core
  validates every use and reports a rejected option as a configuration
  error with its path (`sources.<id>.options.<option>`,
  `process.<n>.options.<option>`). A processor's `output_key(options)`
  gives the run's default key; the entry's `key`, outside `options`,
  overrides it. Options live in the configuration only: the database does
  not store them.
- **Objects.** Objects are built once and receive what each task needs as
  method arguments: providers the source, the HTTP client and the source's
  options, and processors, remixers and sinks the database, the scope, the
  entry's key and options.
- **Names.** Object names are unique per type across plugins and are what
  sources and entries refer to. A provider, processor, remixer or sink is
  usually named after its plugin module, so naming it loads it. Processors,
  remixers and sinks own their name, a class attribute, and are registered
  under it; providers' names exist only in their triples. Annotations,
  artifacts and deliveries are keyed by their entry's key, which defaults
  to the object's name and which the configuration may rename (decisions
  0002 and 0009).
- **Methods.** Each protocol has a method of its own (`retrieve_items`,
  `process`, `remix`), named after the phase that calls it. foundation matches
  declared protocols with `issubclass()`, which compares method names only.
- **Bundles.** Bundles enable all their objects unless their options name
  some (`grouping`); this is a convention of the plugins, not a rule of the
  core. Bundles
  never import each other: they share data through annotations (`llm.embed`
  stores the vectors `grouping.embeddings` reads). Code used by a single
  bundle, such as clustering, lives in that bundle.

## Rejected options

- **One package and `ClassLoader` per type, objects built per use** (the
  first revision of this decision). Every new type needs a new loader, and
  related plugins cannot share a client or an options model.
- **Registering factories (or `Lazy` objects) built with each task's
  arguments.** Objects are built once; per-task inputs are method arguments.
- **Loading plugins on first use.** Invalid options would surface only when
  the plugin first runs; loading everything on start-up fails at once.
- **Option models declared or validated by the core.** The core would have
  to know every plugin; each entry point validates its own options instead.
- **Separate `summarize`, `tagger` and Ollama helper modules.** They
  duplicated the connection options and models; they are one `llm` bundle
  with a shared connection and a subsection per processor.
- **Embeddings computed by the grouping remixer on every `remix`.** They are
  computed once per item by `llm.embed` and stored as annotations.
- **`name` in the protocols.** As a data attribute, `issubclass()` rejects
  the protocol. As a `name()` method, it adds API noise only to let the core
  compare it with the triple. Injected by the entry point, it would allow
  renaming an object from the configuration; annotation keys are what the
  configuration renames instead.
- **A common `run` method.** `issubclass()` cannot tell protocols with the
  same methods apart, so remixers were loaded as processors and vice versa.
  A marker method per protocol would be noise, and registering against base
  classes instead of protocols would force inheritance.
- **Per-use options as keyword arguments bound to the method's signature**
  (the 2026-10-26 revision). Each option was declared twice, in the
  section's model and as a keyword argument; types went unchecked until the
  call; and each object had to fall back to its section with `x or self.x`,
  which cannot unset a section default.
- **Generic per-use option models in the core.** The core would have to
  know every plugin's options; each plugin declares its own model.
- **Per-use options checked when the provider is called**, a `TypeError`
  as the error. It would surface only on import, and a `TypeError` raised
  inside the provider would read as a bad option.
- **A map of per-source values in the plugin's section** (source id →
  value). A mistyped source id goes unnoticed, since a plugin never sees the
  sources, and a source's settings end up in two places.
- **Options passed as one positional dict.** It avoids reserved option
  names, but entry points take keyword arguments. Making `register()`'s
  `name` positional-only would also avoid them, but foundation stays as is.

## Consequences

- The configuration has a single `plugins` section; config files written
  for the `processors` and `remixers` sections must be rewritten.
- Annotations and the `telegram` state keep their names; the old
  `grouping_*` artifacts are left behind, and the grouping remixers produce
  theirs under `singlelink`, `avglink` and `embeddings`.
- Every loaded plugin is imported and built on start-up, so a broken plugin
  or invalid options fail every command, including read-only ones.
- A new plugin type needs a method name of its own: a protocol whose methods
  are a subset of another's is taken as its parent.
- `name` and `self` cannot be plugin options: they are `register()`'s own
  parameters.
- Grouping with embeddings needs `process` to have run `embed` first.
- A plugin needs a section only for options. Config files with `enrich:`
  or `provider_options:` must be rewritten as `process:` (with `key` moved
  out of `options`) and `options:`, and remixers and sinks enabled by their
  section alone must be listed in `remix:` and `deliver:`.
- A source or entry that gives its object an option it does not declare,
  or a value of the wrong type, fails every command at start-up, like
  invalid plugin options.
- Every phase method takes its options as one model, so adding a per-use
  option is a field in the plugin's model, not a new parameter.

## Revisions

- **2026-10-27.** Per-use options are pydantic models validated by each
  object's `use_options`, for providers, processors, remixers and sinks,
  and `remix` and `deliver` list their runs like `process` (with workflows,
  decision 0009). Discarded: signature binding of keyword arguments,
  `output_key(**options)` as the processors' check, and enabling remixers
  and sinks by their plugin section.
- **2026-10-27.** Providers and processors named by sources and `process`
  entries load their plugin on their own, after the listed plugins; entry
  points return instances. `enrich` renamed `process` (section, phase, CLI
  command and `Processor.process`), `provider_options` renamed `options`,
  and an entry's `key` moved out of its `options`. Discarded: "a plugin
  without a section is not loaded"; loading every module to find which one
  provides a name (it imports every plugin on every command); and a root
  `llm:` list of LLM plugins next to `plugins` (two places to declare one
  plugin; listed plugins loading first already orders LLMs before their
  consumers, see 0006).

- **2026-10-26.** Per-use options extended to processors through the
  `enrich` section; the `plugins` section no longer orders `enrich`.
  Discarded: running every loaded processor once, in the order of `plugins`.
- **2026-10-26.** Added per-use options. Discarded: `URLProvider`, the
  single-URL import (`import-url`) that used it, and external pipelines
  (processor chains over one item as scripts in `scripts/`, built on that
  import). Neither was in use; both may return on a model that fits
  sources defined on the fly.
