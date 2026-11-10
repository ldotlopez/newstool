# Graph Report - newstool  (2026-11-10)

## Corpus Check
- 83 files · ~191,077 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 3, .lock 1)

## Summary
- 1956 nodes · 5402 edges · 97 communities (67 shown, 30 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 672 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e07f4c24`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- make_item
- catalog.py
- grouping.py
- test_cli.py
- DocumentFilter
- invoke
- Application
- Entry
- Database (db.py, only SQLite/storage access)
- LockedError
- .record_result
- SourceItem
- CSJuntasGobiernoProvider
- ProcessingScope
- ProcessingTests
- Artifact
- HTTPClient
- Telegram Channel Parsing
- ItemFeedApplet
- cli
- tagger.py
- datetime
- json
- ClassRegister
- SinkOptions
- process_cmd
- .mark_deliveries
- ollama.py
- summarize.py
- DocumentTests
- ScoredItem
- cli.py
- .add_items
- AnnotationTests
- Schedule
- AnnotationTests
- ProcessingScope
- .sources
- Architecture & Processing ADRs
- PluginFailure
- Selection CLI Options
- telegram_channel.py
- Processor & Remixer Bundles
- WebhookOptions
- Plugin System Docs
- Application
- SourceItem
- SourceItemData
- PacingOverride
- .settings_customise_sources
- AppletRun
- inspect_artifacts_cmd
- Spec Glossary Entities
- Sample Pages & Formats
- Decision
- Agent Conventions
- migrate_feed_names.py
- 0012: Delivery ids, changing their state and forced send
- Item Identity ADR
- Database
- Workflow
- HTTPClient
- ProcessorOptions
- Example Sources
- app.py
- Artifact & Remixer
- Grouping Notes
- GoogleChatSinkTests
- Decision
- LogLevelTests
- Services
- __newsmerger_plugin__
- migrate_applets.py
- 0009: Workflows and keyed entries
- chat_image_url
- ExternalErrorTests
- Delivery
- PreflightProvider
- .summary
- ._find_excluded_containers
- setup_logging
- ProcessorOptions
- ProcessorType
- Config
- ADR 0002 Processing state lifecycle
- SourceData
- test_db.py
- LLM
- .summary
- DeliveryTests
- 0014: Ledger rows by subject and the workflow in delivery commands
- 0016: Routes on re-emission, manual queueing and pacing overrides

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
- `Runs and state` --references--> `AppletRun`  [INFERRED]
  docs/decisions/0015-applets-documents-and-routes.md → newstool/models.py
- `Rejected options` --references--> `Services`  [INFERRED]
  docs/decisions/0013-plugin-services-at-init.md → newstool/plugins/__init__.py
- `Routes` --references--> `accepts()`  [INFERRED]
  docs/decisions/0015-applets-documents-and-routes.md → newstool/sinks.py
- `Decision` --references--> `Application`  [INFERRED]
  docs/decisions/0010-plugin-classes-and-catalog.md → newstool/app.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **markdownify -> summarize/tagger -> embed -> grouping data chain** — docs_architecture_markdownify_processor, docs_architecture_summarize_processor, docs_architecture_tagger_processor, docs_architecture_embed_processor, docs_architecture_grouping_remixers [EXTRACTED 1.00]
- **Plugin protocol types consumed by the core** — docs_specification_provider, docs_specification_processor, docs_specification_remixer, docs_specification_sink, docs_decisions_0006_llm_plugins_llm_protocol [EXTRACTED 1.00]
- **Delivery ledger mechanism** — docs_architecture_deliveries_table, docs_decisions_0007_sinks_and_delivery_ledger_delivery_states, docs_architecture_basesink_cycle, docs_decisions_0007_sinks_and_delivery_ledger_strict_fifo_per_source, docs_decisions_0007_sinks_and_delivery_ledger_lookback_window, docs_specification_write_lock [INFERRED 0.85]
- **Prensa Ibérica sample article fixtures (El Periódico Mediterráneo, July 2026)** — tests_samples_prensaiberica_item_132310503_article, tests_samples_prensaiberica_item_132340038_article, tests_samples_prensaiberica_item_132344288_article [INFERRED 0.95]

## Communities (97 total, 30 thin omitted)

### Community 0 - "make_item"
Cohesion: 0.17
Nodes (6): DBSourceItem, ContentStorageTests, IdentityTests, make_item(), make_source(), UpsertSourceItemsTests

### Community 1 - "catalog.py"
Cohesion: 0.06
Nodes (14): Catalog, check_section(), ids_of(), in_default(), Kind, process_key(), Profile, Run (+6 more)

### Community 2 - "grouping.py"
Cohesion: 0.06
Nodes (23): Applets, AppletType, BaseApplet, check_result(), Requirements, run_key(), SourcesOptions, LLMUnavailableError (+15 more)

### Community 3 - "test_cli.py"
Cohesion: 0.07
Nodes (7): ApplicationTests, retrieve(), retrieve_published(), retrieve(), same(), listed(), retrieved()

### Community 4 - "DocumentFilter"
Cohesion: 0.15
Nodes (8): check_all_rows(), check_found(), delete_documents_cmd(), document_options(), wrapper(), inspect_documents_cmd(), select_deliveries(), DocumentFilter

### Community 5 - "invoke"
Cohesion: 0.09
Nodes (8): AppReport, DeleteSummary, MarkSummary, RunSummary, annotation(), CommandTests, InspectCommandTests, invoke()

### Community 6 - "Application"
Cohesion: 0.09
Nodes (3): ollama_url(), AliasTests, ConfigTests

### Community 7 - "Entry"
Cohesion: 0.09
Nodes (4): AppEntry, Entry, LLMEntry, SinkEntry

### Community 8 - "Database (db.py, only SQLite/storage access)"
Cohesion: 0.17
Nodes (11): pre-commit config, ruff-check and ruff-format hooks, newsmerger CLAUDE.md agent guidelines, DTO/ORM from_dto/to_dto/update convention, Consumer-side Protocol decoupling convention, AUTOINCREMENT integer ids, Database (db.py, only SQLite/storage access), foundation.storage.DiskStorage content-addressed storage (+3 more)

### Community 9 - "LockedError"
Cohesion: 0.16
Nodes (6): ConsumerPluginTests, EmbedTests, ProcessorTestCase, StubLLM, SummarizeTests, TaggerTests

### Community 10 - ".record_result"
Cohesion: 0.09
Nodes (4): MigrateAppletsTests, sha256(), make_item(), MigrateAutoincrementTests

### Community 11 - "SourceItem"
Cohesion: 0.09
Nodes (6): AppletReader, SourceItem, DigestApplet, FeedApplet, ItemFeedApplet, SearchTests

### Community 12 - "CSJuntasGobiernoProvider"
Cohesion: 0.19
Nodes (7): PreflightSourceItemData, CSJuntasGobiernoProvider, find_parent_by_tag_name(), get_date_from_text(), PreparseData, NoOptions, TestCSJuntasGobierno

### Community 15 - "Artifact"
Cohesion: 0.12
Nodes (10): Schedule, build_caption(), post(), TelegramSink, BuildCaptionTests, item_document(), ok_response(), options() (+2 more)

### Community 16 - "HTTPClient"
Cohesion: 0.08
Nodes (16): 0013: Plugin services at init, Consequences, Context, Decision, Rejected options, HTTPClient, discover_feed_url(), entry_date() (+8 more)

### Community 17 - "Telegram Channel Parsing"
Cohesion: 0.13
Nodes (9): is_home_page(), page_title(), parse_article(), parse_preview(), Post, preview_url(), TelegramChannelProvider, read_sample() (+1 more)

### Community 18 - "ItemFeedApplet"
Cohesion: 0.15
Nodes (11): 0015: Applets, emitted documents and routes, CLI, Consequences, Context, Decision, Documents, Migration, Reading (+3 more)

### Community 19 - "cli"
Cohesion: 0.17
Nodes (5): apps_group(), cli(), delete_group(), deliveries_group(), inspect_group()

### Community 20 - "tagger.py"
Cohesion: 0.21
Nodes (5): strip_code_fence(), merge_tags(), __newstool_plugin__(), TaggerOptions, TaggerProcessor

### Community 21 - "datetime"
Cohesion: 0.09
Nodes (3): CustomJSON, _encode_value(), UTCDateTime

### Community 22 - "json"
Cohesion: 0.18
Nodes (8): Additional Approved Packages, Framework Usage, newstool Python Specifics, format_value(), json_default(), preview(), print_json(), setup_logging()

### Community 23 - "ClassRegister"
Cohesion: 0.14
Nodes (4): Database & ORM Conventions, DTO, Protocol & ORM Implementation Reference, resolve_config_path(), ClassRegister

### Community 24 - "SinkOptions"
Cohesion: 0.08
Nodes (9): FileOptions, FileSink, CommitTests, DelivererTests, run(), DeliveryOrderTests, FileSinkTests, LedgerTestCase (+1 more)

### Community 25 - "process_cmd"
Cohesion: 0.28
Nodes (3): apps_reset_cmd(), deliver_cmd(), process_cmd()

### Community 27 - "ollama.py"
Cohesion: 0.21
Nodes (5): __newstool_plugin__(), ollama_client(), OllamaLLM, Options, OllamaTests

### Community 28 - "summarize.py"
Cohesion: 0.22
Nodes (4): UsesLLMOptions, __newstool_plugin__(), SummarizeOptions, SummarizeProcessor

### Community 29 - "DocumentTests"
Cohesion: 0.22
Nodes (3): DBDocument, DocumentTests, keys()

### Community 30 - "ScoredItem"
Cohesion: 0.08
Nodes (18): average_between(), average_link_cluster(), build_score_matrix(), cosine_similarity(), EmbeddingsApplet, EmbeddingsOptions, item_ref(), jaccard() (+10 more)

### Community 31 - "cli.py"
Cohesion: 0.08
Nodes (15): apps_run_cmd(), describe_schedule(), format_seconds(), format_time(), lexer_for(), match_snippet(), print_apps(), print_content() (+7 more)

### Community 33 - ".add_items"
Cohesion: 0.14
Nodes (6): GroupingOptions, ItemFeedOptions, AppletTestCase, FeedTests, GroupingTests, ItemFeedTests

### Community 34 - "AnnotationTests"
Cohesion: 0.12
Nodes (17): lookback, title, url, api_base, chat_model, embed_model, plugins, digest (+9 more)

### Community 35 - "Schedule"
Cohesion: 0.21
Nodes (3): Applet, Schedule, ScheduleTests

### Community 37 - "ProcessingScope"
Cohesion: 0.44
Nodes (3): wrapper(), ProcessingScope, GetItemsTests

### Community 38 - ".sources"
Cohesion: 0.13
Nodes (7): 0009: Workflows and keyed entries, Consequences, Context, Decision, Rejected options, Configuration, Plugins

### Community 39 - "Architecture & Processing ADRs"
Cohesion: 0.21
Nodes (14): Architecture, cli.py Click commands, External pipelines (scripts/pipeline_url.py), ADR 0001 Item identity and change detection, ADR 0003 Plugin types and core scope, ADR 0004 Annotation and artifact contents on disk, ADR 0006 LLM plugins, ADR 0007 Sinks and the delivery ledger (+6 more)

### Community 40 - "PluginFailure"
Cohesion: 0.09
Nodes (10): import_one(), describe(), log_failure(), PluginFailure, reason(), get_section(), parse_datetime(), PlazaProvider (+2 more)

### Community 41 - "Selection CLI Options"
Cohesion: 0.15
Nodes (14): options, artifacts, chat_id, interval, item_image, item_url_preview, item_url_text, markdown (+6 more)

### Community 42 - "telegram_channel.py"
Cohesion: 0.15
Nodes (12): exclude, args, entry, files, id, language, name, pass_filenames (+4 more)

### Community 43 - "Processor & Remixer Bundles"
Cohesion: 0.22
Nodes (12): digest remixer, embed processor, grouping remixers (singlelink, avglink, embeddings), markdownify processor, summarize processor, tagger processor, telegram bundle (telegram, telegram_artifacts sinks), LLM plugins must be listed before their consumers (+4 more)

### Community 44 - "WebhookOptions"
Cohesion: 0.09
Nodes (10): build_card(), chat_image_url(), GoogleChatSink, __newstool_plugin__(), WebhookOptions, card_widgets(), ChatImageUrlTests, GoogleChatSinkTests (+2 more)

### Community 45 - "Plugin System Docs"
Cohesion: 0.11
Nodes (15): cache, expiration, llms, input, processors, options, processor, remixers (+7 more)

### Community 47 - "SourceItem"
Cohesion: 0.21
Nodes (5): import_cmd(), import_sources(), print_import(), run_cmd(), run_each()

### Community 51 - ".settings_customise_sources"
Cohesion: 0.09
Nodes (7): EnvAliasSource, expand_variables(), load_context(), LoadContext, LoadEnvSettingsSource, MissingVariableError, parse_duration()

### Community 54 - "Spec Glossary Entities"
Cohesion: 0.29
Nodes (6): UnavailableProcessor / UnavailableRemixer / UnavailableSink, Annotation, Delivery, Exponential backoff 60s*2^(n-1), capped 24h, max_retries, Processor, Sink

### Community 55 - "Sample Pages & Formats"
Cohesion: 0.43
Nodes (7): El Periódico Mediterráneo, Prensa Ibérica article HTML format (og:/article: meta tags), Telegram t.me/s channel preview HTML (tgme_widget_message, data-post), El eco perdido de las fiestas de julio nacidas del asedio carlista sobre Castellón (sample article), El Grau se vuelca en las fiestas de la Virgen del Carmen (sample article), Castellón apoya a la selección española desde la plaza Mayor (sample article), Telegram channel mediterraneoelperiodico (sample web preview)

### Community 57 - "Decision"
Cohesion: 0.14
Nodes (8): 0010: Plugin classes and the configuration catalog, Consequences, Context, Decision, Rejected options, LLMType, factory(), factory()

### Community 58 - "Agent Conventions"
Cohesion: 0.33
Nodes (4): BaseSink deliver cycle (queue, select, send), deliveries table (the ledger), ADR 0005 Remixers with external side effects, Strict FIFO per source

### Community 59 - "migrate_feed_names.py"
Cohesion: 0.11
Nodes (13): __newstool_plugin__(), __newstool_plugin__(), __newstool_plugin__(), Options, PluginOptions, __newstool_plugin__(), __newstool_plugin__(), Options (+5 more)

### Community 60 - "0012: Delivery ids, changing their state and forced send"
Cohesion: 0.33
Nodes (5): 0012: Delivery ids, changing their state and forced send, Consequences, Context, Decision, Rejected options

### Community 61 - "Item Identity ADR"
Cohesion: 0.40
Nodes (3): IndexSiteProvider / URLProvider, Item, Provider

### Community 62 - "Database"
Cohesion: 0.06
Nodes (3): _configure_sqlite_connection(), Database, DBProcessingState

### Community 66 - "ProcessorOptions"
Cohesion: 0.22
Nodes (4): MarkdownifyProcessor, SkipItem, make_pdf(), MarkdownifyPdfTests

### Community 68 - "app.py"
Cohesion: 0.09
Nodes (7): Alias, CacheConfig, backoff_seconds(), DeliveryStatus, ProcessingStatus, _sha256_column(), Annotation

### Community 72 - "Decision"
Cohesion: 0.15
Nodes (16): app_from_context(), delete_annotations_cmd(), delete_deliveries_cmd(), delete_items_cmd(), deliveries_send_cmd(), deliveries_set_status_cmd(), delivery_filters(), inspect_annotations_cmd() (+8 more)

### Community 73 - "LogLevelTests"
Cohesion: 0.29
Nodes (7): foundation internal library, foundation.plugin.Register plugin loading, __newsmerger_plugin__(services, **options) entry point, PluginOptions (pydantic, unknown keys rejected), plugins configuration section, P1: plain logging and <APP>_LOG_LEVEL fix, P2: rich progress per stream (RICH_STDOUT_*/RICH_STDERR_*)

### Community 75 - "Services"
Cohesion: 0.06
Nodes (17): Sinks, CommittedRun, Document, __newstool_plugin__(), Services, __newstool_plugin__(), StdoutSink, __newstool_plugin__() (+9 more)

### Community 76 - "__newsmerger_plugin__"
Cohesion: 0.33
Nodes (6): sink, workflows, deliver, name, process, sources

### Community 77 - "migrate_applets.py"
Cohesion: 0.07
Nodes (14): LockedError, write_lock(), Base, DBItemAnnotation, columns(), has_table(), main(), migrate() (+6 more)

### Community 79 - "chat_image_url"
Cohesion: 0.28
Nodes (4): annotation_options(), delivery_options(), wrapper(), scope_options()

### Community 87 - "._find_excluded_containers"
Cohesion: 0.17
Nodes (3): _extract_href(), _get_modified_at(), PrensaIbericaProvider

### Community 89 - "ProcessorOptions"
Cohesion: 0.17
Nodes (5): EmbedOptions, EmbedProcessor, tags_text(), ProcessorOptions, ClassRegisterTests

### Community 91 - "ProcessorType"
Cohesion: 0.13
Nodes (5): __newstool_plugin__(), __newstool_plugin__(), __newstool_plugin__(), Processor, ProcessorType

### Community 92 - "Config"
Cohesion: 0.12
Nodes (6): 0011: Environment overrides, relative paths and one storage directory, Consequences, Context, Decision, Config, DirectoryTests

### Community 98 - "SourceData"
Cohesion: 0.13
Nodes (5): DBSource, SourceData, CastellonInformacionProvider, TheGuardianProvider, IndexSiteProvider

### Community 101 - "test_db.py"
Cohesion: 0.20
Nodes (4): DBDelivery, ConnectionTests, DatabaseTestCase, DeleteTests

### Community 105 - "0014: Ledger rows by subject and the workflow in delivery commands"
Cohesion: 0.33
Nodes (5): 0014: Ledger rows by subject and the workflow in delivery commands, Consequences, Context, Decision, Rejected options

### Community 106 - "0016: Routes on re-emission, manual queueing and pacing overrides"
Cohesion: 0.33
Nodes (5): 0016: Routes on re-emission, manual queueing and pacing overrides, Consequences, Context, Decision, Rejected options

## Knowledge Gaps
- **13 isolated node(s):** `newstool`, `External pipelines (scripts/pipeline_url.py)`, `Annotation`, `Telegram t.me/s channel preview HTML (tgme_widget_message, data-post)`, `IndexSiteProvider / URLProvider` (+8 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 585 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **30 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ADR 0008 inspect and delete CLI and numeric ids` connect `Architecture & Processing ADRs` to `migrate_applets.py`?**
  _High betweenness centrality (0.111) - this node is a cross-community bridge._
- **Are the 31 inferred relationships involving `SourceItem` (e.g. with `Application` and `AppletReader`) actually correct?**
  _`SourceItem` has 31 INFERRED edges - model-reasoned connections that need verification._
- **What connects `newstool`, `External pipelines (scripts/pipeline_url.py)`, `Annotation` to the rest of the system?**
  _13 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `catalog.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0625 - nodes in this community are weakly interconnected._
- **Why does `Services` connect `Services` to `grouping.py`, `LockedError`, `SourceItem`, `CSJuntasGobiernoProvider`, `Artifact`, `HTTPClient`, `Telegram Channel Parsing`, `tagger.py`, `ClassRegister`, `SinkOptions`, `ollama.py`, `summarize.py`, `.add_items`, `WebhookOptions`, `Decision`, `migrate_feed_names.py`, `Database`, `ProcessorOptions`, `app.py`, `PreflightProvider`, `.summary`, `._find_excluded_containers`, `ProcessorOptions`, `ProcessorType`, `LLM`, `.summary`?**
  _High betweenness centrality (0.105) - this node is a cross-community bridge._
- **Are the 24 inferred relationships involving `Database` (e.g. with `Context` and `Application`) actually correct?**
  _`Database` has 24 INFERRED edges - model-reasoned connections that need verification._
- **Should `grouping.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05860805860805861 - nodes in this community are weakly interconnected._