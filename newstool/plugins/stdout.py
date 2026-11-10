"""The `stdout` sink prints each document routed to it as one line of JSON
on standard output, with every field and its content: a way to see what an
applet emits, for test configurations and debugging."""

import dataclasses
import json
import sys

from ..models import Document
from ..sinks import ANY_CONTENT_TYPE, SinkOptions, SinkType
from . import PluginTypes, Services


class StdoutSink:
    name = "stdout"
    options_model = SinkOptions
    accepts = frozenset({ANY_CONTENT_TYPE})

    def __init__(self, options: SinkOptions, services: Services) -> None:
        self.options = options

    def send(self, document: Document) -> None:
        fields = dataclasses.asdict(document)
        if document.emitted_at is not None:
            fields["emitted_at"] = document.emitted_at.isoformat()
        print(json.dumps(fields, ensure_ascii=False), file=sys.stdout, flush=True)


def __newstool_plugin__() -> PluginTypes:
    return [(StdoutSink.name, SinkType, StdoutSink)]
