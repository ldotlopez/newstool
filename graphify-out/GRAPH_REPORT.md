# Graph Report - digest-plan  (2026-11-11)

## Corpus Check
- 80 files · ~194,435 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 4, .lock 1)

## Summary
- 2008 nodes · 5475 edges · 89 communities (61 shown, 28 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 679 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d374cce6`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- make_item
- catalog.py
- Services
- ApplicationTests
- selection_options
- invoke
- .from_text
- Entry
- Database (db.py, only SQLite/storage access)
- StubLLM
- .record_result
- SourceItem
- PreflightSourceItemData
- DeleteCommandTests
- expand_variables
- TelegramSinkTests
- TestFeedReader
- test_providers.py
- Document
- DigestApplet
- EmittedDocument
- datetime
- test_db.py
- describe
- Delivery
- DocumentTests
- ProcessingTests
- OllamaLLM
- GoogleChatSinkTests
- chat_image_url
- grouping.py
- cli.py
- TelegramSink
- .add_items
- plugins
- .summary
- GoogleChatSink
- AnnotationTests
- app_from_context
- ADR 0007 Sinks and the delivery ledger
- LogFailureTests
- options
- hooks
- Services object (services.llm(name))
- DatabaseTestCase
- config.example.yaml
- Application
- SourceItemData
- EmbeddingGroupingTests
- Framework Usage
- newstool
- Processor
- El Periódico Mediterráneo
- feedreader.py
- ProcessingScope
- deliveries table (the ledger)
- PluginFailure
- Schedule
- Item
- FileSinkTests
- .commit_app_run
- BaseProcessor
- Example sources (prensaiberica_plain, castelloninformacion, plaza, theguardian)
- Artifact
- Grouping notes: NLP clustering pipeline
- 0011: Environment overrides, relative paths and one storage directory
- DocumentFilter
- foundation internal library
- 0018: Annotations hold their run state; a content change deletes them
- app.py
- workflows
- TestSourceItemDataContent
- .settings_customise_sources
- LogLevelTests
- ClassRegister
- Database
- Decision
- .__init__
- Config
- ollama_url
- ADR 0002 Processing state lifecycle
- db.py
- AppletRun
- 0016: Routes on re-emission, manual queueing and pacing overrides

## God Nodes (most connected - your core abstractions)
1. `SourceItem` - 107 edges
2. `Database` - 95 edges
3. `Application` - 93 edges
4. `Services` - 92 edges
5. `PluginFailure` - 72 edges
6. `SourceData` - 72 edges
7. `Document` - 72 edges
8. `ApplicationTests` - 70 edges
9. `SourceItemData` - 56 edges
10. `ProcessingScope` - 53 edges

## Surprising Connections (you probably didn't know these)
- `Reading` --references--> `AppletReader`  [INFERRED]
  docs/decisions/0015-applets-documents-and-routes.md → newstool/applets.py
- `Decision` --references--> `Config`  [INFERRED]
  docs/decisions/0011-environment-overrides-and-storage-dir.md → newstool/config.py
- `Decision` --references--> `Database`  [INFERRED]
  docs/decisions/0018-annotations-hold-their-run-state.md → newstool/db.py
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

## Communities (89 total, 28 thin omitted)

### Community 0 - "make_item"
Cohesion: 0.21
Nodes (4): ContentStorageTests, make_item(), make_source(), UpsertSourceItemsTests

### Community 1 - "catalog.py"
Cohesion: 0.06
Nodes (13): Catalog, check_section(), ids_of(), in_default(), Kind, process_key(), Profile, Run (+5 more)

### Community 2 - "Services"
Cohesion: 0.05
Nodes (24): Decision, LLM, LLMType, LLMUnavailableError, strip_code_fence(), EmbedOptions, __newstool_plugin__(), Services (+16 more)

### Community 3 - "ApplicationTests"
Cohesion: 0.06
Nodes (9): LockedError, write_lock(), ApplicationTests, retrieve(), retrieve_published(), retrieve(), same(), listed() (+1 more)

### Community 5 - "invoke"
Cohesion: 0.06
Nodes (9): AppReport, DeleteSummary, MarkSummary, RunSummary, annotation(), CommandTests, ExternalErrorTests, InspectCommandTests (+1 more)

### Community 6 - ".from_text"
Cohesion: 0.07
Nodes (3): AliasTests, ConfigTests, EnvironmentOverrideTests

### Community 7 - "Entry"
Cohesion: 0.09
Nodes (4): AppEntry, Entry, LLMEntry, SinkEntry

### Community 8 - "Database (db.py, only SQLite/storage access)"
Cohesion: 0.17
Nodes (11): pre-commit config, ruff-check and ruff-format hooks, newsmerger CLAUDE.md agent guidelines, DTO/ORM from_dto/to_dto/update convention, Consumer-side Protocol decoupling convention, AUTOINCREMENT integer ids, Database (db.py, only SQLite/storage access), foundation.storage.DiskStorage content-addressed storage (+3 more)

### Community 9 - "StubLLM"
Cohesion: 0.08
Nodes (7): tags_prompt(), Processor, EmbedTests, ProcessorTestCase, StubLLM, SummarizeTests, TaggerTests

### Community 11 - "SourceItem"
Cohesion: 0.13
Nodes (5): AppletReader, SourceItem, FeedApplet, tagged_items(), ItemFeedApplet

### Community 12 - "PreflightSourceItemData"
Cohesion: 0.13
Nodes (6): PreflightSourceItemData, CSJuntasGobiernoProvider, PreparseData, PreflightProvider, Provider, TestCSJuntasGobierno

### Community 15 - "TelegramSinkTests"
Cohesion: 0.24
Nodes (6): Schedule, item_document(), ok_response(), options(), sink(), TelegramSinkTests

### Community 17 - "test_providers.py"
Cohesion: 0.10
Nodes (13): Options, merge_options(), NoOptions, PluginOptions, Options, is_home_page(), Options, parse_article() (+5 more)

### Community 18 - "Document"
Cohesion: 0.17
Nodes (4): Document, StdoutSink, Sink, StdoutSinkTests

### Community 19 - "DigestApplet"
Cohesion: 0.16
Nodes (5): DigestApplet, DigestOptions, DigestAppletTests, DigestPluginTests, factory()

### Community 20 - "EmittedDocument"
Cohesion: 0.26
Nodes (4): check_result(), EmittedDocument, CheckResultTests, ReaderTests

### Community 22 - "test_db.py"
Cohesion: 0.17
Nodes (6): DBItemAnnotation, next_annotation(), ProcessingStatus, Annotation, DeleteTests, NextAnnotationTests

### Community 23 - "describe"
Cohesion: 0.07
Nodes (16): apps_phase(), deliver_each(), delivery_phase(), failed_report(), failed_summary(), format_time(), import_sources(), import_failed() (+8 more)

### Community 24 - "Delivery"
Cohesion: 0.07
Nodes (12): backoff_seconds(), DBDelivery, Delivery, Deliverer, DeliveryTests, CommitTests, DelivererTests, run() (+4 more)

### Community 25 - "DocumentTests"
Cohesion: 0.27
Nodes (3): DBDocument, DocumentTests, keys()

### Community 26 - "ProcessingTests"
Cohesion: 0.16
Nodes (7): 0012: Delivery ids, changing their state and forced send, Consequences, Context, Decision, Rejected options, Deliveries, ProcessingTests

### Community 27 - "OllamaLLM"
Cohesion: 0.21
Nodes (5): __newstool_plugin__(), ollama_client(), OllamaLLM, Options, OllamaTests

### Community 29 - "chat_image_url"
Cohesion: 0.25
Nodes (3): build_card(), chat_image_url(), ChatImageUrlTests

### Community 30 - "grouping.py"
Cohesion: 0.09
Nodes (20): Requirements, average_between(), average_link_cluster(), AverageLinkApplet, build_score_matrix(), cosine_similarity(), EmbeddingsApplet, EmbeddingsOptions (+12 more)

### Community 31 - "cli.py"
Cohesion: 0.06
Nodes (23): apps_group(), cli(), delete_group(), deliveries_group(), describe_schedule(), format_seconds(), format_value(), inspect_apps_cmd() (+15 more)

### Community 32 - "TelegramSink"
Cohesion: 0.18
Nodes (4): build_caption(), post(), TelegramSink, BuildCaptionTests

### Community 33 - ".add_items"
Cohesion: 0.21
Nodes (4): ItemFeedOptions, AppletTestCase, GroupingTests, ItemFeedTests

### Community 34 - "plugins"
Cohesion: 0.12
Nodes (17): lookback, title, url, api_base, chat_model, embed_model, plugins, digest (+9 more)

### Community 35 - ".summary"
Cohesion: 0.07
Nodes (22): 0009: Workflows and keyed entries, Consequences, Context, Decision, Rejected options, 0010: Plugin classes and the configuration catalog, Consequences, Context (+14 more)

### Community 36 - "GoogleChatSink"
Cohesion: 0.16
Nodes (5): GoogleChatSink, __newstool_plugin__(), WebhookOptions, OptionsTests, webhook_options()

### Community 38 - "app_from_context"
Cohesion: 0.11
Nodes (13): app_from_context(), apps_reset_cmd(), apps_run_cmd(), deliver_cmd(), deliveries_rename_cmd(), import_cmd(), inspect_content_cmd(), process_cmd() (+5 more)

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

### Community 44 - "DatabaseTestCase"
Cohesion: 0.20
Nodes (4): ConnectionTests, ContentChangeTests, DatabaseTestCase, IdentityTests

### Community 45 - "config.example.yaml"
Cohesion: 0.11
Nodes (15): cache, expiration, llms, input, processors, options, processor, remixers (+7 more)

### Community 46 - "Application"
Cohesion: 0.05
Nodes (10): Application, AppStatus, lookup(), workflow_scope(), AppInstance, process_workflow(), selected_sinks(), workflow_phases() (+2 more)

### Community 48 - "SourceItemData"
Cohesion: 0.09
Nodes (6): SourceItemData, _extract_href(), _get_modified_at(), PrensaIbericaProvider, read_sample(), TestPrensaIberica

### Community 51 - "Framework Usage"
Cohesion: 0.50
Nodes (3): Additional Approved Packages, Framework Usage, newstool Python Specifics

### Community 54 - "Processor"
Cohesion: 0.29
Nodes (6): UnavailableProcessor / UnavailableRemixer / UnavailableSink, Annotation, Delivery, Exponential backoff 60s*2^(n-1), capped 24h, max_retries, Processor, Sink

### Community 55 - "El Periódico Mediterráneo"
Cohesion: 0.43
Nodes (7): El Periódico Mediterráneo, Prensa Ibérica article HTML format (og:/article: meta tags), Telegram t.me/s channel preview HTML (tgme_widget_message, data-post), El eco perdido de las fiestas de julio nacidas del asedio carlista sobre Castellón (sample article), El Grau se vuelca en las fiestas de la Virgen del Carmen (sample article), Castellón apoya a la selección española desde la plaza Mayor (sample article), Telegram channel mediterraneoelperiodico (sample web preview)

### Community 56 - "feedreader.py"
Cohesion: 0.14
Nodes (10): HTTPClient, discover_feed_url(), entry_date(), FeedReaderProvider, fetch_article(), fetch_feed(), find_image(), parse_entry() (+2 more)

### Community 57 - "ProcessingScope"
Cohesion: 0.33
Nodes (3): wrapper(), ProcessingScope, GetItemsTests

### Community 58 - "deliveries table (the ledger)"
Cohesion: 0.33
Nodes (4): BaseSink deliver cycle (queue, select, send), deliveries table (the ledger), ADR 0005 Remixers with external side effects, Strict FIFO per source

### Community 59 - "PluginFailure"
Cohesion: 0.06
Nodes (21): PluginFailure, SourceData, CastellonInformacionProvider, __newstool_plugin__(), find_parent_by_tag_name(), get_date_from_text(), __newstool_plugin__(), __newstool_plugin__() (+13 more)

### Community 61 - "Item"
Cohesion: 0.40
Nodes (3): IndexSiteProvider / URLProvider, Item, Provider

### Community 64 - "FileSinkTests"
Cohesion: 0.17
Nodes (3): FileOptions, FileSink, FileSinkTests

### Community 66 - "BaseProcessor"
Cohesion: 0.06
Nodes (14): 0013: Plugin services at init, Consequences, Context, Decision, Rejected options, EmbedProcessor, tags_text(), MarkdownifyProcessor (+6 more)

### Community 71 - "0011: Environment overrides, relative paths and one storage directory"
Cohesion: 0.40
Nodes (4): 0011: Environment overrides, relative paths and one storage directory, Consequences, Context, Decision

### Community 72 - "DocumentFilter"
Cohesion: 0.08
Nodes (25): annotation_options(), check_all_rows(), check_found(), delete_annotations_cmd(), delete_deliveries_cmd(), delete_documents_cmd(), delete_items_cmd(), deliveries_send_cmd() (+17 more)

### Community 73 - "foundation internal library"
Cohesion: 0.29
Nodes (7): foundation internal library, foundation.plugin.Register plugin loading, __newsmerger_plugin__(services, **options) entry point, PluginOptions (pydantic, unknown keys rejected), plugins configuration section, P1: plain logging and <APP>_LOG_LEVEL fix, P2: rich progress per stream (RICH_STDOUT_*/RICH_STDERR_*)

### Community 74 - "0018: Annotations hold their run state; a content change deletes them"
Cohesion: 0.40
Nodes (4): 0018: Annotations hold their run state; a content change deletes them, Consequences, Context, Decision

### Community 75 - "app.py"
Cohesion: 0.06
Nodes (13): Sinks, Alias, CacheConfig, reason(), __newstool_plugin__(), __newstool_plugin__(), __newstool_plugin__(), TelegramOptions (+5 more)

### Community 76 - "workflows"
Cohesion: 0.33
Nodes (6): sink, workflows, deliver, name, process, sources

### Community 79 - ".settings_customise_sources"
Cohesion: 0.10
Nodes (6): EnvAliasSource, load_context(), LoadContext, LoadEnvSettingsSource, parse_duration(), resolve_config_path()

### Community 85 - "Decision"
Cohesion: 0.12
Nodes (13): 0015: Applets, emitted documents and routes, CLI, Consequences, Context, Decision, Documents, Migration, Plugins (+5 more)

### Community 92 - "Config"
Cohesion: 0.10
Nodes (4): Database & ORM Conventions, DTO, Protocol & ORM Implementation Reference, Config, DirectoryTests

### Community 98 - "db.py"
Cohesion: 0.12
Nodes (4): Base, DBSource, DBSourceItem, _sha256_column()

### Community 99 - "AppletRun"
Cohesion: 0.08
Nodes (16): Applets, Applet, AppletType, BaseApplet, run_key(), SourcesOptions, DBApp, AppletResult (+8 more)

### Community 106 - "0016: Routes on re-emission, manual queueing and pacing overrides"
Cohesion: 0.33
Nodes (5): 0016: Routes on re-emission, manual queueing and pacing overrides, Consequences, Context, Decision, Rejected options

## Knowledge Gaps
- **13 isolated node(s):** `newstool`, `External pipelines (scripts/pipeline_url.py)`, `Annotation`, `Telegram t.me/s channel preview HTML (tgme_widget_message, data-post)`, `IndexSiteProvider / URLProvider` (+8 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 603 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **28 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Application` connect `Application` to `catalog.py`, `Services`, `ApplicationTests`, `invoke`, `.from_text`, `StubLLM`, `.record_result`, `SourceItem`, `PreflightSourceItemData`, `Document`, `test_db.py`, `describe`, `Delivery`, `cli.py`, `.summary`, `app_from_context`, `.delete_documents`, `SourceItemData`, `feedreader.py`, `ProcessingScope`, `PluginFailure`, `.session_scope`, `BaseProcessor`, `DocumentFilter`, `app.py`, `Database`, `.get_content`, `Config`, `AppletRun`?**
  _High betweenness centrality (0.115) - this node is a cross-community bridge._
- **Are the 30 inferred relationships involving `SourceItem` (e.g. with `Application` and `AppletReader`) actually correct?**
  _`SourceItem` has 30 INFERRED edges - model-reasoned connections that need verification._
- **What connects `newstool`, `External pipelines (scripts/pipeline_url.py)`, `Annotation` to the rest of the system?**
  _13 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `catalog.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06349206349206349 - nodes in this community are weakly interconnected._
- **Why does `SourceItem` connect `SourceItem` to `make_item`, `Services`, `ApplicationTests`, `invoke`, `StubLLM`, `.record_result`, `DeleteCommandTests`, `DigestApplet`, `datetime`, `test_db.py`, `grouping.py`, `cli.py`, `.add_items`, `.summary`, `AnnotationTests`, `Application`, `SourceItemData`, `PluginFailure`, `BaseProcessor`, `app.py`, `Database`, `.get_content`, `db.py`, `AppletRun`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **Are the 23 inferred relationships involving `Database` (e.g. with `Context` and `Decision`) actually correct?**
  _`Database` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Should `Services` be split into smaller, more focused modules?**
  _Cohesion score 0.0493221131369799 - nodes in this community are weakly interconnected._