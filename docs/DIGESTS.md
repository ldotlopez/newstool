# Story digests

For AI agents working on the `digest` applet and the processors that feed it.
It is the single source for the digests' design decisions, roadmap, plan and
backlog; `PLAN.md` only points here. Read it before changing
`newstool/plugins/digest.py`, `classify.py`, `tagger.py` or `embed.py`.

The user-facing options are in `README.md` (*Applets*, *Processors*); the
module map is in `docs/ARCHITECTURE.md`. **There is no decision record yet,
on purpose**: the design is written down as an ADR only after it has been
tested on real data (Roadmap, phase 3). Until then this file holds the
decisions; do not write `docs/decisions/00xx` for digests without asking.

## Goal

One digest of the stories several sources covered over whole days, to
publish as a web page or send: items about the same story merged, some
topics dropped, others ranked up, written by an LLM.

Two reference instances are the yardstick for every change
(`config.example.yaml`):

| | `castello-weekly` | `spain-abroad` (commented out) |
| :--- | :--- | :--- |
| Sources | local media, Spanish and Valencian | foreign media (EN/FR/DE) on Spain |
| Period | `span_days: 7`, Mondays | `span_days: 1`, daily |
| Filter | `exclude: {topics: [deportes, sucesos]}` | `include: {about/spain: ["yes"]}` |
| Ranking | `topic_weights` (housing, urbanism) | outlets weighted, coverage |
| Grouping | tags (`singlelink`) | `embeddings` over `summary/es` |
| Voice | neutral editor | reporter naming each outlet, in Spanish |

## Pipeline

```
process (per item, stored annotations)        digest (per run, nothing stored but documents)
  markdownify → markdown                        read_candidates  items in the window with `input`,
  summarize   → summary (/es)                                    filtered by include/exclude
  tagger      → tags        (entities)          select_stories   score_matrix → CLUSTERERS[algorithm]
  classify    → topics, about/spain (closed)                     → story_score → top max_stories
  embed       → <key>/embedding                 emit             plan (JSON); with write, digest
                                                                 (one LLM call per story + intro)
```

Files: `newstool/plugins/{tagger,classify,embed,digest}.py`; the shared
helpers `publisher_tags` and `embedding_key` in `newstool/processors.py`;
tests in `tests/test_digest.py` and `tests/test_llm.py`.

## Design decisions

Each states what was decided, why, and what not to do.

1. **One `digest` instance = one digest across its sources.** It replaced
   the per-source digest (2026-11-11); one instance per source gives the
   old behaviour. Do not reintroduce per-source documents inside one run.

2. **Two annotation roles: `tags` find stories, `topics` filter and rank.**
   `tagger` writes free-form entities (good for overlap, useless for
   "drop sports"); `classify` picks from a closed `labels` list. Relevance
   ("about Spain") is one more `classify` run with its own `key`. Keep them
   separate processors: the prompts and outputs differ.

3. **The first relevance filter is the source.** Foreign outlets are read
   from their Spain-section feeds, so few irrelevant items are processed;
   `about/spain` only catches what slips through. Prefer narrowing a source
   over adding classification.

4. **The publisher's tags are hints.** `tagger` and `classify` get the
   item's `data["tags"]` in their prompt (`publisher_tags`); `tagger` also
   merges them into its result. Bundles never import each other, which is
   why the helper lives in `processors.py`.

5. **One working language.** Items in several languages (ES/CA locally,
   EN/FR/DE abroad) meet only if they are compared in one: summarize into
   the output language (`summary/es`), embed that (`embed` with `input:
   summary/es`) and write from it (`digest.input`).

6. **Embedding keys are `<first part>/embedding/<rest>`** (`tags/embedding`,
   `summary/embedding/es`), computed by `embedding_key` only. Do not build
   the key by hand anywhere else.

7. **Groups are computed on each run, never stored as item annotations.**
   A group belongs to a window and a set of parameters, not to an item:
   storing it would rewrite every member's annotation when a story gains an
   item, conflict with per-item run state (decisions 0002, 0018) and fix
   one answer where experiments need many. The `plan` document is the
   record of what was grouped.

8. **The grouping lives in `digest.py`.** The former `grouping` applets
   (`singlelink`, `avglink`, `embeddings`) were unused and were absorbed
   with all three algorithms, selected by `algorithm` through the
   `CLUSTERERS` mapping (no `if algorithm == ...` chains). Items without
   tags or vectors stay as stories of their own (the old applets dropped
   them): a digest should not lose a story because `embed` has not run.

9. **Plan, then write.** Filtering, grouping, ranking and selection are
   deterministic and emitted as the `plan` document; the LLM only writes
   the chosen stories. `write: false` emits only the plan, so options are
   tuned with no LLM cost. Keep the plan readable (`ensure_ascii=False`)
   and complete enough to explain the digest.

10. **Ranking is code, not the LLM.** `story_score` = distinct sources +
    the `topic_weights` of the story's topics + the highest
    `source_weights` of its sources. Coverage across sources is the main
    importance signal. Reproducible and tunable; do not ask the LLM to rank.

11. **Writing is bounded by stories, not by the period.** One call per
    story from its items' `input` (summaries, not markdown), one for the
    opening paragraph; prompts are options (`story_prompt`, `intro_prompt`)
    so each instance sets its voice.

12. **Whole local days.** The window is the `span_days` days before the
    run's local day (`period`): today is never included. Keys are
    `<from>_<to>` (first and last day, instance-scoped), so a re-run over
    the same days emits nothing new. The option is `span_days`, not `days`,
    which already names the schedule's weekdays.

13. **First version is the bare minimum.** Happy paths and one test per
    piece; validations, corner cases and polish wait in the Backlog until
    the design has been tested.

### Gotchas

- `requirements(options)` is checked at startup: every key a digest reads
  (`input`, `tags`, filter keys, `topics` when weighted, the embedding key)
  must be written by a process run on its sources, or the config fails.
- YAML 1.1 reads `yes`/`no` as booleans: quote labels (`["yes", "no"]`).
- `classify` silently drops labels outside `labels`; a typo in a filter or
  weight matches nothing and raises nothing (Backlog).
- The `LLM` protocol has `json_mode` only, no schema parameter; parse and
  validate answers in the processor.
- `digest` has two outputs, so an instance needs `routes`, not the `sink`
  shorthand.
- To re-run the same days while tuning: `apps reset --app ID
  --with-documents`.

## Roadmap

| Phase | State | Exit criterion |
| :--- | :--- | :--- |
| 0. First version | **done** 2026-11-11, on `main` | tests pass, both reference configs validate |
| 1. Test on real data | **next** | both reference instances give plans and digests the user accepts |
| 2. Second version | after phase 1 | the Backlog items phase 1 showed are needed |
| 3. Decision record and full docs | after phase 2 | ADR written with the user's approval; SPECIFICATION and ARCHITECTURE complete |

Phase 1 may reorder or drop Backlog items; record what it shows here.

## Plan

### Done: first version (phase 0)

- [x] `tagger` shows the publisher's tags to the LLM.
- [x] `classify` processor: `labels`, `question`; key from config.
- [x] `embed.input` any annotation key; keys from `embedding_key`.
- [x] `digest` rewrite absorbing `grouping`: window, filters, three
  algorithms, ranking, `plan` and `digest` outputs, `write`, prompts,
  `title`.
- [x] `config.example.yaml` (`castello-weekly`; `spain-abroad` commented
  with its runs), README, ARCHITECTURE.

### Next: test on real data (phase 1)

Use a separate config and `storage_dir`, not the production database. Per
step, what to check:

1. `import --default`, `process --default` with `markdownify`,
   `summarize`, `tagger` and the `topics` `classify` run.
   Check with `inspect annotations --key tags` / `--key topics`: tags of
   the same story overlap across outlets; topics are right and the label
   list is short enough for the model.
2. `castello-weekly` with `write: false`: `apps run --app castello-weekly
   --force --no-deliver`, then `inspect documents`. Check: stories merge
   items from different outlets, excluded topics are gone, the order
   matches the weights. Tune `min_score`, `algorithm`, weights.
3. `write: true`: the entries and intro read well; links are right.
4. `embed` (`tags/embedding`, then `summary/es`) and `algorithm:
   embeddings`: does it merge stories tags miss (ES/CA spellings)?
5. `spain-abroad`: Spain-section feeds, `summary/es`, `about/spain`, the
   reporter prompt; check day-to-day repetition (Backlog: novelty).

Record findings in this file (a *Findings* section) as they come.

## Backlog (second version)

Set aside to keep the first version small; phase 1 decides which are
needed.

- **`classify` strictness**: an unknown label fails the item (retried by
  `max_retries`) instead of being dropped; `multiple: false` for exactly
  one label; an `input` option; label lists checked at startup against the
  digests' `topic_weights` and filters.
- **Typed stories**: the clustering returns frozen `Story`/cluster models
  with their pair scores and shared tags, not index lists.
- **Filter rules** as `[{key, include | exclude}]` with a defined rule for
  items missing the key; the plan lists what was dropped and why.
- **Ranking**: weights for coverage, size and recency; the score's parts in
  the plan.
- **Structured writing**: story answers as JSON `{headline, body}`, an
  invalid one fails the run; a `language` option; long stories cut to
  `context_length`.
- **HTML page**: output `page` (`text/html`) rendered from the structured
  entries with `html.escape` (no Markdown library), for a `file` sink.
- **Novelty** for daily instances: read the instance's earlier `plan`
  documents (`reader.documents(app=run.app, output="plan")`) to drop
  stories already reported and mark updates.
- **Time zone**: the window in the schedule's `tz`, if it becomes
  configurable (today it is the system's).
- **Docs and decision record** (phase 3).
