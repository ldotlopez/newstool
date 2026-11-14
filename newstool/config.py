from __future__ import annotations

import dataclasses
import os
import re
import string
from collections.abc import Callable, Mapping
from contextvars import ContextVar
from datetime import time
from pathlib import Path
from typing import Annotated, Any, Literal
from urllib.parse import urlsplit, urlunsplit

import platformdirs
import pydantic
import pytimeparse2
import yaml
from dotenv import dotenv_values
from foundation.jsonlib import JsonCompatible
from pydantic_settings import (
    BaseSettings,
    EnvSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from .consts import PACKAGE_NAME
from .models import SourceData

# Ids (of catalog entries, applet and sink instances), workflow names and
# output names.
NAME_PATTERN = re.compile(r"[a-z0-9_-]+")
# `days` of an applet instance, Monday first.
type Weekday = Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
OLLAMA_PORT = 11434


def ollama_url(host: str) -> str:
    """The URL for an `OLLAMA_HOST` value, which Ollama itself accepts as
    `host`, `host:port` or a URL, and sets to `0.0.0.0` to listen everywhere:
    a bare host gets `http://` and Ollama's port, and a listen-everywhere
    address becomes `localhost`."""
    url = urlsplit(host if "://" in host else f"http://{host}")
    try:
        port = url.port
    except ValueError:
        return host
    if "://" not in host and port is None:
        port = OLLAMA_PORT
    if url.hostname in ("0.0.0.0", "::"):
        name = "localhost"
    else:
        name = url.hostname or ""
        if ":" in name:
            name = f"[{name}]"
    return urlunsplit(url._replace(netloc=f"{name}:{port}" if port else name))


@dataclasses.dataclass(frozen=True, slots=True)
class Alias:
    """The config key an external variable fills, and how its value reads."""

    path: tuple[str, ...]
    convert: Callable[[str], str] = str


# Well-known variables of external systems, below the config file: the user
# need not repeat them as NEWSTOOL_* variables.
ENV_ALIASES: dict[str, Alias] = {
    "OLLAMA_HOST": Alias(("plugins", "ollama", "api_base"), ollama_url),
    "OLLAMA_API_KEY": Alias(("plugins", "ollama", "api_key")),
}


class ConfigError(ValueError):
    """The configuration file cannot be loaded."""


class MissingVariableError(ConfigError):
    """A `${VAR}` reference names a variable that is not set."""

    def __init__(self, variable: str, location: str) -> None:
        super().__init__(f"{location}: environment variable '{variable}' is not set")
        self.variable = variable


def parse_duration(value: Any) -> Any:
    """Seconds from a duration with a unit suffix (`90s`, `5m`, `2h`, `3d`,
    `1h30m`); numbers, and the rest, are left to the field's validation."""
    if not isinstance(value, str):
        return value
    seconds = pytimeparse2.parse(value)
    if seconds is None:
        raise ValueError(f"invalid duration '{value}': use seconds or 5m, 2h, 3d")
    return seconds


# A length of time in the config: seconds, or a string with a unit suffix.
type Duration = Annotated[
    float, pydantic.BeforeValidator(parse_duration), pydantic.Field(ge=0)
]


@dataclasses.dataclass(frozen=True, slots=True)
class LoadContext:
    """What a config load resolves against: the directory relative paths are
    anchored at and the variables `${VAR}` and the aliases read."""

    config_dir: Path
    environ: Mapping[str, str]


# Set while a config loads: `BaseSettings` passes no validation context.
LOAD_CONTEXT: ContextVar[LoadContext | None] = ContextVar(
    "newstool_load_context", default=None
)


def load_context() -> LoadContext:
    """The load in progress; outside one, the current directory and the
    process environment."""
    return LOAD_CONTEXT.get() or LoadContext(Path.cwd(), os.environ)


def resolve_config_path(value: Path) -> Path:
    """`value` as an absolute path: `~` expanded, a relative path anchored at
    the config file's directory."""
    return (load_context().config_dir / value.expanduser()).resolve()


# A path in the config; relative ones are relative to the config file.
type ConfigPath = Annotated[Path, pydantic.AfterValidator(resolve_config_path)]


class CacheConfig(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")
    expiration: Duration = 60 * 60


class Entry(pydantic.BaseModel):
    """A configured use of a plugin type: its `options` over the type's
    `plugins` section. `id` names it in the catalog, so that workflows can
    refer to it."""

    model_config = pydantic.ConfigDict(extra="forbid", frozen=True)
    id: str | None = None
    options: dict[str, JsonCompatible] = {}

    @pydantic.field_validator("id")
    @classmethod
    def id_is_valid(cls, value: str | None) -> str | None:
        if value is not None and not NAME_PATTERN.fullmatch(value):
            raise ValueError(f"invalid id '{value}'")
        return value

    @property
    def type_name(self) -> str:
        """The plugin type it uses."""
        raise NotImplementedError


class LLMEntry(Entry):
    """An LLM. Objects that use one name it by `id`, or by type; the first
    entry serves those that name none."""

    llm: str

    @pydantic.model_validator(mode="before")
    @classmethod
    def from_name(cls, value: Any) -> Any:
        """A bare type name is the type with its section's options."""
        return {"llm": value} if isinstance(value, str) else value

    @property
    def type_name(self) -> str:
        return self.llm


class ProcessEntry(Entry):
    """A processor run. `key` names the annotation it writes (default: the
    processor's own for its options)."""

    processor: str
    key: str | None = None

    @pydantic.model_validator(mode="before")
    @classmethod
    def from_name(cls, value: Any) -> Any:
        """A bare type name is the type with its section's options."""
        return {"processor": value} if isinstance(value, str) else value

    @property
    def type_name(self) -> str:
        return self.processor

    @property
    def ref(self) -> str:
        """What workflows refer to it by: its `id`, or else its type name."""
        return self.id or self.processor


class SinkEntry(Entry):
    """A sink instance (decision 0015): where documents routed to it go, and
    how fast. Applet instances name it by `id` in their routes."""

    id: str
    sink: str

    @property
    def type_name(self) -> str:
        return self.sink


class AppEntry(Entry):
    """An applet instance (decision 0015). `every`, `at` and `days` say when
    it is due; `routes` sends each of its outputs to sink instances, and
    `sink` is the shorthand for an applet with a single output."""

    id: str
    app: str
    every: Duration = 0
    at: time | None = None  # local time
    # Not `on`, which YAML 1.1 (PyYAML) reads as the boolean true.
    days: list[Weekday] = []
    sink: str | None = None
    routes: dict[str, list[str]] = {}

    @pydantic.model_validator(mode="after")
    def sink_or_routes(self) -> AppEntry:
        if self.sink is not None and self.routes:
            raise ValueError(f"app '{self.id}': set either `sink` or `routes`")
        return self

    @property
    def type_name(self) -> str:
        return self.app


class Workflow(pydantic.BaseModel):
    """A chain (decision 0019): its sources are imported, its process entries
    run on them in order, then its applet instances, whose outputs go to the
    sinks they are routed to. Every entry is a catalog id."""

    model_config = pydantic.ConfigDict(extra="forbid", frozen=True)
    name: str
    sources: list[str]
    process: list[str] = []  # `processors` refs
    apps: list[str] = []

    @pydantic.model_validator(mode="before")
    @classmethod
    def entries_are_ids(cls, value: Any) -> Any:
        """Entries of a workflow's own were removed: point to the catalog."""
        if not isinstance(value, Mapping):
            return value
        for field, section in (("process", "processors"), ("apps", "apps")):
            for index, entry in enumerate(value.get(field) or []):
                if not isinstance(entry, str):
                    # A ValueError: pydantic reports it as a validation error.
                    raise ValueError(  # noqa: TRY004
                        f"workflow '{value.get('name')}': {field}.{index}: define"
                        f" it in `{section}` with an `id` and refer to it"
                    )
        return value

    @pydantic.model_validator(mode="after")
    def entries_are_valid(self) -> Workflow:
        if not NAME_PATTERN.fullmatch(self.name):
            raise ValueError(f"invalid workflow name '{self.name}'")
        for field in ("sources", "process", "apps"):
            ids: list[str] = getattr(self, field)
            if repeated := sorted({id_ for id_ in ids if ids.count(id_) > 1}):
                raise ValueError(
                    f"workflow '{self.name}': {field} lists {', '.join(repeated)} twice"
                )
        return self


class LoadEnvSettingsSource(EnvSettingsSource):
    """`NEWSTOOL_*` variables of the load's environment, which a `.env` next
    to the config file completes, rather than of the process alone."""

    def _load_env_vars(self) -> Mapping[str, str | None]:
        return {name.lower(): value for name, value in load_context().environ.items()}


class EnvAliasSource(PydanticBaseSettingsSource):
    """The `ENV_ALIASES` variables set in the load's environment, as the
    nested config they fill."""

    def get_field_value(self, field: Any, field_name: str) -> tuple[Any, str, bool]:
        return None, field_name, False  # the mapping is built in `__call__`

    def __call__(self) -> dict[str, Any]:
        environ = load_context().environ
        values: dict[str, Any] = {}
        for variable, alias in ENV_ALIASES.items():
            if not environ.get(variable):
                continue
            node = values
            for key in alias.path[:-1]:
                node = node.setdefault(key, {})
            node[alias.path[-1]] = alias.convert(environ[variable])
        return values


class Config(BaseSettings):
    """The configuration. From highest priority: `NEWSTOOL_*` environment
    variables (`__` nests: `NEWSTOOL_CACHE__EXPIRATION`), the same in a `.env`
    next to the config file, the YAML, the `ENV_ALIASES` variables, defaults."""

    model_config = SettingsConfigDict(
        extra="forbid",
        env_prefix="NEWSTOOL_",
        env_nested_delimiter="__",
    )
    # Used when neither --log-level, -v/-q nor NEWSTOOL_LOG_LEVEL set one.
    log_level: str = "warning"
    # Plugin type name -> the defaults of its options in every use of the
    # type. Nothing is built from a section.
    plugins: dict[str, dict[str, Any] | None] = {}
    # The catalog (decision 0019): what can run, built when a workflow runs
    # it. Applet instances route their outputs to the sinks.
    llms: list[LLMEntry] = []
    sources: list[SourceData] = []
    processors: list[ProcessEntry] = []
    apps: list[AppEntry] = []
    sinks: list[SinkEntry] = []
    # What runs, by name; a list, since YAML drops duplicate keys.
    workflows: list[Workflow] = []
    cache: CacheConfig = CacheConfig()
    # Where the HTTP cache lives.
    cache_dir: ConfigPath = pydantic.Field(
        default_factory=lambda: platformdirs.user_cache_path(PACKAGE_NAME)
    )
    # Everything stored: the SQLite database and the content directory.
    storage_dir: ConfigPath = pydantic.Field(
        default_factory=lambda: platformdirs.user_data_path(PACKAGE_NAME)
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Highest priority first; `init_settings` carries the YAML."""
        return (
            LoadEnvSettingsSource(settings_cls),
            init_settings,
            EnvAliasSource(settings_cls),
        )

    @property
    def database_uri(self) -> str:
        return f"sqlite:///{self.storage_dir / 'data.db'}"

    @property
    def content_dir(self) -> Path:
        return self.storage_dir / "content"

    @pydantic.model_validator(mode="before")
    @classmethod
    def no_skip_default(cls, value: Any) -> Any:
        """`skip_default` was removed (decision 0019): say what replaces it."""
        if not isinstance(value, Mapping):
            return value
        for section in ("sources", "processors", "apps"):
            for index, entry in enumerate(value.get(section) or []):
                if isinstance(entry, Mapping) and "skip_default" in entry:
                    raise ValueError(
                        f"{section}.{index}: `skip_default` was removed (decision"
                        " 0019): list what runs in `workflows`"
                    )
        return value

    @pydantic.model_validator(mode="after")
    def catalog_ids_are_unique(self) -> Config:
        catalog: dict[str, list[str]] = {
            "sources": [source.id for source in self.sources],
            "llms": [entry.id for entry in self.llms if entry.id is not None],
            "processors": [entry.ref for entry in self.processors],
            "apps": [entry.id for entry in self.apps],
            "sinks": [entry.id for entry in self.sinks],
        }
        for section, ids in catalog.items():
            if duplicated := sorted({id_ for id_ in ids if ids.count(id_) > 1}):
                hint = (
                    " (an entry without `id` takes its type name: give each its own)"
                    if section == "processors"
                    else ""
                )
                raise ValueError(
                    f"{section}: id(s) {', '.join(duplicated)} used twice{hint}"
                )
        return self

    @pydantic.model_validator(mode="after")
    def workflows_are_valid(self) -> Config:
        """Names are unique, every entry is in the catalog, and an applet
        instance belongs to one workflow."""
        names = [workflow.name for workflow in self.workflows]
        if len(names) != len(set(names)):
            raise ValueError("workflow names must be unique")
        known = {
            "source": {source.id for source in self.sources},
            "processor": {entry.ref for entry in self.processors},
            "applet instance": {entry.id for entry in self.apps},
        }
        owners: dict[str, str] = {}
        for workflow in self.workflows:
            for kind, ids in (
                ("source", workflow.sources),
                ("processor", workflow.process),
                ("applet instance", workflow.apps),
            ):
                if unknown := [id_ for id_ in ids if id_ not in known[kind]]:
                    raise ValueError(
                        f"workflow '{workflow.name}': unknown {kind}(s)"
                        f" {', '.join(unknown)}"
                    )
            for app_id in workflow.apps:
                if (owner := owners.setdefault(app_id, workflow.name)) != workflow.name:
                    raise ValueError(
                        f"app '{app_id}' is in workflows '{owner}' and"
                        f" '{workflow.name}'; an applet instance belongs to one"
                    )
        return self

    def workflow_of_app(self, app_id: str) -> Workflow | None:
        """The workflow an applet instance belongs to, if any."""
        return next((w for w in self.workflows if app_id in w.apps), None)

    def get_source(self, source_id: str) -> SourceData:
        for source in self.sources:
            if source.id == source_id:
                return source
        raise ConfigError(f"source '{source_id}' is not configured")

    @classmethod
    def from_file(cls, path: Path) -> Config:
        """Load a config file. `${VAR}` takes values from the environment,
        then from a `.env` file next to the config file, if any; relative
        paths in it are relative to the file."""
        dotenv = {
            name: value
            for name, value in dotenv_values(path.parent / ".env").items()
            if value is not None
        }
        try:
            return cls.from_text(
                path.read_text(),
                environ={**dotenv, **os.environ},
                base_dir=path.parent,
            )
        except MissingVariableError as e:
            raise ConfigError(
                f"{path}: {e}\n"
                f"Set {e.variable} in the environment or in {path.parent / '.env'}."
            ) from e

    @classmethod
    def from_text(
        cls,
        text: str,
        *,
        environ: Mapping[str, str] | None = None,
        base_dir: Path | None = None,
    ) -> Config:
        """Parse YAML, then expand `${VAR}` references in its string values
        from `environ` (the process environment by default). Comments and
        keys are never expanded. Values from `NEWSTOOL_*` variables of `environ`
        and the aliases are taken as they are.

        Relative paths are relative to `base_dir` (the current directory by
        default). A literal `$` in a value must be written as `$$`.
        """
        environ = os.environ if environ is None else environ
        expanded = expand_variables(yaml.safe_load(text) or {}, environ, ())
        context = LoadContext((base_dir or Path.cwd()).resolve(), environ)
        token = LOAD_CONTEXT.set(context)
        try:
            return cls(**expanded)
        except pydantic.ValidationError as e:
            raise ConfigError(str(e)) from e
        finally:
            LOAD_CONTEXT.reset(token)


def expand_variables(
    value: Any, environ: Mapping[str, str], location: tuple[str | int, ...]
) -> Any:
    """`value` with `${VAR}` references expanded in every string it holds.
    `location` is its path in the config, for error messages."""
    if isinstance(value, dict):
        return {
            key: expand_variables(item, environ, (*location, key))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [
            expand_variables(item, environ, (*location, index))
            for index, item in enumerate(value)
        ]
    if not isinstance(value, str):
        return value
    try:
        return string.Template(value).substitute(environ)
    except KeyError as e:
        raise MissingVariableError(e.args[0], ".".join(map(str, location))) from e
    except ValueError as e:
        raise ConfigError(
            f"{'.'.join(map(str, location))}: invalid ${{VAR}} reference: {e}"
        ) from e


def options_error(location: str, error: pydantic.ValidationError) -> ConfigError:
    """Rejected options at `location` in the config, one line per error with
    its config path."""
    lines = [
        f"{'.'.join(map(str, (location, *detail['loc'])))}: {detail['msg']}"
        for detail in error.errors()
    ]
    return ConfigError("invalid options:\n" + "\n".join(lines))
