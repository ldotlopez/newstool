"""The `file` sink (decision 0015) publishes each document routed to it by
writing its content to `path`, replacing the file: a daily feed, a page a
web server serves. `{app}`, `{output}` and `{key}` in `path` are replaced by
the document's (`/` in a key becomes `_`), so one instance can keep a file
per document.
"""

from pathlib import Path
from typing import Self

import pydantic

from ..models import Document
from ..sinks import ANY_CONTENT_TYPE, SinkOptions, SinkType
from . import PluginTypes, Services


class FileOptions(SinkOptions):
    path: str  # absolute, `~` allowed; may contain {app}, {output}, {key}

    @pydantic.model_validator(mode="after")
    def path_is_absolute(self) -> Self:
        if not Path(self.path).expanduser().is_absolute():
            raise ValueError(f"path '{self.path}' must be absolute")
        try:
            self.path.format(app="", output="", key="")
        except (KeyError, IndexError, ValueError) as e:
            raise ValueError(
                f"path '{self.path}' may only use {{app}}, {{output}} and {{key}}"
            ) from e
        return self


class FileSink:
    name = "file"
    options_model = FileOptions
    accepts = frozenset({ANY_CONTENT_TYPE})

    def __init__(self, options: FileOptions, services: Services) -> None:
        self.options = options

    def target(self, document: Document) -> Path:
        """Where the document is written."""
        return Path(
            self.options.path.format(
                app=document.app,
                output=document.output,
                key=document.key.replace("/", "_"),
            )
        ).expanduser()

    def send(self, document: Document) -> dict[str, str]:
        target = self.target(document)
        target.parent.mkdir(parents=True, exist_ok=True)
        # Written next to the target, then renamed over it: readers never see
        # a partial file.
        partial = target.with_name(f".{target.name}.partial")
        partial.write_text(document.content or "")
        partial.replace(target)
        return {"path": str(target)}


def __newstool_plugin__() -> PluginTypes:
    return [(FileSink.name, SinkType, FileSink)]
