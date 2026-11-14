import datetime
import hashlib
import unittest
from pathlib import Path
from unittest.mock import Mock

import pydantic

from newstool.models import PreflightSourceItemData, SourceData, SourceItemData
from newstool.plugins import NoOptions, Services, merge_options
from newstool.plugins.csjuntasgobierno import CSJuntasGobiernoProvider
from newstool.plugins.feedreader import FeedReaderProvider, Options
from newstool.plugins.prensaiberica import Options as PrensaIbericaOptions
from newstool.plugins.prensaiberica import PrensaIbericaProvider
from newstool.plugins.telegram_channel import Options as ChannelOptions
from newstool.plugins.telegram_channel import (
    TelegramChannelProvider,
    parse_article,
    parse_preview,
    preview_url,
)


def read_sample(name: str) -> bytes:
    filepath = Path(__file__).parent / "samples" / name
    return filepath.read_bytes()


class TestCSJuntasGobierno(unittest.TestCase):
    def test_session_dates_follow_madrid_dst(self) -> None:
        index = b"""<ul>
        <li>Sesi\xc3\xb3n del d\xc3\xada 28 de mayo de 2026
            <a href="/a.pdf/1">Descargar extracto</a></li>
        <li>Sesi\xc3\xb3n del d\xc3\xada 3 de diciembre de 2026
            <a href="/b.pdf/1">Descargar extracto</a></li>
        </ul>"""
        provider = CSJuntasGobiernoProvider(
            NoOptions(), Services(db=Mock(), fetcher=Mock())
        )
        links = provider._iter_pdf_links(index, "https://x.test/")

        summer, winter = (link.dt.utcoffset() for link in links)
        self.assertEqual(summer, datetime.timedelta(hours=2))
        self.assertEqual(winter, datetime.timedelta(hours=1))

    def test_pdfs_are_downloaded_only_when_retrieved(self) -> None:
        index = b"""<ul><li>Sesi\xc3\xb3n del d\xc3\xada 28 de mayo de 2026
            <a href="/a.pdf/1">Descargar extracto</a></li></ul>"""
        pages = {"https://x.test/": index, "https://x.test/a.pdf/1": b"%PDF"}
        fetched: list[str] = []
        fetcher = Mock(get=lambda url: fetched.append(url) or pages[url])
        source = Mock(id="src", url="https://x.test/")

        provider = CSJuntasGobiernoProvider(
            NoOptions(), Services(db=Mock(), fetcher=fetcher)
        )
        (preflight_item,) = provider.iter_items(source)
        self.assertEqual(fetched, ["https://x.test/"])
        self.assertEqual(
            preflight_item.modified_at.utcoffset(), datetime.timedelta(hours=2)
        )

        item = provider.retrieve_item(preflight_item)
        self.assertEqual((item.uid, item.content), (preflight_item.uid, b"%PDF"))
        self.assertEqual(fetched, ["https://x.test/", "https://x.test/a.pdf/1"])


ARTICLE_PAGE = (
    b'<html><body><article><div class="body"><p>full</p></div></article></body></html>'
)


class TestFeedReader(unittest.TestCase):
    def parse(
        self,
        feed: bytes,
        default_selector: str | None = None,
        article_page: bytes = ARTICLE_PAGE,
        **provider_options: str | bool,
    ) -> list[SourceItemData]:
        pages = {"https://x.test/feed": feed, "https://x.test/1": article_page}
        source = Mock(id="src", url="https://x.test/feed")
        # The source's options over the plugin section, as the core merges them.
        section = {"article_selector": default_selector}
        options = Options.model_validate(merge_options(section, provider_options))
        fetcher = Mock(get=lambda url: pages[url])
        provider = FeedReaderProvider(options, Services(db=Mock(), fetcher=fetcher))
        return list(provider.retrieve_items(source))

    def test_rss_with_encoded_content(self) -> None:
        feed = b"""<?xml version="1.0"?>
        <rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/"
             xmlns:dc="http://purl.org/dc/elements/1.1/"
             xmlns:media="http://search.yahoo.com/mrss/"><channel>
        <item>
          <title>One</title><link>https://x.test/1</link><guid>id-1</guid>
          <dc:creator>Ana</dc:creator>
          <category>Local</category><category>Politics</category>
          <pubDate>Mon, 26 Oct 2026 10:00:00 +0100</pubDate>
          <description>short</description>
          <content:encoded><![CDATA[<p>full body</p>]]></content:encoded>
          <media:content url="https://x.test/1.jpg" medium="image"/>
        </item>
        <item><link>https://x.test/2</link><description>only summary</description></item>
        <item><title>no link</title></item>
        </channel></rss>"""
        first, second = self.parse(feed)

        self.assertEqual(first.uid, hashlib.sha256(b"id-1").hexdigest())
        self.assertEqual(first.content, b"<p>full body</p>")
        self.assertEqual(first.mimetype, "text/html")
        self.assertEqual(
            first.published_at,
            datetime.datetime(2026, 10, 26, 9, tzinfo=datetime.UTC),
        )
        self.assertIsNone(first.modified_at)
        self.assertEqual(
            first.data,
            {
                "author": "Ana",
                "image": "https://x.test/1.jpg",
                "section": "Local",
                "tags": ["Local", "Politics"],
            },
        )
        self.assertEqual(second.uid, hashlib.sha256(b"https://x.test/2").hexdigest())
        self.assertEqual(second.title, "")
        self.assertEqual(second.content, b"only summary")
        self.assertIsNone(second.published_at)

    def test_atom_updated_and_enclosure(self) -> None:
        feed = b"""<?xml version="1.0"?>
        <feed xmlns="http://www.w3.org/2005/Atom"><entry>
          <title>A</title><id>urn:a</id><link href="https://x.test/a"/>
          <link rel="enclosure" type="image/png" href="https://x.test/a.png"/>
          <updated>2026-10-26T12:00:00Z</updated>
          <author><name>B</name></author><author><name>C</name></author>
          <content type="html">&lt;b&gt;x&lt;/b&gt;</content>
        </entry></feed>"""
        (item,) = self.parse(feed)

        self.assertEqual(
            item.modified_at,
            datetime.datetime(2026, 10, 26, 12, tzinfo=datetime.UTC),
        )
        self.assertEqual(item.data["author"], "B, C")
        self.assertEqual(item.data["image"], "https://x.test/a.png")
        self.assertEqual(item.content, b"<b>x</b>")

    def test_image_from_content_and_bad_date(self) -> None:
        feed = b"""<?xml version="1.0"?><rss version="2.0"><channel><item>
          <link>https://x.test/1</link><pubDate>someday</pubDate>
          <description>&lt;p&gt;&lt;img src="/i.jpg"&gt;&lt;/p&gt;</description>
        </item></channel></rss>"""
        with self.assertLogs("newstool.plugins.feedreader", "WARNING"):
            (item,) = self.parse(feed)

        self.assertIsNone(item.published_at)
        self.assertEqual(item.data["image"], "https://x.test/i.jpg")
        self.assertIsNone(item.data["section"])

    def test_article_selector_on_the_fetched_page(self) -> None:
        feed = b"""<?xml version="1.0"?><rss version="2.0"><channel><item>
          <link>https://x.test/1</link><description>teaser</description>
        </item></channel></rss>"""
        # The source's option beats the plugin's default.
        (item,) = self.parse(
            feed, "nav", article_selector="article .body", fetch_article=True
        )

        self.assertEqual(item.content, b'<div class="body"><p>full</p></div>')
        self.assertEqual(item.mimetype, "text/html")

    def test_article_selector_defaults_to_the_plugin_option(self) -> None:
        feed = b"""<?xml version="1.0"?><rss version="2.0"><channel><item>
          <link>https://x.test/1</link><description>teaser</description>
        </item></channel></rss>"""
        (item,) = self.parse(feed, "article .body", fetch_article=True)

        self.assertEqual(item.content, b'<div class="body"><p>full</p></div>')

    def test_article_selector_on_the_feed_html(self) -> None:
        feed = b"""<?xml version="1.0"?><rss version="2.0"><channel><item>
          <link>https://x.test/1</link>
          <description>&lt;nav&gt;menu&lt;/nav&gt;&lt;p&gt;text&lt;/p&gt;</description>
        </item></channel></rss>"""
        (item,) = self.parse(feed, article_selector="p")

        self.assertEqual(item.content, b"<p>text</p>")

    def test_article_selector_keeps_plain_text(self) -> None:
        feed = b"""<?xml version="1.0"?>
        <feed xmlns="http://www.w3.org/2005/Atom"><entry>
          <id>urn:a</id><link href="https://x.test/1"/>
          <content type="text">teaser</content>
        </entry></feed>"""
        (item,) = self.parse(feed, article_selector="p")

        self.assertEqual(item.content, b"teaser")
        self.assertEqual(item.mimetype, "text/plain")

    def test_fetch_article_keeps_the_whole_page(self) -> None:
        feed = b"""<?xml version="1.0"?><rss version="2.0"><channel><item>
          <link>https://x.test/1</link><description>teaser</description>
        </item></channel></rss>"""
        (item,) = self.parse(feed, fetch_article=True)

        self.assertEqual(item.content, ARTICLE_PAGE)
        self.assertEqual(item.mimetype, "text/html")

    def test_fetched_page_must_be_utf8(self) -> None:
        feed = b"""<?xml version="1.0"?><rss version="2.0"><channel><item>
          <link>https://x.test/1</link><description>teaser</description>
        </item></channel></rss>"""
        with self.assertLogs("newstool.plugins.feedreader", "ERROR"):
            items = self.parse(feed, article_page=b"<p>caf\xe9</p>", fetch_article=True)

        self.assertEqual(items, [])

    def test_home_page_links_to_its_feed(self) -> None:
        home = b"""<html><head>
        <link rel="stylesheet" href="/s.css">
        <link rel="alternate" type="application/rss+xml" href="/feed">
        </head><body>news</body></html>"""
        feed = b"""<?xml version="1.0"?><rss version="2.0"><channel><item>
          <link>https://x.test/1</link><description>hi</description>
        </item></channel></rss>"""
        pages = {"https://x.test/": home, "https://x.test/feed": feed}
        source = Mock(id="src", url="https://x.test/")
        fetcher = Mock(get=lambda url: pages[url])

        provider = FeedReaderProvider(Options(), Services(db=Mock(), fetcher=fetcher))
        (item,) = provider.retrieve_items(source)

        self.assertEqual(item.content, b"hi")

    def test_not_a_feed(self) -> None:
        with self.assertRaises(ValueError):
            self.parse(b"<html><body>404</body></html>")


class TestPrensaIberica(unittest.TestCase):
    def setUp(self) -> None:
        self.fetcher = Mock()
        self.provider = PrensaIbericaProvider(
            PrensaIbericaOptions(
                exclude_sections=["comarcas", "VÍDEOS Y GALERÍAS DE CASTELLÓN"]
            ),
            Services(db=Mock(), fetcher=self.fetcher),
        )

    def check_parser(self, filename: str, expected: SourceItemData):
        buff = read_sample(filename)
        entry_data = self.provider.parse_item(buff)
        self.assertEqual(entry_data.uid, expected.uid)
        self.assertEqual(entry_data.uri, expected.uri)
        self.assertEqual(entry_data.title, expected.title)
        self.assertTrue(len(entry_data.content) > 1000)
        self.assertEqual(entry_data.data["image"], expected.data["image"])
        self.assertEqual(entry_data.data["section"], expected.data["section"])
        self.assertEqual(entry_data.data["author"], expected.data["author"])
        self.assertEqual(set(entry_data.data["tags"]), set(expected.data["tags"]))

    def test_parse_item_0(self) -> None:
        self.check_parser(
            "prensaiberica-item-132310503.html",
            SourceItemData(
                uid="ec16b09f034ca03296e75d7e5c304f10337f2e77a0327b0d045c54f0a1d970e8",
                title="El eco perdido de las fiestas de julio nacidas del asedio carlista sobre Castellón",
                uri="https://www.elperiodicomediterraneo.com/castello/2026/07/11/eco-perdido-fiestas-julio-castellon-ribalta-carlista-historia-132310503.html",
                content=b"[ignore]",
                mimetype="text/html",
                data={
                    "author": "Ximo Górriz",
                    "image": "https://estaticos-cdn.prensaiberica.es/clip/66d17ffb-8e7c-43cf-9a9f-40d50ef6654d_16-9-discover-aspect-ratio_default_0_x683y256.png",
                    "section": "Castelló Ciutat",
                    "tags": [
                        "Banda Municipal de Castelló",
                        "Castellón",
                        "cultura",
                        "Democracia",
                        "dictadura",
                        "Educación",
                        "Fiestas",
                        "guerras",
                        "Hemeroteca",
                        "historia",
                        "julio",
                        "Liberalismo",
                        "Parque Ribalta",
                        "Política",
                        "prensa",
                        "Religión",
                        "Tráfico",
                        "Urbanismo",
                    ],
                },
            ),
        )

    def test_parse_item_1(self) -> None:
        self.check_parser(
            "prensaiberica-item-132340038.html",
            SourceItemData(
                uid="1cdcc387ffb74bf5aac47f4362155338180c7c2a791ace14068a3dc7eecfd436",
                title="El Grau se vuelca en las fiestas en honor a la Virgen "
                "del Carmen: los 22 actos del programa y todas las "
                "novedades",
                content=b"[ignore]",
                mimetype="text/html",
                uri="https://www.elperiodicomediterraneo.com/castello/2026/07/11/grau-vuelca-fiestas-honor-virgen-carmen-actos-castello-castellon-132340038.html",
                data={
                    "author": "Paloma Aguilar",
                    "image": "https://estaticos-cdn.prensaiberica.es/clip/dc0a25d9-fc1d-4d2b-9b47-59120753422c_16-9-discover-aspect-ratio_default_0_x783y366.jpg",
                    "mod_date": datetime.datetime(
                        2026,
                        7,
                        11,
                        6,
                        10,
                        18,
                        tzinfo=datetime.timezone(datetime.timedelta(seconds=7200)),
                    ),
                    "pub_date": datetime.datetime(
                        2026,
                        7,
                        11,
                        6,
                        10,
                        18,
                        tzinfo=datetime.timezone(datetime.timedelta(seconds=7200)),
                    ),
                    "section": "Castelló Ciutat",
                    "tags": [
                        "Castelló",
                        "novedades",
                        "La Virgen",
                        "Fiestas",
                        "El Grau",
                    ],
                },
            ),
        )

    def test_parse_item_2(self) -> None:
        self.check_parser(
            "prensaiberica-item-132344288.html",
            SourceItemData(
                uid="12cd5c47e09f096cdb188afee9bd8d25ee06d40ee41feb1c2ec2d11f1679f96b",
                title="Castellón apoya a la selección española desde la plaza Mayor",
                uri="https://www.elperiodicomediterraneo.com/deportes/2026/07/10/castellon-apoya-seleccion-espanola-plaza-belgica-mayor-132344288.html",
                content=b"[ignore]",
                mimetype="text/html",
                data={
                    "author": "David Oliver",
                    "image": "https://estaticos-cdn.prensaiberica.es/clip/2e7b2496-8242-4717-b9ed-738592c3f461_16-9-discover-aspect-ratio_default_0_x731y325.jpg",
                    "mod_date": datetime.datetime(
                        2026,
                        7,
                        10,
                        22,
                        17,
                        29,
                        tzinfo=datetime.timezone(datetime.timedelta(seconds=7200)),
                    ),
                    "pub_date": datetime.datetime(
                        2026,
                        7,
                        10,
                        22,
                        17,
                        29,
                        tzinfo=datetime.timezone(datetime.timedelta(seconds=7200)),
                    ),
                    "section": "Deportes",
                    "tags": [
                        "Deportes",
                        "Castellón",
                        "Selección Española",
                        "plaza Mayor",
                        "Ayuntamiento",
                        "En directo",
                    ],
                },
            ),
        )

    def test_iter_items_excluded_sections_default_and_empty(self) -> None:
        index = read_sample("prensaiberica-index-castello.html")
        source = Mock(url="https://www.elperiodicomediterraneo.com/castello/")
        for options, expected in (
            (PrensaIbericaOptions(), 21),
            (PrensaIbericaOptions(exclude_sections=[]), 41),
        ):
            fetcher = Mock(get=Mock(return_value=index))
            services = Services(db=Mock(), fetcher=fetcher)
            provider = PrensaIbericaProvider(options, services)
            self.assertEqual(len(list(provider.iter_items(source))), expected)

    def test_iter_items_lists_dated_articles_without_excluded_sections(self) -> None:
        # The excluded titles differ in case from the index's headers.
        index = read_sample("prensaiberica-index-castello.html")
        source = Mock(url="https://www.elperiodicomediterraneo.com/castello/")
        fetcher = self.fetcher
        fetcher.get.return_value = index

        items = list(self.provider.iter_items(source))

        fetcher.get.assert_called_once_with(
            "https://www.elperiodicomediterraneo.com/castello/"
        )
        self.assertEqual(len(items), 21)
        refs = [item.ref for item in items]
        self.assertEqual(len(set(refs)), len(refs))
        self.assertFalse(any("/comarcas/" in ref or "/videos/" in ref for ref in refs))
        self.assertTrue(
            all(
                item.uid == hashlib.sha256(item.ref.encode()).hexdigest()
                for item in items
            )
        )
        self.assertEqual(
            items[0].ref,
            "https://www.elperiodicomediterraneo.com/castello/2026/10/30/luces-navidad-castello-ayuntamiento-encendido-castellon-135891703.html",
        )
        self.assertEqual(
            items[0].modified_at,
            datetime.datetime(
                2026,
                10,
                30,
                6,
                10,
                45,
                tzinfo=datetime.timezone(datetime.timedelta(hours=1)),
            ),
        )

    def test_iter_items_card_template(self) -> None:
        # This index links articles relatively, has no dates and other headers.
        index = read_sample("prensaiberica-index-castello-provincia.html")
        source = Mock(url="https://www.elperiodicomediterraneo.com/castello-provincia/")
        for options, expected in (
            (PrensaIbericaOptions(), 63),
            (PrensaIbericaOptions(exclude_sections=[]), 67),
        ):
            fetcher = Mock(get=Mock(return_value=index))
            provider = PrensaIbericaProvider(
                options, Services(db=Mock(), fetcher=fetcher)
            )
            items = list(provider.iter_items(source))
            refs = [item.ref for item in items]
            self.assertEqual(len(refs), expected)
            self.assertEqual(len(set(refs)), len(refs))
            self.assertTrue(
                all(
                    ref.startswith("https://www.elperiodicomediterraneo.com/")
                    for ref in refs
                )
            )
            self.assertTrue(all(item.modified_at is None for item in items))
        self.assertEqual(
            refs[0],
            "https://www.elperiodicomediterraneo.com/castello-provincia/2026/10/30/cadena-supermercados-castellon-borde-final-oromarket-135892901.html",
        )

    def test_retrieve_item_fetches_and_parses_ref(self) -> None:
        content = read_sample("prensaiberica-item-132310503.html")
        fetcher = self.fetcher
        fetcher.get.return_value = content
        preflight_item = PreflightSourceItemData(
            uid="ec16b09f034ca03296e75d7e5c304f10337f2e77a0327b0d045c54f0a1d970e8",
            ref="https://example.test/article",
        )
        item = self.provider.retrieve_item(preflight_item)

        fetcher.get.assert_called_once_with("https://example.test/article")
        self.assertEqual(item.uid, preflight_item.uid)


ARTICLE = b"""<!DOCTYPE html><html><head>
<meta property="og:url" content="https://example.test/news/a.html">
<meta property="og:title" content="A title">
</head><body><article><p>Body</p></article></body></html>"""


class TestTelegramChannel(unittest.TestCase):
    PAGE_URL = "https://t.me/s/mediterraneoelperiodico"

    def source(self, url: str = "https://t.me/mediterraneoelperiodico") -> SourceData:
        return SourceData(id="tg", name="tg", url=url, provider="telegram_channel")

    def test_preview_url_accepts_channel_and_preview_urls(self) -> None:
        self.assertEqual(preview_url(self.source()), self.PAGE_URL)
        self.assertEqual(preview_url(self.source(self.PAGE_URL + "/")), self.PAGE_URL)
        with self.assertRaises(ValueError):
            preview_url(self.source("https://t.me/"))

    def test_parse_preview(self) -> None:
        content = read_sample("telegram-channel-mediterraneoelperiodico.html")
        posts, older = parse_preview(content, self.PAGE_URL)

        self.assertEqual(len(posts), 20)
        self.assertEqual(older, self.PAGE_URL + "?before=5154")
        first = posts[0]
        self.assertEqual(first.id, "mediterraneoelperiodico/5154")
        self.assertEqual(first.links, ["https://mrf.lu/2vjWp"])
        self.assertEqual(
            first.published_at,
            datetime.datetime(2026, 10, 22, 7, 34, 7, tzinfo=datetime.UTC),
        )
        self.assertTrue(first.text.startswith("Amenaza con un machete"))
        self.assertTrue(first.image.startswith("https://cdn4.telesco.pe/file/g1cDYUR3"))
        self.assertTrue(all(post.image for post in posts))
        for post in posts:
            self.assertFalse(any("t.me/" in link for link in post.links))

    def test_parse_article_uses_canonical_url(self) -> None:
        item = parse_article(ARTICLE)
        self.assertEqual(item.uri, "https://example.test/news/a.html")
        self.assertEqual(item.title, "A title")
        self.assertEqual(item.mimetype, "text/html")

    def test_parse_article_rejects_non_articles(self) -> None:
        with self.assertRaises(ValueError):
            parse_article(b"%PDF-1.7 \xff\xfe")
        with self.assertRaises(ValueError):
            parse_article(b"<html><head><title>406</title></head></html>")

    def test_retrieve_items_one_item_per_link_and_skips_bad_pages(self) -> None:
        pages = {
            self.PAGE_URL: read_sample("telegram-channel-mediterraneoelperiodico.html"),
            "https://mrf.lu/2vjWp": ARTICLE,
        }
        fetcher = Mock()
        fetcher.get.side_effect = lambda url, use_cache=True: pages.get(
            url, b"not html"
        )

        with self.assertLogs("newstool.plugins.telegram_channel", "ERROR"):
            items = list(
                TelegramChannelProvider(
                    ChannelOptions(), Services(db=Mock(), fetcher=fetcher)
                ).retrieve_items(self.source())
            )

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].data["telegram_post"], "mediterraneoelperiodico/5154")
        self.assertTrue(items[0].data["image"].startswith("https://cdn4.telesco.pe/"))
        self.assertEqual(items[0].published_at.hour, 7)
        # One uncached preview page plus one cached fetch per linked article.
        self.assertEqual(fetcher.get.call_count, 21)
        self.assertEqual(fetcher.get.call_args_list[0].kwargs, {"use_cache": False})
        self.assertEqual(fetcher.get.call_args_list[1].kwargs, {})

    def test_retrieve_items_skips_the_front_page(self) -> None:
        front_page = ARTICLE.replace(
            b"https://example.test/news/a.html",
            b"https://example.test/?utm_source=telegram&amp;mrfcid=1",
        )
        pages = {
            self.PAGE_URL: read_sample("telegram-channel-mediterraneoelperiodico.html"),
            "https://mrf.lu/2vjWp": ARTICLE,
            "https://mrf.lu/2NbpV": front_page,
        }
        fetcher = Mock()
        fetcher.get.side_effect = lambda url, use_cache=True: pages.get(
            url, b"not html"
        )

        with self.assertLogs("newstool.plugins.telegram_channel", "ERROR"):
            items = list(
                TelegramChannelProvider(
                    ChannelOptions(), Services(db=Mock(), fetcher=fetcher)
                ).retrieve_items(self.source())
            )

        self.assertEqual(
            [item.uri for item in items], ["https://example.test/news/a.html"]
        )

    def test_retrieve_items_rejects_non_public_channels(self) -> None:
        fetcher = Mock()
        fetcher.get.return_value = b"<html><head></head><body></body></html>"
        with self.assertRaises(ValueError):
            list(
                TelegramChannelProvider(
                    ChannelOptions(), Services(db=Mock(), fetcher=fetcher)
                ).retrieve_items(self.source())
            )


class TestSourceItemDataContent(unittest.TestCase):
    def make(self, content: bytes, mimetype: str) -> SourceItemData:
        return SourceItemData(
            uid="u",
            title="t",
            uri="https://example.test/a",
            content=content,
            mimetype=mimetype,
        )

    def test_text_must_be_utf8(self) -> None:
        with self.assertRaises(pydantic.ValidationError):
            self.make("ñ".encode("latin-1"), "text/html")

    def test_mimetype_must_not_carry_charset(self) -> None:
        with self.assertRaises(pydantic.ValidationError):
            self.make(b"<p>", "text/html; charset=utf-8")

    def test_binary_is_not_decoded(self) -> None:
        self.assertEqual(self.make(b"\xff\xfe", "application/pdf").content, b"\xff\xfe")


if __name__ == "__main__":
    unittest.main()
