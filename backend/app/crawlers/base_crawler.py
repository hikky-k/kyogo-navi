"""ベースクローラー - 全クローラーの共通インターフェース"""

import logging
import time
from abc import ABC, abstractmethod
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx
from sqlalchemy.orm import Session

from app.models.crawl_source import CrawlSource

logger = logging.getLogger(__name__)

# リクエスト間隔（秒）- robots.txtを尊重
MIN_REQUEST_INTERVAL = 2.0
# 最大リトライ回数
MAX_RETRIES = 3
# リトライ間隔（秒）
RETRY_DELAY = 5.0
# リクエストタイムアウト（秒）
REQUEST_TIMEOUT = 30.0

USER_AGENT = "KyogoNavi/1.0 (+https://kyogo-navi.com/bot)"


class CrawlResult:
    """クロール結果"""

    def __init__(self, source: CrawlSource, success: bool, items: list[dict] | None = None, error: str | None = None):
        self.source = source
        self.success = success
        self.items = items or []
        self.error = error


class BaseCrawler(ABC):
    """全クローラーの基底クラス"""

    def __init__(self, db: Session):
        self.db = db
        self._last_request_time = 0.0
        self._robots_cache: dict[str, RobotFileParser] = {}

    @property
    @abstractmethod
    def source_type(self) -> str:
        """対応するソースタイプ（official / news / review / job）"""
        ...

    @abstractmethod
    def parse(self, url: str, html: str, source: CrawlSource) -> list[dict]:
        """HTMLをパースしてデータを抽出する。サブクラスで実装。

        Returns:
            抽出したデータのリスト（各dictはDBモデルに対応するフィールドを持つ）
        """
        ...

    @abstractmethod
    def save_items(self, items: list[dict], source: CrawlSource) -> int:
        """抽出したデータをDBに保存する。サブクラスで実装。

        Returns:
            新規保存した件数
        """
        ...

    def crawl(self, source: CrawlSource) -> CrawlResult:
        """1つのソースをクロールする（リトライ付き）"""
        url = source.url
        logger.info(f"クロール開始: {url} (source_id={source.id})")

        # robots.txtチェック
        if not self._is_allowed(url):
            msg = f"robots.txtにより拒否: {url}"
            logger.warning(msg)
            return CrawlResult(source=source, success=False, error=msg)

        # リトライ付きでHTMLを取得
        html = None
        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                html = self._fetch(url)
                break
            except Exception as e:
                last_error = str(e)
                logger.warning(f"クロール失敗 (試行{attempt}/{MAX_RETRIES}): {url} - {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)

        if html is None:
            msg = f"クロール失敗（{MAX_RETRIES}回リトライ後）: {url} - {last_error}"
            logger.error(msg)
            return CrawlResult(source=source, success=False, error=msg)

        # パースとデータ抽出
        try:
            items = self.parse(url, html, source)
        except Exception as e:
            msg = f"パース失敗: {url} - {e}"
            logger.error(msg)
            return CrawlResult(source=source, success=False, error=msg)

        # DB保存
        try:
            saved_count = self.save_items(items, source)
            logger.info(f"クロール完了: {url} - {saved_count}件保存")
        except Exception as e:
            msg = f"DB保存失敗: {url} - {e}"
            logger.error(msg)
            return CrawlResult(source=source, success=False, items=items, error=msg)

        return CrawlResult(source=source, success=True, items=items)

    def crawl_all(self, company_id: int | None = None) -> list[CrawlResult]:
        """対応する全ソースをクロールする"""
        query = self.db.query(CrawlSource).filter(
            CrawlSource.source_type == self.source_type,
            CrawlSource.is_active == True,  # noqa: E712
        )
        if company_id:
            query = query.filter(CrawlSource.company_id == company_id)

        sources = query.all()
        results = []
        for source in sources:
            result = self.crawl(source)
            # last_crawled_at を更新
            from datetime import datetime, timezone
            source.last_crawled_at = datetime.now(timezone.utc)
            self.db.commit()
            results.append(result)

        return results

    def _fetch(self, url: str) -> str:
        """URLからHTMLを取得する（リクエスト間隔を制御）"""
        # リクエスト間隔を守る
        elapsed = time.time() - self._last_request_time
        if elapsed < MIN_REQUEST_INTERVAL:
            time.sleep(MIN_REQUEST_INTERVAL - elapsed)

        with httpx.Client(timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
            response = client.get(url, headers={"User-Agent": USER_AGENT})
            response.raise_for_status()

        self._last_request_time = time.time()
        return response.text

    def _is_allowed(self, url: str) -> bool:
        """robots.txtを確認してクロール可否を判定する"""
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        if base_url not in self._robots_cache:
            rp = RobotFileParser()
            rp.set_url(f"{base_url}/robots.txt")
            try:
                rp.read()
            except Exception:
                # robots.txtが取得できない場合は許可とみなす
                return True
            self._robots_cache[base_url] = rp

        return self._robots_cache[base_url].can_fetch(USER_AGENT, url)
