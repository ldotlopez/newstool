# newstool

Collects news from several websites, keeps the articles, and builds things
from them: markdown copies, LLM summaries and tags, event groupings, RSS
feeds and digests, and Telegram posts. It was written for local news (Castelló), but any
site can be added with a provider.

It works in two stages:

1. **Workflows** import and process:
   - **import**: each configured **source** (a website) is fetched with its
     **provider**, and every article becomes an **item**. Re-importing an
     unchanged article does nothing; a changed one is updated in place.
   - **process**: **processors** add **annotations** to each item (its
     markdown, a summary, tags...).
2. **Applets** build and deliver: each configured **applet instance** runs
   when it is due (every hour, Mondays at 7:00...), reads what is stored,
   and emits **documents** (an RSS feed, a weekly digest, a message per new
   summarized item...). Each output of an instance is routed to **sinks**,
   which send its documents to the outside world (a Telegram chat, a file a
   web server serves...) and record each **delivery**, so nothing is sent
   twice.

Providers, processors, applets and sinks come from **plugins**. A
**workflow** says which sources to import and what to process on them; the
configuration's root keys are the `default` workflow, and `workflows` adds
more. Applets and sinks belong to no workflow.

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- Optionally, an Ollama server for the `ollama` LLM plugin, which
  `summarize`, `tagger`, `embed` and `digest` use

## Install

```sh
uv sync
```

## Configuration

Pass a YAML file with `-c/--config`. Every section is optional;
`config.example.yaml` is a starting point.

```yaml
storage_dir: /path/to/storage        # data.db and content/; default: <user data dir>/newstool
cache_dir: /path/to/cache            # default: <user cache dir>/newstool

cache:
  expiration: 6h                     # HTTP cache lifetime (seconds, or 5m, 2h, 3d)

plugins:                             # defaults of each type's options
  ollama:
    api_base: https://ollama.example.com
    api_key: ${OLLAMA_API_KEY}       # or leave it to the OLLAMA_API_KEY variable
  tagger:
    model: gemma4:12b
  telegram:
    bot_token: ${TELEGRAM_BOT_TOKEN}

llms:                                # the first serves those that name none
  - ollama

sources:
  - id: castellonplaza               # required, stable: part of each item's key
    name: Castellón Plaza
    provider: plaza                  # see "Providers" below
    url: https://castellonplaza.com/castellon9/

processors:                          # the `default` workflow runs them in order
  - markdownify
  - summarize
  - tagger

sinks:                               # where documents go
  - {id: main-chat, sink: telegram, options: {chat_id: "${TELEGRAM_CHAT_ID}", interval: 30m}}
  - {id: site, sink: file, options: {path: "/srv/www/{app}.xml"}}

apps:                                # run by `apps run`, when due
  - {id: items, app: itemfeed, sink: main-chat}
  - {id: headlines, app: feed, every: 1h, options: {title: Castelló news}, sink: site}
```

A source's `id` identifies its items: its `url` and `provider` can change
without losing anything, but renaming the `id` starts the source from
scratch. Removing a source from the file keeps its items; they just stop
being updated.

`${VAR}` in a value is replaced with the environment variable `VAR` when the
file is loaded, or with `VAR` from a `.env` file next to the config file (the
real environment wins). A missing variable is an error. Pass secrets (API
keys, bot tokens) this way, never as literals; `.env` is git-ignored.
Comments and keys are left alone. Write a literal `$` in a value as `$$`,
and quote a reference inside `{...}` or `[...]` (`{api_key: '${KEY}'}`).

Relative paths (`storage_dir`, `cache_dir`) are relative to the config file's
directory, and `~` is expanded: with `/a/b/config.yaml`, `data` and `./data`
mean `/a/b/data` and `../data` means `/a/data`.

Any key can be set by a `NEWSTOOL_`-prefixed environment variable, with `__`
for nesting (`NEWSTOOL_CACHE__EXPIRATION=2h`,
`NEWSTOOL_PLUGINS__OLLAMA__API_BASE=http://box:11434`,
`NEWSTOOL_STORAGE_DIR=data`), or by the same in the `.env` file. From highest
priority: the environment, the `.env` file, the config file, the aliases below,
the defaults. Lists (`sources`, `workflows`...) are configured in the file.
Values from the environment and `.env` are taken as they are, without `${VAR}`
expansion. `OLLAMA_HOST` and `OLLAMA_API_KEY` are aliases for
`plugins.ollama.api_base` and `plugins.ollama.api_key` when nothing else sets
them; `OLLAMA_HOST` is read as Ollama does (`box` means `http://box:11434`,
`0.0.0.0` means `localhost`).

```sh
# .env
OLLAMA_API_KEY=...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

### Plugin types and the catalog

Plugins provide **types**: providers, processors, applets, sinks and LLMs,
each with a name (listed below). `plugins.<type>` holds the defaults of a
type's options for every use of it; the missing ones take the defaults
listed below, and unknown or invalid ones are rejected with their path
(`plugins.summarize.max_retries: ...`). A section builds nothing.

The **catalog** lists the uses: `llms`, `sources` and `processors`. An
entry is a type name, or a type with `id`, `key` and `options`. Its options
override its type's section, merged key by key in nested mappings (any
other value, lists included, replaces). `id` names the entry so workflows
can refer to it, and cannot be a type's name. Everything configured is
checked at start-up, whether it runs or not; an object is built only when
a run needs it.

Every processor run writes one annotation **key**, the processor's own
unless the entry names another with `key` (lowercase words, optionally in
`/`-separated parts: `summary`, `summary/es`), so a processor can run
several times with different options and keys:

```yaml
processors:
  - markdownify                      # writes `markdown`
  - summarize                        # writes `summary`
  - processor: summarize
    id: summary-es                   # for the workflows that name it
    key: summary/es
    skip_default: true
    options:
      prompt: "Resume en español el siguiente artículo:\n\n"
      model: gemma4:27b
```

An entry that gives its type an option it does not take fails every command
at start-up with the option's path
(`processors.1.options.temperature: Extra inputs are not permitted`).

### Applets and sinks

`apps` and `sinks` list **instances**, each with a required `id`, its type
(`app:` or `sink:`) and `options` over the type's section. They belong to
no workflow.

A **sink instance** is a destination with its own pacing: where to deliver
(a chat, a webhook, a file) and how fast (`interval`, `max_per_run`). Two
instances of one type can post to different places.

An **applet instance** decides when it runs and what it emits:

- **When:** `every` (a duration after its last successful run), `at`
  (`"HH:MM"`, local time: once a day from then) and `days` (weekdays,
  `[mon, fri]`). They combine; without any, it runs on every `apps run`.
  `days` is not `on`, which YAML reads as `true`.
- **What it reads:** its options say which sources (`sources`, default
  every source) and what else; an applet keeps a state of its own between
  runs (a cursor, the last period it covered), so it can emit only what is
  new.
- **Where it goes:** each applet has named **outputs**; `routes` sends each
  to sink instances, and `sink` is the shorthand for an applet with one
  output. An output without a route keeps its documents for other applets
  to read.

```yaml
sinks:
  - {id: chat, sink: telegram, options: {chat_id: "-1001234", interval: 30m}}
  - {id: politics, sink: telegram, options: {chat_id: "-1009876", max_per_run: 1}}
  - {id: site, sink: file, options: {path: "/srv/www/{app}.xml"}}

apps:
  - id: items                        # each new summarized item, once
    app: itemfeed
    sink: chat
  - id: politics-es
    app: itemfeed
    options: {sources: [juntas], annotation: summary/es}
    sink: politics
  - id: weekly                       # Mondays at 7:00
    app: digest
    at: "07:00"
    days: [mon]
    routes: {digest: [chat]}
  - {id: headlines, app: feed, every: 1h, options: {max_items: 10}, sink: site}
```

At start-up, a route to an unknown output or sink, or to a sink that does
not accept the output's content (an RSS feed to Telegram), is an error, and
so is an applet that reads an unknown source or an annotation no process
run writes on its sources.

### Workflows

The `default` workflow uses every source and runs every catalog processor,
in order, except those with `skip_default: true`. `workflows` lists more,
each with the ids of its sources and its process runs: a catalog `id`, a
type name (the type with its section's options) or an entry of its own,
without `id`. A reference runs the entry as it is; to change an option,
write an entry of the workflow's own.

```yaml
sources:
  - {id: castellonplaza, name: Castellón Plaza, provider: plaza, url: ...}
  - {id: juntas, name: Juntas, provider: csjuntasgobierno, url: ..., skip_default: true}

workflows:
  - name: juntas
    sources: [juntas]
    process: [markdownify, summary-es]
```

`skip_default` only leaves an entry out of `default`: the workflows that
name it still run it. `import`, `process` and `run` run `default` unless
given `-w/--workflow NAME`, so each workflow is its own cron line
(`newstool run -w juntas`), and `apps run` another one, every few minutes.
A workflow only touches its sources.

Annotations belong to items. Within a workflow a key is written by one run;
on sources that workflows share, one processor type writes it, and other
options for it only get a warning (the first run to process an item writes
it). Every key a run reads must be written by a process run on its
workflow's sources, in any workflow. Ids, workflow names and output names
use lowercase letters, digits, `_` and `-`; `default` is reserved.

`summarize`, `tagger`, `embed` and `digest` use an LLM: `llm` names an
`llms` entry by `id`, or an LLM type (with its section's options), and
defaults to the first `llms` entry; `model` defaults to that LLM's default
model. A name that resolves to no LLM, or an LLM consumer with `llms`
empty, fails every command at start-up. Everything else works without an
LLM, but `grouping` and `itemfeed` read the tags and summaries those
processors write.

Changing a type's or an entry's options never regenerates existing
annotations; use `process --force` for that. What is stored is keyed by a
source's `id`, a process run's `key`, and an applet or sink instance's
`id`: renaming an applet instance starts it from scratch, and renaming a
sink instance starts its deliveries anew.

## Usage

```sh
# Import every configured source
uv run newstool -c config.yaml import

# Run every process run of the workflow in order, or only one processor's
uv run newstool -c config.yaml process
uv run newstool -c config.yaml process markdownify --source castellonplaza --limit 20

# Run import and process in turn (e.g. from cron), for a workflow with -w
uv run newstool -c config.yaml run
uv run newstool -c config.yaml run -w juntas
uv run newstool -c config.yaml run --all     # every workflow, default first

# Run the applet instances that are due, then deliver (cron, every few minutes)
uv run newstool -c config.yaml apps run
uv run newstool -c config.yaml apps run --app weekly --force
uv run newstool -c config.yaml apps run --dry-run
uv run newstool -c config.yaml apps run --app items --no-deliver

# Deliver what is pending, without running applets
uv run newstool -c config.yaml deliver
uv run newstool -c config.yaml deliver --sink chat --dry-run
uv run newstool -c config.yaml deliver --sink chat --ignore-interval --ignore-max-per-run

# Start an applet instance from scratch, optionally dropping its documents
uv run newstool -c config.yaml apps reset items
uv run newstool -c config.yaml apps reset weekly --with-documents

# Inspect what is stored (read-only), as a table or --format json
uv run newstool -c config.yaml inspect items --source castellonplaza --limit 20
uv run newstool -c config.yaml inspect items --item 4127
uv run newstool -c config.yaml inspect content --sha256 <sha256> > item.html
uv run newstool -c config.yaml inspect annotations --item 4127
uv run newstool -c config.yaml inspect annotations --annotation 512
uv run newstool -c config.yaml inspect annotations --key summary/telegram/es
uv run newstool -c config.yaml inspect apps
uv run newstool -c config.yaml inspect documents --app weekly
uv run newstool -c config.yaml inspect documents --document 31 > digest.md
uv run newstool -c config.yaml inspect deliveries --sink chat --status error

# Change the state of ledger rows, or send them now
uv run newstool -c config.yaml deliveries set-status --as queued --status error
uv run newstool -c config.yaml deliveries set-status --as done --delivery 31
uv run newstool -c config.yaml deliveries send --delivery 31

# Queue documents for a sink by hand (routed to it or not), or mark them as sent
uv run newstool -c config.yaml deliveries set-status --sink chat --app weekly --as queued
uv run newstool -c config.yaml deliveries set-status --sink chat --all --as done --dry-run

# Delete, without asking: the same options as inspect select what goes
uv run newstool -c config.yaml delete items --item 4127
uv run newstool -c config.yaml delete annotations --processor summarize --source castellonplaza
uv run newstool -c config.yaml delete annotations --key summary/telegram/es
uv run newstool -c config.yaml delete documents --app headlines --until 2026-10-01
uv run newstool -c config.yaml delete deliveries --sink chat --document 31
uv run newstool -c config.yaml delete deliveries --sink chat --all
```

Items and annotations are selected by their numeric id, which `inspect`
shows; documents and deliveries too (`--document`, `--delivery`).
`process`, `inspect items|annotations` and `delete items|annotations`
accept `--source` (a source id), `--since`, `--until` (publication),
`--item` (repeatable) and `--limit`; `inspect` and `delete` add
`--processor`, `--key` and `--annotation` for annotations. Documents are
selected by `--app`, `--output`, `--key`, `--since` and `--until`
(emission), `--document` and `--limit`, and deliveries by the same plus
`--sink`, `--delivery` and `--status`. Filters combine; an id that the
selection does not return is an error.

`inspect` and `delete` sort with `--sort` (default `updated`, `emitted` for
documents), always ascending, so dates go oldest first; the sort also
decides which rows `--limit` keeps. The keys: `id`, `source`, `published`,
`imported`, `updated` and `title` for items; `id`, `item`, `processor` and
`updated` for annotations; `id`, `app`, `type` and `emitted` for
documents; `id`, `sink`, `status` and `updated` for deliveries.

`inspect items` lists each item's annotations as `<id> <processor>.<key>`;
one `--item` shows all its fields, a row per annotation, and the
`inspect content --sha256 <sha256>` command that writes its stored content
to stdout as is.
`inspect annotations` shows a one-line preview per key, and one
`--annotation` prints its full value (text as is, the rest as JSON).
`inspect documents` loads contents only for `--document`, and one
`--document` writes the content to stdout and its metadata to stderr, so
it can be redirected. `inspect apps` shows each instance's schedule, last
run, last success, next due time (local time) and last error.
`--format json` prints full records.

`apps run` runs every instance that is due (`--app`, repeatable, limits
it; `--force` runs them whether due or not), then delivers what is pending
for every sink, or with `--app` for the sinks those instances are routed
to. `--no-deliver` stores and queues what they emit and sends nothing, for
`deliver` to send later. Its table shows, per instance, the documents it
emitted that are new, those already stored, and `Routed`: the rows it
queued for stored documents routed since they were emitted (see *How
delivery behaves*). A failing instance is reported and the others still run;
its state is kept, so its next run covers what the failed one did not. The
exit status is non-zero if anything failed. `--dry-run` runs the applets
and shows the documents they would emit (new, or already stored) and their
new state, storing and delivering nothing. `apps reset ID` forgets an
instance's state and run times; its documents stay, so what it emits again
under their keys is not sent again, unless `--with-documents` deletes them
and their deliveries too.

`delete` never asks, so run `inspect` with the same options first. A
selection with no filter or id is refused. Deleting an item takes its
processing state and annotations with it, and an item still in its
source's index comes back on the next `import` with a new id.
`delete annotations` deletes exactly what `inspect annotations` lists with
the same options (by processor, key such as `summary/telegram/es`, id or
item), each with its processing state, so the run that wrote the key
processes the item again. `delete documents` deletes documents with their
deliveries, and refuses those with a delivery that is not `done`. Deleting
a document frees its key: an applet that emits it again stores and
delivers it again. `delete deliveries` drops ledger rows, or every row (of
`--sink`) with `--all` and no other filter.

`deliveries set-status`, `deliveries send` and `delete deliveries` take the
selection of `inspect deliveries` and need at least one filter or id, so
run `inspect` first.

`set-status --as queued|done|error` sets the state of deliveries:
`queued` also gives fresh attempts, so the next delivery sends them, and
`done` records a delivery you settled by hand.

- With `--sink` and document filters (`--app`, `--output`, `--key`,
  `--since`, `--until`, `--document`), each selected document without a row
  of that sink gets one in that state, whether its output is routed to the
  sink or not; a content type the sink does not accept is refused, and
  nothing is marked. With `--sink` and `--all`, only the documents routed to
  that sink. `--limit` counts documents. Existing rows are left as they
  are, with a warning, unless `--overwrite`. So `--as queued` queues
  documents for a sink without editing the configuration.
- Otherwise, or with `--delivery` or `--status`, it changes the selected
  rows; `--all` alone changes every row.

`--dry-run` counts what would change without changing it. `send` sends the
selected rows now, whatever their state (`done` ones too), with no backoff
or pacing, and exits non-zero if one fails; a row whose sink is no longer
in the configuration is skipped with a warning. It creates no rows.

Global options: `--log-level LEVEL` (also accepts specs such as
`info,db:debug`), and `-v`/`-q`, repeatable, to raise or lower it one step
each from `warning` (`-v` shows progress messages, `-vv` debug). Without
them, the level comes from `NEWSTOOL_LOG_LEVEL`, then from `log_level` in
the config, then `warning`.

Failures of a plugin or of something external (network, LLM backend,
database, disk) are reported as `Type: message`; the traceback is shown only
with debug logging (`-vv`). Unexpected errors always show it.

Results (tables, `inspect` output, contents, `--help`, and the summaries of
`run`, `import`, `process`, `apps run` and `deliver`) go to stdout;
progress and logs go to stderr. Each stream is rich only when it is a
terminal, so `newstool run > summary.txt` keeps the progress rows on screen
and writes tab-separated tables, and with stderr redirected (cron) there is
no progress and logs are one plain line per record. The progress shows a
row per phase in `run` and a row per source, processor, applet or sink
while it runs. Set `DISABLE_RICH=1` (or `RICH_DISABLED=1`), or
`TERM=dumb`, for plain output on both streams; `NO_COLOR=1` only drops the
colors.

### The phases, step by step

newstool runs in four phases. Each is a command of its own, so they can
run from separate cron lines or one by one by hand; `run` and `apps run`
chain two of them. Every phase is safe to run again: what is already done
is skipped, and what failed is retried.

| Phase | Command | Reads | Writes |
| :--- | :--- | :--- | :--- |
| Import | `import` | the sources' websites | items |
| Process | `process` | items, annotations | annotations |
| Applets | `apps run` | items, annotations, documents | documents, delivery rows, applet state |
| Deliver | `deliver` | delivery rows, documents | the outside world, delivery rows |

**1. Import** (`import [-w WORKFLOW]`) fetches every source of the
workflow (`default` without `-w`) with its provider and stores each
article as an item, oldest first. An unchanged article is left as it is;
a changed one is updated in place, so its processors run on it again. A
failing source is reported and the others are still imported; what was
fetched before an error is kept. The `Import` table shows, per source,
the items read and the error, if any.

**2. Process** (`process [PROCESSOR] [-w WORKFLOW]`) runs the workflow's
process entries in configuration order, or only those of one processor
type, over the items of its sources. Each entry writes one annotation key
(`markdown`, `summary/telegram/es`...) and only picks the items that need
it (see *How `process` behaves*). `--source`, `--since`, `--until`,
`--item` and `--limit` narrow the items; `--force` reprocesses them all.
The `Process` table shows, per key, the items done, ignored (skipped by
the processor) and failed.

`run [-w WORKFLOW]` runs import, then process; a failing phase is logged
and the next one still runs. It is the usual cron line, one per workflow;
`run --all` runs every workflow's phases in turn, `default` first, and
excludes `-w`.

**3. Applets** (`apps run`) runs every applet instance that is due by its
schedule (`every`, `at`, `days`; without any, on every call), or the ones
`--app` names; `--force` runs them whether due or not. Each run reads what
is stored, emits its documents and saves its state, all in one
transaction:

- a document whose key the instance already stored is not stored again,
  so an applet can emit the same item on every run without it being sent
  twice;
- every emitted document gets a `queued` delivery row for each sink its
  output is routed to that it has none of: new ones, and stored ones
  routed since they were emitted.

The `Apps` table shows, per instance, whether it was due, the documents
that are `New`, those `Already stored`, the rows `Routed` for stored ones,
and the error. A failing instance keeps its previous state and does not
stop the others. Then `apps run` delivers (phase 4): to every sink, or with
`--app` to the sinks those instances are routed to. `--no-deliver` stops
before that; `--dry-run` shows what the applets would emit and their new
state, storing and sending nothing.

**4. Deliver** (`deliver [--sink ID]`) sends the pending delivery rows of
every sink instance, or of the ones named: `queued` rows, and failed ones
with attempts left once their backoff has passed. Each sink goes oldest
first and keeps its own pace: with an `interval`, one row once its last
delivery is that old; then at most `max_per_run` rows. `--ignore-interval`,
`--ignore-max-per-run` and `--max-per-run N` override that pace for one
run, and `--dry-run` lists what would be sent. The `Deliver` table shows,
per sink, the rows delivered and failed.

A typical setup, two cron lines:

```sh
*/30 * * * *  uv run newstool -c config.yaml run -w news   # import and process
*/5  * * * *  uv run newstool -c config.yaml apps run      # applets, then deliver
```

Both take the write lock, so a run that starts while the other holds it
fails with a lock error and is picked up by its next cron run; keep them
from overlapping where possible (`apps run` holds the lock while it
sends). The same phases by hand, checking each step before the next:

```sh
uv run newstool -c config.yaml run -w news                     # import and process
uv run newstool -c config.yaml inspect annotations --key summary
uv run newstool -c config.yaml apps run --app items --dry-run  # what it would emit
uv run newstool -c config.yaml apps run --app items --no-deliver
uv run newstool -c config.yaml inspect documents --app items
uv run newstool -c config.yaml inspect deliveries --status queued
uv run newstool -c config.yaml deliver --sink chat --dry-run
uv run newstool -c config.yaml deliver --sink chat
```

### How `process` behaves

- Each entry handles every item once, and keeps its own state per item
  under its key. It runs again on an item only when the item's content
  changed, or when the processor itself was upgraded.
- A processor can skip items it does not apply to (e.g. `markdownify` on a
  PDF). Skipped items stay skipped until their content changes.
- Failures are retried on later runs, up to 3 attempts by default (the
  `max_retries` option), waiting longer each time (1 min, 2 min, 4 min... up
  to 24 h).
- A run only sees items whose run of the key it reads finished (see the
  *Reads* column below). Items skipped upstream never reach it.
- `--force` reprocesses everything in scope, skipped items included, with
  fresh retry attempts.

### Providers

Each provider is a plugin of the same name, without options except
`prensaiberica`, `telegram_channel` and `feedreader`.

| Provider | Site | Content |
| :--- | :--- | :--- |
| `prensaiberica` | Index page of a Prensa Ibérica paper's section (El Periódico Mediterráneo...); unchanged articles are not fetched again | HTML |
| `castelloninformacion` | Castellón Información | HTML |
| `plaza` | Castellón Plaza | HTML |
| `theguardian` | The Guardian | HTML |
| `csjuntasgobierno` | Index page of *juntas de gobierno* minutes | PDF |
| `telegram_channel` | Articles linked from a public Telegram channel (`url: https://t.me/<channel>`) | HTML |
| `feedreader` | Any RSS or Atom feed (`url:` the feed) | The feed's HTML or text, or the article's HTML with `fetch_article` or `article_selector` |

`prensaiberica` imports the articles its section's index page lists. Its
`exclude_sections` option leaves out the articles of the index's sections
with those header titles, compared case-insensitively. It defaults to
`Comarcas` and `Vídeos y galerías de Castellón`; `[]` excludes none:

```yaml
sources:
  - id: elperiodicomediterraneo-castello
    name: El Periódico Mediterraneo (Castelló ciudad)
    provider: prensaiberica
    url: https://www.elperiodicomediterraneo.com/castello
    options:
      exclude_sections: [Comarcas, Vídeos y galerías de Castellón]
```

`telegram_channel` reads the channel's web preview, which only public
channels have, and imports one item per linked article, keyed by its
canonical URL; the post id, text and photo go into the item's `data`. Links that
resolve to the site's front page, such as a daily front-page post, are
skipped. Its `pages`
option (default 1, 20 posts each) reads further back. The preview is always
fetched fresh, never from the HTTP cache.

`feedreader` imports one item per feed entry: its full content (or summary),
author, categories as `tags` (the first also as `section`) and an image.
Feeds that carry only a summary can set `fetch_article: true`: each entry's
link is then fetched and its page becomes the item's content, from which
`markdownify` extracts the article. `article_selector`, a CSS selector of
the article body, keeps only that element of the item's HTML, the feed's or,
with `fetch_article`, the page's; plain-text content is kept whole. Set
them in the plugin's section for every feed, or per source in its
`options`, which win:

```yaml
sources:
  - id: some-blog
    name: Some blog
    provider: feedreader
    url: https://blog.example.com/feed.xml
    options:
      fetch_article: true
      article_selector: article .post-body  # optional
```

To support a new site, see
[Writing a plugin](docs/ARCHITECTURE.md#writing-a-plugin).

### Processors

| Plugin | Processor | Reads | Writes | Does |
| :--- | :--- | :--- | :--- | :--- |
| `markdownify` | `markdownify` | item content | `markdown` | Extracts the article's markdown from HTML and PDF items |
| `summarize` | `summarize` | `markdown` | `summary` | Summarizes the article with an LLM |
| `tagger` | `tagger` | `markdown` | `tags` | Extracts entity tags with an LLM |
| `embed` | `embed` | `tags` or `markdown` | `<input>_embedding` | Embeds the tags (sorted and comma-separated) or the markdown with an LLM |
| `truncate` | `truncate` | `markdown` | `summary` | The markdown's first `length` characters (default 200): a fast, offline stand-in for `summarize` in tests |

Every option can be set in the type's section, as the default, or per
entry. Every processor takes `max_retries` (default 3), and `summarize`,
`tagger` and `embed` take `llm` (see above) and `model`; `summarize` takes
`prompt` (followed by the article's markdown) and `embed` takes `input`
(`tags`, the default, or `markdown`; one entry per input). `truncate`
accepts `summarize`'s options and ignores them, so an entry swaps one for
the other by its type alone; its `llm` is not checked, so it needs no
`llms`. On shared sources, two types cannot write one key: give each its
own. Consumers read annotations by key:
`itemfeed` reads `summary` (or its `annotation` option's key), `grouping`
reads `tags` and
`<embedding>_embedding`, and `digest` and `search` read `markdown`.

### LLMs

| Plugin | LLM | Does |
| :--- | :--- | :--- |
| `ollama` | `ollama` | Prompts and embeddings with an Ollama server |

Options of `ollama`: `api_base` (default `http://localhost:11434`),
`api_key`, `chat_model` (default `gemma4:12b`) and `embed_model` (default
`mxbai-embed-large:latest`).

### Applets

| Plugin | Applet | Output (content type) | Document keys | Does |
| :--- | :--- | :--- | :--- | :--- |
| `itemfeed` | `itemfeed` | `items` (`text/plain`) | `item:<source>/<uid>` | One document per newly imported item with its `annotation`: the annotation as text, with the item's title, link and image |
| `feed` | `feed` | `feed` (`application/rss+xml`) | the run's time | RSS feed of the newest items of its sources |
| `digest` | `digest` | `digest` (`text/markdown`) | `<source id>/<since>_<until>` | Markdown digest of the highlights of each source over the last `lookback`, written with an LLM from `markdown` |
| `grouping` | `singlelink` | `groups` (`application/json`) | the run's time | Clusters tagged items into events (single-link over tag overlap) |
| `grouping` | `avglink` | `groups` (`application/json`) | the run's time | Clusters tagged items into events (average-link over tag overlap) |
| `grouping` | `embeddings` | `groups` (`application/json`) | the run's time | Clusters tagged items by tag overlap blended with the similarity of their `tags_embedding` or `markdown_embedding` (single-link) |

Options, in the type's section as defaults or per instance. Every applet
takes `sources` (the source ids it reads; default every source). Lengths
of time, here and in every other option, are seconds or a number with a
unit suffix: `90s`, `5m`, `2h`, `3d`, `1h30m`.

- `itemfeed`: `annotation` (the key emitted as the text, default
  `summary`), `backfill` (how far before its first run it starts: default
  0, so its first run only starts counting and what is already stored is
  not sent; `1d` emits the last day's items on the first run; `all`, the
  whole history; nothing imported before that start is ever emitted) and
  `wait` (default 1d: an item imported up to this long before a run is
  still emitted once its annotation exists, but never before the start).
- `feed`: `title` (default `newstool feed`), `link`, `description`
  (default: the title), `max_items` (default 100). Route it to a `file`
  sink to publish it.
- `digest`: `llm` and `model` (see above), `lookback` (default 7d: the
  period each run covers), `max_items` (newest items per source, default
  50), `max_article_chars` (each article's markdown is cut to this, default
  3000) and `context_length` (the model's context window in tokens, default
  32768). Schedule it for its period (`days: [mon]`, `at: "07:00"`); a
  second run over the same period emits nothing new.
- `singlelink`, `avglink` and `embeddings`: `min_score` (default 0.3), `tau` (time
  decay, default 24h; `null` disables it), `lookback` (default 7d: the
  items each run groups). `embeddings` adds `embedding` (`tags` or
  `markdown`, default `tags`) and `embedding_weight` (0 to 1, default 0.5).
  Items without the annotations an applet reads are left out of its groups,
  so `embeddings` needs `process` to have run `embed` with that input first.

Applets never act outside newstool: they emit documents, and sinks deliver
them. A document is never rewritten; one emitted again under the same key
is ignored. Documents are kept until `delete documents` removes them.

### Sinks

| Plugin | Sink | Accepts | Delivers |
| :--- | :--- | :--- | :--- |
| `telegram` | `telegram` | `text/plain`, `text/markdown` | Documents to a Telegram chat: as a message (title, text, link, image) when it fits, else as a file |
| `googlechat` | `googlechat` | `text/plain`, `text/markdown` | Documents to a Google Chat space, by incoming webhook, as a card |
| `filesink` | `file` | anything | Writes each document to a file, replacing it |
| `stdout` | `stdout` | anything | Prints each document as a line of JSON on stdout, for tests and debugging |

Every sink takes `interval` (time between its deliveries, default 0: no
pacing), `max_per_run` (deliveries per run at most, default 5) and
`max_retries` (default 3).
`telegram` adds `images` (post the document's image, when it has one, as a
photo with the text as its caption; default true), `link_text` (the text of
the link, default `original article`), `link_preview` (let Telegram show the
link's preview on messages without an image, default false) and `markdown`
(post in Telegram's legacy Markdown, the text unescaped so that its
formatting renders, instead of HTML-escaped text; default false). Telegram
refuses a post whose Markdown does not parse, such as a lone `_` or `*`. A
document longer than a message (4096 characters, such as a digest) goes as
a file, its title as the caption.

Every `telegram` instance needs a `bot_token` and a `chat_id`, its own or
its type's section's, which holds their defaults and is optional: instances
can post with different bots. The `googlechat` section or instance gives
the webhook as `url`, or as `channel` (the space id) and `token`. Each
document goes as a card: title and text, then the image if any, then a
button to the link if any. It takes `images` and `link_text`, as
`telegram`'s; Chat has no link preview to control. Chat shows no image
hosted at `blogger.googleusercontent.com`, so those go at full size through
the `wsrv.nl` image proxy, which sees their URLs. `file` takes `path`, an
absolute path (`~` allowed) where `{app}`, `{output}` and `{key}` are
replaced by the document's (`/` in a key becomes `_`); the file is
replaced whole, never left half-written. `stdout` takes only the common
options; each line holds every field of the document, its content
included, and it records no reference. It shares stdout with the
commands' tables.

```yaml
plugins:
  telegram:
    bot_token: ${TELEGRAM_BOT_TOKEN}
    chat_id: ${TELEGRAM_CHAT_ID}
  googlechat:
    url: ${GOOGLECHAT_WEBHOOK_URL}
sinks:
  - {id: chat, sink: telegram, options: {interval: 30m}}
  - {id: space, sink: googlechat}
apps:
  - {id: items, app: itemfeed, routes: {items: [chat, space]}}
```

How delivery behaves:

- Each document an applet emits is queued for every sink its output is
  routed to. `apps run` delivers after running the applets, and `deliver`
  on its own.
- A document has no destination of its own: `inspect documents` shows what
  was emitted and by whom (applet, output, key, content, title, link,
  image, time), and no sink. The destination is the applet's `sink` or
  `routes` in the configuration, and delivering only sends ledger rows
  (`inspect deliveries`). Each document a run emits, new or already
  stored, gets a row for each sink its output is routed to at that moment
  and it has none of. So an applet without a route stores documents that
  are never delivered, and a route added later reaches the stored
  documents the applet emits again (an `itemfeed`'s window), not older
  ones. A row deleted by hand comes back if the applet emits its document
  again while routed to that sink. To deliver documents without a row,
  route them or not, then create their rows and send them:

  ```sh
  uv run newstool -c config.yaml deliveries set-status --sink chat --app items --as queued
  uv run newstool -c config.yaml deliver --sink chat
  ```

  Or start over with `apps reset items --with-documents`: for `itemfeed`,
  the next run is a first run again, so only what its `backfill` reaches
  is emitted (with the default 0, none of the items already imported).
- A sink instance delivers oldest first, whatever applet emitted them:
  by when each document was emitted, and within one run in the order the
  applet emitted them. `itemfeed` emits the oldest item first (by
  publication time, or import time for an item without one), so a chat
  gets articles in the order they were published. The order is fixed for
  now. With an `interval`, it delivers one document once its last delivery
  is that old; without one, every pending document, up to `max_per_run`
  per run. Two applets routed to one chat share its pace. `deliver`
  overrides the pacing for one run: `--ignore-interval` sends now, up to
  `max_per_run`; `--ignore-max-per-run` sends every due row, which on a
  sink with an `interval` needs `--ignore-interval` too (one row per run
  otherwise); `--max-per-run N` replaces the limit. Retries still wait for
  their backoff.
- A failed delivery is retried like a processor's; it holds nothing else
  back.
- Nothing is delivered twice to the same sink instance.
- A delivery is marked `sending` before the call. If a run is interrupted
  there, its outcome is unknown and it is never retried on its own: check
  the chat, then settle it with `deliveries set-status --as done|queued
  --delivery ID` (the id `inspect deliveries` shows), or leave it.
- `inspect deliveries` shows the ledger: each row's id, sink, document,
  state, attempts and last error.

## Data and backups

Everything lives in `storage_dir`: the SQLite database (`data.db`) and the
content directory (`content/`), which holds article contents, annotation
values and documents. Back up both together. The database runs in
WAL mode, so back it up with SQLite's backup API (or with no process using
it), not by copying `data.db` alone.

The schema is created, never migrated: after an upgrade that changes it,
move the old `data.db` and `content/` aside and re-import. New tables are
added on their own. Three upgrades come with a one-shot script for existing
databases (back up first):

- `scripts/migrate_autoincrement.py -c config.yaml`: ids that are never
  reused, which `--item` and `--annotation` rely on.
- `sqlite3 -bail data.db < scripts/migrate_annotation_keys.sql`: keys
  processing state and annotations by annotation key,
  keeping every row and id. Run it before the first `process` on the new
  schema.
- `scripts/migrate_applets.py -c config.yaml`: applets (decision 0015).
  Adds each item's import date (its publication date, for the items
  already stored), and drops the remixers' artifacts and the old delivery
  history. `itemfeed` instances start counting on their first run, so
  nothing already posted is posted again.

The plugin catalog (decision 0010) needs a new database and a rewritten
configuration: `process` moves to `processors` (or to workflows),
`default: false` becomes `skip_default: true` and LLMs are listed in
`llms`. Applets (decision 0015) need a rewritten configuration too:
`remixers` and the workflows' `remix` and `deliver` become `apps` with
routes to `sinks` instances; the `telegram` and `googlechat` item sinks
become an `itemfeed` instance routed to them, and `telegram_artifacts`
becomes a route from the digest's output to a `telegram` instance.

Commands that write take a lock next to the database (`data.db.lock`), so
a second one fails at once instead of running alongside the first.

## Known limitations

- The same article in two sources is stored, and processed, twice.
- Items of a removed source still appear in documents unless the applet
  filters them out.

## Scripting

Other tools use `Application`, the same core the CLI uses:

```python
from pathlib import Path

from newstool.app import Application
from newstool.models import DocumentFilter

with Application.from_config_file(Path("config.yaml"), create_schema=False) as app:
    feeds = app.find_documents(DocumentFilter(app="headlines"), with_content=True)
```

Code that writes takes `app.lock()` first.

## Development

```sh
DISABLE_RICH=1 uv run python -m unittest discover -s tests
uv run ruff check --fix .
uv run ruff format .
```

See [docs/SPECIFICATION.md](docs/SPECIFICATION.md) for the full definition
of the application, [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the
internals and how to write a plugin, [docs/decisions/](docs/decisions/) for the recorded
design decisions and [PLAN.md](PLAN.md) for pending work.
