"""口コミサイト クローラー

OpenWork, Glassdoor からの情報を収集する。
- 総合評価スコア推移
- 待遇・成長機会・ワークライフバランス
- ポジティブ/ネガティブなレビュー傾向
"""

import logging
import re

from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.crawlers.base_crawler import BaseCrawler
from app.models.crawl_source import CrawlSource
from app.models.review_score import ReviewScore

logger = logging.getLogger(__name__)

# 口コミサイトのカテゴリマッピング
REVIEW_CATEGORIES = [
    "待遇満足度",
    "社員の士気",
    "風通しの良さ",
    "社員の相互尊重",
    "20代成長環境",
    "人材の長期育成",
    "法令遵守意識",
    "人事評価の適正感",
    "ワークライフバランス",
]


class ReviewCrawler(BaseCrawler):
    """口コミサイトクローラー"""

    def __init__(self, db: Session):
        super().__init__(db)

    @property
    def source_type(self) -> str:
        return "review"

    def parse(self, url: str, html: str, source: CrawlSource) -> list[dict]:
        """口コミサイトのHTMLをパースしてスコア情報を抽出する"""
        soup = BeautifulSoup(html, "html.parser")

        # ソースを判別
        if "openwork" in url.lower() or "vorkers" in url.lower():
            return self._parse_openwork(soup, source)
        elif "glassdoor" in url.lower():
            return self._parse_glassdoor(soup, source)
        else:
            return self._parse_generic(soup, source)

    def save_items(self, items: list[dict], source: CrawlSource) -> int:
        """口コミスコアをDBに保存"""
        saved = 0
        for item in items:
            score = ReviewScore(**item)
            self.db.add(score)
            saved += 1

        if saved > 0:
            self.db.commit()
        return saved

    def _parse_openwork(self, soup: BeautifulSoup, source: CrawlSource) -> list[dict]:
        """OpenWorkのスコアをパース"""
        result = {
            "company_id": source.company_id,
            "source": "openwork",
            "overall_score": 0.0,
            "categories_json": {},
            "review_count": 0,
        }

        # 総合スコア
        score_el = soup.find(class_=re.compile(r"(total.*score|rating.*num|score.*total)", re.I))
        if score_el:
            score_text = score_el.get_text(strip=True)
            score = self._extract_score(score_text)
            if score:
                result["overall_score"] = score

        # カテゴリ別スコア
        categories = {}
        score_items = soup.find_all(class_=re.compile(r"(score.*item|rating.*item|category)", re.I))
        for item in score_items:
            label = item.find(class_=re.compile(r"(label|name|title)", re.I))
            value = item.find(class_=re.compile(r"(score|value|num)", re.I))
            if label and value:
                label_text = label.get_text(strip=True)
                score = self._extract_score(value.get_text(strip=True))
                if score:
                    categories[label_text] = score

        result["categories_json"] = categories

        # レビュー件数
        count_el = soup.find(string=re.compile(r"(\d+)\s*件"))
        if count_el:
            match = re.search(r"(\d+)\s*件", count_el)
            if match:
                result["review_count"] = int(match.group(1))

        if result["overall_score"] > 0:
            return [result]

        logger.warning(f"OpenWorkスコアの抽出に失敗: company_id={source.company_id}")
        return []

    def _parse_glassdoor(self, soup: BeautifulSoup, source: CrawlSource) -> list[dict]:
        """Glassdoorのスコアをパース"""
        result = {
            "company_id": source.company_id,
            "source": "glassdoor",
            "overall_score": 0.0,
            "categories_json": {},
            "review_count": 0,
        }

        # 総合評価
        rating_el = soup.find(attrs={"data-test": re.compile(r"rating", re.I)})
        if not rating_el:
            rating_el = soup.find(class_=re.compile(r"(overall.*rating|ratingNum)", re.I))
        if rating_el:
            score = self._extract_score(rating_el.get_text(strip=True))
            if score:
                result["overall_score"] = score

        # カテゴリ別
        categories = {}
        cat_items = soup.find_all(class_=re.compile(r"(category.*rating|subcategory)", re.I))
        for item in cat_items:
            label = item.find(class_=re.compile(r"(name|label)", re.I))
            value = item.find(class_=re.compile(r"(rating|score)", re.I))
            if label and value:
                categories[label.get_text(strip=True)] = self._extract_score(value.get_text(strip=True)) or 0

        result["categories_json"] = categories

        # レビュー件数
        count_el = soup.find(attrs={"data-test": "reviewCount"})
        if count_el:
            count_match = re.search(r"([\d,]+)", count_el.get_text())
            if count_match:
                result["review_count"] = int(count_match.group(1).replace(",", ""))

        if result["overall_score"] > 0:
            return [result]

        logger.warning(f"Glassdoorスコアの抽出に失敗: company_id={source.company_id}")
        return []

    def _parse_generic(self, soup: BeautifulSoup, source: CrawlSource) -> list[dict]:
        """汎用パース（スコアらしきものを探す）"""
        result = {
            "company_id": source.company_id,
            "source": "other",
            "overall_score": 0.0,
            "categories_json": {},
            "review_count": 0,
        }

        # 数字でスコアらしきもの（1.0〜5.0）を探す
        score_elements = soup.find_all(class_=re.compile(r"(score|rating|star)", re.I))
        for el in score_elements:
            score = self._extract_score(el.get_text(strip=True))
            if score and 1.0 <= score <= 5.0:
                result["overall_score"] = score
                return [result]

        return []

    def _extract_score(self, text: str) -> float | None:
        """テキストからスコア（数値）を抽出"""
        match = re.search(r"(\d+\.?\d*)", text)
        if match:
            value = float(match.group(1))
            if 0 <= value <= 5.0:
                return value
        return None
