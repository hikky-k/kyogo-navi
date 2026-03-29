"""日次バッチスケジューラー

全クローラーを順番に実行し、失敗時はアラートを記録する。
cronで毎日実行: 0 6 * * * docker compose exec backend python -m app.crawlers.scheduler
"""

import logging
import sys
from datetime import datetime, timezone

from app.crawlers.base_crawler import CrawlResult
from app.crawlers.official_crawler import OfficialCrawler
from app.crawlers.news_crawler import NewsCrawler
from app.crawlers.review_crawler import ReviewCrawler
from app.crawlers.job_crawler import JobCrawler
from app.database import SessionLocal
from app.models.alert import Alert

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def create_failure_alert(db, result: CrawlResult) -> None:
    """クロール失敗時にアラートを記録する"""
    alert = Alert(
        company_id=result.source.company_id,
        event_type="crawl_failure",
        severity="中",
        title=f"クロール失敗: {result.source.source_type}",
        message=f"URL: {result.source.url}\nエラー: {result.error}",
        is_read=False,
    )
    db.add(alert)
    db.commit()


def run_all_crawlers() -> dict:
    """全クローラーを実行し結果を返す"""
    db = SessionLocal()
    summary = {
        "start_time": datetime.now(timezone.utc).isoformat(),
        "crawlers": {},
        "total_success": 0,
        "total_failure": 0,
    }

    crawler_classes = [
        ("official", OfficialCrawler),
        ("news", NewsCrawler),
        ("review", ReviewCrawler),
        ("job", JobCrawler),
    ]

    try:
        for name, CrawlerClass in crawler_classes:
            logger.info(f"=== {name} クローラー開始 ===")
            crawler = CrawlerClass(db)
            results = crawler.crawl_all()

            success_count = sum(1 for r in results if r.success)
            failure_count = sum(1 for r in results if not r.success)

            # 失敗したソースのアラートを記録
            for result in results:
                if not result.success:
                    create_failure_alert(db, result)
                    logger.error(f"失敗: {result.source.url} - {result.error}")

            summary["crawlers"][name] = {
                "total": len(results),
                "success": success_count,
                "failure": failure_count,
            }
            summary["total_success"] += success_count
            summary["total_failure"] += failure_count

            logger.info(f"=== {name} クローラー完了: 成功={success_count}, 失敗={failure_count} ===")

    finally:
        summary["end_time"] = datetime.now(timezone.utc).isoformat()
        db.close()

    return summary


def main():
    """バッチ実行のエントリポイント"""
    logger.info("===== 日次クロールバッチ開始 =====")
    summary = run_all_crawlers()

    logger.info("===== 日次クロールバッチ完了 =====")
    logger.info(f"成功: {summary['total_success']}, 失敗: {summary['total_failure']}")

    # 失敗があった場合は終了コード1
    if summary["total_failure"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
