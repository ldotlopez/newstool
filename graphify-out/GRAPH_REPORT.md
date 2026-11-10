# Graph Report - run-all-workflows  (2026-11-10)

## Corpus Check
- 83 files · ~190,978 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 4, .lock 1)

## Summary
- 1962 nodes · 5415 edges · 105 communities (71 shown, 34 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 673 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ff02195a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ProcessingScope
- catalog.py
- Services
- ApplicationTests
- DocumentFilter
- invoke
- .from_text
- Any
- Database (db.py, only SQLite/storage access)
- StubLLM
- Database
- AppletReader
- CSJuntasGobiernoProvider
- DeleteCommandTests
- config.py
- TelegramSinkTests
- TestFeedReader
- TelegramChannelProvider
- Document
- feed.py
- SourceItem
- datetime
- inspect_annotations_cmd
- ClassRegister
- DelivererTests
- FileSinkTests
- build_caption
- OllamaLLM
- BaseApplet
- AppletResult
- grouping.py
- cli.py
- .add_items
- plugins
- Schedule
- WebhookOptions
- EmbeddingGroupingTests
- .process_keys
- ADR 0007 Sinks and the delivery ledger
- describe
- options
- hooks
- Services object (services.llm(name))
- GoogleChatSinkTests
- config.example.yaml
- Application
- run_delivery
- SourceItemData
- PacingOverride
- .settings_customise_sources
- AppletRun
- newstool
- Processor
- El Periódico Mediterráneo
- HTTPClient
- .llm
- deliveries table (the ledger)
- SourceData
- .close
- Item
- print_table
- PluginFailure
- SinkOptions
- ProcessorOptions
- Example sources (prensaiberica_plain, castelloninformacion, plaza, theguardian)
- app.py
- Artifact
- Grouping notes: NLP clustering pipeline
- Delivery
- app_from_context
- foundation internal library
- PlazaProvider
- models.py
- workflows
- migrate
- TestSourceItemDataContent
- .content_dir
- LogLevelTests
- .from_file
- PreflightSourceItemData
- Base
- .digest
- Sink
- .__init__
- PrensaIbericaProvider
- BaseProcessor
- embed.py
- setup_logging
- ProcessorType
- DirectoryTests
- AliasTests
- ADR 0002 Processing state lifecycle
- 0011: Environment overrides, relative paths and one storage directory
- CastellonInformacionProvider
- IndexSiteProvider
- __newstool_plugin__
- merge_options
- DeliveryTests
- 0014: Ledger rows by subject and the workflow in delivery commands
- 0016: Routes on re-emission, manual queueing and pacing overrides

## God Nodes (most connected - your core abstractions)
1. `SourceItem` - 114 edges
2. `Database` - 101 edges
3. `Services` - 92 edges
4. `Application` - 83 edges
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

## Communities (105 total, 34 thin omitted)

### Community 0 - "ProcessingScope"
Cohesion: 0.06
Nodes (21): 0012: Delivery ids, changing their state and forced send, Consequences, Context, Decision, Rejected options, Deliveries, wrapper(), DBSource (+13 more)

### Community 1 - "catalog.py"
Cohesion: 0.05
Nodes (18): AppInstance, Catalog, check_section(), ids_of(), in_default(), Kind, process_key(), Profile (+10 more)

### Community 2 - "Services"
Cohesion: 0.06
Nodes (17): Decision, AppletType, SourcesOptions, ProcessingStatus, LLM, LLMType, LLMUnavailableError, strip_code_fence() (+9 more)

### Community 3 - "ApplicationTests"
Cohesion: 0.07
Nodes (7): ApplicationTests, retrieve(), retrieve_published(), retrieve(), same(), listed(), retrieved()

### Community 4 - "DocumentFilter"
Cohesion: 0.12
Nodes (15): check_all_rows(), delete_deliveries_cmd(), delete_documents_cmd(), deliveries_send_cmd(), deliveries_set_status_cmd(), delivery_filters(), delivery_options(), document_options() (+7 more)

### Community 5 - "invoke"
Cohesion: 0.09
Nodes (8): AppReport, DeleteSummary, MarkSummary, RunSummary, annotation(), CommandTests, InspectCommandTests, invoke()

### Community 8 - "Database (db.py, only SQLite/storage access)"
Cohesion: 0.17
Nodes (11): pre-commit config, ruff-check and ruff-format hooks, newsmerger CLAUDE.md agent guidelines, DTO/ORM from_dto/to_dto/update convention, Consumer-side Protocol decoupling convention, AUTOINCREMENT integer ids, Database (db.py, only SQLite/storage access), foundation.storage.DiskStorage content-addressed storage (+3 more)

### Community 9 - "StubLLM"
Cohesion: 0.15
Nodes (6): ConsumerPluginTests, EmbedTests, ProcessorTestCase, StubLLM, SummarizeTests, TaggerTests

### Community 10 - "Database"
Cohesion: 0.12
Nodes (3): Database, MigrateAppletsTests, sha256()

### Community 12 - "CSJuntasGobiernoProvider"
Cohesion: 0.23
Nodes (6): CSJuntasGobiernoProvider, find_parent_by_tag_name(), get_date_from_text(), PreparseData, NoOptions, TestCSJuntasGobierno

### Community 14 - "config.py"
Cohesion: 0.09
Nodes (7): Alias, CacheConfig, expand_variables(), LLMEntry, MissingVariableError, ollama_url(), SinkEntry

### Community 15 - "TelegramSinkTests"
Cohesion: 0.24
Nodes (6): run(), item_document(), ok_response(), options(), sink(), TelegramSinkTests

### Community 16 - "TestFeedReader"
Cohesion: 0.10
Nodes (10): discover_feed_url(), entry_date(), FeedReaderProvider, fetch_article(), fetch_feed(), find_image(), parse_entry(), select_article() (+2 more)

### Community 17 - "TelegramChannelProvider"
Cohesion: 0.16
Nodes (7): is_home_page(), page_title(), parse_article(), parse_preview(), Post, TelegramChannelProvider, TestTelegramChannel

### Community 18 - "Document"
Cohesion: 0.15
Nodes (4): DBDocument, Document, post(), TelegramSink

### Community 19 - "feed.py"
Cohesion: 0.19
Nodes (4): run_key(), FeedApplet, Options, FeedTests

### Community 20 - "SourceItem"
Cohesion: 0.19
Nodes (3): SourceItem, DigestApplet, SearchTests

### Community 21 - "datetime"
Cohesion: 0.12
Nodes (3): CustomJSON, _encode_value(), UTCDateTime

### Community 22 - "inspect_annotations_cmd"
Cohesion: 0.13
Nodes (11): annotation_options(), check_found(), delete_annotations_cmd(), format_value(), inspect_annotations_cmd(), inspect_items_cmd(), json_default(), preview() (+3 more)

### Community 24 - "DelivererTests"
Cohesion: 0.16
Nodes (5): CommitTests, DelivererTests, DeliveryOrderTests, LedgerTestCase, RecordingSink

### Community 25 - "FileSinkTests"
Cohesion: 0.17
Nodes (3): FileOptions, FileSink, FileSinkTests

### Community 26 - "build_caption"
Cohesion: 0.16
Nodes (5): build_card(), chat_image_url(), build_caption(), ChatImageUrlTests, BuildCaptionTests

### Community 27 - "OllamaLLM"
Cohesion: 0.21
Nodes (5): __newstool_plugin__(), ollama_client(), OllamaLLM, Options, OllamaTests

### Community 28 - "BaseApplet"
Cohesion: 0.17
Nodes (5): BaseApplet, Requirements, AverageLinkApplet, EmbeddingsApplet, GroupingApplet

### Community 29 - "AppletResult"
Cohesion: 0.15
Nodes (8): check_result(), AppletResult, EmittedDocument, CheckResultTests, ReaderTests, DocumentTests, keys(), emitted()

### Community 30 - "grouping.py"
Cohesion: 0.11
Nodes (14): average_between(), average_link_cluster(), build_score_matrix(), cosine_similarity(), item_ref(), jaccard(), member_payload(), pair_payload() (+6 more)

### Community 31 - "cli.py"
Cohesion: 0.08
Nodes (11): apps_group(), cli(), delete_group(), deliveries_group(), describe_schedule(), format_seconds(), format_time(), inspect_group() (+3 more)

### Community 33 - ".add_items"
Cohesion: 0.27
Nodes (3): ItemFeedOptions, AppletTestCase, ItemFeedTests

### Community 34 - "plugins"
Cohesion: 0.12
Nodes (17): lookback, title, url, api_base, chat_model, embed_model, plugins, digest (+9 more)

### Community 35 - "Schedule"
Cohesion: 0.06
Nodes (24): 0009: Workflows and keyed entries, Consequences, Context, Decision, Rejected options, 0015: Applets, emitted documents and routes, Applets, CLI (+16 more)

### Community 36 - "WebhookOptions"
Cohesion: 0.18
Nodes (4): __newstool_plugin__(), WebhookOptions, OptionsTests, webhook_options()

### Community 37 - "EmbeddingGroupingTests"
Cohesion: 0.22
Nodes (5): EmbeddingsOptions, GroupingOptions, SingleLinkApplet, EmbeddingGroupingTests, GroupingTests

### Community 39 - "ADR 0007 Sinks and the delivery ledger"
Cohesion: 0.21
Nodes (14): Architecture, cli.py Click commands, External pipelines (scripts/pipeline_url.py), ADR 0001 Item identity and change detection, ADR 0003 Plugin types and core scope, ADR 0004 Annotation and artifact contents on disk, ADR 0006 LLM plugins, ADR 0007 Sinks and the delivery ledger (+6 more)

### Community 40 - "describe"
Cohesion: 0.15
Nodes (6): import_sources(), import_one(), wrapper(), describe(), log_failure(), DescribeTests

### Community 41 - "options"
Cohesion: 0.15
Nodes (14): options, artifacts, chat_id, interval, item_image, item_url_preview, item_url_text, markdown (+6 more)

### Community 42 - "hooks"
Cohesion: 0.15
Nodes (12): exclude, args, entry, files, id, language, name, pass_filenames (+4 more)

### Community 43 - "Services object (services.llm(name))"
Cohesion: 0.22
Nodes (12): digest remixer, embed processor, grouping remixers (singlelink, avglink, embeddings), markdownify processor, summarize processor, tagger processor, telegram bundle (telegram, telegram_artifacts sinks), LLM plugins must be listed before their consumers (+4 more)

### Community 44 - "GoogleChatSinkTests"
Cohesion: 0.30
Nodes (3): GoogleChatSink, card_widgets(), GoogleChatSinkTests

### Community 45 - "config.example.yaml"
Cohesion: 0.11
Nodes (15): cache, expiration, llms, input, processors, options, processor, remixers (+7 more)

### Community 47 - "run_delivery"
Cohesion: 0.22
Nodes (4): print_deliver(), progress_rows(), run_delivery(), run_each()

### Community 51 - ".settings_customise_sources"
Cohesion: 0.15
Nodes (4): EnvAliasSource, load_context(), LoadContext, LoadEnvSettingsSource

### Community 52 - "AppletRun"
Cohesion: 0.16
Nodes (3): CommittedRun, DBApp, AppletRun

### Community 54 - "Processor"
Cohesion: 0.29
Nodes (6): UnavailableProcessor / UnavailableRemixer / UnavailableSink, Annotation, Delivery, Exponential backoff 60s*2^(n-1), capped 24h, max_retries, Processor, Sink

### Community 55 - "El Periódico Mediterráneo"
Cohesion: 0.43
Nodes (7): El Periódico Mediterráneo, Prensa Ibérica article HTML format (og:/article: meta tags), Telegram t.me/s channel preview HTML (tgme_widget_message, data-post), El eco perdido de las fiestas de julio nacidas del asedio carlista sobre Castellón (sample article), El Grau se vuelca en las fiestas de la Virgen del Carmen (sample article), Castellón apoya a la selección española desde la plaza Mayor (sample article), Telegram channel mediterraneoelperiodico (sample web preview)

### Community 57 - ".llm"
Cohesion: 0.12
Nodes (9): 0010: Plugin classes and the configuration catalog, Consequences, Context, Rejected options, SummarizeOptions, merge_tags(), TaggerProcessor, factory() (+1 more)

### Community 58 - "deliveries table (the ledger)"
Cohesion: 0.33
Nodes (4): BaseSink deliver cycle (queue, select, send), deliveries table (the ledger), ADR 0005 Remixers with external side effects, Strict FIFO per source

### Community 59 - "SourceData"
Cohesion: 0.11
Nodes (15): SourceData, __newstool_plugin__(), __newstool_plugin__(), __newstool_plugin__(), Options, PluginOptions, __newstool_plugin__(), __newstool_plugin__() (+7 more)

### Community 61 - "Item"
Cohesion: 0.40
Nodes (3): IndexSiteProvider / URLProvider, Item, Provider

### Community 63 - "print_table"
Cohesion: 0.18
Nodes (6): print_apps(), print_emitted(), print_import(), print_process(), print_table(), workflow_phases()

### Community 64 - "PluginFailure"
Cohesion: 0.11
Nodes (5): PluginFailure, __newstool_plugin__(), SummarizeProcessor, ExternalErrorTests, LogFailureTests

### Community 65 - "SinkOptions"
Cohesion: 0.33
Nodes (4): StdoutSink, TelegramOptions, SinkOptions, StdoutSinkTests

### Community 66 - "ProcessorOptions"
Cohesion: 0.17
Nodes (6): MarkdownifyProcessor, ProcessorOptions, SkipItem, ClassRegisterTests, make_pdf(), MarkdownifyPdfTests

### Community 68 - "app.py"
Cohesion: 0.10
Nodes (4): LockedError, workflow_scope(), write_lock(), _sha256_column()

### Community 71 - "Delivery"
Cohesion: 0.14
Nodes (4): backoff_seconds(), DBDelivery, Delivery, Deliverer

### Community 72 - "app_from_context"
Cohesion: 0.17
Nodes (13): app_from_context(), apps_reset_cmd(), apps_run_cmd(), delete_items_cmd(), deliver_cmd(), import_cmd(), inspect_apps_cmd(), inspect_content_cmd() (+5 more)

### Community 73 - "foundation internal library"
Cohesion: 0.29
Nodes (7): foundation internal library, foundation.plugin.Register plugin loading, __newsmerger_plugin__(services, **options) entry point, PluginOptions (pydantic, unknown keys rejected), plugins configuration section, P1: plain logging and <APP>_LOG_LEVEL fix, P2: rich progress per stream (RICH_STDOUT_*/RICH_STDERR_*)

### Community 74 - "PlazaProvider"
Cohesion: 0.29
Nodes (3): get_section(), parse_datetime(), PlazaProvider

### Community 75 - "models.py"
Cohesion: 0.09
Nodes (10): Routes, reason(), Annotation, __newstool_plugin__(), __newstool_plugin__(), __newstool_plugin__(), accepts(), SinkType (+2 more)

### Community 76 - "workflows"
Cohesion: 0.33
Nodes (6): sink, workflows, deliver, name, process, sources

### Community 77 - "migrate"
Cohesion: 0.10
Nodes (10): columns(), has_table(), main(), migrate(), migrate_tables(), MigrationSummary, main(), migrate() (+2 more)

### Community 79 - ".content_dir"
Cohesion: 0.29
Nodes (3): Database & ORM Conventions, DTO, Protocol & ORM Implementation Reference, resolve_config_path()

### Community 82 - "PreflightSourceItemData"
Cohesion: 0.14
Nodes (3): PreflightSourceItemData, PreflightProvider, Provider

### Community 83 - "Base"
Cohesion: 0.29
Nodes (3): Base, DBItemAnnotation, DBProcessingState

### Community 84 - ".digest"
Cohesion: 0.21
Nodes (6): 0013: Plugin services at init, Consequences, Context, Decision, Rejected options, DigestAppletTests

### Community 87 - "PrensaIbericaProvider"
Cohesion: 0.16
Nodes (4): _extract_href(), _get_modified_at(), PrensaIbericaProvider, read_sample()

### Community 89 - "embed.py"
Cohesion: 0.21
Nodes (4): EmbedOptions, EmbedProcessor, __newstool_plugin__(), tags_text()

### Community 90 - "setup_logging"
Cohesion: 0.33
Nodes (4): Additional Approved Packages, Framework Usage, newstool Python Specifics, setup_logging()

### Community 91 - "ProcessorType"
Cohesion: 0.13
Nodes (5): __newstool_plugin__(), __newstool_plugin__(), __newstool_plugin__(), Processor, ProcessorType

### Community 95 - "0011: Environment overrides, relative paths and one storage directory"
Cohesion: 0.40
Nodes (4): 0011: Environment overrides, relative paths and one storage directory, Consequences, Context, Decision

### Community 105 - "0014: Ledger rows by subject and the workflow in delivery commands"
Cohesion: 0.33
Nodes (5): 0014: Ledger rows by subject and the workflow in delivery commands, Consequences, Context, Decision, Rejected options

### Community 106 - "0016: Routes on re-emission, manual queueing and pacing overrides"
Cohesion: 0.33
Nodes (5): 0016: Routes on re-emission, manual queueing and pacing overrides, Consequences, Context, Decision, Rejected options

## Knowledge Gaps
- **13 isolated node(s):** `newstool`, `External pipelines (scripts/pipeline_url.py)`, `Annotation`, `Telegram t.me/s channel preview HTML (tgme_widget_message, data-post)`, `IndexSiteProvider / URLProvider` (+8 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 588 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **34 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Application` connect `Application` to `ProcessingScope`, `catalog.py`, `Services`, `ApplicationTests`, `DocumentFilter`, `invoke`, `.from_text`, `Database`, `AppletReader`, `Document`, `SourceItem`, `cli.py`, `.get_annotation_values`, `Schedule`, `.process_keys`, `describe`, `run_delivery`, `SourceItemData`, `PacingOverride`, `AppletRun`, `HTTPClient`, `SourceData`, `.session_scope`, `print_table`, `app.py`, `Delivery`, `app_from_context`, `models.py`, `.from_file`, `PreflightSourceItemData`, `.digest`, `.close`, `.get_stored_content`?**
  _High betweenness centrality (0.107) - this node is a cross-community bridge._
- **Are the 31 inferred relationships involving `SourceItem` (e.g. with `Application` and `AppletReader`) actually correct?**
  _`SourceItem` has 31 INFERRED edges - model-reasoned connections that need verification._
- **What connects `newstool`, `External pipelines (scripts/pipeline_url.py)`, `Annotation` to the rest of the system?**
  _13 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `ProcessingScope` be split into smaller, more focused modules?**
  _Cohesion score 0.05826330532212885 - nodes in this community are weakly interconnected._
- **Why does `SourceItem` connect `SourceItem` to `ProcessingScope`, `Services`, `ApplicationTests`, `invoke`, `StubLLM`, `Database`, `AppletReader`, `DeleteCommandTests`, `feed.py`, `datetime`, `inspect_annotations_cmd`, `grouping.py`, `cli.py`, `.get_annotation_values`, `.add_items`, `Schedule`, `EmbeddingGroupingTests`, `Application`, `.llm`, `.close`, `PluginFailure`, `ProcessorOptions`, `app.py`, `models.py`, `PreflightSourceItemData`, `.digest`, `BaseProcessor`, `embed.py`?**
  _High betweenness centrality (0.099) - this node is a cross-community bridge._
- **Are the 24 inferred relationships involving `Database` (e.g. with `Context` and `Application`) actually correct?**
  _`Database` has 24 INFERRED edges - model-reasoned connections that need verification._
- **Should `catalog.py` be split into smaller, more focused modules?**
  _Cohesion score 0.047905909351692484 - nodes in this community are weakly interconnected._