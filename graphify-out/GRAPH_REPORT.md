# Graph Report - applets-decision  (2026-11-07)

## Corpus Check
- 79 files · ~185,541 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 4, .lock 1)

## Summary
- 1887 nodes · 5163 edges · 80 communities (58 shown, 22 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 639 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9d2cc259`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ProcessingScope
- ConfigError
- app.py
- ApplicationTests
- PluginFailure
- invoke
- .from_text
- Decision
- Database (db.py, only SQLite/storage access)
- StubLLM
- Entry
- inspect_apps_cmd
- CSJuntasGobiernoProvider
- DeleteCommandTests
- AppletRun
- TelegramSinkTests
- Deliverer
- TelegramChannelProvider
- ProcessorType
- Services
- .close
- Any
- AppletResult
- report_user_errors
- .emit
- DigestApplet
- Database
- OllamaLLM
- Document
- .get_items
- grouping.py
- cli.py
- migrate_applets.py
- .add_items
- plugins
- Schedule
- FileSinkTests
- Config
- 0014: Ledger rows by subject and the workflow in delivery commands
- ADR 0007 Sinks and the delivery ledger
- SourceData
- options
- hooks
- Services object (services.llm(name))
- GoogleChatSinkTests
- config.example.yaml
- Application
- SourceItem
- PreflightSourceItemData
- test_markdownify.py
- config.py
- newstool
- Processor
- El Periódico Mediterráneo
- LogFailureTests
- deliveries table (the ledger)
- catalog.py
- feed.py
- Item
- .__init__
- app_from_context
- SourceItemData
- HTTPClient
- Example sources (prensaiberica_plain, castelloninformacion, plaza, theguardian)
- .sources
- Artifact
- Grouping notes: NLP clustering pipeline
- .get_unprocessed_items
- foundation internal library
- workflows
- DocumentFilter
- TestSourceItemDataContent
- LogLevelTests
- Delivery
- PrensaIbericaProvider
- 0010: Plugin classes and the configuration catalog
- ADR 0002 Processing state lifecycle

## God Nodes (most connected - your core abstractions)
1. `SourceItem` - 105 edges
2. `Database` - 96 edges
3. `Services` - 86 edges
4. `Application` - 79 edges
5. `SourceData` - 74 edges
6. `PluginFailure` - 72 edges
7. `Document` - 66 edges
8. `ApplicationTests` - 64 edges
9. `SourceItemData` - 56 edges
10. `ProcessingScope` - 55 edges

## Surprising Connections (you probably didn't know these)
- `Reading` --references--> `AppletReader`  [INFERRED]
  docs/decisions/0015-applets-documents-and-routes.md → newstool/applets.py
- `Runs and state` --references--> `AppletRun`  [INFERRED]
  docs/decisions/0015-applets-documents-and-routes.md → newstool/models.py
- `Rejected options` --references--> `Services`  [INFERRED]
  docs/decisions/0013-plugin-services-at-init.md → newstool/plugins/__init__.py
- `Decision` --references--> `Application`  [INFERRED]
  docs/decisions/0010-plugin-classes-and-catalog.md → newstool/app.py
- `Decision` --references--> `Application`  [INFERRED]
  docs/decisions/0013-plugin-services-at-init.md → newstool/app.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **markdownify -> summarize/tagger -> embed -> grouping data chain** — docs_architecture_markdownify_processor, docs_architecture_summarize_processor, docs_architecture_tagger_processor, docs_architecture_embed_processor, docs_architecture_grouping_remixers [EXTRACTED 1.00]
- **Plugin protocol types consumed by the core** — docs_specification_provider, docs_specification_processor, docs_specification_remixer, docs_specification_sink, docs_decisions_0006_llm_plugins_llm_protocol [EXTRACTED 1.00]
- **Delivery ledger mechanism** — docs_architecture_deliveries_table, docs_decisions_0007_sinks_and_delivery_ledger_delivery_states, docs_architecture_basesink_cycle, docs_decisions_0007_sinks_and_delivery_ledger_strict_fifo_per_source, docs_decisions_0007_sinks_and_delivery_ledger_lookback_window, docs_specification_write_lock [INFERRED 0.85]
- **Prensa Ibérica sample article fixtures (El Periódico Mediterráneo, July 2026)** — tests_samples_prensaiberica_item_132310503_article, tests_samples_prensaiberica_item_132340038_article, tests_samples_prensaiberica_item_132344288_article [INFERRED 0.95]

## Communities (80 total, 22 thin omitted)

### Community 0 - "ProcessingScope"
Cohesion: 0.05
Nodes (23): 0012: Delivery ids, changing their state and forced send, Consequences, Context, Decision, Rejected options, Deliveries, wrapper(), DBDocument (+15 more)

### Community 1 - "ConfigError"
Cohesion: 0.07
Nodes (11): Catalog, check_section(), ids_of(), in_default(), Kind, process_key(), Profile, share_sources() (+3 more)

### Community 2 - "app.py"
Cohesion: 0.12
Nodes (4): check_result(), ProcessingStatus, _sha256_column(), Annotation

### Community 3 - "ApplicationTests"
Cohesion: 0.07
Nodes (7): ApplicationTests, retrieve(), retrieve_published(), retrieve(), same(), listed(), retrieved()

### Community 4 - "PluginFailure"
Cohesion: 0.07
Nodes (14): Decision, import_one(), describe(), log_failure(), PluginFailure, reason(), select_article(), __newstool_plugin__() (+6 more)

### Community 5 - "invoke"
Cohesion: 0.07
Nodes (9): AppReport, DeleteSummary, MarkSummary, RunSummary, annotation(), CommandTests, ExternalErrorTests, InspectCommandTests (+1 more)

### Community 6 - ".from_text"
Cohesion: 0.08
Nodes (3): AliasTests, ConfigTests, EnvironmentOverrideTests

### Community 7 - "Decision"
Cohesion: 0.17
Nodes (10): 0015: Applets, emitted documents and routes, CLI, Consequences, Context, Decision, Documents, Migration, Reading (+2 more)

### Community 8 - "Database (db.py, only SQLite/storage access)"
Cohesion: 0.17
Nodes (11): pre-commit config, ruff-check and ruff-format hooks, newsmerger CLAUDE.md agent guidelines, DTO/ORM from_dto/to_dto/update convention, Consumer-side Protocol decoupling convention, AUTOINCREMENT integer ids, Database (db.py, only SQLite/storage access), foundation.storage.DiskStorage content-addressed storage (+3 more)

### Community 9 - "StubLLM"
Cohesion: 0.20
Nodes (5): EmbedTests, ProcessorTestCase, StubLLM, SummarizeTests, TaggerTests

### Community 10 - "Entry"
Cohesion: 0.09
Nodes (4): AppEntry, Entry, LLMEntry, SinkEntry

### Community 11 - "inspect_apps_cmd"
Cohesion: 0.14
Nodes (10): Additional Approved Packages, Framework Usage, newstool Python Specifics, format_value(), inspect_apps_cmd(), json_default(), preview(), print_item() (+2 more)

### Community 12 - "CSJuntasGobiernoProvider"
Cohesion: 0.23
Nodes (6): CSJuntasGobiernoProvider, find_parent_by_tag_name(), get_date_from_text(), PreparseData, NoOptions, TestCSJuntasGobierno

### Community 14 - "AppletRun"
Cohesion: 0.07
Nodes (13): Applets, Applet, AppletType, BaseApplet, Requirements, DBApp, AppletRun, __newstool_plugin__() (+5 more)

### Community 15 - "TelegramSinkTests"
Cohesion: 0.11
Nodes (10): Schedule, build_caption(), post(), TelegramSink, BuildCaptionTests, item_document(), ok_response(), options() (+2 more)

### Community 17 - "TelegramChannelProvider"
Cohesion: 0.18
Nodes (6): is_home_page(), parse_article(), parse_preview(), Post, TelegramChannelProvider, TestTelegramChannel

### Community 18 - "ProcessorType"
Cohesion: 0.12
Nodes (6): Decision, __newstool_plugin__(), ClassRegister, __newstool_plugin__(), Processor, ProcessorType

### Community 19 - "Services"
Cohesion: 0.06
Nodes (15): LLM, LLMType, LLMUnavailableError, strip_code_fence(), EmbedOptions, EmbedProcessor, tags_text(), Services (+7 more)

### Community 21 - "Any"
Cohesion: 0.11
Nodes (3): CustomJSON, _encode_value(), UTCDateTime

### Community 22 - "AppletResult"
Cohesion: 0.17
Nodes (6): AppletResult, EmittedDocument, CheckResultTests, ReaderTests, DeliveryTests, emitted()

### Community 23 - "report_user_errors"
Cohesion: 0.15
Nodes (12): annotation_options(), check_found(), delete_annotations_cmd(), delete_items_cmd(), document_options(), wrapper(), inspect_annotations_cmd(), inspect_documents_cmd() (+4 more)

### Community 24 - ".emit"
Cohesion: 0.19
Nodes (4): CommitTests, DelivererTests, LedgerTestCase, RecordingSink

### Community 25 - "DigestApplet"
Cohesion: 0.15
Nodes (6): DigestApplet, DigestOptions, __newstool_plugin__(), DigestAppletTests, DigestPluginTests, factory()

### Community 27 - "OllamaLLM"
Cohesion: 0.21
Nodes (5): __newstool_plugin__(), ollama_client(), OllamaLLM, Options, OllamaTests

### Community 28 - "Document"
Cohesion: 0.07
Nodes (15): Routes, Sinks, Document, __newstool_plugin__(), build_card(), GoogleChatSink, merge_options(), __newstool_plugin__() (+7 more)

### Community 30 - "grouping.py"
Cohesion: 0.07
Nodes (21): AppletReader, average_between(), average_link_cluster(), AverageLinkApplet, build_score_matrix(), cosine_similarity(), EmbeddingsApplet, EmbeddingsOptions (+13 more)

### Community 31 - "cli.py"
Cohesion: 0.07
Nodes (13): apps_group(), cli(), delete_group(), deliveries_group(), describe_schedule(), format_seconds(), format_time(), inspect_group() (+5 more)

### Community 32 - "migrate_applets.py"
Cohesion: 0.07
Nodes (14): LockedError, write_lock(), Base, DBItemAnnotation, columns(), has_table(), main(), migrate() (+6 more)

### Community 33 - ".add_items"
Cohesion: 0.26
Nodes (4): GroupingOptions, AppletTestCase, GroupingTests, ItemFeedTests

### Community 34 - "plugins"
Cohesion: 0.12
Nodes (17): lookback, title, url, api_base, chat_model, embed_model, plugins, digest (+9 more)

### Community 36 - "FileSinkTests"
Cohesion: 0.17
Nodes (3): FileOptions, FileSink, FileSinkTests

### Community 37 - "Config"
Cohesion: 0.09
Nodes (8): Database & ORM Conventions, DTO, Protocol & ORM Implementation Reference, 0011: Environment overrides, relative paths and one storage directory, Consequences, Context, Decision, Config, DirectoryTests

### Community 38 - "0014: Ledger rows by subject and the workflow in delivery commands"
Cohesion: 0.33
Nodes (5): 0014: Ledger rows by subject and the workflow in delivery commands, Consequences, Context, Decision, Rejected options

### Community 39 - "ADR 0007 Sinks and the delivery ledger"
Cohesion: 0.21
Nodes (14): Architecture, cli.py Click commands, External pipelines (scripts/pipeline_url.py), ADR 0001 Item identity and change detection, ADR 0003 Plugin types and core scope, ADR 0004 Annotation and artifact contents on disk, ADR 0006 LLM plugins, ADR 0007 Sinks and the delivery ledger (+6 more)

### Community 40 - "SourceData"
Cohesion: 0.11
Nodes (6): DBSource, SourceData, CastellonInformacionProvider, PlazaProvider, TheGuardianProvider, IndexSiteProvider

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
Cohesion: 0.11
Nodes (8): chat_image_url(), __newstool_plugin__(), WebhookOptions, card_widgets(), ChatImageUrlTests, GoogleChatSinkTests, OptionsTests, webhook_options()

### Community 45 - "config.example.yaml"
Cohesion: 0.11
Nodes (15): cache, expiration, llms, input, processors, options, processor, remixers (+7 more)

### Community 46 - "Application"
Cohesion: 0.05
Nodes (4): Application, AppStatus, lookup(), AppInstance

### Community 48 - "PreflightSourceItemData"
Cohesion: 0.16
Nodes (3): PreflightSourceItemData, PreflightProvider, Provider

### Community 50 - "test_markdownify.py"
Cohesion: 0.12
Nodes (6): MarkdownifyProcessor, __newstool_plugin__(), SkipItem, ClassRegisterTests, make_pdf(), MarkdownifyPdfTests

### Community 51 - "config.py"
Cohesion: 0.06
Nodes (12): Alias, CacheConfig, EnvAliasSource, expand_variables(), load_context(), LoadContext, LoadEnvSettingsSource, MissingVariableError (+4 more)

### Community 54 - "Processor"
Cohesion: 0.29
Nodes (6): UnavailableProcessor / UnavailableRemixer / UnavailableSink, Annotation, Delivery, Exponential backoff 60s*2^(n-1), capped 24h, max_retries, Processor, Sink

### Community 55 - "El Periódico Mediterráneo"
Cohesion: 0.43
Nodes (7): El Periódico Mediterráneo, Prensa Ibérica article HTML format (og:/article: meta tags), Telegram t.me/s channel preview HTML (tgme_widget_message, data-post), El eco perdido de las fiestas de julio nacidas del asedio carlista sobre Castellón (sample article), El Grau se vuelca en las fiestas de la Virgen del Carmen (sample article), Castellón apoya a la selección española desde la plaza Mayor (sample article), Telegram channel mediterraneoelperiodico (sample web preview)

### Community 58 - "deliveries table (the ledger)"
Cohesion: 0.33
Nodes (4): BaseSink deliver cycle (queue, select, send), deliveries table (the ledger), ADR 0005 Remixers with external side effects, Strict FIFO per source

### Community 59 - "catalog.py"
Cohesion: 0.10
Nodes (16): __newstool_plugin__(), __newstool_plugin__(), __newstool_plugin__(), Options, PluginOptions, get_section(), __newstool_plugin__(), parse_datetime() (+8 more)

### Community 60 - "feed.py"
Cohesion: 0.17
Nodes (5): run_key(), SourcesOptions, FeedApplet, Options, FeedTests

### Community 61 - "Item"
Cohesion: 0.40
Nodes (3): IndexSiteProvider / URLProvider, Item, Provider

### Community 63 - "app_from_context"
Cohesion: 0.09
Nodes (17): app_from_context(), apps_reset_cmd(), apps_run_cmd(), deliver_cmd(), import_cmd(), import_sources(), inspect_content_cmd(), print_apps() (+9 more)

### Community 66 - "HTTPClient"
Cohesion: 0.09
Nodes (14): 0013: Plugin services at init, Consequences, Context, Rejected options, HTTPClient, discover_feed_url(), entry_date(), FeedReaderProvider (+6 more)

### Community 68 - ".sources"
Cohesion: 0.09
Nodes (10): 0009: Workflows and keyed entries, Consequences, Context, Decision, Rejected options, Configuration, Plugins, workflow_scope() (+2 more)

### Community 73 - "foundation internal library"
Cohesion: 0.29
Nodes (7): foundation internal library, foundation.plugin.Register plugin loading, __newsmerger_plugin__(services, **options) entry point, PluginOptions (pydantic, unknown keys rejected), plugins configuration section, P1: plain logging and <APP>_LOG_LEVEL fix, P2: rich progress per stream (RICH_STDOUT_*/RICH_STDERR_*)

### Community 76 - "workflows"
Cohesion: 0.33
Nodes (6): sink, workflows, deliver, name, process, sources

### Community 77 - "DocumentFilter"
Cohesion: 0.12
Nodes (13): check_all_rows(), delete_deliveries_cmd(), delete_documents_cmd(), deliveries_send_cmd(), deliveries_set_status_cmd(), delivery_filters(), delivery_options(), inspect_deliveries_cmd() (+5 more)

### Community 87 - "PrensaIbericaProvider"
Cohesion: 0.16
Nodes (4): _extract_href(), _get_modified_at(), PrensaIbericaProvider, read_sample()

### Community 89 - "0010: Plugin classes and the configuration catalog"
Cohesion: 0.40
Nodes (4): 0010: Plugin classes and the configuration catalog, Consequences, Context, Rejected options

## Knowledge Gaps
- **13 isolated node(s):** `newstool`, `External pipelines (scripts/pipeline_url.py)`, `Annotation`, `Telegram t.me/s channel preview HTML (tgme_widget_message, data-post)`, `IndexSiteProvider / URLProvider` (+8 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 566 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Database` connect `Database` to `ProcessingScope`, `app.py`, `StubLLM`, `DeleteCommandTests`, `AppletRun`, `Deliverer`, `Services`, `.close`, `Any`, `AppletResult`, `.emit`, `DigestApplet`, `Document`, `.get_items`, `grouping.py`, `.add_items`, `Config`, `SourceData`, `Application`, `SourceItem`, `.delete_documents`, `.delete_deliveries`, `.__init__`, `HTTPClient`, `.get_unprocessed_items`, `DocumentFilter`, `Delivery`?**
  _High betweenness centrality (0.105) - this node is a cross-community bridge._
- **Are the 28 inferred relationships involving `SourceItem` (e.g. with `Application` and `AppletReader`) actually correct?**
  _`SourceItem` has 28 INFERRED edges - model-reasoned connections that need verification._
- **What connects `newstool`, `External pipelines (scripts/pipeline_url.py)`, `Annotation` to the rest of the system?**
  _13 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `ProcessingScope` be split into smaller, more focused modules?**
  _Cohesion score 0.05236091631603553 - nodes in this community are weakly interconnected._
- **Why does `ADR 0008 inspect and delete CLI and numeric ids` connect `ADR 0007 Sinks and the delivery ledger` to `migrate_applets.py`?**
  _High betweenness centrality (0.102) - this node is a cross-community bridge._
- **Are the 23 inferred relationships involving `Database` (e.g. with `Context` and `Application`) actually correct?**
  _`Database` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Should `ConfigError` be split into smaller, more focused modules?**
  _Cohesion score 0.06883116883116883 - nodes in this community are weakly interconnected._