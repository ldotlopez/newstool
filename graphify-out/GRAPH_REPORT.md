# Graph Report - newstool  (2026-11-10)

## Corpus Check
- 83 files · ~191,657 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 3, .lock 1)

## Summary
- 1979 nodes · 5462 edges · 93 communities (61 shown, 32 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 680 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b607bbb4`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- make_item
- catalog.py
- models.py
- test_cli.py
- DocumentFilter
- invoke
- Application
- Entry
- Database (db.py, only SQLite/storage access)
- LockedError
- .record_result
- AppletReader
- CSJuntasGobiernoProvider
- ProcessingScope
- expand_variables
- Artifact
- TestFeedReader
- Telegram Channel Parsing
- Document
- cli
- itemfeed.py
- datetime
- Schedule
- Delivery
- process_cmd
- .mark_deliveries
- ClassRegister
- summarize.py
- DocumentTests
- ScoredItem
- cli.py
- TelegramSink
- .add_items
- AnnotationTests
- Schedule
- AnnotationTests
- Requirements
- .sources
- Architecture & Processing ADRs
- PluginFailure
- Selection CLI Options
- telegram_channel.py
- Processor & Remixer Bundles
- WebhookOptions
- Plugin System Docs
- Application
- process_cmd
- SourceItemData
- cli
- .settings_customise_sources
- inspect_artifacts_cmd
- Spec Glossary Entities
- Sample Pages & Formats
- HTTPClient
- AppletType
- Agent Conventions
- migrate_feed_names.py
- Item Identity ADR
- ProcessEntry
- LogFailureTests
- search_cmd
- BaseProcessor
- Example Sources
- app.py
- Artifact & Remixer
- Grouping Notes
- app_from_context
- LogLevelTests
- Services
- __newsmerger_plugin__
- migrate_applets.py
- 0009: Workflows and keyed entries
- Path
- ExternalErrorTests
- Delivery
- PreflightProvider
- .__init__
- ._find_excluded_containers
- setup_logging
- Config
- AliasTests
- ADR 0002 Processing state lifecycle
- 0011: Environment overrides, relative paths and one storage directory
- SourceData
- __newstool_plugin__
- test_db.py
- 0016: Routes on re-emission, manual queueing and pacing overrides

## God Nodes (most connected - your core abstractions)
1. `SourceItem` - 114 edges
2. `Database` - 103 edges
3. `Services` - 92 edges
4. `Application` - 84 edges
5. `SourceData` - 75 edges
6. `PluginFailure` - 72 edges
7. `Document` - 72 edges
8. `ApplicationTests` - 69 edges
9. `SourceItemData` - 56 edges
10. `ProcessingScope` - 55 edges

## Surprising Connections (you probably didn't know these)
- `Reading` --references--> `AppletReader`  [INFERRED]
  docs/decisions/0015-applets-documents-and-routes.md → newstool/applets.py
- `Decision` --references--> `Config`  [INFERRED]
  docs/decisions/0011-environment-overrides-and-storage-dir.md → newstool/config.py
- `Runs and state` --references--> `AppletRun`  [INFERRED]
  docs/decisions/0015-applets-documents-and-routes.md → newstool/models.py
- `Rejected options` --references--> `Services`  [INFERRED]
  docs/decisions/0013-plugin-services-at-init.md → newstool/plugins/__init__.py
- `Schedule` --references--> `options()`  [INFERRED]
  docs/decisions/0015-applets-documents-and-routes.md → tests/test_telegram.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **markdownify -> summarize/tagger -> embed -> grouping data chain** — docs_architecture_markdownify_processor, docs_architecture_summarize_processor, docs_architecture_tagger_processor, docs_architecture_embed_processor, docs_architecture_grouping_remixers [EXTRACTED 1.00]
- **Plugin protocol types consumed by the core** — docs_specification_provider, docs_specification_processor, docs_specification_remixer, docs_specification_sink, docs_decisions_0006_llm_plugins_llm_protocol [EXTRACTED 1.00]
- **Delivery ledger mechanism** — docs_architecture_deliveries_table, docs_decisions_0007_sinks_and_delivery_ledger_delivery_states, docs_architecture_basesink_cycle, docs_decisions_0007_sinks_and_delivery_ledger_strict_fifo_per_source, docs_decisions_0007_sinks_and_delivery_ledger_lookback_window, docs_specification_write_lock [INFERRED 0.85]
- **Prensa Ibérica sample article fixtures (El Periódico Mediterráneo, July 2026)** — tests_samples_prensaiberica_item_132310503_article, tests_samples_prensaiberica_item_132340038_article, tests_samples_prensaiberica_item_132344288_article [INFERRED 0.95]

## Communities (93 total, 32 thin omitted)

### Community 0 - "make_item"
Cohesion: 0.06
Nodes (23): 0012: Delivery ids, changing their state and forced send, Consequences, Context, Decision, Rejected options, Deliveries, wrapper(), DBProcessingState (+15 more)

### Community 1 - "catalog.py"
Cohesion: 0.08
Nodes (7): Catalog, check_section(), Kind, Run, share_sources(), ConfigError, options_error()

### Community 2 - "models.py"
Cohesion: 0.08
Nodes (12): ProcessingStatus, strip_code_fence(), __newstool_plugin__(), UsesLLMOptions, __newstool_plugin__(), __newstool_plugin__(), SummarizeOptions, __newstool_plugin__() (+4 more)

### Community 3 - "test_cli.py"
Cohesion: 0.07
Nodes (7): ApplicationTests, retrieve(), retrieve_published(), retrieve(), same(), listed(), retrieved()

### Community 4 - "DocumentFilter"
Cohesion: 0.11
Nodes (10): annotation_options(), check_all_rows(), delivery_options(), document_options(), wrapper(), inspect_documents_cmd(), wrapper(), scope_options() (+2 more)

### Community 5 - "invoke"
Cohesion: 0.07
Nodes (9): AppReport, DeleteSummary, MarkSummary, RunSummary, annotation(), CommandTests, ExternalErrorTests, InspectCommandTests (+1 more)

### Community 7 - "Entry"
Cohesion: 0.09
Nodes (4): AppEntry, Entry, LLMEntry, SinkEntry

### Community 8 - "Database (db.py, only SQLite/storage access)"
Cohesion: 0.17
Nodes (11): pre-commit config, ruff-check and ruff-format hooks, newsmerger CLAUDE.md agent guidelines, DTO/ORM from_dto/to_dto/update convention, Consumer-side Protocol decoupling convention, AUTOINCREMENT integer ids, Database (db.py, only SQLite/storage access), foundation.storage.DiskStorage content-addressed storage (+3 more)

### Community 9 - "LockedError"
Cohesion: 0.15
Nodes (6): Processor, EmbedTests, ProcessorTestCase, StubLLM, SummarizeTests, TaggerTests

### Community 10 - ".record_result"
Cohesion: 0.09
Nodes (5): Database, SourceItem, MigrateAppletsTests, sha256(), make_item()

### Community 11 - "AppletReader"
Cohesion: 0.14
Nodes (4): AppletReader, DigestApplet, AverageLinkApplet, GroupingApplet

### Community 12 - "CSJuntasGobiernoProvider"
Cohesion: 0.27
Nodes (5): CSJuntasGobiernoProvider, find_parent_by_tag_name(), get_date_from_text(), PreparseData, TestCSJuntasGobierno

### Community 15 - "Artifact"
Cohesion: 0.24
Nodes (6): run(), item_document(), ok_response(), options(), sink(), TelegramSinkTests

### Community 17 - "Telegram Channel Parsing"
Cohesion: 0.16
Nodes (7): is_home_page(), parse_article(), parse_preview(), Post, preview_url(), TelegramChannelProvider, TestTelegramChannel

### Community 18 - "Document"
Cohesion: 0.11
Nodes (5): CommittedRun, DBDocument, Document, DocumentTests, keys()

### Community 19 - "cli"
Cohesion: 0.17
Nodes (5): run_key(), SourcesOptions, FeedApplet, Options, FeedTests

### Community 24 - "Delivery"
Cohesion: 0.07
Nodes (10): backoff_seconds(), DBDelivery, Delivery, Deliverer, DeliveryTests, CommitTests, DelivererTests, DeliveryOrderTests (+2 more)

### Community 25 - "process_cmd"
Cohesion: 0.17
Nodes (3): FileOptions, FileSink, FileSinkTests

### Community 26 - ".mark_deliveries"
Cohesion: 0.25
Nodes (3): build_card(), chat_image_url(), ChatImageUrlTests

### Community 27 - "ClassRegister"
Cohesion: 0.09
Nodes (9): Decision, LLM, LLMType, ClassRegister, __newstool_plugin__(), ollama_client(), OllamaLLM, Options (+1 more)

### Community 29 - "DocumentTests"
Cohesion: 0.13
Nodes (9): Documents, Migration, Applet, check_result(), AppletResult, EmittedDocument, CheckResultTests, ReaderTests (+1 more)

### Community 30 - "ScoredItem"
Cohesion: 0.11
Nodes (15): average_between(), average_link_cluster(), build_score_matrix(), cosine_similarity(), GroupingOptions, item_ref(), member_payload(), pair_payload() (+7 more)

### Community 31 - "cli.py"
Cohesion: 0.08
Nodes (16): apps_run_cmd(), describe_schedule(), format_seconds(), format_time(), format_value(), inspect_apps_cmd(), json_default(), lexer_for() (+8 more)

### Community 32 - "TelegramSink"
Cohesion: 0.22
Nodes (4): build_caption(), post(), TelegramSink, BuildCaptionTests

### Community 33 - ".add_items"
Cohesion: 0.20
Nodes (5): DBApp, AppletRun, AppletTestCase, GroupingTests, ItemFeedTests

### Community 34 - "AnnotationTests"
Cohesion: 0.12
Nodes (17): lookback, title, url, api_base, chat_model, embed_model, plugins, digest (+9 more)

### Community 35 - "Schedule"
Cohesion: 0.05
Nodes (28): 0009: Workflows and keyed entries, Consequences, Context, Decision, Rejected options, 0010: Plugin classes and the configuration catalog, Consequences, Context (+20 more)

### Community 36 - "AnnotationTests"
Cohesion: 0.18
Nodes (4): __newstool_plugin__(), WebhookOptions, OptionsTests, webhook_options()

### Community 37 - "Requirements"
Cohesion: 0.23
Nodes (5): Requirements, EmbeddingsApplet, EmbeddingsOptions, jaccard(), EmbeddingGroupingTests

### Community 38 - ".sources"
Cohesion: 0.12
Nodes (3): AppStatus, lookup(), AppInstance

### Community 39 - "Architecture & Processing ADRs"
Cohesion: 0.21
Nodes (14): Architecture, cli.py Click commands, External pipelines (scripts/pipeline_url.py), ADR 0001 Item identity and change detection, ADR 0003 Plugin types and core scope, ADR 0004 Annotation and artifact contents on disk, ADR 0006 LLM plugins, ADR 0007 Sinks and the delivery ledger (+6 more)

### Community 40 - "PluginFailure"
Cohesion: 0.18
Nodes (3): describe(), log_failure(), DescribeTests

### Community 41 - "Selection CLI Options"
Cohesion: 0.15
Nodes (14): options, artifacts, chat_id, interval, item_image, item_url_preview, item_url_text, markdown (+6 more)

### Community 42 - "telegram_channel.py"
Cohesion: 0.15
Nodes (12): exclude, args, entry, files, id, language, name, pass_filenames (+4 more)

### Community 43 - "Processor & Remixer Bundles"
Cohesion: 0.22
Nodes (12): digest remixer, embed processor, grouping remixers (singlelink, avglink, embeddings), markdownify processor, summarize processor, tagger processor, telegram bundle (telegram, telegram_artifacts sinks), LLM plugins must be listed before their consumers (+4 more)

### Community 45 - "Plugin System Docs"
Cohesion: 0.11
Nodes (15): cache, expiration, llms, input, processors, options, processor, remixers (+7 more)

### Community 46 - "Application"
Cohesion: 0.06
Nodes (3): Application, Profile, PacingOverride

### Community 47 - "process_cmd"
Cohesion: 0.11
Nodes (11): failed_summary(), import_cmd(), import_sources(), import_failed(), print_import(), print_process(), process_cmd(), progress_rows() (+3 more)

### Community 48 - "SourceItemData"
Cohesion: 0.18
Nodes (5): PreflightSourceItemData, SourceItemData, PrensaIbericaProvider, read_sample(), TestPrensaIberica

### Community 50 - "cli"
Cohesion: 0.17
Nodes (5): apps_group(), cli(), delete_group(), deliveries_group(), inspect_group()

### Community 51 - ".settings_customise_sources"
Cohesion: 0.12
Nodes (5): EnvAliasSource, load_context(), LoadContext, LoadEnvSettingsSource, parse_duration()

### Community 54 - "Spec Glossary Entities"
Cohesion: 0.29
Nodes (6): UnavailableProcessor / UnavailableRemixer / UnavailableSink, Annotation, Delivery, Exponential backoff 60s*2^(n-1), capped 24h, max_retries, Processor, Sink

### Community 55 - "Sample Pages & Formats"
Cohesion: 0.43
Nodes (7): El Periódico Mediterráneo, Prensa Ibérica article HTML format (og:/article: meta tags), Telegram t.me/s channel preview HTML (tgme_widget_message, data-post), El eco perdido de las fiestas de julio nacidas del asedio carlista sobre Castellón (sample article), El Grau se vuelca en las fiestas de la Virgen del Carmen (sample article), Castellón apoya a la selección española desde la plaza Mayor (sample article), Telegram channel mediterraneoelperiodico (sample web preview)

### Community 56 - "HTTPClient"
Cohesion: 0.20
Nodes (5): HTTPClient, discover_feed_url(), fetch_article(), fetch_feed(), TestHTTPClient

### Community 57 - "AppletType"
Cohesion: 0.08
Nodes (13): Applets, AppletType, LLMUnavailableError, DigestOptions, __newstool_plugin__(), SummarizeProcessor, merge_tags(), TaggerProcessor (+5 more)

### Community 58 - "Agent Conventions"
Cohesion: 0.33
Nodes (4): BaseSink deliver cycle (queue, select, send), deliveries table (the ledger), ADR 0005 Remixers with external side effects, Strict FIFO per source

### Community 59 - "migrate_feed_names.py"
Cohesion: 0.07
Nodes (25): PluginFailure, SourceData, __newstool_plugin__(), __newstool_plugin__(), entry_date(), find_image(), __newstool_plugin__(), Options (+17 more)

### Community 61 - "Item Identity ADR"
Cohesion: 0.40
Nodes (3): IndexSiteProvider / URLProvider, Item, Provider

### Community 63 - "ProcessEntry"
Cohesion: 0.20
Nodes (5): ids_of(), in_default(), process_key(), Use, ProcessEntry

### Community 66 - "BaseProcessor"
Cohesion: 0.06
Nodes (15): 0013: Plugin services at init, Consequences, Context, Decision, Rejected options, EmbedOptions, EmbedProcessor, tags_text() (+7 more)

### Community 68 - "app.py"
Cohesion: 0.07
Nodes (8): workflow_scope(), Alias, CacheConfig, Workflow, _encode_value(), _sha256_column(), reason(), Annotation

### Community 72 - "app_from_context"
Cohesion: 0.12
Nodes (21): app_from_context(), apps_reset_cmd(), check_found(), delete_annotations_cmd(), delete_deliveries_cmd(), delete_documents_cmd(), delete_items_cmd(), deliver_cmd() (+13 more)

### Community 73 - "LogLevelTests"
Cohesion: 0.29
Nodes (7): foundation internal library, foundation.plugin.Register plugin loading, __newsmerger_plugin__(services, **options) entry point, PluginOptions (pydantic, unknown keys rejected), plugins configuration section, P1: plain logging and <APP>_LOG_LEVEL fix, P2: rich progress per stream (RICH_STDOUT_*/RICH_STDERR_*)

### Community 75 - "Services"
Cohesion: 0.06
Nodes (17): Routes, Sinks, __newstool_plugin__(), GoogleChatSink, Services, __newstool_plugin__(), StdoutSink, __newstool_plugin__() (+9 more)

### Community 76 - "__newsmerger_plugin__"
Cohesion: 0.33
Nodes (6): sink, workflows, deliver, name, process, sources

### Community 77 - "migrate_applets.py"
Cohesion: 0.06
Nodes (15): LockedError, write_lock(), Base, DBItemAnnotation, columns(), has_table(), main(), migrate() (+7 more)

### Community 90 - "setup_logging"
Cohesion: 0.33
Nodes (4): Additional Approved Packages, Framework Usage, newstool Python Specifics, setup_logging()

### Community 92 - "Config"
Cohesion: 0.11
Nodes (4): Database & ORM Conventions, DTO, Protocol & ORM Implementation Reference, Config, DirectoryTests

### Community 95 - "0011: Environment overrides, relative paths and one storage directory"
Cohesion: 0.40
Nodes (4): 0011: Environment overrides, relative paths and one storage directory, Consequences, Context, Decision

### Community 99 - "__newstool_plugin__"
Cohesion: 0.29
Nodes (3): __newstool_plugin__(), __newstool_plugin__(), __newstool_plugin__()

### Community 106 - "0016: Routes on re-emission, manual queueing and pacing overrides"
Cohesion: 0.33
Nodes (5): 0016: Routes on re-emission, manual queueing and pacing overrides, Consequences, Context, Decision, Rejected options

## Knowledge Gaps
- **13 isolated node(s):** `newstool`, `External pipelines (scripts/pipeline_url.py)`, `Annotation`, `Telegram t.me/s channel preview HTML (tgme_widget_message, data-post)`, `IndexSiteProvider / URLProvider` (+8 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 594 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **32 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SourceItem` connect `.record_result` to `make_item`, `.add_items`, `models.py`, `Schedule`, `app.py`, `BaseProcessor`, `test_cli.py`, `invoke`, `LockedError`, `AppletReader`, `ProcessingScope`, `Application`, `cli`, `itemfeed.py`, `datetime`, `AppletType`, `ScoredItem`, `cli.py`?**
  _High betweenness centrality (0.116) - this node is a cross-community bridge._
- **Are the 31 inferred relationships involving `SourceItem` (e.g. with `Application` and `AppletReader`) actually correct?**
  _`SourceItem` has 31 INFERRED edges - model-reasoned connections that need verification._
- **What connects `newstool`, `External pipelines (scripts/pipeline_url.py)`, `Annotation` to the rest of the system?**
  _13 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `make_item` be split into smaller, more focused modules?**
  _Cohesion score 0.05616509926854754 - nodes in this community are weakly interconnected._
- **Why does `Application` connect `Application` to `make_item`, `catalog.py`, `models.py`, `test_cli.py`, `DocumentFilter`, `invoke`, `Application`, `.record_result`, `AppletReader`, `Document`, `Delivery`, `ClassRegister`, `cli.py`, `.add_items`, `Schedule`, `.sources`, `process_cmd`, `SourceItemData`, `AppletRun`, `HTTPClient`, `migrate_feed_names.py`, `Database`, `BaseProcessor`, `app.py`, `app_from_context`, `migrate_applets.py`, `PreflightProvider`, `Config`, `.close`?**
  _High betweenness centrality (0.110) - this node is a cross-community bridge._
- **Are the 24 inferred relationships involving `Database` (e.g. with `Context` and `Application`) actually correct?**
  _`Database` has 24 INFERRED edges - model-reasoned connections that need verification._
- **Should `catalog.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0786308973172988 - nodes in this community are weakly interconnected._