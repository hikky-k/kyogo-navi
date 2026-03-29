"""求人サイト クローラー

LinkedIn, ビズリーチ等からの情報を収集する。
- 募集ポジション・職種・年収レンジ
- 採用規模の変化（求人数の増減）
- 採用要件・待遇条件のトレンド
"""

import logging
import re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.crawlers.base_crawler import BaseCrawler
from app.models.crawl_source import CrawlSource
from app.models.job_posting import JobPosting

logger = logging.getLogger(__name__)


class JobCrawler(BaseCrawler):
    """求人サイトクローラー"""

    def __init__(self, db: Session):
        super().__init__(db)

    @property
    def source_type(self) -> str:
        return "job"

    def parse(self, url: str, html: str, source: CrawlSource) -> list[dict]:
        """求人一覧ページのHTMLをパースする"""
        soup = BeautifulSoup(html, "html.parser")

        if "linkedin" in url.lower():
            return self._parse_linkedin(soup, url, source)
        elif "bizreach" in url.lower():
            return self._parse_bizreach(soup, url, source)
        else:
            return self._parse_generic(soup, url, source)

    def save_items(self, items: list[dict], source: CrawlSource) -> int:
        """求人情報をDBに保存（重複チェック付き）"""
        saved = 0
        for item in items:
            # タイトル + 企業 + ソースで重複チェック
            existing = self.db.query(JobPosting).filter(
                JobPosting.company_id == item["company_id"],
                JobPosting.title == item["title"],
                JobPosting.source == item["source"],
            ).first()

            if existing:
                # 既存の場合は更新
                for key, value in item.items():
                    if key != "company_id" and value is not None:
                        setattr(existing, key, value)
            else:
                posting = JobPosting(**item)
                self.db.add(posting)
                saved += 1

        if saved > 0 or items:
            self.db.commit()
        return saved

    def _parse_linkedin(self, soup: BeautifulSoup, url: str, source: CrawlSource) -> list[dict]:
        """LinkedInの求人一覧をパース"""
        items = []

        job_cards = soup.find_all(class_=re.compile(r"(job.*card|result.*card|jobs-search)", re.I))
        if not job_cards:
            job_cards = soup.find_all("li", class_=re.compile(r"(job|result)", re.I))

        for card in job_cards:
            title_el = card.find(["h3", "h2", "a"], class_=re.compile(r"(title|name)", re.I))
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if not title:
                continue

            department = None
            dept_el = card.find(class_=re.compile(r"(subtitle|department|location)", re.I))
            if dept_el:
                department = dept_el.get_text(strip=True)

            items.append({
                "company_id": source.company_id,
                "source": "linkedin",
                "title": title,
                "department": department,
                "salary_range": self._extract_salary(card),
                "requirements": self._extract_requirements(card),
                "posted_at": self._extract_date(card),
                "is_active": True,
            })

        logger.info(f"LinkedInから{len(items)}件の求人を検出: {url}")
        return items[:50]

    def _parse_bizreach(self, soup: BeautifulSoup, url: str, source: CrawlSource) -> list[dict]:
        """ビズリーチの求人一覧をパース"""
        items = []

        job_cards = soup.find_all(class_=re.compile(r"(job|search.*result|list.*item)", re.I))

        for card in job_cards:
            title_el = card.find(["h2", "h3", "a"], class_=re.compile(r"(title|name|heading)", re.I))
            if not title_el:
                title_el = card.find("a", href=True)
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if not title or len(title) < 3:
                continue

            items.append({
                "company_id": source.company_id,
                "source": "bizreach",
                "title": title,
                "department": self._extract_department(card),
                "salary_range": self._extract_salary(card),
                "requirements": self._extract_requirements(card),
                "posted_at": self._extract_date(card),
                "is_active": True,
            })

        logger.info(f"ビズリーチから{len(items)}件の求人を検出: {url}")
        return items[:50]

    def _parse_generic(self, soup: BeautifulSoup, url: str, source: CrawlSource) -> list[dict]:
        """汎用求人ページパース"""
        items = []
        domain = urlparse(url).netloc

        job_elements = soup.find_all(["article", "li", "div", "tr"], class_=re.compile(
            r"(job|position|career|recruit|vacancy|opening)", re.I
        ))

        for el in job_elements:
            link = el.find("a", href=True)
            title_el = el.find(["h2", "h3", "h4"]) or link
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if not title or len(title) < 3:
                continue

            items.append({
                "company_id": source.company_id,
                "source": domain,
                "title": title,
                "department": self._extract_department(el),
                "salary_range": self._extract_salary(el),
                "requirements": self._extract_requirements(el),
                "posted_at": self._extract_date(el),
                "is_active": True,
            })

        logger.info(f"求人サイトから{len(items)}件の求人を検出: {url}")
        return items[:50]

    def _extract_department(self, element) -> str | None:
        """部署・部門を抽出"""
        dept_el = element.find(class_=re.compile(r"(department|team|division|category)", re.I))
        if dept_el:
            return dept_el.get_text(strip=True)[:200]
        return None

    def _extract_salary(self, element) -> str | None:
        """年収レンジを抽出"""
        salary_el = element.find(class_=re.compile(r"(salary|compensation|pay|年収)", re.I))
        if salary_el:
            return salary_el.get_text(strip=True)[:200]

        # テキスト内の年収パターン
        text = element.get_text()
        match = re.search(r"(\d{3,4}万?\s*[~〜～ー-]\s*\d{3,4}万?円?)", text)
        if match:
            return match.group(1)
        return None

    def _extract_requirements(self, element) -> str | None:
        """応募要件を抽出"""
        req_el = element.find(class_=re.compile(r"(requirement|qualification|skill|description)", re.I))
        if req_el:
            return req_el.get_text(strip=True)[:1000]
        return None

    def _extract_date(self, element) -> datetime | None:
        """掲載日を抽出"""
        time_tag = element.find("time")
        if time_tag:
            dt_str = time_tag.get("datetime", time_tag.get_text(strip=True))
            return self._parse_date_str(dt_str)

        date_el = element.find(class_=re.compile(r"(date|posted|publish)", re.I))
        if date_el:
            return self._parse_date_str(date_el.get_text(strip=True))
        return None

    def _parse_date_str(self, text: str) -> datetime | None:
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
