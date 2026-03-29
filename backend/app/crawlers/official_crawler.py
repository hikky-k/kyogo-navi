"""公式サイト・プレスリリース クローラー

企業のコーポレートサイト、採用ページ、ニュースルームからの情報を収集する。
- 組織再編・新サービス開始
- 経営陣交代・人事異動
- 採用強化情報・イベント
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


class OfficialCrawler(BaseCrawler):
    """公式サイトクローラー"""

    def __init__(self, db: Session):
        super().__init__(db)

    @property
    def source_type(self) -> str:
        return "official"

    def parse(self, url: str, html: str, source: CrawlSource) -> list[dict]:
        """公式サイトのHTML（ニュース/プレスリリース一覧）をパースする"""
        soup = BeautifulSoup(html, "html.parser")
        items = []

        # 一般的なニュース・プレスリリース一覧のパターンを探索
        # <a> タグでニュース記事へのリンクを持つ要素を探す
        article_links = self._find_article_links(soup, url)

        for link in article_links:
            item = {
                "company_id": source.company_id,
                "source": urlparse(url).netloc,
                "source_url": link["url"],
                "title": link["title"],
                "content": None,
                "published_at": link.get("date"),
            }
            items.append(item)

        logger.info(f"公式サイトから{len(items)}件の記事を検出: {url}")
        return items

    def save_items(self, items: list[dict], source: CrawlSource) -> int:
        """ニュース記事をDBに保存（重複チェック付き）"""
        saved = 0
        for item in items:
            # source_urlで重複チェック
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

    def _find_article_links(self, soup: BeautifulSoup, base_url: str) -> list[dict]:
        """ページ内からニュース記事リンクを抽出する"""
        results = []
        seen_urls = set()

        # パターン1: <article>, <li>, <div> 内の <a> タグ
        containers = soup.find_all(["article", "li", "div"], class_=re.compile(
            r"(news|press|release|article|post|entry|item|topics)", re.I
        ))

        for container in containers:
            link = container.find("a", href=True)
            if not link:
                continue

            href = urljoin(base_url, link["href"])
            if href in seen_urls:
                continue
            seen_urls.add(href)

            # タイトル取得
            title = self._extract_title(container, link)
            if not title or len(title) < 5:
                continue

            # 日付取得
            date = self._extract_date(container)

            results.append({"url": href, "title": title, "date": date})

        # パターン2: 直接 <a> タグでニュースキーワードを含むもの（上記で見つからない場合）
        if not results:
            for link in soup.find_all("a", href=True):
                href = link.get("href", "")
                if not re.search(r"(news|press|release|topics|info)", href, re.I):
                    continue

                full_url = urljoin(base_url, href)
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                title = link.get_text(strip=True)
                if not title or len(title) < 5:
                    continue

                results.append({"url": full_url, "title": title, "date": None})

        return results[:50]  # 最大50件

    def _extract_title(self, container, link) -> str:
        """コンテナからタイトルを抽出する"""
        # h2, h3, h4 タグを優先
        heading = container.find(["h2", "h3", "h4"])
        if heading:
            return heading.get_text(strip=True)
        # リンクテキストをフォールバック
        return link.get_text(strip=True)

    def _extract_date(self, container) -> datetime | None:
        """コンテナから日付を抽出する"""
        # <time> タグ
        time_tag = container.find("time")
        if time_tag:
            dt = time_tag.get("datetime", time_tag.get_text(strip=True))
            return self._parse_date(dt)

        # class に date を含む要素
        date_el = container.find(class_=re.compile(r"date|time", re.I))
        if date_el:
            return self._parse_date(date_el.get_text(strip=True))

        return None

    def _parse_date(self, text: str) -> datetime | None:
        """日付文字列をパースする"""
        # よくある日付形式を試行
        patterns = [
            r"(\d{4})[/.-](\d{1,2})[/.-](\d{1,2})",  # 2024/01/15, 2024-01-15
            r"(\d{4})年(\d{1,2})月(\d{1,2})日",  # 2024年1月15日
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
