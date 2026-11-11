# Graph Report - digest-plan  (2026-11-11)

## Corpus Check
- 81 files · ~194,782 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 4, .lock 1)

## Summary
- 2023 nodes · 5531 edges · 113 communities (68 shown, 45 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 684 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d5c66f12`
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
- expand_variables
- TelegramSinkTests
- TestFeedReader
- test_providers.py
- Document
- DigestApplet
- AppletResult
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
- Database
- inspect_annotations_cmd
- FileSinkTests
- Delivery
- MarkdownifyProcessor
- Example sources (prensaiberica_plain, castelloninformacion, plaza, theguardian)
- feed.py
- Artifact
- Grouping notes: NLP clustering pipeline
- 0011: Environment overrides, relative paths and one storage directory
- DocumentFilter
- foundation internal library
- 0013: Plugin services at init
- app.py
- workflows
- .from_file
- TestSourceItemDataContent
- .settings_customise_sources
- LogLevelTests
- SinkOptions
- CSJuntasGobiernoProvider
- Decision
- .__init__
- PacingOverride
- ._find_excluded_containers
- describe
- model_validator
- Config
- AliasTests
- ADR 0002 Processing state lifecycle
- .selected_documents
- Workflow
- ProcessEntry
- db.py
- AppletType
- test_markdownify.py
- .content_dir
- 0012: Delivery ids, changing their state and forced send
- 0014: Ledger rows by subject and the workflow in delivery commands
- 0016: Routes on re-emission, manual queueing and pacing overrides
- Sink
- 0010: Plugin classes and the configuration catalog
- check_section
- check_result
- options_error

## God Nodes (most connected - your core abstractions)
1. `SourceItem` - 110 edges
2. `Database` - 95 edges
3. `Services` - 95 edges
4. `Application` - 93 edges
5. `PluginFailure` - 75 edges
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

## Communities (113 total, 45 thin omitted)

### Community 0 - "make_item"
Cohesion: 0.14
Nodes (8): Base, DBSourceItem, ContentChangeTests, ContentStorageTests, IdentityTests, make_item(), make_source(), UpsertSourceItemsTests

### Community 1 - "catalog.py"
Cohesion: 0.09
Nodes (7): Catalog, Kind, process_key(), Profile, Run, share_sources(), ConfigError

### Community 2 - "Services"
Cohesion: 0.05
Nodes (31): Decision, Decision, LLMUnavailableError, strip_code_fence(), classify_prompt(), ClassifyOptions, ClassifyProcessor, known_labels() (+23 more)

### Community 3 - "ApplicationTests"
Cohesion: 0.06
Nodes (9): LockedError, write_lock(), ApplicationTests, retrieve(), retrieve_published(), retrieve(), same(), listed() (+1 more)

### Community 4 - "scope_options"
Cohesion: 0.24
Nodes (5): annotation_options(), wrapper(), scope_options(), selection_options(), decorate()

### Community 5 - "invoke"
Cohesion: 0.06
Nodes (9): AppReport, DeleteSummary, MarkSummary, RunSummary, annotation(), CommandTests, ExternalErrorTests, InspectCommandTests (+1 more)

### Community 7 - "Entry"
Cohesion: 0.15
Nodes (3): AppEntry, Entry, SinkEntry

### Community 8 - "Database (db.py, only SQLite/storage access)"
Cohesion: 0.17
Nodes (11): pre-commit config, ruff-check and ruff-format hooks, newsmerger CLAUDE.md agent guidelines, DTO/ORM from_dto/to_dto/update convention, Consumer-side Protocol decoupling convention, AUTOINCREMENT integer ids, Database (db.py, only SQLite/storage access), foundation.storage.DiskStorage content-addressed storage (+3 more)

### Community 9 - "StubLLM"
Cohesion: 0.13
Nodes (8): tags_prompt(), Processor, ClassifyTests, EmbedTests, ProcessorTestCase, StubLLM, SummarizeTests, TaggerTests

### Community 15 - "TelegramSinkTests"
Cohesion: 0.24
Nodes (6): Schedule, item_document(), ok_response(), options(), sink(), TelegramSinkTests

### Community 17 - "test_providers.py"
Cohesion: 0.18
Nodes (6): is_home_page(), parse_article(), parse_preview(), Post, TelegramChannelProvider, TestTelegramChannel

### Community 18 - "Document"
Cohesion: 0.13
Nodes (3): DBDocument, Document, FileSink

### Community 19 - "DigestApplet"
Cohesion: 0.14
Nodes (6): DigestApplet, DigestOptions, __newstool_plugin__(), DigestAppletTests, DigestPluginTests, factory()

### Community 20 - "AppletResult"
Cohesion: 0.15
Nodes (7): AppletResult, EmittedDocument, CheckResultTests, ReaderTests, DeliveryTests, JSONColumnTests, emitted()

### Community 21 - "datetime"
Cohesion: 0.14
Nodes (3): CustomJSON, _encode_value(), UTCDateTime

### Community 22 - "test_db.py"
Cohesion: 0.19
Nodes (4): DBItemAnnotation, next_annotation(), Annotation, NextAnnotationTests

### Community 23 - "describe"
Cohesion: 0.07
Nodes (18): apps_phase(), deliver_each(), delivery_phase(), failed_summary(), format_time(), import_sources(), import_failed(), phase_title() (+10 more)

### Community 24 - "Delivery"
Cohesion: 0.10
Nodes (8): backoff_seconds(), Deliverer, CommitTests, DelivererTests, run(), DeliveryOrderTests, LedgerTestCase, RecordingSink

### Community 27 - "OllamaLLM"
Cohesion: 0.15
Nodes (6): LLMType, __newstool_plugin__(), ollama_client(), OllamaLLM, Options, OllamaTests

### Community 29 - "chat_image_url"
Cohesion: 0.25
Nodes (3): build_card(), chat_image_url(), ChatImageUrlTests

### Community 30 - "grouping.py"
Cohesion: 0.08
Nodes (20): AppletReader, run_key(), average_between(), average_link_cluster(), AverageLinkApplet, build_score_matrix(), cosine_similarity(), EmbeddingsApplet (+12 more)

### Community 31 - "cli.py"
Cohesion: 0.09
Nodes (9): apps_group(), cli(), delete_group(), deliveries_group(), describe_schedule(), format_seconds(), inspect_group(), lexer_for() (+1 more)

### Community 32 - "TelegramSink"
Cohesion: 0.22
Nodes (4): build_caption(), post(), TelegramSink, BuildCaptionTests

### Community 33 - ".add_items"
Cohesion: 0.18
Nodes (6): SourcesOptions, GroupingOptions, ItemFeedOptions, AppletTestCase, GroupingTests, ItemFeedTests

### Community 34 - "plugins"
Cohesion: 0.12
Nodes (17): lookback, title, url, api_base, chat_model, embed_model, plugins, digest (+9 more)

### Community 35 - ".summary"
Cohesion: 0.11
Nodes (13): 0009: Workflows and keyed entries, Consequences, Context, Decision, Rejected options, Configuration, 0017: Explicit run selection, Consequences (+5 more)

### Community 36 - "GoogleChatSink"
Cohesion: 0.18
Nodes (4): __newstool_plugin__(), WebhookOptions, OptionsTests, webhook_options()

### Community 38 - "app_from_context"
Cohesion: 0.15
Nodes (15): app_from_context(), apps_reset_cmd(), apps_run_cmd(), delete_annotations_cmd(), delete_items_cmd(), deliver_cmd(), deliveries_rename_cmd(), import_cmd() (+7 more)

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
Cohesion: 0.32
Nodes (3): ConnectionTests, DatabaseTestCase, DeleteTests

### Community 45 - "config.example.yaml"
Cohesion: 0.11
Nodes (15): cache, expiration, llms, input, processors, options, processor, remixers (+7 more)

### Community 46 - "Application"
Cohesion: 0.07
Nodes (5): Application, AppInstance, routed_from(), selected_apps(), selected_sinks()

### Community 48 - "SourceItemData"
Cohesion: 0.20
Nodes (5): PreflightSourceItemData, SourceItemData, PrensaIbericaProvider, read_sample(), TestPrensaIberica

### Community 51 - "Framework Usage"
Cohesion: 0.33
Nodes (4): Additional Approved Packages, Framework Usage, newstool Python Specifics, setup_logging()

### Community 52 - "SourceData"
Cohesion: 0.12
Nodes (5): DBSource, SourceData, CastellonInformacionProvider, TheGuardianProvider, IndexSiteProvider

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
Cohesion: 0.29
Nodes (3): wrapper(), ProcessingScope, GetItemsTests

### Community 58 - "deliveries table (the ledger)"
Cohesion: 0.33
Nodes (4): BaseSink deliver cycle (queue, select, send), deliveries table (the ledger), ADR 0005 Remixers with external side effects, Strict FIFO per source

### Community 59 - "PluginFailure"
Cohesion: 0.08
Nodes (23): PluginFailure, __newstool_plugin__(), __newstool_plugin__(), entry_date(), find_image(), __newstool_plugin__(), Options, parse_entry() (+15 more)

### Community 60 - "AppletRun"
Cohesion: 0.17
Nodes (5): BaseApplet, Schedule, DBApp, AppletRun, ScheduleTests

### Community 61 - "Item"
Cohesion: 0.40
Nodes (3): IndexSiteProvider / URLProvider, Item, Provider

### Community 63 - "inspect_annotations_cmd"
Cohesion: 0.15
Nodes (11): format_value(), inspect_annotations_cmd(), inspect_apps_cmd(), json_default(), preview(), print_apps(), print_emitted(), print_import() (+3 more)

### Community 65 - "Delivery"
Cohesion: 0.14
Nodes (3): CommittedRun, DBDelivery, Delivery

### Community 66 - "MarkdownifyProcessor"
Cohesion: 0.23
Nodes (5): MarkdownifyProcessor, SkipItem, ClassRegisterTests, make_pdf(), MarkdownifyPdfTests

### Community 68 - "feed.py"
Cohesion: 0.21
Nodes (3): FeedApplet, Options, FeedTests

### Community 71 - "0011: Environment overrides, relative paths and one storage directory"
Cohesion: 0.40
Nodes (4): 0011: Environment overrides, relative paths and one storage directory, Consequences, Context, Decision

### Community 72 - "DocumentFilter"
Cohesion: 0.11
Nodes (16): check_all_rows(), check_found(), delete_deliveries_cmd(), delete_documents_cmd(), deliveries_send_cmd(), deliveries_set_status_cmd(), delivery_filters(), delivery_options() (+8 more)

### Community 73 - "foundation internal library"
Cohesion: 0.29
Nodes (7): foundation internal library, foundation.plugin.Register plugin loading, __newsmerger_plugin__(services, **options) entry point, PluginOptions (pydantic, unknown keys rejected), plugins configuration section, P1: plain logging and <APP>_LOG_LEVEL fix, P2: rich progress per stream (RICH_STDOUT_*/RICH_STDERR_*)

### Community 74 - "0013: Plugin services at init"
Cohesion: 0.18
Nodes (8): 0013: Plugin services at init, Consequences, Context, Rejected options, 0018: Annotations hold their run state; a content change deletes them, Consequences, Context, Decision

### Community 75 - "app.py"
Cohesion: 0.06
Nodes (12): Alias, CacheConfig, reason(), LLM, __newstool_plugin__(), ClassRegister, merge_options(), __newstool_plugin__() (+4 more)

### Community 76 - "workflows"
Cohesion: 0.33
Nodes (6): sink, workflows, deliver, name, process, sources

### Community 79 - ".settings_customise_sources"
Cohesion: 0.12
Nodes (5): EnvAliasSource, load_context(), LoadContext, LoadEnvSettingsSource, parse_duration()

### Community 81 - "SinkOptions"
Cohesion: 0.17
Nodes (7): Sinks, StdoutSink, TelegramOptions, accepts(), SinkOptions, AcceptsTests, StdoutSinkTests

### Community 82 - "CSJuntasGobiernoProvider"
Cohesion: 0.23
Nodes (6): CSJuntasGobiernoProvider, find_parent_by_tag_name(), get_date_from_text(), PreparseData, NoOptions, TestCSJuntasGobierno

### Community 85 - "Decision"
Cohesion: 0.14
Nodes (12): 0015: Applets, emitted documents and routes, CLI, Consequences, Context, Decision, Documents, Migration, Plugins (+4 more)

### Community 90 - "describe"
Cohesion: 0.22
Nodes (3): failed_report(), describe(), DescribeTests

### Community 97 - "ProcessEntry"
Cohesion: 0.25
Nodes (4): ids_of(), in_default(), Use, ProcessEntry

### Community 99 - "AppletType"
Cohesion: 0.17
Nodes (7): Applets, Applet, AppletType, __newstool_plugin__(), __newstool_plugin__(), __newstool_plugin__(), PluginRegistrationTests

### Community 101 - ".content_dir"
Cohesion: 0.29
Nodes (3): Database & ORM Conventions, DTO, Protocol & ORM Implementation Reference, resolve_config_path()

### Community 104 - "0012: Delivery ids, changing their state and forced send"
Cohesion: 0.33
Nodes (5): 0012: Delivery ids, changing their state and forced send, Consequences, Context, Decision, Rejected options

### Community 105 - "0014: Ledger rows by subject and the workflow in delivery commands"
Cohesion: 0.33
Nodes (5): 0014: Ledger rows by subject and the workflow in delivery commands, Consequences, Context, Decision, Rejected options

### Community 106 - "0016: Routes on re-emission, manual queueing and pacing overrides"
Cohesion: 0.33
Nodes (5): 0016: Routes on re-emission, manual queueing and pacing overrides, Consequences, Context, Decision, Rejected options

### Community 108 - "0010: Plugin classes and the configuration catalog"
Cohesion: 0.40
Nodes (4): 0010: Plugin classes and the configuration catalog, Consequences, Context, Rejected options

## Knowledge Gaps
- **13 isolated node(s):** `newstool`, `External pipelines (scripts/pipeline_url.py)`, `Annotation`, `Telegram t.me/s channel preview HTML (tgme_widget_message, data-post)`, `IndexSiteProvider / URLProvider` (+8 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 607 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **45 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Application` connect `Application` to `catalog.py`, `Services`, `ApplicationTests`, `invoke`, `.from_text`, `SourceItem`, `PreflightSourceItemData`, `DeleteCommandTests`, `Document`, `test_db.py`, `describe`, `Delivery`, `grouping.py`, `cli.py`, `.summary`, `app_from_context`, `.delete_documents`, `SourceItemData`, `SourceData`, `feedreader.py`, `ProcessingScope`, `AppletRun`, `Database`, `Delivery`, `DocumentFilter`, `app.py`, `.from_file`, `PacingOverride`, `Config`, `.selected_documents`, `Workflow`, `db.py`, `.process_keys`, `.close`?**
  _High betweenness centrality (0.116) - this node is a cross-community bridge._
- **Are the 31 inferred relationships involving `SourceItem` (e.g. with `Application` and `AppletReader`) actually correct?**
  _`SourceItem` has 31 INFERRED edges - model-reasoned connections that need verification._
- **What connects `newstool`, `External pipelines (scripts/pipeline_url.py)`, `Annotation` to the rest of the system?**
  _13 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `make_item` be split into smaller, more focused modules?**
  _Cohesion score 0.13630229419703105 - nodes in this community are weakly interconnected._
- **Why does `SourceItem` connect `SourceItem` to `make_item`, `Services`, `ApplicationTests`, `invoke`, `StubLLM`, `ItemFeedApplet`, `DeleteCommandTests`, `DigestApplet`, `datetime`, `grouping.py`, `cli.py`, `.add_items`, `.summary`, `AnnotationTests`, `test_db.py`, `Application`, `Database`, `inspect_annotations_cmd`, `MarkdownifyProcessor`, `feed.py`, `app.py`, `.get_unprocessed_items`, `._run_item`, `db.py`, `test_markdownify.py`?**
  _High betweenness centrality (0.098) - this node is a cross-community bridge._
- **Are the 23 inferred relationships involving `Database` (e.g. with `Context` and `Decision`) actually correct?**
  _`Database` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Should `catalog.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08985200845665962 - nodes in this community are weakly interconnected._