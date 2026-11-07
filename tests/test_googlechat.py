import unittest
from typing import Any
from unittest.mock import Mock, patch

import pydantic
import requests

from newstool.errors import PluginFailure
from newstool.models import Document
from newstool.plugins import Services, googlechat, merge_options
from newstool.plugins.googlechat import (
    WEBHOOK_KEY,
    GoogleChatSink,
    WebhookOptions,
    chat_image_url,
)
from newstool.sinks import SinkType

BLOGGER_IMAGE = (
    "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvX/s72-c/A%20b.png"
)


def card_widgets(message: dict[str, Any]) -> list[dict[str, Any]]:
    ((section,),) = (card["card"]["sections"] for card in message["cardsV2"])
    return section["widgets"]


class ChatImageUrlTests(unittest.TestCase):
    def test_keeps_other_hosts(self) -> None:
        self.assertEqual(
            chat_image_url("https://a.test/s72-c/image.jpg"),
            "https://a.test/s72-c/image.jpg",
        )

    def test_proxies_blogger_at_full_size(self) -> None:
        for size in ("s72-c", "s300", "w1200", "s1600"):
            with self.subTest(size):
                self.assertEqual(
                    chat_image_url(BLOGGER_IMAGE.replace("s72-c", size)),
                    "https://wsrv.nl/?url=https%3A%2F%2Fblogger.googleusercontent.com"
                    "%2Fimg%2Fb%2FR29vZ2xl%2FAVvX%2Fs1600%2FA%2520b.png",
                )


def webhook_options(section: dict[str, Any], overrides: dict[str, Any]) -> Any:
    """A use's options over its plugin section, as the core merges them."""
    return WebhookOptions.model_validate(merge_options(section, overrides))


class OptionsTests(unittest.TestCase):
    def test_builds_the_url_from_channel_and_token(self) -> None:
        cfg = WebhookOptions(channel="AAAA", token="t0k=")
        self.assertEqual(
            cfg.webhook_url().get_secret_value(),
            "https://chat.googleapis.com/v1/spaces/AAAA/messages"
            f"?key={WEBHOOK_KEY}&token=t0k%3D",
        )

    def test_takes_the_url_as_given(self) -> None:
        cfg = WebhookOptions(url="https://chat.test/hook")
        self.assertEqual(cfg.webhook_url().get_secret_value(), "https://chat.test/hook")

    def test_needs_exactly_one_form(self) -> None:
        for options in (
            {},
            {"channel": "AAAA"},
            {"token": "t"},
            {"url": "https://chat.test/hook", "channel": "AAAA", "token": "t"},
        ):
            with self.subTest(options), self.assertRaises(pydantic.ValidationError):
                WebhookOptions.model_validate(options)

    def test_an_entry_overrides_the_section(self) -> None:
        section = {"channel": "AAAA", "token": "t"}
        self.assertEqual(webhook_options(section, {}).channel, "AAAA")
        self.assertEqual(webhook_options(section, {"channel": "BBBB"}).channel, "BBBB")
        with self.assertRaises(pydantic.ValidationError):
            webhook_options({}, {})

    def test_entry_point_registers_the_sink_class(self) -> None:
        ((name, protocol, cls),) = googlechat.__newstool_plugin__()
        self.assertEqual(
            (name, protocol, cls), ("googlechat", SinkType, GoogleChatSink)
        )


@patch("newstool.plugins.googlechat.requests.post")
class GoogleChatSinkTests(unittest.TestCase):
    def send(self, document: Document, **options: Any) -> Any:
        sink = GoogleChatSink(
            webhook_options({"channel": "AAAA", "token": "secret"}, options),
            Services(db=Mock(), fetcher=Mock()),
        )
        return sink.send(document)

    @staticmethod
    def document(image_url: str | None = None) -> Document:
        return Document(
            app="items",
            output="items",
            key="item:a/h1",
            content_type="text/plain",
            content="S summary",
            title="A <b> & c",
            url="https://a.test/1?a=1&b=2",
            image_url=image_url,
        )

    @staticmethod
    def ok(post: Mock) -> None:
        post.return_value = Mock(ok=True)
        post.return_value.json.return_value = {"name": "spaces/AAAA/messages/m1"}

    def test_posts_title_text_and_link_as_a_card(self, post: Mock) -> None:
        self.ok(post)

        reference = self.send(self.document())

        self.assertEqual(
            card_widgets(post.call_args.kwargs["json"]),
            [
                {
                    "textParagraph": {
                        "text": "<b>A &lt;b&gt; &amp; c</b><br><br>S summary"
                    }
                },
                {
                    "buttonList": {
                        "buttons": [
                            {
                                "text": "original article",
                                "onClick": {
                                    "openLink": {"url": "https://a.test/1?a=1&b=2"}
                                },
                            }
                        ]
                    }
                },
            ],
        )
        self.assertEqual(reference, {"message": "spaces/AAAA/messages/m1"})

    def test_without_title_or_link_only_the_text(self, post: Mock) -> None:
        self.ok(post)

        self.send(Document("d", "digest", "k", "text/markdown", "# Week"))

        self.assertEqual(
            card_widgets(post.call_args.kwargs["json"]),
            [{"textParagraph": {"text": "# Week"}}],
        )

    def test_image_and_link_text(self, post: Mock) -> None:
        self.ok(post)

        self.send(self.document("https://a.test/image.jpg"), link_text="Leer <más>")
        self.send(self.document(BLOGGER_IMAGE))

        messages = [card_widgets(call.kwargs["json"]) for call in post.call_args_list]
        self.assertEqual(
            messages[0][1]["image"],
            {"imageUrl": "https://a.test/image.jpg", "altText": "A <b> & c"},
        )
        self.assertEqual(
            messages[1][1]["image"]["imageUrl"], chat_image_url(BLOGGER_IMAGE)
        )
        (button,) = messages[0][2]["buttonList"]["buttons"]
        self.assertEqual(button["text"], "Leer <más>")

    def test_images_off_sends_text_only(self, post: Mock) -> None:
        self.ok(post)

        self.send(self.document("https://a.test/image.jpg"), images=False)

        widgets = card_widgets(post.call_args.kwargs["json"])
        self.assertFalse(any("image" in widget for widget in widgets))

    def test_failed_post_does_not_leak_the_token(self, post: Mock) -> None:
        post.side_effect = requests.ConnectionError("url: ...&token=secret")

        with self.assertRaises(PluginFailure) as raised:
            self.send(self.document())

        self.assertEqual(str(raised.exception), "ConnectionError")
        self.assertIsNone(raised.exception.__cause__)

    def test_api_error_is_a_failure(self, post: Mock) -> None:
        post.return_value = Mock(ok=False)
        post.return_value.json.return_value = {"error": {"message": "bad space"}}

        with self.assertRaisesRegex(PluginFailure, "bad space"):
            self.send(self.document())


if __name__ == "__main__":
    unittest.main()
