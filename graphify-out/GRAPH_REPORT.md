# Graph Report - private-migration  (2026-11-11)

## Corpus Check
- 80 files · ~192,942 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 4, .lock 1)

## Summary
- 2001 nodes · 5460 edges · 95 communities (64 shown, 31 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 678 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `df054212`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- make_item
- Catalog
- Services
- ApplicationTests
- DocumentFilter
- invoke
- .from_text
- Entry
- Database (db.py, only SQLite/storage access)
- StubLLM
- Database
- SourceItem
- test_providers.py
- DeliveryStatus
- expand_variables
- TelegramSinkTests
- TestFeedReader
- PluginFailure
- Sink
- .feed
- ItemFeedApplet
- datetime
- test_db.py
- describe
- DelivererTests
- Document
- ProcessingTests
- OllamaLLM
- Delivery
- ._profile
- grouping.py
- cli.py
- build_caption
- .add_items
- plugins
- .summary
- GoogleChatSinkTests
- AnnotationTests
- apps_run_cmd
- ADR 0007 Sinks and the delivery ledger
- LogFailureTests
- options
- hooks
- Services object (services.llm(name))
- DatabaseTestCase
- config.example.yaml
- Application
- ConfigError
- SourceItemData
- SinkOptions
- model_validator
- AppletRun
- newstool
- Processor
- El Periódico Mediterráneo
- HTTPClient
- ProcessingScope
- deliveries table (the ledger)
- feedreader.py
- Schedule
- Item
- catalog.py
- FileSinkTests
- .commit_app_run
- BaseProcessor
- Example sources (prensaiberica_plain, castelloninformacion, plaza, theguardian)
- .content_dir
- Artifact
- Grouping notes: NLP clustering pipeline
- 0011: Environment overrides, relative paths and one storage directory
- app_from_context
- foundation internal library
- 0018: Annotations hold their run state; a content change deletes them
- app.py
- workflows
- TestSourceItemDataContent
- .settings_customise_sources
- LogLevelTests
- .from_file
- MarkdownifyProcessor
- .digest
- .__init__
- DeliveryTests
- accepts
- Config
- AliasTests
- ADR 0002 Processing state lifecycle
- DBSourceItem
- AppletResult
- 0016: Routes on re-emission, manual queueing and pacing overrides

## God Nodes (most connected - your core abstractions)
1. `SourceItem` - 106 edges
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

## Communities (95 total, 31 thin omitted)

### Community 0 - "make_item"
Cohesion: 0.21
Nodes (4): ContentStorageTests, make_item(), make_source(), UpsertSourceItemsTests

### Community 1 - "Catalog"
Cohesion: 0.14
Nodes (3): Catalog, Run, share_sources()

### Community 2 - "Services"
Cohesion: 0.05
Nodes (23): Decision, LLM, LLMType, LLMUnavailableError, strip_code_fence(), __newstool_plugin__(), ClassRegister, Services (+15 more)

### Community 3 - "ApplicationTests"
Cohesion: 0.06
Nodes (9): LockedError, write_lock(), ApplicationTests, retrieve(), retrieve_published(), retrieve(), same(), listed() (+1 more)

### Community 4 - "DocumentFilter"
Cohesion: 0.10
Nodes (8): check_all_rows(), delivery_filters(), document_options(), wrapper(), wrapper(), selection_options(), decorate(), DocumentFilter

### Community 5 - "invoke"
Cohesion: 0.06
Nodes (9): AppReport, DeleteSummary, MarkSummary, RunSummary, annotation(), CommandTests, ExternalErrorTests, InspectCommandTests (+1 more)

### Community 7 - "Entry"
Cohesion: 0.17
Nodes (3): AppEntry, Entry, SinkEntry

### Community 8 - "Database (db.py, only SQLite/storage access)"
Cohesion: 0.17
Nodes (11): pre-commit config, ruff-check and ruff-format hooks, newsmerger CLAUDE.md agent guidelines, DTO/ORM from_dto/to_dto/update convention, Consumer-side Protocol decoupling convention, AUTOINCREMENT integer ids, Database (db.py, only SQLite/storage access), foundation.storage.DiskStorage content-addressed storage (+3 more)

### Community 9 - "StubLLM"
Cohesion: 0.11
Nodes (6): Processor, EmbedTests, ProcessorTestCase, StubLLM, SummarizeTests, TaggerTests

### Community 11 - "SourceItem"
Cohesion: 0.12
Nodes (6): AppletReader, run_key(), SourceItem, DigestApplet, FeedApplet, tagged_items()

### Community 12 - "test_providers.py"
Cohesion: 0.13
Nodes (11): CSJuntasGobiernoProvider, find_parent_by_tag_name(), get_date_from_text(), PreparseData, Options, merge_options(), NoOptions, PluginOptions (+3 more)

### Community 15 - "TelegramSinkTests"
Cohesion: 0.22
Nodes (8): Schedule, TelegramSink, run(), item_document(), ok_response(), options(), sink(), TelegramSinkTests

### Community 17 - "PluginFailure"
Cohesion: 0.06
Nodes (17): PluginFailure, SourceData, CastellonInformacionProvider, select_article(), get_section(), parse_datetime(), PlazaProvider, is_home_page() (+9 more)

### Community 19 - ".feed"
Cohesion: 0.15
Nodes (7): SourcesOptions, DigestOptions, __newstool_plugin__(), Options, FeedTests, DigestPluginTests, factory()

### Community 21 - "datetime"
Cohesion: 0.10
Nodes (3): CustomJSON, _encode_value(), UTCDateTime

### Community 22 - "test_db.py"
Cohesion: 0.17
Nodes (6): DBItemAnnotation, next_annotation(), ProcessingStatus, Annotation, DeleteTests, NextAnnotationTests

### Community 23 - "describe"
Cohesion: 0.10
Nodes (9): failed_report(), failed_summary(), import_sources(), import_failed(), process_workflow(), run_each(), describe(), log_failure() (+1 more)

### Community 24 - "DelivererTests"
Cohesion: 0.17
Nodes (5): CommitTests, DelivererTests, DeliveryOrderTests, LedgerTestCase, RecordingSink

### Community 25 - "Document"
Cohesion: 0.14
Nodes (5): DBDocument, Document, FileSink, DocumentTests, keys()

### Community 26 - "ProcessingTests"
Cohesion: 0.16
Nodes (7): 0012: Delivery ids, changing their state and forced send, Consequences, Context, Decision, Rejected options, Deliveries, ProcessingTests

### Community 27 - "OllamaLLM"
Cohesion: 0.21
Nodes (5): __newstool_plugin__(), ollama_client(), OllamaLLM, Options, OllamaTests

### Community 28 - "Delivery"
Cohesion: 0.14
Nodes (4): backoff_seconds(), DBDelivery, Delivery, Deliverer

### Community 30 - "grouping.py"
Cohesion: 0.09
Nodes (20): Requirements, average_between(), average_link_cluster(), AverageLinkApplet, build_score_matrix(), cosine_similarity(), EmbeddingsApplet, EmbeddingsOptions (+12 more)

### Community 31 - "cli.py"
Cohesion: 0.05
Nodes (22): Additional Approved Packages, Framework Usage, newstool Python Specifics, apps_group(), cli(), delete_group(), deliveries_group(), describe_schedule() (+14 more)

### Community 32 - "build_caption"
Cohesion: 0.15
Nodes (3): build_caption(), post(), BuildCaptionTests

### Community 33 - ".add_items"
Cohesion: 0.17
Nodes (5): ItemFeedOptions, AppletTestCase, EmbeddingGroupingTests, GroupingTests, ItemFeedTests

### Community 34 - "plugins"
Cohesion: 0.12
Nodes (17): lookback, title, url, api_base, chat_model, embed_model, plugins, digest (+9 more)

### Community 35 - ".summary"
Cohesion: 0.07
Nodes (22): 0009: Workflows and keyed entries, Consequences, Context, Decision, Rejected options, 0010: Plugin classes and the configuration catalog, Consequences, Context (+14 more)

### Community 36 - "GoogleChatSinkTests"
Cohesion: 0.09
Nodes (10): build_card(), chat_image_url(), GoogleChatSink, __newstool_plugin__(), WebhookOptions, card_widgets(), ChatImageUrlTests, GoogleChatSinkTests (+2 more)

### Community 38 - "apps_run_cmd"
Cohesion: 0.09
Nodes (15): apps_run_cmd(), import_cmd(), phase_title(), print_import(), print_process(), process_cmd(), progress_rows(), routed_from() (+7 more)

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
Cohesion: 0.19
Nodes (4): ConnectionTests, ContentChangeTests, DatabaseTestCase, IdentityTests

### Community 45 - "config.example.yaml"
Cohesion: 0.11
Nodes (15): cache, expiration, llms, input, processors, options, processor, remixers (+7 more)

### Community 46 - "Application"
Cohesion: 0.04
Nodes (12): Application, AppStatus, lookup(), workflow_scope(), AppInstance, apps_phase(), deliver_each(), delivery_phase() (+4 more)

### Community 47 - "ConfigError"
Cohesion: 0.18
Nodes (3): check_section(), ConfigError, options_error()

### Community 48 - "SourceItemData"
Cohesion: 0.08
Nodes (8): PreflightSourceItemData, SourceItemData, _extract_href(), PrensaIbericaProvider, PreflightProvider, Provider, read_sample(), TestPrensaIberica

### Community 50 - "SinkOptions"
Cohesion: 0.24
Nodes (4): __newstool_plugin__(), StdoutSink, SinkOptions, StdoutSinkTests

### Community 52 - "AppletRun"
Cohesion: 0.13
Nodes (5): Applets, Applet, BaseApplet, DBApp, AppletRun

### Community 54 - "Processor"
Cohesion: 0.29
Nodes (6): UnavailableProcessor / UnavailableRemixer / UnavailableSink, Annotation, Delivery, Exponential backoff 60s*2^(n-1), capped 24h, max_retries, Processor, Sink

### Community 55 - "El Periódico Mediterráneo"
Cohesion: 0.43
Nodes (7): El Periódico Mediterráneo, Prensa Ibérica article HTML format (og:/article: meta tags), Telegram t.me/s channel preview HTML (tgme_widget_message, data-post), El eco perdido de las fiestas de julio nacidas del asedio carlista sobre Castellón (sample article), El Grau se vuelca en las fiestas de la Virgen del Carmen (sample article), Castellón apoya a la selección española desde la plaza Mayor (sample article), Telegram channel mediterraneoelperiodico (sample web preview)

### Community 56 - "HTTPClient"
Cohesion: 0.17
Nodes (6): HTTPClient, discover_feed_url(), FeedReaderProvider, fetch_article(), fetch_feed(), TestHTTPClient

### Community 57 - "ProcessingScope"
Cohesion: 0.33
Nodes (3): wrapper(), ProcessingScope, GetItemsTests

### Community 58 - "deliveries table (the ledger)"
Cohesion: 0.33
Nodes (4): BaseSink deliver cycle (queue, select, send), deliveries table (the ledger), ADR 0005 Remixers with external side effects, Strict FIFO per source

### Community 59 - "feedreader.py"
Cohesion: 0.11
Nodes (13): __newstool_plugin__(), __newstool_plugin__(), entry_date(), find_image(), __newstool_plugin__(), parse_entry(), __newstool_plugin__(), _get_modified_at() (+5 more)

### Community 61 - "Item"
Cohesion: 0.40
Nodes (3): IndexSiteProvider / URLProvider, Item, Provider

### Community 63 - "catalog.py"
Cohesion: 0.20
Nodes (5): ids_of(), in_default(), process_key(), Use, ProcessEntry

### Community 66 - "BaseProcessor"
Cohesion: 0.08
Nodes (10): 0013: Plugin services at init, Consequences, Context, Decision, Rejected options, EmbedOptions, EmbedProcessor, tags_text() (+2 more)

### Community 68 - ".content_dir"
Cohesion: 0.29
Nodes (3): Database & ORM Conventions, DTO, Protocol & ORM Implementation Reference, resolve_config_path()

### Community 71 - "0011: Environment overrides, relative paths and one storage directory"
Cohesion: 0.40
Nodes (4): 0011: Environment overrides, relative paths and one storage directory, Consequences, Context, Decision

### Community 72 - "app_from_context"
Cohesion: 0.10
Nodes (25): annotation_options(), app_from_context(), apps_reset_cmd(), check_found(), delete_annotations_cmd(), delete_deliveries_cmd(), delete_documents_cmd(), delete_items_cmd() (+17 more)

### Community 73 - "foundation internal library"
Cohesion: 0.29
Nodes (7): foundation internal library, foundation.plugin.Register plugin loading, __newsmerger_plugin__(services, **options) entry point, PluginOptions (pydantic, unknown keys rejected), plugins configuration section, P1: plain logging and <APP>_LOG_LEVEL fix, P2: rich progress per stream (RICH_STDOUT_*/RICH_STDERR_*)

### Community 74 - "0018: Annotations hold their run state; a content change deletes them"
Cohesion: 0.40
Nodes (4): 0018: Annotations hold their run state; a content change deletes them, Consequences, Context, Decision

### Community 75 - "app.py"
Cohesion: 0.06
Nodes (9): Alias, CacheConfig, _sha256_column(), reason(), __newstool_plugin__(), __newstool_plugin__(), TelegramOptions, SinkType (+1 more)

### Community 76 - "workflows"
Cohesion: 0.33
Nodes (6): sink, workflows, deliver, name, process, sources

### Community 79 - ".settings_customise_sources"
Cohesion: 0.12
Nodes (5): EnvAliasSource, load_context(), LoadContext, LoadEnvSettingsSource, parse_duration()

### Community 83 - "MarkdownifyProcessor"
Cohesion: 0.16
Nodes (5): MarkdownifyProcessor, SkipItem, ClassRegisterTests, make_pdf(), MarkdownifyPdfTests

### Community 85 - ".digest"
Cohesion: 0.13
Nodes (12): 0015: Applets, emitted documents and routes, CLI, Consequences, Context, Decision, Documents, Migration, Plugins (+4 more)

### Community 90 - "accepts"
Cohesion: 0.33
Nodes (3): Routes, accepts(), AcceptsTests

### Community 98 - "DBSourceItem"
Cohesion: 0.18
Nodes (3): Base, DBSource, DBSourceItem

### Community 99 - "AppletResult"
Cohesion: 0.11
Nodes (12): AppletType, check_result(), AppletResult, EmittedDocument, __newstool_plugin__(), __newstool_plugin__(), __newstool_plugin__(), CheckResultTests (+4 more)

### Community 106 - "0016: Routes on re-emission, manual queueing and pacing overrides"
Cohesion: 0.33
Nodes (5): 0016: Routes on re-emission, manual queueing and pacing overrides, Consequences, Context, Decision, Rejected options

## Knowledge Gaps
- **13 isolated node(s):** `newstool`, `External pipelines (scripts/pipeline_url.py)`, `Annotation`, `Telegram t.me/s channel preview HTML (tgme_widget_message, data-post)`, `IndexSiteProvider / URLProvider` (+8 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 600 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **31 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Application` connect `Application` to `Catalog`, `Services`, `ApplicationTests`, `DocumentFilter`, `invoke`, `.from_text`, `Database`, `SourceItem`, `DeliveryStatus`, `PluginFailure`, `test_db.py`, `describe`, `Document`, `Delivery`, `._profile`, `cli.py`, `.summary`, `apps_run_cmd`, `ConfigError`, `SourceItemData`, `AppletRun`, `HTTPClient`, `ProcessingScope`, `.rename_sink`, `BaseProcessor`, `app_from_context`, `app.py`, `.close`, `.from_file`, `.get_content`, `Config`?**
  _High betweenness centrality (0.123) - this node is a cross-community bridge._
- **Are the 29 inferred relationships involving `SourceItem` (e.g. with `Application` and `AppletReader`) actually correct?**
  _`SourceItem` has 29 INFERRED edges - model-reasoned connections that need verification._
- **What connects `newstool`, `External pipelines (scripts/pipeline_url.py)`, `Annotation` to the rest of the system?**
  _13 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Catalog` be split into smaller, more focused modules?**
  _Cohesion score 0.1380952380952381 - nodes in this community are weakly interconnected._
- **Why does `Database` connect `Database` to `make_item`, `Services`, `DocumentFilter`, `StubLLM`, `SourceItem`, `DeliveryStatus`, `PluginFailure`, `Sink`, `datetime`, `test_db.py`, `DelivererTests`, `Document`, `Delivery`, `build_caption`, `.add_items`, `.summary`, `DatabaseTestCase`, `Application`, `AppletRun`, `ProcessingScope`, `.rename_sink`, `.commit_app_run`, `BaseProcessor`, `0018: Annotations hold their run state; a content change deletes them`, `app.py`, `.get_unprocessed_items`, `.digest`, `.__init__`, `.get_content`, `Config`, `AppletResult`?**
  _High betweenness centrality (0.090) - this node is a cross-community bridge._
- **Are the 23 inferred relationships involving `Database` (e.g. with `Context` and `Decision`) actually correct?**
  _`Database` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Should `Services` be split into smaller, more focused modules?**
  _Cohesion score 0.049367088607594936 - nodes in this community are weakly interconnected._