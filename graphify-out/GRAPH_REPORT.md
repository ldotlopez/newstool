# Graph Report - explicit-selection  (2026-11-10)

## Corpus Check
- 84 files · ~193,648 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 4, .lock 1)

## Summary
- 2018 nodes · 5569 edges · 99 communities (68 shown, 31 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 697 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `200e5baa`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ProcessingScope
- ConfigError
- plugins/__init__.py
- ApplicationTests
- DocumentFilter
- invoke
- .from_text
- Entry
- Database (db.py, only SQLite/storage access)
- StubLLM
- Database
- AppletReader
- csjuntasgobierno.py
- DeleteCommandTests
- expand_variables
- TelegramSinkTests
- TestFeedReader
- test_providers.py
- Sink
- .feed
- ItemFeedApplet
- datetime
- db.py
- ClassRegister
- DelivererTests
- Document
- chat_image_url
- OllamaLLM
- Delivery
- EmittedDocument
- grouping.py
- cli.py
- TelegramSink
- .add_items
- plugins
- Schedule
- WebhookOptions
- Requirements
- run_cmd
- ADR 0007 Sinks and the delivery ledger
- PluginFailure
- options
- hooks
- Services object (services.llm(name))
- GoogleChatSinkTests
- config.example.yaml
- Application
- print_table
- SourceItemData
- EnvAliasSource
- AppletRun
- newstool
- Processor
- El Periódico Mediterráneo
- HTTPClient
- Services
- deliveries table (the ledger)
- feedreader.py
- .close
- Item
- ProcessEntry
- SourceItem
- apps_run_cmd
- BaseProcessor
- Example sources (prensaiberica_plain, castelloninformacion, plaza, theguardian)
- app.py
- Artifact
- Grouping notes: NLP clustering pipeline
- .key
- app_from_context
- foundation internal library
- plaza.py
- sinks.py
- workflows
- migrate_applets.py
- TestSourceItemDataContent
- load_context
- LogLevelTests
- .from_file
- PreflightSourceItemData
- MarkdownifyProcessor
- .get_unprocessed_items
- .digest
- .__init__
- DeliveryTests
- EmbedProcessor
- GroupingTests
- accepts
- Config
- AliasTests
- ADR 0002 Processing state lifecycle
- SourceData
- applets.py
- 0016: Routes on re-emission, manual queueing and pacing overrides

## God Nodes (most connected - your core abstractions)
1. `SourceItem` - 111 edges
2. `Database` - 103 edges
3. `Application` - 93 edges
4. `Services` - 92 edges
5. `SourceData` - 74 edges
6. `PluginFailure` - 72 edges
7. `Document` - 72 edges
8. `ApplicationTests` - 70 edges
9. `SourceItemData` - 56 edges
10. `ProcessingScope` - 53 edges

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

## Communities (99 total, 31 thin omitted)

### Community 0 - "ProcessingScope"
Cohesion: 0.06
Nodes (20): 0012: Delivery ids, changing their state and forced send, Consequences, Context, Decision, Rejected options, Deliveries, wrapper(), DBSourceItem (+12 more)

### Community 1 - "ConfigError"
Cohesion: 0.07
Nodes (8): Catalog, check_section(), Kind, process_key(), Profile, share_sources(), ConfigError, options_error()

### Community 2 - "plugins/__init__.py"
Cohesion: 0.09
Nodes (14): Decision, LLMType, strip_code_fence(), EmbedOptions, __newstool_plugin__(), UsesLLMOptions, __newstool_plugin__(), __newstool_plugin__() (+6 more)

### Community 3 - "ApplicationTests"
Cohesion: 0.07
Nodes (7): ApplicationTests, retrieve(), retrieve_published(), retrieve(), same(), listed(), retrieved()

### Community 4 - "DocumentFilter"
Cohesion: 0.12
Nodes (8): check_all_rows(), delivery_filters(), document_options(), wrapper(), wrapper(), selection_options(), decorate(), DocumentFilter

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
Cohesion: 0.16
Nodes (6): Processor, EmbedTests, ProcessorTestCase, StubLLM, SummarizeTests, TaggerTests

### Community 10 - "Database"
Cohesion: 0.14
Nodes (3): Database, MigrateAppletsTests, sha256()

### Community 11 - "AppletReader"
Cohesion: 0.12
Nodes (6): AppletReader, BaseApplet, DigestApplet, AverageLinkApplet, GroupingApplet, SingleLinkApplet

### Community 12 - "csjuntasgobierno.py"
Cohesion: 0.16
Nodes (8): CSJuntasGobiernoProvider, find_parent_by_tag_name(), get_date_from_text(), __newstool_plugin__(), PreparseData, NoOptions, BaseProvider, TestCSJuntasGobierno

### Community 15 - "TelegramSinkTests"
Cohesion: 0.22
Nodes (7): Schedule, run(), item_document(), ok_response(), options(), sink(), TelegramSinkTests

### Community 16 - "TestFeedReader"
Cohesion: 0.22
Nodes (3): FeedReaderProvider, select_article(), TestFeedReader

### Community 17 - "test_providers.py"
Cohesion: 0.10
Nodes (16): Additional Approved Packages, Framework Usage, newstool Python Specifics, Options, PluginOptions, Options, is_home_page(), __newstool_plugin__() (+8 more)

### Community 21 - "datetime"
Cohesion: 0.14
Nodes (3): CustomJSON, _encode_value(), UTCDateTime

### Community 22 - "db.py"
Cohesion: 0.15
Nodes (5): DeliveryStatus, ProcessingStatus, _sha256_column(), Annotation, AppletResult

### Community 24 - "DelivererTests"
Cohesion: 0.16
Nodes (6): CommitTests, DelivererTests, DeliveryOrderTests, emitted(), LedgerTestCase, RecordingSink

### Community 25 - "Document"
Cohesion: 0.09
Nodes (9): CommittedRun, DBDocument, Document, FileOptions, FileSink, StdoutSink, SinkOptions, FileSinkTests (+1 more)

### Community 26 - "chat_image_url"
Cohesion: 0.25
Nodes (3): build_card(), chat_image_url(), ChatImageUrlTests

### Community 27 - "OllamaLLM"
Cohesion: 0.21
Nodes (5): __newstool_plugin__(), ollama_client(), OllamaLLM, Options, OllamaTests

### Community 28 - "Delivery"
Cohesion: 0.16
Nodes (3): DBDelivery, Delivery, Deliverer

### Community 29 - "EmittedDocument"
Cohesion: 0.19
Nodes (5): EmittedDocument, CheckResultTests, ReaderTests, DocumentTests, keys()

### Community 30 - "grouping.py"
Cohesion: 0.12
Nodes (15): average_between(), average_link_cluster(), build_score_matrix(), cosine_similarity(), EmbeddingsApplet, item_ref(), jaccard(), member_payload() (+7 more)

### Community 31 - "cli.py"
Cohesion: 0.06
Nodes (17): apps_group(), apps_phase(), cli(), delete_group(), deliveries_group(), delivery_phase(), describe_schedule(), failed_report() (+9 more)

### Community 32 - "TelegramSink"
Cohesion: 0.16
Nodes (4): build_caption(), post(), TelegramSink, BuildCaptionTests

### Community 33 - ".add_items"
Cohesion: 0.27
Nodes (3): ItemFeedOptions, AppletTestCase, ItemFeedTests

### Community 34 - "plugins"
Cohesion: 0.12
Nodes (17): lookback, title, url, api_base, chat_model, embed_model, plugins, digest (+9 more)

### Community 35 - "Schedule"
Cohesion: 0.05
Nodes (28): 0009: Workflows and keyed entries, Consequences, Context, Decision, Rejected options, 0015: Applets, emitted documents and routes, Applets, CLI (+20 more)

### Community 36 - "WebhookOptions"
Cohesion: 0.18
Nodes (4): __newstool_plugin__(), WebhookOptions, OptionsTests, webhook_options()

### Community 37 - "Requirements"
Cohesion: 0.25
Nodes (3): Requirements, EmbeddingsOptions, EmbeddingGroupingTests

### Community 38 - "run_cmd"
Cohesion: 0.14
Nodes (7): import_cmd(), routed_from(), run_cmd(), selected_apps(), selected_sinks(), selected_workflows(), workflows_cmd()

### Community 39 - "ADR 0007 Sinks and the delivery ledger"
Cohesion: 0.21
Nodes (14): Architecture, cli.py Click commands, External pipelines (scripts/pipeline_url.py), ADR 0001 Item identity and change detection, ADR 0003 Plugin types and core scope, ADR 0004 Annotation and artifact contents on disk, ADR 0006 LLM plugins, ADR 0007 Sinks and the delivery ledger (+6 more)

### Community 40 - "PluginFailure"
Cohesion: 0.09
Nodes (7): import_failed(), describe(), PluginFailure, CastellonInformacionProvider, TheGuardianProvider, DescribeTests, LogFailureTests

### Community 41 - "options"
Cohesion: 0.15
Nodes (14): options, artifacts, chat_id, interval, item_image, item_url_preview, item_url_text, markdown (+6 more)

### Community 42 - "hooks"
Cohesion: 0.15
Nodes (12): exclude, args, entry, files, id, language, name, pass_filenames (+4 more)

### Community 43 - "Services object (services.llm(name))"
Cohesion: 0.22
Nodes (12): digest remixer, embed processor, grouping remixers (singlelink, avglink, embeddings), markdownify processor, summarize processor, tagger processor, telegram bundle (telegram, telegram_artifacts sinks), LLM plugins must be listed before their consumers (+4 more)

### Community 45 - "config.example.yaml"
Cohesion: 0.11
Nodes (15): cache, expiration, llms, input, processors, options, processor, remixers (+7 more)

### Community 46 - "Application"
Cohesion: 0.05
Nodes (9): Application, lookup(), deliver_each(), failed_summary(), import_sources(), process_workflow(), run_each(), workflow_phases() (+1 more)

### Community 47 - "print_table"
Cohesion: 0.12
Nodes (10): format_value(), json_default(), preview(), print_apps(), print_emitted(), print_import(), print_item(), print_process() (+2 more)

### Community 48 - "SourceItemData"
Cohesion: 0.12
Nodes (5): SourceItemData, _extract_href(), PrensaIbericaProvider, read_sample(), TestPrensaIberica

### Community 51 - "EnvAliasSource"
Cohesion: 0.11
Nodes (3): EnvAliasSource, LLMEntry, parse_duration()

### Community 54 - "Processor"
Cohesion: 0.29
Nodes (6): UnavailableProcessor / UnavailableRemixer / UnavailableSink, Annotation, Delivery, Exponential backoff 60s*2^(n-1), capped 24h, max_retries, Processor, Sink

### Community 55 - "El Periódico Mediterráneo"
Cohesion: 0.43
Nodes (7): El Periódico Mediterráneo, Prensa Ibérica article HTML format (og:/article: meta tags), Telegram t.me/s channel preview HTML (tgme_widget_message, data-post), El eco perdido de las fiestas de julio nacidas del asedio carlista sobre Castellón (sample article), El Grau se vuelca en las fiestas de la Virgen del Carmen (sample article), Castellón apoya a la selección española desde la plaza Mayor (sample article), Telegram channel mediterraneoelperiodico (sample web preview)

### Community 56 - "HTTPClient"
Cohesion: 0.15
Nodes (8): 0013: Plugin services at init, Consequences, Context, Decision, Rejected options, HTTPClient, fetch_article(), TestHTTPClient

### Community 57 - "Services"
Cohesion: 0.07
Nodes (11): LLM, LLMUnavailableError, DigestOptions, __newstool_plugin__(), GoogleChatSink, Services, DigestPluginTests, factory() (+3 more)

### Community 58 - "deliveries table (the ledger)"
Cohesion: 0.33
Nodes (4): BaseSink deliver cycle (queue, select, send), deliveries table (the ledger), ADR 0005 Remixers with external side effects, Strict FIFO per source

### Community 59 - "feedreader.py"
Cohesion: 0.15
Nodes (11): __newstool_plugin__(), discover_feed_url(), entry_date(), fetch_feed(), find_image(), __newstool_plugin__(), parse_entry(), _get_modified_at() (+3 more)

### Community 61 - "Item"
Cohesion: 0.40
Nodes (3): IndexSiteProvider / URLProvider, Item, Provider

### Community 63 - "ProcessEntry"
Cohesion: 0.25
Nodes (4): ids_of(), in_default(), Use, ProcessEntry

### Community 64 - "SourceItem"
Cohesion: 0.17
Nodes (5): SourceItem, SummarizeProcessor, merge_tags(), TaggerProcessor, TruncateProcessor

### Community 65 - "apps_run_cmd"
Cohesion: 0.19
Nodes (5): apps_reset_cmd(), apps_run_cmd(), deliver_cmd(), progress_rows(), run_delivery()

### Community 68 - "app.py"
Cohesion: 0.09
Nodes (7): AppStatus, workflow_scope(), AppInstance, Run, Alias, CacheConfig, Workflow

### Community 71 - ".key"
Cohesion: 0.14
Nodes (9): 0010: Plugin classes and the configuration catalog, Consequences, Context, Rejected options, 0014: Ledger rows by subject and the workflow in delivery commands, Consequences, Context, Decision (+1 more)

### Community 72 - "app_from_context"
Cohesion: 0.11
Nodes (24): annotation_options(), app_from_context(), check_found(), delete_annotations_cmd(), delete_deliveries_cmd(), delete_documents_cmd(), delete_items_cmd(), deliveries_rename_cmd() (+16 more)

### Community 73 - "foundation internal library"
Cohesion: 0.29
Nodes (7): foundation internal library, foundation.plugin.Register plugin loading, __newsmerger_plugin__(services, **options) entry point, PluginOptions (pydantic, unknown keys rejected), plugins configuration section, P1: plain logging and <APP>_LOG_LEVEL fix, P2: rich progress per stream (RICH_STDOUT_*/RICH_STDERR_*)

### Community 74 - "plaza.py"
Cohesion: 0.21
Nodes (4): get_section(), __newstool_plugin__(), parse_datetime(), PlazaProvider

### Community 75 - "sinks.py"
Cohesion: 0.09
Nodes (10): backoff_seconds(), log_failure(), reason(), __newstool_plugin__(), merge_options(), __newstool_plugin__(), __newstool_plugin__(), TelegramOptions (+2 more)

### Community 76 - "workflows"
Cohesion: 0.33
Nodes (6): sink, workflows, deliver, name, process, sources

### Community 77 - "migrate_applets.py"
Cohesion: 0.08
Nodes (14): LockedError, write_lock(), Base, DBItemAnnotation, columns(), has_table(), main(), migrate() (+6 more)

### Community 79 - "load_context"
Cohesion: 0.13
Nodes (6): Database & ORM Conventions, DTO, Protocol & ORM Implementation Reference, load_context(), LoadContext, LoadEnvSettingsSource, resolve_config_path()

### Community 82 - "PreflightSourceItemData"
Cohesion: 0.16
Nodes (3): PreflightSourceItemData, PreflightProvider, Provider

### Community 83 - "MarkdownifyProcessor"
Cohesion: 0.32
Nodes (4): MarkdownifyProcessor, SkipItem, make_pdf(), MarkdownifyPdfTests

### Community 90 - "accepts"
Cohesion: 0.33
Nodes (3): Routes, accepts(), AcceptsTests

### Community 92 - "Config"
Cohesion: 0.09
Nodes (6): 0011: Environment overrides, relative paths and one storage directory, Consequences, Context, Decision, Config, DirectoryTests

### Community 98 - "SourceData"
Cohesion: 0.18
Nodes (3): DBSource, SourceData, IndexSiteProvider

### Community 99 - "applets.py"
Cohesion: 0.10
Nodes (9): AppletType, check_result(), run_key(), SourcesOptions, __newstool_plugin__(), Options, __newstool_plugin__(), __newstool_plugin__() (+1 more)

### Community 106 - "0016: Routes on re-emission, manual queueing and pacing overrides"
Cohesion: 0.33
Nodes (5): 0016: Routes on re-emission, manual queueing and pacing overrides, Consequences, Context, Decision, Rejected options

## Knowledge Gaps
- **13 isolated node(s):** `newstool`, `External pipelines (scripts/pipeline_url.py)`, `Annotation`, `Telegram t.me/s channel preview HTML (tgme_widget_message, data-post)`, `IndexSiteProvider / URLProvider` (+8 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 606 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **31 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SourceItem` connect `SourceItem` to `ProcessingScope`, `plugins/__init__.py`, `ApplicationTests`, `invoke`, `StubLLM`, `Database`, `AppletReader`, `DeleteCommandTests`, `.feed`, `ItemFeedApplet`, `datetime`, `db.py`, `grouping.py`, `cli.py`, `.add_items`, `Schedule`, `Application`, `print_table`, `.close`, `BaseProcessor`, `app.py`, `.key`, `MarkdownifyProcessor`, `.get_unprocessed_items`, `.digest`, `EmbedProcessor`, `GroupingTests`, `.get_content`, `SourceData`, `applets.py`?**
  _High betweenness centrality (0.128) - this node is a cross-community bridge._
- **Are the 30 inferred relationships involving `SourceItem` (e.g. with `Application` and `AppletReader`) actually correct?**
  _`SourceItem` has 30 INFERRED edges - model-reasoned connections that need verification._
- **What connects `newstool`, `External pipelines (scripts/pipeline_url.py)`, `Annotation` to the rest of the system?**
  _13 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `ProcessingScope` be split into smaller, more focused modules?**
  _Cohesion score 0.06265432098765432 - nodes in this community are weakly interconnected._
- **Why does `Application` connect `Application` to `ProcessingScope`, `ConfigError`, `plugins/__init__.py`, `ApplicationTests`, `DocumentFilter`, `invoke`, `.from_text`, `Database`, `AppletReader`, `db.py`, `Document`, `Delivery`, `cli.py`, `Schedule`, `run_cmd`, `SourceItemData`, `._release_contents`, `AppletRun`, `HTTPClient`, `Services`, `.session_scope`, `SourceItem`, `apps_run_cmd`, `app.py`, `app_from_context`, `.from_file`, `PreflightSourceItemData`, `.get_content`, `Config`, `.get_annotation_keys`, `SourceData`?**
  _High betweenness centrality (0.111) - this node is a cross-community bridge._
- **Are the 24 inferred relationships involving `Database` (e.g. with `Context` and `Application`) actually correct?**
  _`Database` has 24 INFERRED edges - model-reasoned connections that need verification._
- **Should `ConfigError` be split into smaller, more focused modules?**
  _Cohesion score 0.07372549019607844 - nodes in this community are weakly interconnected._