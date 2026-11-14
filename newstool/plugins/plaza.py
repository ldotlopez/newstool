import hashlib
import logging
import re
from collections.abc import Iterator
from datetime import datetime
from urllib.parse import urljoin

import bs4
from foundation.dtlib import get_local_tz
from foundation.scrapelib import (
    drop_selectors,
    find_canonical_url,
    head_meta_get_value,
    prune_to_spine,
    soupify,
)

from ..errors import PluginFailure
from ..models import SourceData, SourceItemData
from ..providers import URI, IndexSiteProvider, ProviderType
from . import PluginTypes

LOGGER = logging.getLogger(__name__)

DATETIME_RE = re.compile(r"(\d{2})/(\d{2})/(\d{4})[^\d]+(\d{2}):(\d{2})")


def get_section(tag: bs4.Tag, title: str) -> bs4.Tag:
    for section in tag.select("h2 span"):
        if section.get_text().strip().lower() == title.lower():
            return section
    raise PluginFailure(f"Could not find section '{title}' in index page")


def parse_datetime(tag: bs4.Tag) -> datetime:
    text = tag.get_text().strip()
    if (m := DATETIME_RE.search(text)) is None:
        raise PluginFailure(f"Could not parse datetime from text: {text}")
    day, month, year, hour, minute = map(int, m.groups())
    dt = datetime(year, month, day, hour, minute, tzinfo=get_local_tz())
    return dt


class PlazaProvider(IndexSiteProvider):
    def parse_index(self, content: bytes, source: SourceData) -> Iterator[URI]:
        soup = soupify(content.decode("utf-8"))
        section = get_section(soup, "Castellón")
        container = section.find_parent("div", {"class": "wrap-SUPERIOR"})
        headlines = container.find_all(["h2", "h3"], {"itemprop": "headline"})
        for h in headlines:
            path = h.find("a").attrs.get("href")
            url = urljoin(str(source.url), path)
            yield url

    def parse_item(self, content: bytes) -> SourceItemData:
        soup = soupify(content.decode("utf-8"))

        title = head_meta_get_value(soup, {"property": "og:title"})
        image = head_meta_get_value(soup, {"property": "og:image"})
        if (url := find_canonical_url(soup)) is None:
            raise PluginFailure("no canonical URL")
        author = soup.select_one(".redactor a").get_text().strip()
        content = soup.select_one(".wrap-FULL")
        drop_selectors(content, [".container-mega", ".COLUMNA-DER"])
        prune_to_spine(content)

        try:
            pub_time = parse_datetime(soup.select_one(".fecha-pub"))
        except ValueError:
            LOGGER.warning(f"Could not parse publication date of '{url}'")
            pub_time = None

        try:
            mod_time = parse_datetime(soup.select_one(".fecha-mod"))
        except ValueError:
            mod_time = None

        return SourceItemData(
            uid=hashlib.sha256(url.encode()).hexdigest(),
            title=title,
            uri=url,
            content=str(content).encode("utf-8"),
            mimetype="text/html",
            published_at=pub_time,
            modified_at=mod_time,
            data={
                "author": author,
                "image": image,
            },
        )


def __newstool_plugin__() -> PluginTypes:
    return [("plaza", ProviderType, PlazaProvider)]
