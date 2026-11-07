"""The `telegram` sink (decision 0015) posts the documents routed to it to a
chat: a document that fits in a message is posted as one (title, text and
link, with its image as a photo when it has one); a longer one is sent as a
file, which avoids the 4096-character limit of messages.

Each instance posts with its `bot_token` to its `chat_id`; the type's
`plugins` section, which is optional, holds their defaults, so one bot can
post to many chats and instances can use different bots. What was delivered
is in the ledger (`inspect deliveries`), so nothing is ever posted twice
unless forced.
"""

import html
import logging
import mimetypes
import sys
from typing import Any

import requests
from pydantic import SecretStr

from ..errors import PluginFailure
from ..models import Document
from ..sinks import SinkOptions, SinkType
from . import PluginTypes, Services

LOGGER = logging.getLogger(__name__)

MAX_CAPTION_LENGTH = 1024
MAX_MESSAGE_LENGTH = 4096


def build_caption(
    title: str | None,
    text: str,
    uri: str | None,
    link_text: str = "original article",
    markdown: bool = False,
    max_length: int = MAX_CAPTION_LENGTH,
) -> str:
    """The message in Telegram's HTML or, with `markdown`, in its legacy
    Markdown with the text unescaped, so that its formatting renders. The
    text is cut to fit `max_length`."""
    heading = footer = ""
    if markdown:
        # Legacy Markdown cannot escape an entity's delimiter inside it.
        if title:
            heading = f"*{title.replace('*', '')}*\n\n"
        if uri:
            footer = f"\n\n[{link_text.replace(']', '')}]({uri.replace(')', '%29')})"
        escaped_text = text
    else:
        if title:
            heading = f"<b>{html.escape(title)}</b>\n\n"
        if uri:
            escaped_uri = html.escape(uri, quote=True)
            footer = f'\n\n<a href="{escaped_uri}">{html.escape(link_text)}</a>'
        escaped_text = html.escape(text)
    available_text_length = max_length - len(heading) - len(footer)

    if available_text_length <= 0:
        return (heading + footer)[:max_length]

    if len(escaped_text) > available_text_length:
        suffix = "..."
        escaped_text = (
            escaped_text[: max(0, available_text_length - len(suffix))] + suffix
        )

    return heading + escaped_text + footer


class TelegramOptions(SinkOptions):
    bot_token: SecretStr
    chat_id: str
    images: bool = True  # post the document's image, when it has one, as a photo
    link_preview: bool = False  # Telegram's link preview, text messages only
    link_text: str = "original article"
    markdown: bool = False  # the text as Markdown, not as plain text


def post(bot_token: SecretStr, method: str, **request: Any) -> int:
    """Call the Bot API `method` with `requests.post` keyword arguments;
    return the id of the message sent."""
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{bot_token.get_secret_value()}/{method}",
            timeout=30,
            **request,
        )
        result = response.json()
    except requests.RequestException as e:
        # Only the class: the message holds the URL, which embeds the bot token.
        raise PluginFailure(type(e).__name__) from None
    if not result.get("ok"):
        raise PluginFailure(result.get("description", str(result)))
    return result["result"]["message_id"]


class TelegramSink:
    name = "telegram"
    options_model = TelegramOptions
    accepts = frozenset({"text/plain", "text/markdown"})

    def __init__(self, options: TelegramOptions, services: Services) -> None:
        self.options = options

    def send(self, document: Document) -> dict[str, Any]:
        options = self.options
        text = document.content or ""
        whole = build_caption(
            document.title,
            text,
            document.url,
            options.link_text,
            options.markdown,
            max_length=sys.maxsize,
        )
        if len(whole) <= MAX_MESSAGE_LENGTH:
            message_id = self._send_message(document, text)
        else:
            message_id = self._send_file(document, text)
        # A message id is only unique within its chat.
        return {"chat_id": options.chat_id, "message_id": message_id}

    def _send_message(self, document: Document, text: str) -> int:
        options = self.options
        parse_mode = "Markdown" if options.markdown else "HTML"
        image = document.image_url
        if options.images and image and image.strip():
            caption = build_caption(
                document.title, text, document.url, options.link_text, options.markdown
            )
            # Uploaded, not by URL: Telegram cannot fetch some URLs, such as
            # its own CDN's (cdn*.telesco.pe) from `telegram_channel`.
            response = requests.get(image, timeout=30)
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "image/jpeg")
            extension = mimetypes.guess_extension(content_type) or ".jpg"
            return post(
                options.bot_token,
                "sendPhoto",
                data={
                    "chat_id": options.chat_id,
                    "caption": caption,
                    "parse_mode": parse_mode,
                },
                files={"photo": (f"image{extension}", response.content, content_type)},
            )
        payload = {
            "chat_id": options.chat_id,
            "text": build_caption(
                document.title,
                text,
                document.url,
                options.link_text,
                options.markdown,
                max_length=MAX_MESSAGE_LENGTH,
            ),
            "parse_mode": parse_mode,
            "link_preview_options": {"is_disabled": not options.link_preview},
        }
        return post(options.bot_token, "sendMessage", json=payload)

    def _send_file(self, document: Document, text: str) -> int:
        options = self.options
        extension = mimetypes.guess_extension(document.content_type) or ".txt"
        if document.content_type == "text/markdown":
            extension = ".md"
        filename = f"{document.app}-{document.key.replace('/', '_')}{extension}"
        return post(
            options.bot_token,
            "sendDocument",
            data={
                "chat_id": options.chat_id,
                "caption": (document.title or document.label)[:MAX_CAPTION_LENGTH],
            },
            files={"document": (filename, text.encode(), document.content_type)},
        )


def __newstool_plugin__() -> PluginTypes:
    return [(TelegramSink.name, SinkType, TelegramSink)]
