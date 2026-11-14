import hashlib
import logging
import re
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import bs4

from ..errors import PluginFailure
from ..models import PreflightSourceItemData, SourceData, SourceItemData
from ..providers import BaseProvider, ProviderType
from . import PluginTypes

LOGGER = logging.getLogger(__name__)
# A named zone, not the import time's UTC offset: sessions span DST changes.
MADRID_TZ = ZoneInfo("Europe/Madrid")


MONTH_TABLE = {
    "ene": 1,
    "feb": 2,
    "mar": 3,
    "abr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "ago": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dic": 12,
}
DATE_RE = re.compile(
    r"(\d{1,2})\s+(?:de\s+)?(\S+)\s+(?:de\s+)?(\d{4})",
    re.IGNORECASE | re.DOTALL | re.MULTILINE,
)


@dataclass
class PreparseData:
    uri: str
    dt: datetime
    type_: str
    title: str


class CSJuntasGobiernoProvider(BaseProvider):
    def iter_items(
        self, source: SourceData
    ) -> Iterator[PreflightSourceItemData[PreparseData]]:
        # The index lists every session since 2006 and dates each one: the
        # core skips the stored sessions undownloaded.
        index = self.fetcher.get(str(source.url))
        for protodata in self._iter_pdf_links(index, str(source.url)):
            yield PreflightSourceItemData(
                uid=hashlib.sha256(protodata.uri.encode("utf-8")).hexdigest(),
                ref=protodata,
                modified_at=protodata.dt,
            )

    def retrieve_item(
        self,
        preflight_item: PreflightSourceItemData[PreparseData],
    ) -> SourceItemData:
        protodata = preflight_item.ref
        return SourceItemData(
            uid=preflight_item.uid,
            uri=protodata.uri,
            title=protodata.title,
            published_at=protodata.dt,
            modified_at=protodata.dt,
            content=self.fetcher.get(protodata.uri),
            mimetype="application/pdf",
            data={
                "type": protodata.type_,
            },
        )

    def _iter_pdf_links(self, content: bytes, base_url: str) -> Iterator[PreparseData]:

        soup = bs4.BeautifulSoup(content.decode("utf-8"), "html5lib")

        for link in soup.select("a[href]"):
            # Build the uri
            href = link.get("href") or ""
            if ".pdf/" not in href:
                # Ignore this type of link, as it is not relevant for our purposes
                continue
            uri = urljoin(base_url, href)  # ty: ignore[invalid-argument-type]

            # Parse the type
            if "orden del día" in link.get_text(strip=True).lower():
                type_ = "order"
            elif "extracto" in link.get_text(strip=True).lower():
                type_ = "extract"
            else:
                # Ignore this type of link, as it is not relevant for our purposes
                continue

            # Parse date
            li_parent = link.find_parent("li")
            if li_parent is None:
                LOGGER.warning(f"no parent <li> found for link: {href}")
                continue

            try:
                dt = get_date_from_text(li_parent, DATE_RE)
            except ValueError as exc:
                LOGGER.warning(
                    f"unable to extract date from {li_parent.get_text(strip=True)}: {exc}"
                )
                continue

            day, month_str, year = dt.groups()
            month_key = month_str[:3].lower()
            try:
                month = MONTH_TABLE[month_key]
            except KeyError:
                LOGGER.warning(f"unknown month: {month_str}")
                continue

            dt = datetime(
                year=int(year),
                month=month,
                day=int(day),
                hour=12,
                tzinfo=MADRID_TZ,
            )

            yield PreparseData(
                uri=uri, dt=dt, type_=type_, title=li_parent.get_text(strip=True)
            )


def get_date_from_text(tag: bs4.Tag, pattern: re.Pattern[str]) -> re.Match[str]:
    text = tag.get_text().strip()
    if (m := pattern.search(text)) is None:
        raise PluginFailure(f"Unable to extract date from: {text!r}")

    return m


def __newstool_plugin__() -> PluginTypes:
    return [("csjuntasgobierno", ProviderType, CSJuntasGobiernoProvider)]
