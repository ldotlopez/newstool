import unittest
from typing import Any
from unittest.mock import Mock, patch

import pydantic
import requests

from newstool.errors import PluginFailure
from newstool.models import Document
from newstool.plugins import Services, merge_options, telegram
from newstool.plugins.telegram import (
    MAX_CAPTION_LENGTH,
    TelegramOptions,
    TelegramSink,
    build_caption,
)
from newstool.sinks import SinkType

SECTION = {"bot_token": "s3cr3t", "chat_id": "chat"}


def options(section: dict[str, Any], overrides: dict[str, Any]) -> TelegramOptions:
    """An instance's options over its plugin section, as the core merges them."""
    return TelegramOptions.model_validate(merge_options(section, overrides))


def sink(**overrides: Any) -> TelegramSink:
    return TelegramSink(
        options(SECTION, overrides), Services(db=Mock(), fetcher=Mock())
    )


def item_document(content: str = "Summary", image_url: str | None = None) -> Document:
    return Document(
        app="items",
        output="items",
        key="item:a/h3",
        content_type="text/plain",
        content=content,
        title="Hour <3>",
        url="https://a.test/3?a=1&b=2",
        image_url=image_url,
    )


def ok_response(message_id: int = 42) -> Mock:
    response = Mock()
    response.json.return_value = {"ok": True, "result": {"message_id": message_id}}
    return response


@patch("newstool.plugins.telegram.requests.post")
class TelegramSinkTests(unittest.TestCase):
    def test_sends_text_without_image(self, post: Mock) -> None:
        post.return_value = ok_response()

        reference = sink().send(item_document())

        (request_url,) = post.call_args.args
        payload = post.call_args.kwargs["json"]
        self.assertTrue(request_url.endswith("/sendMessage"))
        self.assertIn("<b>Hour &lt;3&gt;</b>", payload["text"])
        self.assertIn("Summary", payload["text"])
        self.assertIn(">original article</a>", payload["text"])
        self.assertEqual(payload["link_preview_options"], {"is_disabled": True})
        self.assertEqual(reference, {"chat_id": "chat", "message_id": 42})

    def test_an_instance_needs_a_token_and_a_chat(self, post: Mock) -> None:
        for section, overrides in (
            ({"bot_token": "token"}, {}),
            ({"chat_id": "chat"}, {}),
            ({}, {"chat_id": "c"}),
        ):
            with (
                self.subTest(overrides=overrides),
                self.assertRaises(pydantic.ValidationError),
            ):
                options(section, overrides)

    def test_an_instance_overrides_or_replaces_the_section(self, post: Mock) -> None:
        post.return_value = ok_response()
        # No section: the instance says it all.
        instance_options = options({}, {"bot_token": "other", "chat_id": "@channel"})

        TelegramSink(instance_options, Services(db=Mock(), fetcher=Mock())).send(
            item_document()
        )

        (request_url,) = post.call_args.args
        self.assertEqual(request_url, "https://api.telegram.org/botother/sendMessage")
        self.assertEqual(post.call_args.kwargs["json"]["chat_id"], "@channel")
        self.assertNotIn("other", repr(instance_options))  # the token stays secret

    def test_failed_post_does_not_leak_the_token(self, post: Mock) -> None:
        post.side_effect = requests.ConnectionError("url: /bots3cr3t/sendMessage")

        with self.assertRaises(PluginFailure) as raised:
            sink().send(item_document())

        self.assertEqual(str(raised.exception), "ConnectionError")
        self.assertIsNone(raised.exception.__cause__)

    def test_api_error_is_a_failure(self, post: Mock) -> None:
        post.return_value.json.return_value = {"ok": False, "description": "Nope"}

        with self.assertRaisesRegex(PluginFailure, "Nope"):
            sink().send(item_document())

    @patch("newstool.plugins.telegram.requests.get")
    def test_uploads_photo_with_escaped_caption(self, get: Mock, post: Mock) -> None:
        get.return_value.content = b"JPEG"
        get.return_value.headers = {"Content-Type": "image/jpeg"}
        post.return_value = ok_response()

        sink().send(item_document(image_url="https://a.test/image.jpg"))

        get.assert_called_once_with("https://a.test/image.jpg", timeout=30)
        (request_url,) = post.call_args.args
        payload = post.call_args.kwargs["data"]
        self.assertTrue(request_url.endswith("/sendPhoto"))
        self.assertEqual(
            post.call_args.kwargs["files"],
            {"photo": ("image.jpg", b"JPEG", "image/jpeg")},
        )
        self.assertIn("Hour &lt;3&gt;", payload["caption"])
        self.assertIn('href="https://a.test/3?a=1&amp;b=2"', payload["caption"])

    @patch("newstool.plugins.telegram.requests.get")
    def test_image_download_failure_fails_the_send(self, get: Mock, post: Mock) -> None:
        get.return_value.raise_for_status.side_effect = requests.HTTPError("404")

        with self.assertRaises(requests.HTTPError):
            sink().send(item_document(image_url="https://a.test/image.jpg"))
        post.assert_not_called()

    def test_images_off_sends_text(self, post: Mock) -> None:
        post.return_value = ok_response()

        sink(images=False).send(item_document(image_url="https://a.test/image.jpg"))

        (request_url,) = post.call_args.args
        self.assertTrue(request_url.endswith("/sendMessage"))

    def test_link_text_and_preview_are_configurable(self, post: Mock) -> None:
        post.return_value = ok_response()

        sink(link_preview=True, link_text="Leer <más>").send(item_document())

        payload = post.call_args.kwargs["json"]
        self.assertIn(">Leer &lt;más&gt;</a>", payload["text"])
        self.assertEqual(payload["link_preview_options"], {"is_disabled": False})

    def test_markdown_posts_the_text_unescaped(self, post: Mock) -> None:
        post.return_value = ok_response()

        sink(markdown=True).send(item_document())

        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["parse_mode"], "Markdown")
        self.assertIn("*Hour <3>*", payload["text"])
        self.assertIn("[original article](https://a.test/3?a=1&b=2)", payload["text"])

    def test_a_document_too_long_for_a_message_is_sent_as_a_file(
        self, post: Mock
    ) -> None:
        post.return_value = ok_response(7)
        digest = Document(
            app="weekly",
            output="digest",
            key="a/2026-10-01_2026-10-08",
            content_type="text/markdown",
            content="# Week\n" + "x" * 5000,
            title="A: 2026-10-01 – 2026-10-08",
        )

        reference = sink().send(digest)

        (request_url,) = post.call_args.args
        self.assertTrue(request_url.endswith("/sendDocument"))
        self.assertEqual(
            post.call_args.kwargs["data"],
            {"chat_id": "chat", "caption": "A: 2026-10-01 – 2026-10-08"},
        )
        filename, content, content_type = post.call_args.kwargs["files"]["document"]
        self.assertEqual(filename, "weekly-a_2026-10-01_2026-10-08.md")
        self.assertEqual((content[:6], content_type), (b"# Week", "text/markdown"))
        self.assertEqual(reference, {"chat_id": "chat", "message_id": 7})


class PluginTests(unittest.TestCase):
    def test_registers_the_sink_class(self) -> None:
        ((name, protocol, cls),) = telegram.__newstool_plugin__()

        self.assertEqual((name, protocol), ("telegram", SinkType))
        self.assertIsInstance(cls, SinkType)
        self.assertEqual(cls.accepts, {"text/plain", "text/markdown"})


class BuildCaptionTests(unittest.TestCase):
    def test_caption_is_bounded_and_keeps_link(self) -> None:
        caption = build_caption("Title", "A" * 2000, "https://example.test/article")

        self.assertLessEqual(len(caption), MAX_CAPTION_LENGTH)
        self.assertIn("original article", caption)
        self.assertIn("https://example.test/article", caption)

    def test_markdown_caption_keeps_the_text_and_link_parseable(self) -> None:
        caption = build_caption(
            "A *bold* title", "**Big** _news_", "https://w.test/a_(b)", markdown=True
        )

        self.assertEqual(
            caption,
            "*A bold title*\n\n**Big** _news_\n\n"
            "[original article](https://w.test/a_(b%29)",
        )

    def test_title_and_link_are_optional(self) -> None:
        self.assertEqual(build_caption(None, "Just <text>", None), "Just &lt;text&gt;")


if __name__ == "__main__":
    unittest.main()
