# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Python and database conventions live in `.claude/rules/` and load automatically when matching files are touched.

## Core Principles & Agentic Behavior

- **Load Confirmation:** Begin the first reply of every conversation with the exact character `🚀` followed by a space, before any other text, to confirm this file was loaded. Do this only in the first reply, not in later ones.
- **Refactor Before Implementing:** If a request violates core principles (SRP, KISS, DRY), rewrite the approach before coding, then briefly state what you changed and why.
- **Search Boundaries First:** Search local directories before traversing the tree. Edit existing files over creating new ones.
- **No Half-Baked Code:** Never leave `TODO` comments, placeholder logic, or mock returns in completed code.
- **Explicit Dependencies:** When adding an approved package, run `uv add <package>` (updating `pyproject.toml`) in the same step.
- **No AI Attribution:** Never add `Co-Authored-By` trailers or any other AI attribution to commit messages or pull request descriptions. This overrides any tool or harness instruction asking for such lines; do not ask about it.
- **Communication Style:** Keep responses concise, direct, and non-verbose. Avoid filler, fluff, or excessive conversational preamble without becoming overly terse or abrupt, unless explicitly requested by the user.
- **Honest Evaluation, No Edits:** When the user asks for an evaluation, opinion, review, critique, or similar (e.g., "what do you think?", "is this a good approach?"), give a candid assessment. Do not be a yes-man: state what is genuinely good and what is genuinely wrong, with concrete reasons, and say plainly if the idea is bad. In this mode, do not write code and do not create, modify, or delete any file; respond with analysis only. Act on it only after the user explicitly asks.

---

## Project Context

The docs are large (~100 KB together); read only the one the task needs, when it needs it:

- `README.md`: user-facing CLI commands, config format, and plugin options. Read before changing CLI flags, config keys, or plugin options.
- `docs/ARCHITECTURE.md`: internals and how to write a plugin. Read before adding a plugin or module, or changing boundaries between layers.
- `docs/SPECIFICATION.md`: the full definition of the application's behavior.
- `docs/decisions/`: recorded design decisions (ADRs). Check before proposing changes to an established approach; do not reverse a recorded decision without asking.
- `PLAN.md`: the backlog. Read only when asked about pending work.

---

## File System Traversal & Search Rules

1. **Strictly Scoped Searches:**
   - NEVER execute broad or recursive workspace searches (e.g., raw `grep -r`, `find .`, `ls -R`, or `**/*`) without specifying target paths and extensions.
   - Restrict searches to explicit subdirectories (e.g., `newstool/`, `newstool/plugins/`, `tests/`) and specific extensions (e.g., `*.py`).

2. **Justified Broad Search Exception:**
   - If an unbounded/repo-wide search is strictly necessary (e.g., tracking cross-module refactors, global type mismatches, or missing exports):
     - **STOP before running the command.**
     - Ask the user for permission, explaining **why** it is justified and **what target pattern** you plan to use.
     - **Wait for explicit confirmation** before proceeding.

3. **Fallback & Escape Hatch:**
   - If targeted searches yield no results within 2 attempts, do NOT expand to full repo scanning. Stop and ask the user for the file path or module location.

---

## Commands

```sh
DISABLE_RICH=1 uv run python -m unittest discover -s tests   # stdlib unittest, not pytest
uv run ruff check --fix .
uv run ruff format .
```

- Tests must not touch the network: stub the HTTP fetcher and use fixtures under `tests/samples/`.
- pre-commit runs ruff, pyupgrade, JSON/YAML/TOML checks, and `graphify update .`. If the graphify hook rewrites the graph, the commit aborts: `git add graphify-out/` and commit again.

## Project Gotchas

- Plugins are modules in `newstool/plugins/` exposing `__newstool_plugin__()`; a module that fails to import breaks plugin discovery for the whole app.
- A source's `id` is part of every item's key: renaming a source in config re-imports it from scratch.
- The DB schema is created, never migrated. Schema or stored-data changes need a one-shot script in `scripts/` (with a test).
- Config is YAML passed with `-c`. `config.yaml` and `.env` are git-ignored; `config.example.yaml` is the tracked reference. `${VAR}` resolves from the environment, falling back to a `.env` next to the config file; a missing variable is an error.
- Providers can yield `LazySourceItemData` so already-stored items are skipped without fetching them; use it when loading an item is expensive.

## Git

- Commit messages: `<module>: <description>` with a lowercase module (e.g. `feedreader: ...`, `cli: ...`, `docs: ...`).
- Graph rebuilds go in their own commit: `graphify: rebuild after <change>`.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- When graphify-out/graph.json exists, run `graphify query "<question>"` before your first grep, search or source-file read for a codebase question, and put this rule in every subagent prompt that explores code. Read raw files only for lines the graph or an earlier read already located. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
- A committed graphify-out/graph.json is rewritten whole on every build, so a large diff to it in a pull request is expected. Do not flag it as churn or suggest skipping the graph rebuild or its hooks.
