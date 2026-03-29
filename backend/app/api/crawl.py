"""クロール実行API"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.crawlers import OfficialCrawler, NewsCrawler, ReviewCrawler, JobCrawler
from app.crawlers.scheduler import run_all_crawlers
from app.database import get_db
from app.models.alert import Alert
from app.models.crawl_source import CrawlSource
from app.models.user import User
from app.services.auth import require_admin

logger = logging.getLogger(__name__)
router = APIRouter()

CRAWLER_MAP = {
    "official": OfficialCrawler,
    "news": NewsCrawler,
    "review": ReviewCrawler,
    "job": JobCrawler,
}


class CrawlResponse(BaseModel):
    source_id: int
    source_type: str
    url: str
    success: bool
    items_count: int
    error: str | None = None


class BatchResponse(BaseModel):
    total_success: int
    total_failure: int
    crawlers: dict


@router.post("/run/{source_id}", response_model=CrawlResponse)
def run_single_crawl(
    source_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """個別ソースのクロールを手動実行（管理者のみ）"""
    source = db.query(CrawlSource).filter(CrawlSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="クロールソースが見つかりません")

    CrawlerClass = CRAWLER_MAP.get(source.source_type)
    if not CrawlerClass:
        raise HTTPException(status_code=400, detail=f"不明なソースタイプ: {source.source_type}")

    crawler = CrawlerClass(db)
    result = crawler.crawl(source)

    # last_crawled_at を更新
    source.last_crawled_at = datetime.now(timezone.utc)
    db.commit()

    return CrawlResponse(
        source_id=source.id,
        source_type=source.source_type,
        url=source.url,
        success=result.success,
        items_count=len(result.items),
        error=result.error,
    )


@router.post("/run-all", response_model=BatchResponse)
def run_all(
    background_tasks: BackgroundTasks,
    company_id: int | None = Query(None, description="特定企業のみ実行"),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """全クローラーを手動実行（管理者のみ）"""
    summary = {"total_success": 0, "total_failure": 0, "crawlers": {}}

    for name, CrawlerClass in CRAWLER_MAP.items():
        crawler = CrawlerClass(db)
        results = crawler.crawl_all(company_id=company_id)

        success = sum(1 for r in results if r.success)
        failure = sum(1 for r in results if not r.success)

        # 失敗アラート記録
        for result in results:
            if not result.success:
                alert = Alert(
                    company_id=result.source.company_id,
                    event_type="crawl_failure",
                    severity="中",
                    title=f"クロール失敗: {result.source.source_type}",
                    message=f"URL: {result.source.url}\nエラー: {result.error}",
                )
                db.add(alert)

        summary["crawlers"][name] = {"total": len(results), "success": success, "failure": failure}
        summary["total_success"] += success
        summary["total_failure"] += failure

    db.commit()
    return summary


@router.get("/history", response_model=list[dict])
def get_crawl_history(
    company_id: int | None = Query(None),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """クロール失敗履歴（アラートから取得）"""
    query = db.query(Alert).filter(Alert.event_type == "crawl_failure")
    if company_id:
        query = query.filter(Alert.company_id == company_id)

    alerts = query.order_by(Alert.notified_at.desc()).limit(limit).all()
    return [
        {
            "id": a.id,
            "company_id": a.company_id,
            "title": a.title,
            "message": a.message,
            "severity": a.severity,
            "notified_at": a.notified_at.isoformat() if a.notified_at else None,
        }
        for a in alerts
    ]
