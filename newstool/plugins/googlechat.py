"""The `googlechat` sink posts the documents routed to it (title, text, link
and image, see `WebhookOptions`) as a card to a Google Chat space through an
incoming webhook, given either as its `url` or as its `channel` (space id)
and `token`, in the `plugins` section (the default) or in each instance.
What was delivered is in the ledger (`inspect deliveries`), so nothing is
ever posted twice unless forced.
"""

import html
import re
from typing import Any, Self
from urllib.parse import quote, urlsplit, urlunsplit

import pydantic
import requests
from pydantic import SecretStr

from ..errors import PluginFailure
from ..models import Document
from ..sinks import SinkOptions, SinkType
from . import PluginTypes, Services

# The API key Google puts in every incoming webhook URL; only the token is secret.
WEBHOOK_KEY = "AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI"

# Chat shows no image from Blogger's host, so those go through this proxy.
BLOGGER_HOST = "blogger.googleusercontent.com"
IMAGE_PROXY = "https://wsrv.nl/?url="
# The size segment of a Blogger image path (`s72-c`, `w1200`, ...); feeds
# give 72px thumbnails, so cards ask for the full size instead.
BLOGGER_SIZE = re.compile(r"[swh]\d+(-[\w-]+)?")
BLOGGER_FULL_SIZE = "s1600"


def chat_image_url(image_url: str) -> str:
    """Where Chat can fetch the image: Blogger's at full size, through the
    proxy; any other as is."""
    parts = urlsplit(image_url)
    if parts.hostname != BLOGGER_HOST:
        return image_url
    segments = [
        BLOGGER_FULL_SIZE if BLOGGER_SIZE.fullmatch(segment) else segment
        for segment in parts.path.split("/")
    ]
    full_size = urlunsplit(parts._replace(path="/".join(segments)))
    return IMAGE_PROXY + quote(full_size, safe="")


def build_card(
    title: str | None,
    text: str,
    uri: str | None,
    link_text: str = "original article",
    image_url: str | None = None,
) -> dict[str, Any]:
    """The message: title (if any) and text, the image if any, and a link
    button if there is a link."""
    # The paragraph is Chat's HTML subset, so the text must escape `<>&`.
    body = html.escape(text, quote=False).replace("\n", "<br>")
    if title:
        body = f"<b>{html.escape(title, quote=False)}</b><br><br>{body}"
    widgets: list[dict[str, Any]] = [{"textParagraph": {"text": body}}]
    if image_url is not None:
        widgets.append(
            {"image": {"imageUrl": chat_image_url(image_url), "altText": title or ""}}
        )
    if uri:
        widgets.append(
            {
                "buttonList": {
                    "buttons": [
                        {"text": link_text, "onClick": {"openLink": {"url": uri}}}
                    ]
                }
            }
        )
    return {
        "cardsV2": [{"cardId": "item", "card": {"sections": [{"widgets": widgets}]}}]
    }


class WebhookOptions(SinkOptions):
    url: SecretStr | None = None
    channel: str | None = None
    token: SecretStr | None = None
    images: bool = True  # the document's image, when it has one, in the card
    link_text: str = "original article"

    @pydantic.model_validator(mode="after")
    def url_or_channel_and_token(self) -> Self:
        parts = (self.channel, self.token)
        if (self.url is None and None not in parts) or (
            self.url is not None and parts == (None, None)
        ):
            return self
        raise ValueError("set either `url` or both `channel` and `token`")

    def webhook_url(self) -> SecretStr:
        if self.url is not None:
            return self.url
        assert self.channel is not None and self.token is not None
        return SecretStr(
            f"https://chat.googleapis.com/v1/spaces/{quote(self.channel)}/messages"
            f"?key={WEBHOOK_KEY}&token={quote(self.token.get_secret_value())}"
        )


class GoogleChatSink:
    name = "googlechat"
    options_model = WebhookOptions
    accepts = frozenset({"text/plain", "text/markdown"})

    def __init__(self, options: WebhookOptions, services: Services) -> None:
        self.options = options

    def send(self, document: Document) -> dict[str, str]:
        options = self.options
        image = document.image_url
        if not (options.images and image and image.strip()):
            image = None
        message = build_card(
            document.title,
            document.content or "",
            document.url,
            options.link_text,
            image,
        )
        try:
            response = requests.post(
                options.webhook_url().get_secret_value(),
                json=message,
                timeout=30,
            )
            result = response.json()
        except requests.RequestException as e:
            # Only the class: the message holds the URL, which embeds the token.
            raise PluginFailure(type(e).__name__) from None
        if not response.ok:
            raise PluginFailure(result.get("error", {}).get("message", str(result)))
        return {"message": result["name"]}


def __newstool_plugin__() -> PluginTypes:
    return [(GoogleChatSink.name, SinkType, GoogleChatSink)]
