# Graph Report - digest-plan  (2026-11-11)

## Corpus Check
- 81 files · ~194,829 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 4, .lock 1)

## Summary
- 2024 nodes · 5545 edges · 105 communities (70 shown, 35 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 686 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `253d9718`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- make_item
- catalog.py
- Services
- ApplicationTests
- scope_options
- invoke
- .from_text
- Entry
- Database (db.py, only SQLite/storage access)
- StubLLM
- SourceItem
- ItemFeedApplet
- PreflightSourceItemData
- DeleteCommandTests
- ConfigError
- TelegramSinkTests
- TestFeedReader
- AppletReader
- Document
- .digest
- AppletResult
- datetime
- test_db.py
- describe
- Delivery
- InspectCommandTests
- ProcessingTests
- Services
- Deliverer
- ExternalErrorTests
- grouping.py
- cli.py
- build_caption
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
- SourceItemData
- EmbeddingGroupingTests
- Framework Usage
- SourceData
- newstool
- Processor
- El Periódico Mediterráneo
- feedreader.py
- ProcessingScope
- deliveries table (the ledger)
- PluginFailure
- AppletRun
- Item
- AppletRun
- inspect_annotations_cmd
- FileSinkTests
- Delivery
- MarkdownifyProcessor
- Example sources (prensaiberica_plain, castelloninformacion, plaza, theguardian)
- feed.py
- Artifact
- Grouping notes: NLP clustering pipeline
- 0011: Environment overrides, relative paths and one storage directory
- DeliveryTests
- foundation internal library
- 0018: Annotations hold their run state; a content change deletes them
- app.py
- workflows
- .from_file
- TestSourceItemDataContent
- .settings_customise_sources
- LogLevelTests
- errors.py
- CSJuntasGobiernoProvider
- Base
- Decision
- .__init__
- PacingOverride
- ._find_excluded_containers
- parse_entry
- describe
- .delete_documents
- Config
- ADR 0002 Processing state lifecycle
- DocumentFilter
- AppletType
- test_markdownify.py
- 0012: Delivery ids, changing their state and forced send
- .key
- 0016: Routes on re-emission, manual queueing and pacing overrides
- SinkOptions
- 0010: Plugin classes and the configuration catalog

## God Nodes (most connected - your core abstractions)
1. `SourceItem` - 110 edges
2. `Database` - 95 edges
3. `Services` - 95 edges
4. `Application` - 93 edges
5. `PluginFailure` - 78 edges
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
- `Routes` --references--> `accepts()`  [INFERRED]
  docs/decisions/0015-applets-documents-and-routes.md → newstool/sinks.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **markdownify -> summarize/tagger -> embed -> grouping data chain** — docs_architecture_markdownify_processor, docs_architecture_summarize_processor, docs_architecture_tagger_processor, docs_architecture_embed_processor, docs_architecture_grouping_remixers [EXTRACTED 1.00]
- **Plugin protocol types consumed by the core** — docs_specification_provider, docs_specification_processor, docs_specification_remixer, docs_specification_sink, docs_decisions_0006_llm_plugins_llm_protocol [EXTRACTED 1.00]
- **Delivery ledger mechanism** — docs_architecture_deliveries_table, docs_decisions_0007_sinks_and_delivery_ledger_delivery_states, docs_architecture_basesink_cycle, docs_decisions_0007_sinks_and_delivery_ledger_strict_fifo_per_source, docs_decisions_0007_sinks_and_delivery_ledger_lookback_window, docs_specification_write_lock [INFERRED 0.85]
- **Prensa Ibérica sample article fixtures (El Periódico Mediterráneo, July 2026)** — tests_samples_prensaiberica_item_132310503_article, tests_samples_prensaiberica_item_132340038_article, tests_samples_prensaiberica_item_132344288_article [INFERRED 0.95]

## Communities (105 total, 35 thin omitted)

### Community 0 - "make_item"
Cohesion: 0.22
Nodes (4): ContentStorageTests, make_item(), make_source(), UpsertSourceItemsTests

### Community 1 - "catalog.py"
Cohesion: 0.09
Nodes (8): Catalog, ids_of(), in_default(), Kind, process_key(), Profile, Use, ProcessEntry

### Community 2 - "Services"
Cohesion: 0.05
Nodes (22): Decision, classify_prompt(), ClassifyOptions, known_labels(), __newstool_plugin__(), EmbedOptions, EmbedProcessor, __newstool_plugin__() (+14 more)

### Community 3 - "ApplicationTests"
Cohesion: 0.06
Nodes (9): LockedError, write_lock(), ApplicationTests, retrieve(), retrieve_published(), retrieve(), same(), listed() (+1 more)

### Community 4 - "scope_options"
Cohesion: 0.20
Nodes (7): annotation_options(), delivery_options(), document_options(), wrapper(), scope_options(), selection_options(), decorate()

### Community 5 - "invoke"
Cohesion: 0.14
Nodes (4): AppReport, RunSummary, CommandTests, invoke()

### Community 6 - ".from_text"
Cohesion: 0.09
Nodes (3): ollama_url(), AliasTests, ConfigTests

### Community 7 - "Entry"
Cohesion: 0.10
Nodes (4): AppEntry, Entry, LLMEntry, SinkEntry

### Community 8 - "Database (db.py, only SQLite/storage access)"
Cohesion: 0.17
Nodes (11): pre-commit config, ruff-check and ruff-format hooks, newsmerger CLAUDE.md agent guidelines, DTO/ORM from_dto/to_dto/update convention, Consumer-side Protocol decoupling convention, AUTOINCREMENT integer ids, Database (db.py, only SQLite/storage access), foundation.storage.DiskStorage content-addressed storage (+3 more)

### Community 9 - "StubLLM"
Cohesion: 0.14
Nodes (7): Processor, ClassifyTests, EmbedTests, ProcessorTestCase, StubLLM, SummarizeTests, TaggerTests

### Community 12 - "PreflightSourceItemData"
Cohesion: 0.16
Nodes (3): PreflightSourceItemData, PreflightProvider, Provider

### Community 14 - "ConfigError"
Cohesion: 0.07
Nodes (7): check_section(), Run, share_sources(), ConfigError, expand_variables(), MissingVariableError, options_error()

### Community 15 - "TelegramSinkTests"
Cohesion: 0.22
Nodes (7): Schedule, run(), item_document(), ok_response(), options(), sink(), TelegramSinkTests

### Community 17 - "AppletReader"
Cohesion: 0.13
Nodes (3): AppletReader, DigestApplet, tagged_items()

### Community 18 - "Document"
Cohesion: 0.12
Nodes (5): CommittedRun, DBDocument, Document, post(), TelegramSink

### Community 20 - "AppletResult"
Cohesion: 0.13
Nodes (9): check_result(), AppletResult, EmittedDocument, CheckResultTests, ReaderTests, DocumentTests, keys(), JSONColumnTests (+1 more)

### Community 21 - "datetime"
Cohesion: 0.09
Nodes (3): CustomJSON, _encode_value(), UTCDateTime

### Community 22 - "test_db.py"
Cohesion: 0.19
Nodes (4): DBItemAnnotation, next_annotation(), Annotation, NextAnnotationTests

### Community 23 - "describe"
Cohesion: 0.09
Nodes (12): apps_phase(), deliver_each(), delivery_phase(), failed_report(), failed_summary(), format_time(), process_workflow(), progress_rows() (+4 more)

### Community 24 - "Delivery"
Cohesion: 0.17
Nodes (5): CommitTests, DelivererTests, DeliveryOrderTests, LedgerTestCase, RecordingSink

### Community 27 - "Services"
Cohesion: 0.06
Nodes (19): 0013: Plugin services at init, Consequences, Context, Decision, Rejected options, LLM, LLMType, ClassifyProcessor (+11 more)

### Community 30 - "grouping.py"
Cohesion: 0.10
Nodes (19): Requirements, average_between(), average_link_cluster(), AverageLinkApplet, build_score_matrix(), cosine_similarity(), EmbeddingsApplet, GroupingApplet (+11 more)

### Community 31 - "cli.py"
Cohesion: 0.09
Nodes (9): apps_group(), cli(), delete_group(), deliveries_group(), describe_schedule(), format_seconds(), inspect_group(), lexer_for() (+1 more)

### Community 33 - ".add_items"
Cohesion: 0.27
Nodes (3): AppletTestCase, GroupingTests, ItemFeedTests

### Community 34 - "plugins"
Cohesion: 0.12
Nodes (17): lookback, title, url, api_base, chat_model, embed_model, plugins, digest (+9 more)

### Community 35 - ".summary"
Cohesion: 0.10
Nodes (14): 0009: Workflows and keyed entries, Consequences, Context, Decision, Rejected options, Configuration, 0017: Explicit run selection, Consequences (+6 more)

### Community 36 - "GoogleChatSinkTests"
Cohesion: 0.09
Nodes (10): build_card(), chat_image_url(), GoogleChatSink, __newstool_plugin__(), WebhookOptions, card_widgets(), ChatImageUrlTests, GoogleChatSinkTests (+2 more)

### Community 38 - "app_from_context"
Cohesion: 0.10
Nodes (23): app_from_context(), apps_reset_cmd(), apps_run_cmd(), check_all_rows(), delete_annotations_cmd(), delete_deliveries_cmd(), delete_documents_cmd(), delete_items_cmd() (+15 more)

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
Cohesion: 0.15
Nodes (6): DBSourceItem, ConnectionTests, ContentChangeTests, DatabaseTestCase, DeleteTests, IdentityTests

### Community 45 - "config.example.yaml"
Cohesion: 0.11
Nodes (15): cache, expiration, llms, input, processors, options, processor, remixers (+7 more)

### Community 46 - "Application"
Cohesion: 0.08
Nodes (7): Application, AppInstance, print_deliver(), report_delivery(), routed_from(), selected_apps(), selected_sinks()

### Community 50 - "EmbeddingGroupingTests"
Cohesion: 0.33
Nodes (3): EmbeddingsOptions, GroupingOptions, EmbeddingGroupingTests

### Community 51 - "Framework Usage"
Cohesion: 0.33
Nodes (4): Additional Approved Packages, Framework Usage, newstool Python Specifics, setup_logging()

### Community 54 - "Processor"
Cohesion: 0.29
Nodes (6): UnavailableProcessor / UnavailableRemixer / UnavailableSink, Annotation, Delivery, Exponential backoff 60s*2^(n-1), capped 24h, max_retries, Processor, Sink

### Community 55 - "El Periódico Mediterráneo"
Cohesion: 0.43
Nodes (7): El Periódico Mediterráneo, Prensa Ibérica article HTML format (og:/article: meta tags), Telegram t.me/s channel preview HTML (tgme_widget_message, data-post), El eco perdido de las fiestas de julio nacidas del asedio carlista sobre Castellón (sample article), El Grau se vuelca en las fiestas de la Virgen del Carmen (sample article), Castellón apoya a la selección española desde la plaza Mayor (sample article), Telegram channel mediterraneoelperiodico (sample web preview)

### Community 56 - "feedreader.py"
Cohesion: 0.20
Nodes (5): HTTPClient, discover_feed_url(), fetch_article(), fetch_feed(), TestHTTPClient

### Community 57 - "ProcessingScope"
Cohesion: 0.26
Nodes (4): workflow_scope(), wrapper(), ProcessingScope, GetItemsTests

### Community 58 - "deliveries table (the ledger)"
Cohesion: 0.33
Nodes (4): BaseSink deliver cycle (queue, select, send), deliveries table (the ledger), ADR 0005 Remixers with external side effects, Strict FIFO per source

### Community 59 - "PluginFailure"
Cohesion: 0.06
Nodes (29): PluginFailure, SourceData, __newstool_plugin__(), __newstool_plugin__(), __newstool_plugin__(), Options, select_article(), NoOptions (+21 more)

### Community 61 - "Item"
Cohesion: 0.40
Nodes (3): IndexSiteProvider / URLProvider, Item, Provider

### Community 62 - "AppletRun"
Cohesion: 0.09
Nodes (3): AppStatus, DBApp, AppletRun

### Community 63 - "inspect_annotations_cmd"
Cohesion: 0.12
Nodes (15): check_found(), format_value(), inspect_annotations_cmd(), inspect_apps_cmd(), inspect_deliveries_cmd(), inspect_items_cmd(), json_default(), preview() (+7 more)

### Community 64 - "FileSinkTests"
Cohesion: 0.17
Nodes (3): FileOptions, FileSink, FileSinkTests

### Community 65 - "Delivery"
Cohesion: 0.16
Nodes (3): DBDelivery, DeliveryStatus, Delivery

### Community 66 - "MarkdownifyProcessor"
Cohesion: 0.23
Nodes (5): MarkdownifyProcessor, SkipItem, ClassRegisterTests, make_pdf(), MarkdownifyPdfTests

### Community 68 - "feed.py"
Cohesion: 0.17
Nodes (5): run_key(), SourcesOptions, FeedApplet, Options, FeedTests

### Community 71 - "0011: Environment overrides, relative paths and one storage directory"
Cohesion: 0.40
Nodes (4): 0011: Environment overrides, relative paths and one storage directory, Consequences, Context, Decision

### Community 73 - "foundation internal library"
Cohesion: 0.29
Nodes (7): foundation internal library, foundation.plugin.Register plugin loading, __newsmerger_plugin__(services, **options) entry point, PluginOptions (pydantic, unknown keys rejected), plugins configuration section, P1: plain logging and <APP>_LOG_LEVEL fix, P2: rich progress per stream (RICH_STDOUT_*/RICH_STDERR_*)

### Community 74 - "0018: Annotations hold their run state; a content change deletes them"
Cohesion: 0.40
Nodes (4): 0018: Annotations hold their run state; a content change deletes them, Consequences, Context, Decision

### Community 75 - "app.py"
Cohesion: 0.07
Nodes (7): Alias, CacheConfig, ProcessingStatus, _sha256_column(), LLMUnavailableError, strip_code_fence(), ClassRegister

### Community 76 - "workflows"
Cohesion: 0.33
Nodes (6): sink, workflows, deliver, name, process, sources

### Community 79 - ".settings_customise_sources"
Cohesion: 0.09
Nodes (6): EnvAliasSource, load_context(), LoadContext, LoadEnvSettingsSource, parse_duration(), resolve_config_path()

### Community 81 - "errors.py"
Cohesion: 0.08
Nodes (11): Sinks, reason(), __newstool_plugin__(), merge_options(), __newstool_plugin__(), __newstool_plugin__(), TelegramOptions, accepts() (+3 more)

### Community 82 - "CSJuntasGobiernoProvider"
Cohesion: 0.27
Nodes (5): CSJuntasGobiernoProvider, find_parent_by_tag_name(), get_date_from_text(), PreparseData, TestCSJuntasGobierno

### Community 85 - "Decision"
Cohesion: 0.14
Nodes (12): 0015: Applets, emitted documents and routes, CLI, Consequences, Context, Decision, Documents, Migration, Plugins (+4 more)

### Community 88 - "._find_excluded_containers"
Cohesion: 0.16
Nodes (4): _extract_href(), _get_modified_at(), PrensaIbericaProvider, read_sample()

### Community 89 - "parse_entry"
Cohesion: 0.60
Nodes (3): entry_date(), find_image(), parse_entry()

### Community 90 - "describe"
Cohesion: 0.13
Nodes (7): import_sources(), import_failed(), phase_title(), print_process(), workflow_phases(), describe(), DescribeTests

### Community 92 - "Config"
Cohesion: 0.11
Nodes (5): Database & ORM Conventions, DTO, Protocol & ORM Implementation Reference, Config, Workflow, DirectoryTests

### Community 95 - "DocumentFilter"
Cohesion: 0.15
Nodes (3): MarkSummary, wrapper(), DocumentFilter

### Community 99 - "AppletType"
Cohesion: 0.08
Nodes (12): Applets, Applet, AppletType, BaseApplet, DigestOptions, __newstool_plugin__(), __newstool_plugin__(), __newstool_plugin__() (+4 more)

### Community 104 - "0012: Delivery ids, changing their state and forced send"
Cohesion: 0.33
Nodes (5): 0012: Delivery ids, changing their state and forced send, Consequences, Context, Decision, Rejected options

### Community 105 - ".key"
Cohesion: 0.13
Nodes (5): 0014: Ledger rows by subject and the workflow in delivery commands, Consequences, Context, Decision, Rejected options

### Community 106 - "0016: Routes on re-emission, manual queueing and pacing overrides"
Cohesion: 0.33
Nodes (5): 0016: Routes on re-emission, manual queueing and pacing overrides, Consequences, Context, Decision, Rejected options

### Community 107 - "SinkOptions"
Cohesion: 0.21
Nodes (4): StdoutSink, Sink, SinkOptions, StdoutSinkTests

### Community 108 - "0010: Plugin classes and the configuration catalog"
Cohesion: 0.40
Nodes (4): 0010: Plugin classes and the configuration catalog, Consequences, Context, Rejected options

## Knowledge Gaps
- **13 isolated node(s):** `newstool`, `External pipelines (scripts/pipeline_url.py)`, `Annotation`, `Telegram t.me/s channel preview HTML (tgme_widget_message, data-post)`, `IndexSiteProvider / URLProvider` (+8 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 607 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **35 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Application` connect `Application` to `catalog.py`, `Services`, `ApplicationTests`, `invoke`, `SourceItem`, `PreflightSourceItemData`, `ConfigError`, `AppletReader`, `Document`, `datetime`, `test_db.py`, `describe`, `Services`, `Deliverer`, `cli.py`, `.summary`, `app_from_context`, `.delete_documents`, `SourceItemData`, `feedreader.py`, `ProcessingScope`, `PluginFailure`, `AppletRun`, `inspect_annotations_cmd`, `Delivery`, `app.py`, `.from_file`, `.rename_sink`, `PacingOverride`, `describe`, `.delete_documents`, `Config`, `.delete_deliveries`, `DocumentFilter`, `.get_annotation_keys`, `.process_keys`, `.key`?**
  _High betweenness centrality (0.120) - this node is a cross-community bridge._
- **Are the 31 inferred relationships involving `SourceItem` (e.g. with `Application` and `AppletReader`) actually correct?**
  _`SourceItem` has 31 INFERRED edges - model-reasoned connections that need verification._
- **What connects `newstool`, `External pipelines (scripts/pipeline_url.py)`, `Annotation` to the rest of the system?**
  _13 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `catalog.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09176788124156546 - nodes in this community are weakly interconnected._
- **Why does `SourceItem` connect `SourceItem` to `make_item`, `Services`, `ApplicationTests`, `StubLLM`, `ItemFeedApplet`, `DeleteCommandTests`, `AppletReader`, `.digest`, `datetime`, `InspectCommandTests`, `Services`, `grouping.py`, `cli.py`, `.add_items`, `.summary`, `AnnotationTests`, `test_db.py`, `Application`, `inspect_annotations_cmd`, `MarkdownifyProcessor`, `feed.py`, `app.py`, `test_markdownify.py`, `.key`?**
  _High betweenness centrality (0.099) - this node is a cross-community bridge._
- **Are the 23 inferred relationships involving `Database` (e.g. with `Context` and `Decision`) actually correct?**
  _`Database` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Should `Services` be split into smaller, more focused modules?**
  _Cohesion score 0.0506558118498417 - nodes in this community are weakly interconnected._