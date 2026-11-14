import logging

import requests
from foundation import cache

LOGGER = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:142.0) Gecko/20100101 Firefox/142.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ca,en-US;q=0.7,en;q=0.3",
    # Only what requests decodes without extra packages: br/zstd came back raw.
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Priority": "u=0, i",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}


class HTTPClient:
    """GET requests with a browser's headers, through a cache."""

    def __init__(self, cache: cache.Cache) -> None:
        self.cache = cache
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    def get(self, url: str, *, use_cache: bool = True) -> bytes:
        if use_cache:
            try:
                content = self.cache.get(url)
                LOGGER.debug(f"{url} found in cache ({len(content)} bytes)")
                return content
            except cache.CacheMissError:
                pass

        resp = self.session.request("GET", url)
        content = resp.content
        LOGGER.debug(f"{url} fetched {len(content)} bytes")
        # Error pages must not be served from cache for the whole TTL.
        if use_cache and resp.ok:
            self.cache.set(url, content)
            LOGGER.debug(f"{url} saved {len(content)} bytes")
        return content
