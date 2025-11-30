import collections
import logging
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse

import scrapy
import scrapy.crawler as crawler
from twisted.internet import defer, reactor


class UrlSpider(scrapy.Spider):
    name: str = "urlspider"

    custom_settings: Dict[str, Any] = {
        "COOKIES_ENABLED": False,
        # "HTTPCACHE_ENABLED": True,  # useful to have set True locally for repetative runs while debugging code changes
        "LOG_LEVEL": "INFO",
        "CONCURRENT_REQUESTS": 64,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 5,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 64,
        "DOWNLOAD_TIMEOUT": 20,
        "USER_AGENT": "Mozilla/5.0 (compatible; Data Against Feminicide academic research; datoscontrafeminicidio.net)",
    }

    def __init__(
        self,
        handle_parse: Optional[Callable],
        start_urls: List[str],
        *args: List,
        **kwargs: Dict,
    ) -> None:
        """
        Handle_parse will be called with a story:Dict object
        :param handle_parse:
        :param start_urls:
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.on_parse = handle_parse
        self.start_urls = start_urls
        logging.getLogger("scrapy").setLevel(logging.INFO)
        logging.getLogger("scrapy.core.engine").setLevel(logging.INFO)

    def parse(self, response):
        # grab the original, undirected URL so we can relink later
        orig_url = (
            response.request.meta["redirect_urls"][0]
            if "redirect_urls" in response.request.meta
            else response.request.url
        )
        story_data = dict(
            content=response.text, final_url=response.request.url, original_url=orig_url
        )
        if self.on_parse:
            self.on_parse(story_data)
        return None


def group_urls_by_domain(urls: List[str]) -> List[List[str]]:
    """
    Groups URLs by their domain. Skips URLs that do not have extractable domains.
    """
    domain_groups = collections.defaultdict(list)

    for url in urls:
        domain = urlparse(url).netloc
        if domain:
            domain_groups[domain].append(url)

    return list(domain_groups.values())


def fetch_all_html(
    urls: List[str], handle_parse: Callable, num_spiders: int = 4
) -> None:
    if not urls:
        return

    domain_list = group_urls_by_domain(urls)
    batches = [[] for _ in range(num_spiders)]
    for i, domain_urls in enumerate(domain_list):
        batches[i % num_spiders].extend(domain_urls)

    # Single runner for ALL spiders
    runner = crawler.CrawlerRunner()
    deferreds = [
        runner.crawl(UrlSpider, handle_parse=handle_parse, start_urls=batch)
        for batch in batches
        if batch
    ]

    dl = defer.DeferredList(deferreds)
    dl.addBoth(lambda _: reactor.stop())
    reactor.run()
