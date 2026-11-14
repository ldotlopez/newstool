# Graph Report - impl-0019  (2026-11-14)

## Corpus Check
- 82 files · ~198,534 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 4, .lock 1)

## Summary
- 2028 nodes · 5507 edges · 96 communities (70 shown, 26 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 671 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d689de6b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- make_item
- ConfigError
- test_app.py
- ApplicationTests
- scope_options
- invoke
- .from_text
- Entry
- Database (db.py, only SQLite/storage access)
- StubLLM
- SourceItem
- ItemFeedApplet
- TelegramChannelProvider
- DeleteCommandTests
- .add_item
- TelegramSinkTests
- HTTPClient
- read_candidates
- Document
- CommandTests
- AppletResult
- datetime
- Annotation
- describe
- test_sinks.py
- Any
- ProcessingTests
- ollama.py
- Delivery
- BaseProcessor
- Services
- cli.py
- .from_file
- .add_items
- plugins
- .summary
- GoogleChatSinkTests
- AnnotationTests
- app_from_context
- ADR 0007 Sinks and the delivery ledger
- LogFailureTests
- options
- hooks
- Services object (services.llm(name))
- test_db.py
- config.example.yaml
- Application
- Database
- lookup
- ProcessEntry
- SourceData
- newstool
- Processor
- El Periódico Mediterráneo
- Config
- ProcessingScope
- deliveries table (the ledger)
- PluginFailure
- Schedule
- Item
- IndexSiteProvider
- print_table
- CSJuntasGobiernoProvider
- ._find_excluded_containers
- MarkdownifyProcessor
- Example sources (prensaiberica_plain, castelloninformacion, plaza, theguardian)
- AppletReader
- Artifact
- Grouping notes: NLP clustering pipeline
- .__init__
- 0019: Workflows as chains of global entities
- foundation internal library
- 0018: Annotations hold their run state; a content change deletes them
- db.py
- workflows
- ExternalErrorTests
- TestSourceItemDataContent
- config.py
- LogLevelTests
- app.py
- PreflightProvider
- DocumentTests
- Decision
- SelectionTests
- test_cli.py
- SourceItemData
- setup_logging
- deliver_cmd
- 0017: Explicit run selection
- load_context
- ADR 0002 Processing state lifecycle
- 0012: Delivery ids, changing their state and forced send
- 0016: Routes on re-emission, manual queueing and pacing overrides

## God Nodes (most connected - your core abstractions)
1. `SourceItem` - 102 edges
2. `Database` - 95 edges
3. `Services` - 95 edges
4. `Application` - 91 edges
5. `PluginFailure` - 80 edges
6. `Document` - 72 edges
7. `ApplicationTests` - 72 edges
8. `SourceData` - 69 edges
9. `SourceItemData` - 55 edges
10. `ProcessingScope` - 53 edges

## Surprising Connections (you probably didn't know these)
- `Reading` --references--> `AppletReader`  [INFERRED]
  docs/decisions/0015-applets-documents-and-routes.md → newstool/applets.py
- `Decision` --references--> `Database`  [INFERRED]
  docs/decisions/0018-annotations-hold-their-run-state.md → newstool/db.py
- `Gotchas` --references--> `LLM`  [INFERRED]
  docs/DIGESTS.md → newstool/llms.py
- `Runs and state` --references--> `AppletRun`  [INFERRED]
  docs/decisions/0015-applets-documents-and-routes.md → newstool/models.py
- `Rejected options` --references--> `Services`  [INFERRED]
  docs/decisions/0013-plugin-services-at-init.md → newstool/plugins/__init__.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **markdownify -> summarize/tagger -> embed -> grouping data chain** — docs_architecture_markdownify_processor, docs_architecture_summarize_processor, docs_architecture_tagger_processor, docs_architecture_embed_processor, docs_architecture_grouping_remixers [EXTRACTED 1.00]
- **Plugin protocol types consumed by the core** — docs_specification_provider, docs_specification_processor, docs_specification_remixer, docs_specification_sink, docs_decisions_0006_llm_plugins_llm_protocol [EXTRACTED 1.00]
- **Delivery ledger mechanism** — docs_architecture_deliveries_table, docs_decisions_0007_sinks_and_delivery_ledger_delivery_states, docs_architecture_basesink_cycle, docs_decisions_0007_sinks_and_delivery_ledger_strict_fifo_per_source, docs_decisions_0007_sinks_and_delivery_ledger_lookback_window, docs_specification_write_lock [INFERRED 0.85]
- **Prensa Ibérica sample article fixtures (El Periódico Mediterráneo, July 2026)** — tests_samples_prensaiberica_item_132310503_article, tests_samples_prensaiberica_item_132340038_article, tests_samples_prensaiberica_item_132344288_article [INFERRED 0.95]

## Communities (96 total, 26 thin omitted)

### Community 0 - "make_item"
Cohesion: 0.15
Nodes (6): ContentChangeTests, ContentStorageTests, IdentityTests, make_item(), make_source(), UpsertSourceItemsTests

### Community 1 - "ConfigError"
Cohesion: 0.07
Nodes (10): AppInstance, Catalog, check_section(), Kind, Profile, AppEntry, ConfigError, options_error() (+2 more)

### Community 2 - "test_app.py"
Cohesion: 0.07
Nodes (17): Pipeline, ProcessingStatus, classify_prompt(), ClassifyOptions, __newstool_plugin__(), __newstool_plugin__(), UsesLLMOptions, __newstool_plugin__() (+9 more)

### Community 3 - "ApplicationTests"
Cohesion: 0.05
Nodes (10): LockedError, write_lock(), ApplicationTests, retrieve(), retrieve_published(), retrieve(), same(), chain() (+2 more)

### Community 4 - "scope_options"
Cohesion: 0.24
Nodes (6): annotation_options(), delivery_options(), document_options(), wrapper(), wrapper(), scope_options()

### Community 5 - "invoke"
Cohesion: 0.16
Nodes (4): MarkSummary, annotation(), InspectCommandTests, invoke()

### Community 8 - "Database (db.py, only SQLite/storage access)"
Cohesion: 0.17
Nodes (11): pre-commit config, ruff-check and ruff-format hooks, newsmerger CLAUDE.md agent guidelines, DTO/ORM from_dto/to_dto/update convention, Consumer-side Protocol decoupling convention, AUTOINCREMENT integer ids, Database (db.py, only SQLite/storage access), foundation.storage.DiskStorage content-addressed storage (+3 more)

### Community 9 - "StubLLM"
Cohesion: 0.09
Nodes (7): Processor, ClassifyTests, EmbedTests, ProcessorTestCase, StubLLM, SummarizeTests, TaggerTests

### Community 10 - "SourceItem"
Cohesion: 0.14
Nodes (4): DBSourceItem, _encode_value(), SourceItem, TruncateProcessor

### Community 12 - "TelegramChannelProvider"
Cohesion: 0.24
Nodes (3): is_home_page(), TelegramChannelProvider, TestTelegramChannel

### Community 14 - ".add_item"
Cohesion: 0.24
Nodes (3): DigestAppletTests, DigestGroupingTests, DigestTestCase

### Community 15 - "TelegramSinkTests"
Cohesion: 0.12
Nodes (10): Schedule, build_caption(), post(), TelegramSink, BuildCaptionTests, item_document(), ok_response(), options() (+2 more)

### Community 16 - "HTTPClient"
Cohesion: 0.08
Nodes (14): 0013: Plugin services at init, Consequences, Context, Rejected options, HTTPClient, discover_feed_url(), entry_date(), FeedReaderProvider (+6 more)

### Community 17 - "read_candidates"
Cohesion: 0.06
Nodes (29): Backlog (second version), Design decisions, Done: first version (phase 0), Goal, Gotchas, Next: test on real data (phase 1), Plan, Roadmap (+21 more)

### Community 18 - "Document"
Cohesion: 0.08
Nodes (8): Sinks, CommittedRun, Document, FileOptions, FileSink, Sink, run(), FileSinkTests

### Community 19 - "CommandTests"
Cohesion: 0.13
Nodes (4): AppReport, RunSummary, CommandTests, workflow_app()

### Community 20 - "AppletResult"
Cohesion: 0.13
Nodes (7): check_result(), AppletResult, EmittedDocument, CheckResultTests, ReaderTests, DeliveryTests, JSONColumnTests

### Community 21 - "datetime"
Cohesion: 0.09
Nodes (4): backoff_seconds(), _configure_sqlite_connection(), CustomJSON, UTCDateTime

### Community 22 - "Annotation"
Cohesion: 0.16
Nodes (5): Base, DBItemAnnotation, next_annotation(), Annotation, NextAnnotationTests

### Community 23 - "describe"
Cohesion: 0.07
Nodes (15): deliver_each(), delivery_phase(), failed_report(), failed_summary(), format_time(), import_sources(), import_failed(), phase_title() (+7 more)

### Community 24 - "test_sinks.py"
Cohesion: 0.11
Nodes (12): Routes, StdoutSink, accepts(), SinkOptions, AcceptsTests, CommitTests, DelivererTests, DeliveryOrderTests (+4 more)

### Community 27 - "ollama.py"
Cohesion: 0.10
Nodes (8): Decision, LLM, LLMType, __newstool_plugin__(), ollama_client(), OllamaLLM, Options, OllamaTests

### Community 28 - "Delivery"
Cohesion: 0.15
Nodes (3): DBDelivery, Delivery, Deliverer

### Community 29 - "BaseProcessor"
Cohesion: 0.07
Nodes (8): Decision, strip_code_fence(), ClassifyProcessor, known_labels(), tags_text(), merge_tags(), tags_prompt(), BaseProcessor

### Community 30 - "Services"
Cohesion: 0.07
Nodes (14): Applets, BaseApplet, DigestApplet, DigestOptions, EmbedOptions, EmbedProcessor, Services, SummarizeProcessor (+6 more)

### Community 31 - "cli.py"
Cohesion: 0.07
Nodes (12): cli(), delete_group(), deliveries_group(), describe_schedule(), format_seconds(), inspect_group(), keys_by_workflow(), lexer_for() (+4 more)

### Community 33 - ".add_items"
Cohesion: 0.34
Nodes (3): ItemFeedOptions, AppletTestCase, ItemFeedTests

### Community 34 - "plugins"
Cohesion: 0.12
Nodes (17): lookback, title, url, api_base, chat_model, embed_model, plugins, digest (+9 more)

### Community 35 - ".summary"
Cohesion: 0.09
Nodes (16): 0009: Workflows and keyed entries, Consequences, Context, Decision, Rejected options, 0010: Plugin classes and the configuration catalog, Consequences, Context (+8 more)

### Community 36 - "GoogleChatSinkTests"
Cohesion: 0.09
Nodes (10): build_card(), chat_image_url(), GoogleChatSink, __newstool_plugin__(), WebhookOptions, card_widgets(), ChatImageUrlTests, GoogleChatSinkTests (+2 more)

### Community 38 - "app_from_context"
Cohesion: 0.11
Nodes (22): app_from_context(), check_all_rows(), check_found(), delete_annotations_cmd(), delete_apps_cmd(), delete_deliveries_cmd(), delete_documents_cmd(), delete_items_cmd() (+14 more)

### Community 39 - "ADR 0007 Sinks and the delivery ledger"
Cohesion: 0.21
Nodes (14): Architecture, cli.py Click commands, External pipelines (scripts/pipeline_url.py), ADR 0001 Item identity and change detection, ADR 0003 Plugin types and core scope, ADR 0004 Annotation and artifact contents on disk, ADR 0006 LLM plugins, ADR 0007 Sinks and the delivery ledger (+6 more)

### Community 41 - "options"
Cohesion: 0.15
Nodes (14): options, artifacts, chat_id, interval, item_image, item_url_preview, item_url_text, markdown (+6 more)

### Community 42 - "hooks"
Cohesion: 0.15
Nodes (12): exclude, args, entry, files, id, language, name, pass_filenames (+4 more)

### Community 43 - "Services object (services.llm(name))"
Cohesion: 0.22
Nodes (12): digest remixer, embed processor, grouping remixers (singlelink, avglink, embeddings), markdownify processor, summarize processor, tagger processor, telegram bundle (telegram, telegram_artifacts sinks), LLM plugins must be listed before their consumers (+4 more)

### Community 44 - "test_db.py"
Cohesion: 0.28
Nodes (3): ConnectionTests, DatabaseTestCase, DeleteTests

### Community 45 - "config.example.yaml"
Cohesion: 0.11
Nodes (15): cache, expiration, llms, input, processors, options, processor, remixers (+7 more)

### Community 46 - "Application"
Cohesion: 0.05
Nodes (4): Application, DeliveryStatus, DocumentFilter, PacingOverride

### Community 47 - "Database"
Cohesion: 0.06
Nodes (3): Database, DBApp, AppletRun

### Community 50 - "ProcessEntry"
Cohesion: 0.17
Nodes (3): process_key(), Use, ProcessEntry

### Community 52 - "SourceData"
Cohesion: 0.13
Nodes (5): DBSource, SourceData, CastellonInformacionProvider, PlazaProvider, Provider

### Community 54 - "Processor"
Cohesion: 0.29
Nodes (6): UnavailableProcessor / UnavailableRemixer / UnavailableSink, Annotation, Delivery, Exponential backoff 60s*2^(n-1), capped 24h, max_retries, Processor, Sink

### Community 55 - "El Periódico Mediterráneo"
Cohesion: 0.43
Nodes (7): El Periódico Mediterráneo, Prensa Ibérica article HTML format (og:/article: meta tags), Telegram t.me/s channel preview HTML (tgme_widget_message, data-post), El eco perdido de las fiestas de julio nacidas del asedio carlista sobre Castellón (sample article), El Grau se vuelca en las fiestas de la Virgen del Carmen (sample article), Castellón apoya a la selección española desde la plaza Mayor (sample article), Telegram channel mediterraneoelperiodico (sample web preview)

### Community 56 - "Config"
Cohesion: 0.16
Nodes (6): 0011: Environment overrides, relative paths and one storage directory, Consequences, Context, Decision, Config, DirectoryTests

### Community 57 - "ProcessingScope"
Cohesion: 0.33
Nodes (4): workflow_scope(), wrapper(), ProcessingScope, GetItemsTests

### Community 58 - "deliveries table (the ledger)"
Cohesion: 0.33
Nodes (4): BaseSink deliver cycle (queue, select, send), deliveries table (the ledger), ADR 0005 Remixers with external side effects, Strict FIFO per source

### Community 59 - "PluginFailure"
Cohesion: 0.07
Nodes (25): PluginFailure, reason(), PreflightSourceItemData, __newstool_plugin__(), __newstool_plugin__(), __newstool_plugin__(), Options, select_article() (+17 more)

### Community 60 - "Schedule"
Cohesion: 0.21
Nodes (3): Applet, Schedule, ScheduleTests

### Community 61 - "Item"
Cohesion: 0.40
Nodes (3): IndexSiteProvider / URLProvider, Item, Provider

### Community 63 - "print_table"
Cohesion: 0.14
Nodes (10): format_value(), json_default(), preview(), print_apps(), print_emitted(), print_import(), print_item(), print_json() (+2 more)

### Community 64 - "CSJuntasGobiernoProvider"
Cohesion: 0.29
Nodes (4): CSJuntasGobiernoProvider, get_date_from_text(), PreparseData, TestCSJuntasGobierno

### Community 66 - "MarkdownifyProcessor"
Cohesion: 0.23
Nodes (5): MarkdownifyProcessor, SkipItem, ClassRegisterTests, make_pdf(), MarkdownifyPdfTests

### Community 68 - "AppletReader"
Cohesion: 0.15
Nodes (4): AppletReader, FeedApplet, Options, FeedTests

### Community 71 - ".__init__"
Cohesion: 0.13
Nodes (3): Run, warn_unused(), ClassRegister

### Community 72 - "0019: Workflows as chains of global entities"
Cohesion: 0.22
Nodes (8): 0019: Workflows as chains of global entities, A workflow is the whole chain, CLI, Consequences, Context, Decision, Rejected options, The catalog defines, workflows run

### Community 73 - "foundation internal library"
Cohesion: 0.29
Nodes (7): foundation internal library, foundation.plugin.Register plugin loading, __newsmerger_plugin__(services, **options) entry point, PluginOptions (pydantic, unknown keys rejected), plugins configuration section, P1: plain logging and <APP>_LOG_LEVEL fix, P2: rich progress per stream (RICH_STDOUT_*/RICH_STDERR_*)

### Community 74 - "0018: Annotations hold their run state; a content change deletes them"
Cohesion: 0.40
Nodes (4): 0018: Annotations hold their run state; a content change deletes them, Consequences, Context, Decision

### Community 76 - "workflows"
Cohesion: 0.33
Nodes (6): sink, workflows, deliver, name, process, sources

### Community 79 - "config.py"
Cohesion: 0.09
Nodes (7): Alias, CacheConfig, expand_variables(), MissingVariableError, ollama_url(), parse_duration(), AliasTests

### Community 81 - "app.py"
Cohesion: 0.07
Nodes (14): AppletType, run_key(), LLMUnavailableError, __newstool_plugin__(), __newstool_plugin__(), __newstool_plugin__(), merge_options(), __newstool_plugin__() (+6 more)

### Community 83 - "DocumentTests"
Cohesion: 0.22
Nodes (3): DBDocument, DocumentTests, keys()

### Community 85 - "Decision"
Cohesion: 0.14
Nodes (12): 0015: Applets, emitted documents and routes, CLI, Configuration, Consequences, Context, Decision, Documents, Migration (+4 more)

### Community 87 - "test_cli.py"
Cohesion: 0.22
Nodes (3): AppStatus, DeleteSummary, status()

### Community 88 - "SourceItemData"
Cohesion: 0.21
Nodes (4): SourceItemData, PrensaIbericaProvider, read_sample(), TestPrensaIberica

### Community 89 - "setup_logging"
Cohesion: 0.33
Nodes (4): Additional Approved Packages, Framework Usage, newstool Python Specifics, setup_logging()

### Community 90 - "deliver_cmd"
Cohesion: 0.13
Nodes (10): apps_cmd(), deliver_cmd(), import_cmd(), narrow(), process_cmd(), progress_rows(), run_cmd(), selected_sinks() (+2 more)

### Community 91 - "0017: Explicit run selection"
Cohesion: 0.33
Nodes (5): 0017: Explicit run selection, Consequences, Context, Decision, Rejected options

### Community 92 - "load_context"
Cohesion: 0.13
Nodes (6): Database & ORM Conventions, DTO, Protocol & ORM Implementation Reference, load_context(), LoadContext, LoadEnvSettingsSource, resolve_config_path()

### Community 104 - "0012: Delivery ids, changing their state and forced send"
Cohesion: 0.33
Nodes (5): 0012: Delivery ids, changing their state and forced send, Consequences, Context, Decision, Rejected options

### Community 106 - "0016: Routes on re-emission, manual queueing and pacing overrides"
Cohesion: 0.33
Nodes (5): 0016: Routes on re-emission, manual queueing and pacing overrides, Consequences, Context, Decision, Rejected options

## Knowledge Gaps
- **13 isolated node(s):** `newstool`, `External pipelines (scripts/pipeline_url.py)`, `Annotation`, `Telegram t.me/s channel preview HTML (tgme_widget_message, data-post)`, `IndexSiteProvider / URLProvider` (+8 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 621 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **26 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SourceItem` connect `SourceItem` to `make_item`, `test_app.py`, `ApplicationTests`, `invoke`, `StubLLM`, `ItemFeedApplet`, `DeleteCommandTests`, `.add_item`, `read_candidates`, `datetime`, `BaseProcessor`, `Services`, `cli.py`, `.add_items`, `.summary`, `AnnotationTests`, `test_db.py`, `Application`, `Database`, `SourceData`, `print_table`, `MarkdownifyProcessor`, `AppletReader`, `db.py`, `app.py`, `.get_content`, `test_cli.py`?**
  _High betweenness centrality (0.109) - this node is a cross-community bridge._
- **Are the 28 inferred relationships involving `SourceItem` (e.g. with `Application` and `AppletReader`) actually correct?**
  _`SourceItem` has 28 INFERRED edges - model-reasoned connections that need verification._
- **What connects `newstool`, `External pipelines (scripts/pipeline_url.py)`, `Annotation` to the rest of the system?**
  _13 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `ConfigError` be split into smaller, more focused modules?**
  _Cohesion score 0.07053140096618357 - nodes in this community are weakly interconnected._
- **Why does `Application` connect `Application` to `ConfigError`, `test_app.py`, `ApplicationTests`, `.from_text`, `StubLLM`, `SourceItem`, `DeleteCommandTests`, `HTTPClient`, `Document`, `CommandTests`, `Annotation`, `describe`, `ollama.py`, `Delivery`, `BaseProcessor`, `cli.py`, `.from_file`, `app_from_context`, `Database`, `lookup`, `.run_process`, `SourceData`, `Config`, `ProcessingScope`, `AppletReader`, `.__init__`, `app.py`, `PreflightProvider`, `.get_content`, `SourceItemData`, `deliver_cmd`?**
  _High betweenness centrality (0.105) - this node is a cross-community bridge._
- **Are the 23 inferred relationships involving `Database` (e.g. with `Context` and `Decision`) actually correct?**
  _`Database` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_app.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0671602326811211 - nodes in this community are weakly interconnected._