---
paths:
  - "**/*.py"
  - "pyproject.toml"
---

# newstool Python Specifics

Generic Python conventions live in the user-level `rules/python.md`; this file adds what is specific to newstool.

## Framework Usage

- **CLI:** The app has subcommands and uses `click` / `rich-click`; `cli.py` selects plain click or rich-click depending on `DISABLE_RICH`. Use click's parameter types for CLI arguments, never pydantic. Use stdlib `argparse` only for standalone scripts in `scripts/` or `private/`.
- **Plugin options:** subclass `PluginOptions` (pydantic, `extra="forbid"`).
- **DTOs:** This app has a DB layer; see `.claude/rules/database.md`.
- **Logging:** handlers are configured only in `cli.py` (`setup_logging`).

## Additional Approved Packages

| Category / Requirement | Approved Package | Condition / Policy |
| :--- | :--- | :--- |
| **Shared Foundation** | `foundation` *(git dep, `ldotlopez/foundation`)* | Plugin registry, HTTP cache, JSON helpers, CLI helpers. Prefer it over re-implementing these here. |
| **CLI Framework** | `rich-click` | See Framework Usage above. |
| **Config & Env** | `pyyaml`, `python-dotenv` | YAML config loading and `.env` variable substitution. |
| **Durations** | `pytimeparse2` | Parsing `5m` / `2h` / `3d` style durations. |
| **HTML / Feeds / PDF** | `bs4` + `html5lib`, `trafilatura`, `feedparser`, `pymupdf` | Scraping and extracting HTML, parsing RSS/Atom feeds, extracting PDF text. |
| **LLM** | `ollama` | Backend for the LLM plugin. |
