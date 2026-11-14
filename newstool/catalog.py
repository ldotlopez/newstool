"""The configuration resolved against the registered plugin classes
(decisions 0010, 0015, 0019): every configured use of a class as a
`Profile`, its options validated, every workflow's process runs, and the
applet and sink instances with their routes, all checked at startup. Nothing
is built here: `Application` builds a profile's object when it is first
needed.
"""

from __future__ import annotations

import dataclasses
import logging
import re
from collections.abc import Mapping, Sequence
from typing import Annotated, Any

import pydantic

from .applets import WEEKDAYS, AppletType, Schedule
from .config import (
    NAME_PATTERN,
    AppEntry,
    Config,
    ConfigError,
    Entry,
    ProcessEntry,
    Workflow,
    options_error,
)
from .llms import LLMType
from .plugins import ClassRegister, UsesLLMOptions, merge_options
from .processors import ProcessorType
from .providers import ProviderType
from .sinks import SinkType, accepts

LOGGER = logging.getLogger(__name__)

# Annotation keys: lowercase words, optionally in `/`-separated parts.
KEY_PATTERN = re.compile(r"[a-z0-9_]+(/[a-z0-9_]+)*")


@dataclasses.dataclass(frozen=True, slots=True)
class Kind:
    """A kind of plugin type: the Protocol its classes conform to."""

    label: str
    protocol: type


LLM = Kind("llm", LLMType)
PROVIDER = Kind("provider", ProviderType)
PROCESSOR = Kind("processor", ProcessorType)
APPLET = Kind("applet", AppletType)
SINK = Kind("sink", SinkType)


@dataclasses.dataclass(eq=False, slots=True)
class Profile:
    """A configured use of a plugin class (by type name) with its validated
    options, and where it is configured. Equal only to itself: the runs
    that refer to one profile share its object."""

    name: str
    cls: Any
    options: pydantic.BaseModel
    location: str


@dataclasses.dataclass(frozen=True, slots=True)
class Run:
    """A workflow's run of a profile under a key, and where it is named."""

    workflow: Workflow
    key: str
    profile: Profile
    location: str


@dataclasses.dataclass(frozen=True, slots=True)
class Use:
    """A profile under a key, as a catalog entry names it."""

    profile: Profile
    key: str
    location: str


@dataclasses.dataclass(frozen=True, slots=True)
class AppInstance:
    """A configured applet instance: its profile, when it is due, the sink
    instances each of its outputs is routed to, and the workflow it belongs
    to (None: it never runs)."""

    id: str
    profile: Profile
    schedule: Schedule
    routes: Mapping[str, tuple[str, ...]]
    workflow: Workflow | None
    location: str


class Catalog:
    """The profiles, runs and instances of a configuration. Every use is
    validated, run or not."""

    def __init__(self, config: Config, register: ClassRegister) -> None:
        self._classes = {
            kind: register.classes(kind.protocol)
            for kind in (LLM, PROVIDER, PROCESSOR, APPLET, SINK)
        }
        self._sections = {
            name: section or {} for name, section in config.plugins.items()
        }
        self._check_sections()
        self._profiles: list[Profile] = []
        self._type_profiles: dict[tuple[Kind, str], Profile] = {}

        self._llms = self._llm_catalog(config)
        self._default_llm = next(iter(self._llms.values()), None)
        self.sources = {
            source.id: self._profile(
                PROVIDER, source.provider, source.options, f"sources.{source.id}"
            )
            for source in config.sources
        }
        processors = self._processor_uses(config.processors)
        # The key each `processors` entry writes, by `ref`.
        self.processor_keys = {ref: use.key for ref, use in processors.items()}

        # By (workflow, key), in configuration order.
        self.process: dict[tuple[str, str], Run] = {}
        for workflow in config.workflows:
            for index, ref in enumerate(workflow.process):
                use = processors[ref]
                location = f"workflows.{workflow.name}.process.{index}"
                self.process[workflow.name, use.key] = Run(
                    workflow, use.key, use.profile, location
                )
        self._check_requirements()

        # By id, in configuration order.
        self.sinks: dict[str, Profile] = {
            entry.id: self._profile(SINK, entry.sink, entry.options, f"sinks.{index}")
            for index, entry in enumerate(config.sinks)
        }
        self.apps: dict[str, AppInstance] = {
            entry.id: self._app(
                entry, f"apps.{index}", config.workflow_of_app(entry.id)
            )
            for index, entry in enumerate(config.apps)
        }
        self._check_llms()
        warn_unused(config)

    def llm_profile(self, name: str | None, location: str = "llms") -> Profile:
        """The LLM `name` refers to: an `llms` id, an LLM type, or the first
        `llms` entry for None."""
        if name is None:
            if self._default_llm is None:
                raise ConfigError(f"{location}: uses an llm, and `llms` is empty")
            return self._default_llm
        if name in self._llms:
            return self._llms[name]
        if name in self._classes[LLM]:
            return self._type_profile(LLM, name, location)
        raise ConfigError(f"{location}: no llm has the id or type '{name}'")

    # --- Profiles ----------------------------------------------------------

    def _check_sections(self) -> None:
        """Every `plugins` section names a type and sets options it takes."""
        for name, section in self._sections.items():
            classes = [
                classes[name] for classes in self._classes.values() if name in classes
            ]
            if not classes:
                raise ConfigError(f"plugins.{name}: no plugin provides '{name}'")
            for cls in classes:
                check_section(f"plugins.{name}", cls.options_model, section)

    def _profile(
        self, kind: Kind, name: str, overrides: Mapping[str, Any], location: str
    ) -> Profile:
        """The use of the type `name` with `overrides` over its section."""
        if (cls := self._classes[kind].get(name)) is None:
            raise ConfigError(
                f"{location}: no plugin provides the {kind.label} '{name}'"
            )
        options = merge_options(self._sections.get(name, {}), overrides)
        try:
            validated = cls.options_model.model_validate(options)
        except pydantic.ValidationError as e:
            raise options_error(f"{location}.options", e) from None
        profile = Profile(name, cls, validated, location)
        self._profiles.append(profile)
        return profile

    def _type_profile(self, kind: Kind, name: str, location: str) -> Profile:
        """The type `name` with its section's options: one profile for every
        reference to it."""
        if (kind, name) not in self._type_profiles:
            self._type_profiles[kind, name] = self._profile(kind, name, {}, location)
        return self._type_profiles[kind, name]

    def _llm_catalog(self, config: Config) -> dict[str, Profile]:
        """The `llms` entries' profiles, by id, or by position for those
        without one."""
        llms: dict[str, Profile] = {}
        for index, entry in enumerate(config.llms):
            location = f"llms.{index}"
            self._check_id(LLM, entry, location)
            profile = self._profile(LLM, entry.llm, entry.options, location)
            llms[entry.id or f"#{index}"] = profile
        return llms

    def _processor_uses(self, entries: Sequence[ProcessEntry]) -> dict[str, Use]:
        """The `processors` entries' uses, by `ref`. A key is the
        annotation's identity: one entry writes it (decision 0019)."""
        uses: dict[str, Use] = {}
        writers: dict[str, Use] = {}
        for index, entry in enumerate(entries):
            location = f"processors.{index}"
            self._check_id(PROCESSOR, entry, location)
            profile = self._profile(PROCESSOR, entry.type_name, entry.options, location)
            use = Use(profile, process_key(entry, profile), location)
            if not KEY_PATTERN.fullmatch(use.key):
                raise ConfigError(f"{location}: invalid key '{use.key}'")
            if (other := writers.setdefault(use.key, use)) is not use:
                raise ConfigError(
                    f"{location}: key '{use.key}' is written by {other.location}"
                    " too; give one a `key`"
                )
            uses[entry.ref] = use
        return uses

    def _check_id(self, kind: Kind, entry: Entry, location: str) -> None:
        """An id is not a type name, so a reference means one thing."""
        if entry.id is not None and entry.id in self._classes[kind]:
            raise ConfigError(
                f"{location}: the id '{entry.id}' is a {kind.label} type's name"
            )

    # --- Process runs ------------------------------------------------------

    def _check_requirements(self) -> None:
        """Every annotation a process run reads is written by a process run
        on its workflow's sources, in any workflow."""
        for run in self.process.values():
            required = run.profile.cls.required_key(run.profile.options)
            if required is not None and not self._is_written(required, run.workflow):
                raise ConfigError(
                    f"{run.location}: {run.profile.name} reads '{required}', and"
                    " no process run writes it on the sources of workflow"
                    f" '{run.workflow.name}'"
                )

    def _is_written(self, key: str, workflow: Workflow) -> bool:
        """Whether a process run writes `key` in `workflow`, or on one of its
        sources in another workflow."""
        return any(
            writer.key == key
            and (
                writer.workflow.name == workflow.name
                or not set(writer.workflow.sources).isdisjoint(workflow.sources)
            )
            for writer in self.process.values()
        )

    # --- Applet instances --------------------------------------------------

    def _app(
        self, entry: AppEntry, location: str, workflow: Workflow | None
    ) -> AppInstance:
        """An applet instance with its routes, checked against its outputs and
        the sinks, and its requirements against its workflow."""
        profile = self._profile(APPLET, entry.app, entry.options, location)
        outputs = profile.cls.outputs
        if not all(NAME_PATTERN.fullmatch(output) for output in outputs):
            raise ConfigError(f"{location}: {entry.app} declares an invalid output")
        if entry.sink is not None:
            if len(outputs) != 1:
                raise ConfigError(
                    f"{location}: `sink` needs an applet with one output;"
                    f" {entry.app} has {', '.join(outputs)}: use `routes`"
                )
            routes = {next(iter(outputs)): (entry.sink,)}
        else:
            routes = {output: tuple(sinks) for output, sinks in entry.routes.items()}
        for output, sinks in routes.items():
            if output not in outputs:
                raise ConfigError(
                    f"{location}: {entry.app} has no output '{output}'"
                    f" (it has {', '.join(outputs)})"
                )
            for sink in sinks:
                if (sink_profile := self.sinks.get(sink)) is None:
                    raise ConfigError(f"{location}: no sink has the id '{sink}'")
                if not accepts(sink_profile.cls, outputs[output]):
                    raise ConfigError(
                        f"{location}: sink '{sink}' ({sink_profile.name}) does not"
                        f" accept the content of output '{output}'"
                        f" ({', '.join(sorted(outputs[output]))})"
                    )
        if workflow is not None:
            self._check_app_requirements(profile, location, workflow)
        schedule = Schedule(
            every=entry.every,
            at=entry.at,
            days=frozenset(WEEKDAYS.index(day) for day in entry.days),
        )
        return AppInstance(entry.id, profile, schedule, routes, workflow, location)

    def _check_app_requirements(
        self, profile: Profile, location: str, workflow: Workflow
    ) -> None:
        """Every annotation key an instance reads is written by a process
        entry of its own workflow, so its chain produces what it reads."""
        for key in profile.cls.required_keys(profile.options):
            if (workflow.name, key) not in self.process:
                raise ConfigError(
                    f"{location}: {profile.name} reads '{key}', and no process"
                    f" entry of workflow '{workflow.name}' writes it"
                )

    def _check_llms(self) -> None:
        """Every LLM a profile names exists."""
        for profile in list(self._profiles):
            if isinstance(profile.options, UsesLLMOptions):
                self.llm_profile(profile.options.llm, profile.location)


def process_key(entry: ProcessEntry | None, profile: Profile) -> str:
    """The entry's key, or else the processor's own for its options."""
    if entry is not None and entry.key is not None:
        return entry.key
    return profile.cls.output_key(profile.options)


def check_section(
    location: str, model: type[pydantic.BaseModel], section: Mapping[str, Any]
) -> None:
    """Reject options `model` does not declare, or values it does not take.
    Rules across options (model validators) are checked in each use."""
    errors = []
    for option, value in section.items():
        if (field := model.model_fields.get(option)) is None:
            errors.append(f"{location}.{option}: no such option")
            continue
        annotation = (
            Annotated[field.annotation, *field.metadata]
            if field.metadata
            else field.annotation
        )
        try:
            pydantic.TypeAdapter(annotation).validate_python(value)
        except pydantic.ValidationError as e:
            errors.extend(f"{location}.{option}: {d['msg']}" for d in e.errors())
    if errors:
        raise ConfigError("invalid options:\n" + "\n".join(errors))


def warn_unused(config: Config) -> None:
    """Sources, processors and applet instances no workflow refers to never
    run: dead configuration. Sinks still get rows queued by hand."""
    used = {
        "sources": {id_ for w in config.workflows for id_ in w.sources},
        "processors": {ref for w in config.workflows for ref in w.process},
        "apps": {id_ for w in config.workflows for id_ in w.apps},
    }
    defined = {
        "sources": [source.id for source in config.sources],
        "processors": [entry.ref for entry in config.processors],
        "apps": [entry.id for entry in config.apps],
    }
    for section, ids in defined.items():
        if unused := [id_ for id_ in ids if id_ not in used[section]]:
            LOGGER.warning(
                f"{section}: no workflow refers to {', '.join(unused)}; it never runs"
            )
