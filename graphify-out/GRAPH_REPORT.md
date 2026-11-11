# Graph Report - digest-plan  (2026-11-11)

## Corpus Check
- 80 files · ~195,033 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 4, .lock 1)

## Summary
- 2009 nodes · 5463 edges · 96 communities (69 shown, 27 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 669 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6f344646`
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
- itemfeed.py
- test_providers.py
- DeleteCommandTests
- .add_item
- TelegramSinkTests
- HTTPClient
- AppletReader
- Document
- AppletResult
- datetime
- test_db.py
- describe
- Delivery
- .settings_customise_sources
- ProcessingTests
- OllamaLLM
- Deliverer
- reason
- DigestOptions
- cli.py
- TelegramSink
- .add_items
- plugins
- .summary
- WebhookOptions
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
- Database
- apps_run_cmd
- GoogleChatSinkTests
- ._object
- SourceData
- newstool
- Processor
- El Periódico Mediterráneo
- DirectoryTests
- ProcessingScope
- deliveries table (the ledger)
- errors.py
- AppletRun
- Item
- inspect_annotations_cmd
- FileSinkTests
- Delivery
- MarkdownifyProcessor
- Example sources (prensaiberica_plain, castelloninformacion, plaza, theguardian)
- feed.py
- Artifact
- Grouping notes: NLP clustering pipeline
- ClassRegister
- chat_image_url
- foundation internal library
- 0018: Annotations hold their run state; a content change deletes them
- app.py
- workflows
- .summary
- TestSourceItemDataContent
- config.py
- LogLevelTests
- errors.py
- Matrix
- DocumentTests
- Decision
- .__init__
- PacingOverride
- PreflightSourceItemData
- process_cmd
- Config
- ADR 0002 Processing state lifecycle
- AppletType
- 0012: Delivery ids, changing their state and forced send
- 0014: Ledger rows by subject and the workflow in delivery commands
- 0016: Routes on re-emission, manual queueing and pacing overrides

## God Nodes (most connected - your core abstractions)
1. `SourceItem` - 103 edges
2. `Database` - 95 edges
3. `Services` - 95 edges
4. `Application` - 93 edges
5. `PluginFailure` - 80 edges
6. `Document` - 72 edges
7. `ApplicationTests` - 70 edges
8. `SourceData` - 69 edges
9. `SourceItemData` - 56 edges
10. `ProcessingScope` - 53 edges

## Surprising Connections (you probably didn't know these)
- `Reading` --references--> `AppletReader`  [INFERRED]
  docs/decisions/0015-applets-documents-and-routes.md → newstool/applets.py
- `Decision` --references--> `Database`  [INFERRED]
  docs/decisions/0018-annotations-hold-their-run-state.md → newstool/db.py
- `Runs and state` --references--> `AppletRun`  [INFERRED]
  docs/decisions/0015-applets-documents-and-routes.md → newstool/models.py
- `Rejected options` --references--> `Services`  [INFERRED]
  docs/decisions/0013-plugin-services-at-init.md → newstool/plugins/__init__.py
- `Routes` --references--> `accepts()`  [INFERRED]
  docs/decisions/0015-applets-documents-and-routes.md → newstool/sinks.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **markdownify -> summarize/tagger -> embed -> grouping data chain** — docs_architecture_markdownify_processor, docs_architecture_summarize_processor, docs_architecture_tagger_processor, docs_architecture_embed_processor, docs_architecture_grouping_remixers [EXTRACTED 1.00]
- **Plugin protocol types consumed by the core** — docs_specification_provider, docs_specification_processor, docs_specification_remixer, docs_specification_sink, docs_decisions_0006_llm_plugins_llm_protocol [EXTRACTED 1.00]
- **Delivery ledger mechanism** — docs_architecture_deliveries_table, docs_decisions_0007_sinks_and_delivery_ledger_delivery_states, docs_architecture_basesink_cycle, docs_decisions_0007_sinks_and_delivery_ledger_strict_fifo_per_source, docs_decisions_0007_sinks_and_delivery_ledger_lookback_window, docs_specification_write_lock [INFERRED 0.85]
- **Prensa Ibérica sample article fixtures (El Periódico Mediterráneo, July 2026)** — tests_samples_prensaiberica_item_132310503_article, tests_samples_prensaiberica_item_132340038_article, tests_samples_prensaiberica_item_132344288_article [INFERRED 0.95]

## Communities (96 total, 27 thin omitted)

### Community 0 - "make_item"
Cohesion: 0.22
Nodes (4): ContentStorageTests, make_item(), make_source(), UpsertSourceItemsTests

### Community 1 - "catalog.py"
Cohesion: 0.07
Nodes (13): Catalog, check_section(), ids_of(), in_default(), Kind, process_key(), Profile, Run (+5 more)

### Community 2 - "Services"
Cohesion: 0.04
Nodes (35): Decision, Decision, PluginFailure, LLM, LLMType, LLMUnavailableError, strip_code_fence(), classify_prompt() (+27 more)

### Community 3 - "ApplicationTests"
Cohesion: 0.06
Nodes (9): LockedError, write_lock(), ApplicationTests, retrieve(), retrieve_published(), retrieve(), same(), listed() (+1 more)

### Community 4 - "scope_options"
Cohesion: 0.24
Nodes (5): annotation_options(), wrapper(), scope_options(), selection_options(), decorate()

### Community 5 - "invoke"
Cohesion: 0.06
Nodes (9): AppReport, DeleteSummary, MarkSummary, RunSummary, annotation(), CommandTests, ExternalErrorTests, InspectCommandTests (+1 more)

### Community 6 - ".from_text"
Cohesion: 0.07
Nodes (3): AliasTests, ConfigTests, EnvironmentOverrideTests

### Community 7 - "Entry"
Cohesion: 0.15
Nodes (3): AppEntry, Entry, SinkEntry

### Community 8 - "Database (db.py, only SQLite/storage access)"
Cohesion: 0.17
Nodes (11): pre-commit config, ruff-check and ruff-format hooks, newsmerger CLAUDE.md agent guidelines, DTO/ORM from_dto/to_dto/update convention, Consumer-side Protocol decoupling convention, AUTOINCREMENT integer ids, Database (db.py, only SQLite/storage access), foundation.storage.DiskStorage content-addressed storage (+3 more)

### Community 9 - "StubLLM"
Cohesion: 0.15
Nodes (7): Processor, ClassifyTests, EmbedTests, ProcessorTestCase, StubLLM, SummarizeTests, TaggerTests

### Community 10 - "SourceItem"
Cohesion: 0.13
Nodes (3): DBSourceItem, SourceItem, TruncateProcessor

### Community 11 - "itemfeed.py"
Cohesion: 0.12
Nodes (3): BaseApplet, Requirements, ItemFeedApplet

### Community 12 - "test_providers.py"
Cohesion: 0.11
Nodes (13): Options, NoOptions, PluginOptions, Options, is_home_page(), Options, page_title(), parse_article() (+5 more)

### Community 14 - ".add_item"
Cohesion: 0.24
Nodes (3): DigestAppletTests, DigestGroupingTests, DigestTestCase

### Community 15 - "TelegramSinkTests"
Cohesion: 0.24
Nodes (6): Schedule, item_document(), ok_response(), options(), sink(), TelegramSinkTests

### Community 16 - "HTTPClient"
Cohesion: 0.09
Nodes (14): 0013: Plugin services at init, Consequences, Context, Rejected options, HTTPClient, discover_feed_url(), entry_date(), FeedReaderProvider (+6 more)

### Community 17 - "AppletReader"
Cohesion: 0.10
Nodes (10): AppletReader, as_vector(), DigestApplet, labels_of(), lowered(), period(), plan_payload(), read_candidates() (+2 more)

### Community 18 - "Document"
Cohesion: 0.10
Nodes (5): Base, CommittedRun, DBDocument, Document, FileSink

### Community 20 - "AppletResult"
Cohesion: 0.13
Nodes (7): check_result(), AppletResult, EmittedDocument, CheckResultTests, ReaderTests, DeliveryTests, JSONColumnTests

### Community 21 - "datetime"
Cohesion: 0.14
Nodes (3): CustomJSON, _encode_value(), UTCDateTime

### Community 22 - "test_db.py"
Cohesion: 0.17
Nodes (5): DBItemAnnotation, next_annotation(), ProcessingStatus, Annotation, NextAnnotationTests

### Community 23 - "describe"
Cohesion: 0.09
Nodes (11): apps_phase(), deliver_each(), failed_report(), failed_summary(), import_sources(), import_failed(), process_workflow(), run_each() (+3 more)

### Community 24 - "Delivery"
Cohesion: 0.14
Nodes (6): CommitTests, DelivererTests, DeliveryOrderTests, emitted(), LedgerTestCase, RecordingSink

### Community 27 - "OllamaLLM"
Cohesion: 0.21
Nodes (5): __newstool_plugin__(), ollama_client(), OllamaLLM, Options, OllamaTests

### Community 30 - "DigestOptions"
Cohesion: 0.13
Nodes (12): Candidate, cosine_similarity(), DigestOptions, jaccard(), pair_score(), published_timestamp(), score_matrix(), select_stories() (+4 more)

### Community 31 - "cli.py"
Cohesion: 0.08
Nodes (11): apps_group(), delete_group(), deliveries_group(), describe_schedule(), format_seconds(), format_time(), inspect_group(), lexer_for() (+3 more)

### Community 32 - "TelegramSink"
Cohesion: 0.22
Nodes (4): build_caption(), post(), TelegramSink, BuildCaptionTests

### Community 33 - ".add_items"
Cohesion: 0.23
Nodes (5): DBApp, AppletRun, ItemFeedOptions, AppletTestCase, ItemFeedTests

### Community 34 - "plugins"
Cohesion: 0.12
Nodes (17): lookback, title, url, api_base, chat_model, embed_model, plugins, digest (+9 more)

### Community 35 - ".summary"
Cohesion: 0.09
Nodes (15): 0009: Workflows and keyed entries, Consequences, Context, Decision, Rejected options, 0010: Plugin classes and the configuration catalog, Consequences, Context (+7 more)

### Community 36 - "WebhookOptions"
Cohesion: 0.17
Nodes (4): __newstool_plugin__(), WebhookOptions, OptionsTests, webhook_options()

### Community 38 - "app_from_context"
Cohesion: 0.10
Nodes (26): app_from_context(), check_all_rows(), check_found(), delete_annotations_cmd(), delete_deliveries_cmd(), delete_documents_cmd(), delete_items_cmd(), deliveries_rename_cmd() (+18 more)

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
Cohesion: 0.17
Nodes (5): ConnectionTests, ContentChangeTests, DatabaseTestCase, DeleteTests, IdentityTests

### Community 45 - "config.example.yaml"
Cohesion: 0.11
Nodes (15): cache, expiration, llms, input, processors, options, processor, remixers (+7 more)

### Community 46 - "Application"
Cohesion: 0.07
Nodes (6): Application, lookup(), AppInstance, routed_from(), selected_apps(), selected_sinks()

### Community 48 - "apps_run_cmd"
Cohesion: 0.16
Nodes (5): apps_reset_cmd(), apps_run_cmd(), cli(), deliver_cmd(), run_delivery()

### Community 50 - "GoogleChatSinkTests"
Cohesion: 0.33
Nodes (3): GoogleChatSink, card_widgets(), GoogleChatSinkTests

### Community 52 - "SourceData"
Cohesion: 0.08
Nodes (10): DBSource, SourceData, SourceItemData, CastellonInformacionProvider, get_section(), parse_datetime(), PlazaProvider, TheGuardianProvider (+2 more)

### Community 54 - "Processor"
Cohesion: 0.29
Nodes (6): UnavailableProcessor / UnavailableRemixer / UnavailableSink, Annotation, Delivery, Exponential backoff 60s*2^(n-1), capped 24h, max_retries, Processor, Sink

### Community 55 - "El Periódico Mediterráneo"
Cohesion: 0.43
Nodes (7): El Periódico Mediterráneo, Prensa Ibérica article HTML format (og:/article: meta tags), Telegram t.me/s channel preview HTML (tgme_widget_message, data-post), El eco perdido de las fiestas de julio nacidas del asedio carlista sobre Castellón (sample article), El Grau se vuelca en las fiestas de la Virgen del Carmen (sample article), Castellón apoya a la selección española desde la plaza Mayor (sample article), Telegram channel mediterraneoelperiodico (sample web preview)

### Community 57 - "ProcessingScope"
Cohesion: 0.33
Nodes (3): wrapper(), ProcessingScope, GetItemsTests

### Community 58 - "deliveries table (the ledger)"
Cohesion: 0.33
Nodes (4): BaseSink deliver cycle (queue, select, send), deliveries table (the ledger), ADR 0005 Remixers with external side effects, Strict FIFO per source

### Community 59 - "errors.py"
Cohesion: 0.12
Nodes (10): __newstool_plugin__(), __newstool_plugin__(), __newstool_plugin__(), select_article(), __newstool_plugin__(), __newstool_plugin__(), __newstool_plugin__(), __newstool_plugin__() (+2 more)

### Community 61 - "Item"
Cohesion: 0.40
Nodes (3): IndexSiteProvider / URLProvider, Item, Provider

### Community 63 - "inspect_annotations_cmd"
Cohesion: 0.11
Nodes (13): Additional Approved Packages, Framework Usage, newstool Python Specifics, format_value(), json_default(), preview(), print_apps(), print_emitted() (+5 more)

### Community 64 - "FileSinkTests"
Cohesion: 0.21
Nodes (3): FileOptions, run(), FileSinkTests

### Community 66 - "MarkdownifyProcessor"
Cohesion: 0.23
Nodes (5): MarkdownifyProcessor, SkipItem, ClassRegisterTests, make_pdf(), MarkdownifyPdfTests

### Community 68 - "feed.py"
Cohesion: 0.18
Nodes (4): SourcesOptions, FeedApplet, Options, FeedTests

### Community 72 - "chat_image_url"
Cohesion: 0.29
Nodes (3): build_card(), chat_image_url(), ChatImageUrlTests

### Community 73 - "foundation internal library"
Cohesion: 0.29
Nodes (7): foundation internal library, foundation.plugin.Register plugin loading, __newsmerger_plugin__(services, **options) entry point, PluginOptions (pydantic, unknown keys rejected), plugins configuration section, P1: plain logging and <APP>_LOG_LEVEL fix, P2: rich progress per stream (RICH_STDOUT_*/RICH_STDERR_*)

### Community 74 - "0018: Annotations hold their run state; a content change deletes them"
Cohesion: 0.40
Nodes (4): 0018: Annotations hold their run state; a content change deletes them, Consequences, Context, Decision

### Community 75 - "app.py"
Cohesion: 0.08
Nodes (3): run_key(), _sha256_column(), __newstool_plugin__()

### Community 76 - "workflows"
Cohesion: 0.33
Nodes (6): sink, workflows, deliver, name, process, sources

### Community 79 - "config.py"
Cohesion: 0.07
Nodes (10): Alias, CacheConfig, expand_variables(), load_context(), LoadContext, LoadEnvSettingsSource, MissingVariableError, ollama_url() (+2 more)

### Community 81 - "errors.py"
Cohesion: 0.09
Nodes (13): Sinks, __newstool_plugin__(), merge_options(), __newstool_plugin__(), StdoutSink, __newstool_plugin__(), TelegramOptions, accepts() (+5 more)

### Community 82 - "Matrix"
Cohesion: 0.33
Nodes (3): average_between(), average_link_clusters(), single_link_clusters()

### Community 85 - "Decision"
Cohesion: 0.14
Nodes (12): 0015: Applets, emitted documents and routes, CLI, Consequences, Context, Decision, Documents, Migration, Plugins (+4 more)

### Community 87 - "PacingOverride"
Cohesion: 0.12
Nodes (3): AppStatus, PacingOverride, Sink

### Community 88 - "PreflightSourceItemData"
Cohesion: 0.07
Nodes (12): PreflightSourceItemData, CSJuntasGobiernoProvider, find_parent_by_tag_name(), get_date_from_text(), PreparseData, _extract_href(), _get_modified_at(), PrensaIbericaProvider (+4 more)

### Community 90 - "process_cmd"
Cohesion: 0.14
Nodes (11): delivery_phase(), import_cmd(), phase_title(), print_process(), process_cmd(), progress_rows(), run_cmd(), run_phases() (+3 more)

### Community 92 - "Config"
Cohesion: 0.08
Nodes (8): Database & ORM Conventions, DTO, Protocol & ORM Implementation Reference, 0011: Environment overrides, relative paths and one storage directory, Consequences, Context, Decision, Config, Workflow

### Community 99 - "AppletType"
Cohesion: 0.17
Nodes (7): Applets, Applet, AppletType, __newstool_plugin__(), __newstool_plugin__(), __newstool_plugin__(), PluginRegistrationTests

### Community 104 - "0012: Delivery ids, changing their state and forced send"
Cohesion: 0.33
Nodes (5): 0012: Delivery ids, changing their state and forced send, Consequences, Context, Decision, Rejected options

### Community 105 - "0014: Ledger rows by subject and the workflow in delivery commands"
Cohesion: 0.33
Nodes (5): 0014: Ledger rows by subject and the workflow in delivery commands, Consequences, Context, Decision, Rejected options

### Community 106 - "0016: Routes on re-emission, manual queueing and pacing overrides"
Cohesion: 0.33
Nodes (5): 0016: Routes on re-emission, manual queueing and pacing overrides, Consequences, Context, Decision, Rejected options

## Knowledge Gaps
- **13 isolated node(s):** `newstool`, `External pipelines (scripts/pipeline_url.py)`, `Annotation`, `Telegram t.me/s channel preview HTML (tgme_widget_message, data-post)`, `IndexSiteProvider / URLProvider` (+8 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 609 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **27 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Application` connect `Application` to `catalog.py`, `Services`, `ApplicationTests`, `invoke`, `.from_text`, `SourceItem`, `HTTPClient`, `AppletReader`, `Document`, `.close`, `test_db.py`, `describe`, `Deliverer`, `cli.py`, `.add_items`, `.summary`, `app_from_context`, `Database`, `apps_run_cmd`, `._object`, `SourceData`, `ProcessingScope`, `AppletRun`, `Delivery`, `app.py`, `.get_content`, `PacingOverride`, `PreflightSourceItemData`, `process_cmd`, `Config`?**
  _High betweenness centrality (0.114) - this node is a cross-community bridge._
- **Are the 28 inferred relationships involving `SourceItem` (e.g. with `Application` and `AppletReader`) actually correct?**
  _`SourceItem` has 28 INFERRED edges - model-reasoned connections that need verification._
- **What connects `newstool`, `External pipelines (scripts/pipeline_url.py)`, `Annotation` to the rest of the system?**
  _13 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `catalog.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06663141195134849 - nodes in this community are weakly interconnected._
- **Why does `Database` connect `Database` to `make_item`, `Services`, `StubLLM`, `SourceItem`, `DeleteCommandTests`, `.add_item`, `HTTPClient`, `AppletReader`, `Document`, `.close`, `AppletResult`, `datetime`, `test_db.py`, `Delivery`, `Deliverer`, `.add_items`, `app_from_context`, `test_db.py`, `Application`, `SourceData`, `ProcessingScope`, `AppletRun`, `Delivery`, `0018: Annotations hold their run state; a content change deletes them`, `app.py`, `.summary`, `errors.py`, `.get_content`, `.__init__`, `PacingOverride`, `Config`?**
  _High betweenness centrality (0.088) - this node is a cross-community bridge._
- **Are the 23 inferred relationships involving `Database` (e.g. with `Context` and `Decision`) actually correct?**
  _`Database` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Should `Services` be split into smaller, more focused modules?**
  _Cohesion score 0.04200896191187453 - nodes in this community are weakly interconnected._