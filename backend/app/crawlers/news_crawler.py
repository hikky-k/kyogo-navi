"""ニュースサイト・業界メディア クローラー

日経・東洋経済・業界専門誌・ITメディア等からの情報を収集する。
- 業界トレンド・市場動向
- 大型案件受注・アライアンス情報
- 決算・業績情報
"""

import logging
import re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.crawlers.base_crawler import BaseCrawler
from app.models.crawl_source import CrawlSource
from app.models.news_article import NewsArticle

logger = logging.getLogger(__name__)


class NewsCrawler(BaseCrawler):
    """ニュースサイトクローラー"""

    def __init__(self, db: Session):
        super().__init__(db)

    @property
    def source_type(self) -> str:
        return "news"

    def parse(self, url: str, html: str, source: CrawlSource) -> list[dict]:
        """ニュースサイトのHTMLをパースする"""
        soup = BeautifulSoup(html, "html.parser")
        items = []
        seen_urls = set()

        # ニュースサイトの記事リンクを探索
        article_elements = soup.find_all(["article", "li", "div", "section"], class_=re.compile(
            r"(article|news|story|entry|item|post|card|headline)", re.I
        ))

        for element in article_elements:
            link = element.find("a", href=True)
            if not link:
                continue

            href = urljoin(url, link["href"])

            # 同じドメインまたは記事ページのみ対象
            if href in seen_urls:
                continue
            seen_urls.add(href)

            # タイトル取得
            title = self._extract_title(element, link)
            if not title or len(title) < 5:
                continue

            # 概要テキスト取得
            summary = self._extract_summary(element)

            # 日付取得
            date = self._extract_date(element)

            items.append({
                "company_id": source.company_id,
                "source": urlparse(url).netloc,
                "source_url": href,
                "title": title,
                "content": summary,
                "published_at": date,
            })

        logger.info(f"ニュースサイトから{len(items)}件の記事を検出: {url}")
        return items[:30]  # 最大30件

    def save_items(self, items: list[dict], source: CrawlSource) -> int:
        """ニュース記事をDBに保存（重複チェック付き）"""
        saved = 0
        for item in items:
            existing = self.db.query(NewsArticle).filter(
                NewsArticle.source_url == item["source_url"]
            ).first()
            if existing:
                continue

            article = NewsArticle(**item)
            self.db.add(article)
            saved += 1

        if saved > 0:
            self.db.commit()
        return saved

    def _extract_title(self, element, link) -> str:
        """記事タイトルを抽出"""
        heading = element.find(["h1", "h2", "h3", "h4"])
        if heading:
            return heading.get_text(strip=True)
        return link.get_text(strip=True)

    def _extract_summary(self, element) -> str | None:
        """記事概要を抽出"""
        # <p> タグで概要テキストを探す
        desc = element.find("p")
        if desc:
            text = desc.get_text(strip=True)
            if len(text) > 20:
                return text[:500]
        return None

    def _extract_date(self, element) -> datetime | None:
        """日付を抽出"""
        # <time> タグ
        time_tag = element.find("time")
        if time_tag:
            dt_str = time_tag.get("datetime", time_tag.get_text(strip=True))
            return self._parse_date(dt_str)

        # classにdateを含む要素
        date_el = element.find(class_=re.compile(r"date|time|publish", re.I))
        if date_el:
            return self._parse_date(date_el.get_text(strip=True))

        return None

    def _parse_date(self, text: str) -> datetime | None:
        """日付文字列をパース"""
        patterns = [
            r"(\d{4})[/.-](\d{1,2})[/.-](\d{1,2})",
            r"(\d{4})年(\d{1,2})月(\d{1,2})日",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    y, m, d = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    return datetime(y, m, d, tzinfo=timezone.utc)
                except ValueError:
                    continue
        return None
