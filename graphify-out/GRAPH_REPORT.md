# Graph Report - newstool  (2026-11-10)

## Corpus Check
- 83 files · ~189,502 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 3, .lock 1)

## Summary
- 1952 nodes · 5390 edges · 113 communities (72 shown, 41 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 672 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `969bd654`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_db.py
- catalog.py
- grouping.py
- test_cli.py
- Catalog
- invoke
- Application
- Any
- Database (db.py, only SQLite/storage access)
- LockedError
- SourceItem
- AppletReader
- CSJuntasGobiernoProvider
- ProcessingScope
- itemfeed.py
- Artifact
- TestFeedReader
- Telegram Channel Parsing
- Decision
- RunSummary
- datetime
- inspect_annotations_cmd
- ClassRegister
- SinkOptions
- apps_run_cmd
- DocumentFilter
- ollama.py
- ._profile
- Document
- ScoredItem
- cli.py
- recreate
- .add_items
- AnnotationTests
- Schedule
- build_caption
- Config
- .sources
- Architecture & Processing ADRs
- PluginFailure
- Selection CLI Options
- telegram_channel.py
- Processor & Remixer Bundles
- GoogleChatSinkTests
- Plugin System Docs
- Application
- process_cmd
- SourceItemData
- PacingOverride
- .settings_customise_sources
- AppletRun
- inspect_artifacts_cmd
- Spec Glossary Entities
- Sample Pages & Formats
- HTTPClient
- .llm
- Agent Conventions
- migrate_feed_names.py
- feed.py
- Item Identity ADR
- .send
- describe
- ExternalErrorTests
- EmbeddingsApplet
- ProcessorOptions
- Example Sources
- config.py
- Artifact & Remixer
- Grouping Notes
- Deliverer
- DocumentFilter
- LogLevelTests
- 0011: Environment overrides, relative paths and one storage directory
- SinkType
- __newsmerger_plugin__
- app.py
- 0009: Workflows and keyed entries
- scope_options
- LogLevelTests
- .from_file
- Services
- DigestApplet
- Any
- FileSinkTests
- ._find_excluded_containers
- BaseProcessor
- EmbedProcessor
- AliasTests
- models.py
- Config
- setup_logging
- ADR 0002 Processing state lifecycle
- ConfigError
- IndexSiteProvider
- Entry
- Decision
- Delivery
- LLM
- .summary
- DeliveryTests
- 0014: Ledger rows by subject and the workflow in delivery commands
- 0016: Routes on re-emission, manual queueing and pacing overrides
- 0015: Applets, emitted documents and routes
- parse_entry
- ._app
- search_cmd

## God Nodes (most connected - your core abstractions)
1. `SourceItem` - 114 edges
2. `Database` - 101 edges
3. `Services` - 92 edges
4. `Application` - 82 edges
5. `SourceData` - 75 edges
6. `PluginFailure` - 72 edges
7. `Document` - 72 edges
8. `ApplicationTests` - 68 edges
9. `SourceItemData` - 56 edges
10. `ProcessingScope` - 55 edges

## Surprising Connections (you probably didn't know these)
- `Reading` --references--> `AppletReader`  [INFERRED]
  docs/decisions/0015-applets-documents-and-routes.md → newstool/applets.py
- `Decision` --references--> `Config`  [INFERRED]
  docs/decisions/0011-environment-overrides-and-storage-dir.md → newstool/config.py
- `Runs and state` --references--> `AppletRun`  [INFERRED]
  docs/decisions/0015-applets-documents-and-routes.md → newstool/models.py
- `Schedule` --references--> `options()`  [INFERRED]
  docs/decisions/0015-applets-documents-and-routes.md → tests/test_telegram.py
- `Decision` --references--> `Application`  [INFERRED]
  docs/decisions/0010-plugin-classes-and-catalog.md → newstool/app.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **markdownify -> summarize/tagger -> embed -> grouping data chain** — docs_architecture_markdownify_processor, docs_architecture_summarize_processor, docs_architecture_tagger_processor, docs_architecture_embed_processor, docs_architecture_grouping_remixers [EXTRACTED 1.00]
- **Plugin protocol types consumed by the core** — docs_specification_provider, docs_specification_processor, docs_specification_remixer, docs_specification_sink, docs_decisions_0006_llm_plugins_llm_protocol [EXTRACTED 1.00]
- **Delivery ledger mechanism** — docs_architecture_deliveries_table, docs_decisions_0007_sinks_and_delivery_ledger_delivery_states, docs_architecture_basesink_cycle, docs_decisions_0007_sinks_and_delivery_ledger_strict_fifo_per_source, docs_decisions_0007_sinks_and_delivery_ledger_lookback_window, docs_specification_write_lock [INFERRED 0.85]
- **Prensa Ibérica sample article fixtures (El Periódico Mediterráneo, July 2026)** — tests_samples_prensaiberica_item_132310503_article, tests_samples_prensaiberica_item_132340038_article, tests_samples_prensaiberica_item_132344288_article [INFERRED 0.95]

## Communities (113 total, 41 thin omitted)

### Community 0 - "test_db.py"
Cohesion: 0.06
Nodes (20): 0012: Delivery ids, changing their state and forced send, Consequences, Context, Decision, Rejected options, Deliveries, wrapper(), ProcessingScope (+12 more)

### Community 1 - "catalog.py"
Cohesion: 0.13
Nodes (7): ids_of(), in_default(), process_key(), Use, options_error(), ProcessEntry, merge_options()

### Community 2 - "grouping.py"
Cohesion: 0.09
Nodes (15): AppletType, BaseApplet, check_result(), run_key(), SourcesOptions, AppletResult, EmittedDocument, DigestOptions (+7 more)

### Community 3 - "test_cli.py"
Cohesion: 0.07
Nodes (8): MarkSummary, ApplicationTests, retrieve(), retrieve_published(), retrieve(), same(), listed(), retrieved()

### Community 4 - "Catalog"
Cohesion: 0.15
Nodes (3): Catalog, Run, share_sources()

### Community 5 - "invoke"
Cohesion: 0.17
Nodes (3): annotation(), InspectCommandTests, invoke()

### Community 8 - "Database (db.py, only SQLite/storage access)"
Cohesion: 0.17
Nodes (11): pre-commit config, ruff-check and ruff-format hooks, newsmerger CLAUDE.md agent guidelines, DTO/ORM from_dto/to_dto/update convention, Consumer-side Protocol decoupling convention, AUTOINCREMENT integer ids, Database (db.py, only SQLite/storage access), foundation.storage.DiskStorage content-addressed storage (+3 more)

### Community 9 - "LockedError"
Cohesion: 0.17
Nodes (3): Processor, EmbedTests, StubLLM

### Community 10 - "SourceItem"
Cohesion: 0.08
Nodes (11): Database, DBSourceItem, _encode_value(), SourceItem, ProcessorTestCase, SummarizeTests, TaggerTests, MigrateAppletsTests (+3 more)

### Community 11 - "AppletReader"
Cohesion: 0.12
Nodes (5): AppletReader, AverageLinkApplet, GroupingApplet, SingleLinkApplet, tagged_items()

### Community 12 - "CSJuntasGobiernoProvider"
Cohesion: 0.23
Nodes (6): CSJuntasGobiernoProvider, find_parent_by_tag_name(), get_date_from_text(), PreparseData, NoOptions, TestCSJuntasGobierno

### Community 14 - "itemfeed.py"
Cohesion: 0.20
Nodes (3): Requirements, ItemFeedApplet, ItemFeedOptions

### Community 15 - "Artifact"
Cohesion: 0.21
Nodes (7): TelegramOptions, run(), item_document(), ok_response(), options(), sink(), TelegramSinkTests

### Community 16 - "TestFeedReader"
Cohesion: 0.22
Nodes (3): FeedReaderProvider, select_article(), TestFeedReader

### Community 17 - "Telegram Channel Parsing"
Cohesion: 0.16
Nodes (7): is_home_page(), parse_article(), parse_preview(), Post, preview_url(), TelegramChannelProvider, TestTelegramChannel

### Community 18 - "Decision"
Cohesion: 0.25
Nodes (7): CLI, Decision, Documents, Migration, Reading, Runs and state, Schedule

### Community 19 - "RunSummary"
Cohesion: 0.18
Nodes (3): AppReport, RunSummary, CommandTests

### Community 22 - "inspect_annotations_cmd"
Cohesion: 0.15
Nodes (10): format_value(), inspect_apps_cmd(), json_default(), preview(), print_apps(), print_emitted(), print_import(), print_item() (+2 more)

### Community 24 - "SinkOptions"
Cohesion: 0.12
Nodes (9): StdoutSink, SinkOptions, CommitTests, DelivererTests, DeliveryOrderTests, emitted(), LedgerTestCase, RecordingSink (+1 more)

### Community 25 - "apps_run_cmd"
Cohesion: 0.15
Nodes (6): apps_reset_cmd(), apps_run_cmd(), cli(), deliver_cmd(), print_deliver(), run_delivery()

### Community 26 - "DocumentFilter"
Cohesion: 0.13
Nodes (4): DeleteSummary, wrapper(), DocumentFilter, keys()

### Community 27 - "ollama.py"
Cohesion: 0.15
Nodes (6): LLMType, __newstool_plugin__(), ollama_client(), OllamaLLM, Options, OllamaTests

### Community 29 - "Document"
Cohesion: 0.14
Nodes (4): DBDocument, Document, FileSink, DocumentTests

### Community 30 - "ScoredItem"
Cohesion: 0.12
Nodes (14): average_between(), average_link_cluster(), build_score_matrix(), cosine_similarity(), EmbeddingsApplet, item_ref(), jaccard(), member_payload() (+6 more)

### Community 31 - "cli.py"
Cohesion: 0.10
Nodes (9): apps_group(), delete_group(), deliveries_group(), describe_schedule(), format_seconds(), format_time(), inspect_group(), lexer_for() (+1 more)

### Community 33 - ".add_items"
Cohesion: 0.26
Nodes (3): AppletTestCase, GroupingTests, ItemFeedTests

### Community 34 - "AnnotationTests"
Cohesion: 0.12
Nodes (17): lookback, title, url, api_base, chat_model, embed_model, plugins, digest (+9 more)

### Community 36 - "build_caption"
Cohesion: 0.20
Nodes (4): build_caption(), post(), TelegramSink, BuildCaptionTests

### Community 38 - ".sources"
Cohesion: 0.18
Nodes (7): 0009: Workflows and keyed entries, Consequences, Context, Decision, Rejected options, Configuration, Plugins

### Community 39 - "Architecture & Processing ADRs"
Cohesion: 0.21
Nodes (14): Architecture, cli.py Click commands, External pipelines (scripts/pipeline_url.py), ADR 0001 Item identity and change detection, ADR 0003 Plugin types and core scope, ADR 0004 Annotation and artifact contents on disk, ADR 0006 LLM plugins, ADR 0007 Sinks and the delivery ledger (+6 more)

### Community 40 - "PluginFailure"
Cohesion: 0.09
Nodes (8): PluginFailure, CastellonInformacionProvider, get_section(), parse_datetime(), PlazaProvider, page_title(), TheGuardianProvider, LogFailureTests

### Community 41 - "Selection CLI Options"
Cohesion: 0.15
Nodes (14): options, artifacts, chat_id, interval, item_image, item_url_preview, item_url_text, markdown (+6 more)

### Community 42 - "telegram_channel.py"
Cohesion: 0.15
Nodes (12): exclude, args, entry, files, id, language, name, pass_filenames (+4 more)

### Community 43 - "Processor & Remixer Bundles"
Cohesion: 0.22
Nodes (12): digest remixer, embed processor, grouping remixers (singlelink, avglink, embeddings), markdownify processor, summarize processor, tagger processor, telegram bundle (telegram, telegram_artifacts sinks), LLM plugins must be listed before their consumers (+4 more)

### Community 44 - "GoogleChatSinkTests"
Cohesion: 0.09
Nodes (10): build_card(), chat_image_url(), GoogleChatSink, __newstool_plugin__(), WebhookOptions, card_widgets(), ChatImageUrlTests, GoogleChatSinkTests (+2 more)

### Community 45 - "Plugin System Docs"
Cohesion: 0.11
Nodes (15): cache, expiration, llms, input, processors, options, processor, remixers (+7 more)

### Community 46 - "Application"
Cohesion: 0.07
Nodes (5): Application, lookup(), workflow_scope(), AppInstance, Workflow

### Community 47 - "process_cmd"
Cohesion: 0.18
Nodes (7): import_cmd(), import_sources(), print_process(), process_cmd(), progress_rows(), run_cmd(), run_each()

### Community 48 - "SourceItemData"
Cohesion: 0.13
Nodes (5): PreflightSourceItemData, SourceItemData, PreflightProvider, Provider, TestPrensaIberica

### Community 51 - ".settings_customise_sources"
Cohesion: 0.12
Nodes (5): EnvAliasSource, load_context(), LoadContext, LoadEnvSettingsSource, resolve_config_path()

### Community 52 - "AppletRun"
Cohesion: 0.16
Nodes (4): Applets, Applet, DBApp, AppletRun

### Community 54 - "Spec Glossary Entities"
Cohesion: 0.29
Nodes (6): UnavailableProcessor / UnavailableRemixer / UnavailableSink, Annotation, Delivery, Exponential backoff 60s*2^(n-1), capped 24h, max_retries, Processor, Sink

### Community 55 - "Sample Pages & Formats"
Cohesion: 0.43
Nodes (7): El Periódico Mediterráneo, Prensa Ibérica article HTML format (og:/article: meta tags), Telegram t.me/s channel preview HTML (tgme_widget_message, data-post), El eco perdido de las fiestas de julio nacidas del asedio carlista sobre Castellón (sample article), El Grau se vuelca en las fiestas de la Virgen del Carmen (sample article), Castellón apoya a la selección española desde la plaza Mayor (sample article), Telegram channel mediterraneoelperiodico (sample web preview)

### Community 56 - "HTTPClient"
Cohesion: 0.20
Nodes (5): HTTPClient, discover_feed_url(), fetch_article(), fetch_feed(), TestHTTPClient

### Community 57 - ".llm"
Cohesion: 0.15
Nodes (7): Context, LLMUnavailableError, __newstool_plugin__(), DigestPluginTests, factory(), ServicesTests, factory()

### Community 58 - "Agent Conventions"
Cohesion: 0.33
Nodes (4): BaseSink deliver cycle (queue, select, send), deliveries table (the ledger), ADR 0005 Remixers with external side effects, Strict FIFO per source

### Community 59 - "migrate_feed_names.py"
Cohesion: 0.10
Nodes (15): DBSource, SourceData, __newstool_plugin__(), __newstool_plugin__(), __newstool_plugin__(), Options, PluginOptions, __newstool_plugin__() (+7 more)

### Community 61 - "Item Identity ADR"
Cohesion: 0.40
Nodes (3): IndexSiteProvider / URLProvider, Item, Provider

### Community 63 - "describe"
Cohesion: 0.18
Nodes (4): import_one(), describe(), log_failure(), DescribeTests

### Community 65 - "EmbeddingsApplet"
Cohesion: 0.39
Nodes (3): EmbeddingsOptions, GroupingOptions, EmbeddingGroupingTests

### Community 66 - "ProcessorOptions"
Cohesion: 0.32
Nodes (4): MarkdownifyProcessor, SkipItem, make_pdf(), MarkdownifyPdfTests

### Community 72 - "DocumentFilter"
Cohesion: 0.13
Nodes (19): app_from_context(), check_all_rows(), check_found(), delete_annotations_cmd(), delete_deliveries_cmd(), delete_documents_cmd(), delete_items_cmd(), deliveries_send_cmd() (+11 more)

### Community 73 - "LogLevelTests"
Cohesion: 0.29
Nodes (7): foundation internal library, foundation.plugin.Register plugin loading, __newsmerger_plugin__(services, **options) entry point, PluginOptions (pydantic, unknown keys rejected), plugins configuration section, P1: plain logging and <APP>_LOG_LEVEL fix, P2: rich progress per stream (RICH_STDOUT_*/RICH_STDERR_*)

### Community 74 - "0011: Environment overrides, relative paths and one storage directory"
Cohesion: 0.40
Nodes (4): 0011: Environment overrides, relative paths and one storage directory, Consequences, Context, Decision

### Community 75 - "SinkType"
Cohesion: 0.09
Nodes (10): Routes, Sinks, __newstool_plugin__(), __newstool_plugin__(), __newstool_plugin__(), accepts(), Sink, SinkType (+2 more)

### Community 76 - "__newsmerger_plugin__"
Cohesion: 0.33
Nodes (6): sink, workflows, deliver, name, process, sources

### Community 77 - "app.py"
Cohesion: 0.06
Nodes (18): LockedError, write_lock(), backoff_seconds(), Base, DBItemAnnotation, DBProcessingState, DeliveryStatus, ProcessingStatus (+10 more)

### Community 79 - "scope_options"
Cohesion: 0.27
Nodes (5): annotation_options(), delivery_options(), document_options(), wrapper(), scope_options()

### Community 82 - "Services"
Cohesion: 0.12
Nodes (7): 0013: Plugin services at init, Consequences, Context, Decision, Rejected options, Services, ConsumerPluginTests

### Community 87 - "._find_excluded_containers"
Cohesion: 0.16
Nodes (4): _extract_href(), _get_modified_at(), PrensaIbericaProvider, read_sample()

### Community 88 - "BaseProcessor"
Cohesion: 0.11
Nodes (5): SummarizeProcessor, merge_tags(), TaggerProcessor, TruncateProcessor, BaseProcessor

### Community 89 - "EmbedProcessor"
Cohesion: 0.28
Nodes (3): EmbedOptions, EmbedProcessor, tags_text()

### Community 91 - "models.py"
Cohesion: 0.08
Nodes (12): reason(), strip_code_fence(), __newstool_plugin__(), UsesLLMOptions, __newstool_plugin__(), __newstool_plugin__(), SummarizeOptions, __newstool_plugin__() (+4 more)

### Community 92 - "Config"
Cohesion: 0.16
Nodes (3): Database & ORM Conventions, DTO, Protocol & ORM Implementation Reference, Config

### Community 93 - "setup_logging"
Cohesion: 0.33
Nodes (4): Additional Approved Packages, Framework Usage, newstool Python Specifics, setup_logging()

### Community 95 - "ConfigError"
Cohesion: 0.15
Nodes (4): check_section(), ConfigError, expand_variables(), MissingVariableError

### Community 100 - "Decision"
Cohesion: 0.29
Nodes (4): 0010: Plugin classes and the configuration catalog, Consequences, Decision, Rejected options

### Community 101 - "Delivery"
Cohesion: 0.11
Nodes (3): CommittedRun, DBDelivery, Delivery

### Community 105 - "0014: Ledger rows by subject and the workflow in delivery commands"
Cohesion: 0.33
Nodes (5): 0014: Ledger rows by subject and the workflow in delivery commands, Consequences, Context, Decision, Rejected options

### Community 106 - "0016: Routes on re-emission, manual queueing and pacing overrides"
Cohesion: 0.33
Nodes (5): 0016: Routes on re-emission, manual queueing and pacing overrides, Consequences, Context, Decision, Rejected options

### Community 108 - "0015: Applets, emitted documents and routes"
Cohesion: 0.40
Nodes (4): 0015: Applets, emitted documents and routes, Consequences, Context, Rejected options

### Community 109 - "parse_entry"
Cohesion: 0.60
Nodes (3): entry_date(), find_image(), parse_entry()

## Knowledge Gaps
- **13 isolated node(s):** `newstool`, `External pipelines (scripts/pipeline_url.py)`, `Annotation`, `Telegram t.me/s channel preview HTML (tgme_widget_message, data-post)`, `IndexSiteProvider / URLProvider` (+8 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 584 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **41 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Application` connect `Application` to `test_db.py`, `test_cli.py`, `Catalog`, `SourceItem`, `AppletReader`, `RunSummary`, `.get_items`, `apps_run_cmd`, `DocumentFilter`, `._profile`, `Document`, `cli.py`, `.sources`, `process_cmd`, `SourceItemData`, `PacingOverride`, `AppletRun`, `HTTPClient`, `migrate_feed_names.py`, `Deliverer`, `DocumentFilter`, `app.py`, `.from_file`, `Services`, `.find_annotations`, `Config`, `ConfigError`, `.close`, `.session_scope`, `Decision`, `Delivery`, `LLM`, `.get_content`, `.delete_items`?**
  _High betweenness centrality (0.110) - this node is a cross-community bridge._
- **Are the 31 inferred relationships involving `SourceItem` (e.g. with `Application` and `AppletReader`) actually correct?**
  _`SourceItem` has 31 INFERRED edges - model-reasoned connections that need verification._
- **What connects `newstool`, `External pipelines (scripts/pipeline_url.py)`, `Annotation` to the rest of the system?**
  _13 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_db.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06385964912280702 - nodes in this community are weakly interconnected._
- **Why does `SourceItem` connect `SourceItem` to `test_db.py`, `grouping.py`, `test_cli.py`, `invoke`, `AppletReader`, `ProcessingScope`, `itemfeed.py`, `.get_items`, `inspect_annotations_cmd`, `ScoredItem`, `cli.py`, `.add_items`, `Application`, `SourceItemData`, `feed.py`, `ProcessorOptions`, `app.py`, `.find_annotations`, `DigestApplet`, `Any`, `BaseProcessor`, `EmbedProcessor`, `models.py`, `Decision`, `.summary`, `.get_content`?**
  _High betweenness centrality (0.104) - this node is a cross-community bridge._
- **Are the 24 inferred relationships involving `Database` (e.g. with `Context` and `Application`) actually correct?**
  _`Database` has 24 INFERRED edges - model-reasoned connections that need verification._
- **Should `catalog.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12857142857142856 - nodes in this community are weakly interconnected._