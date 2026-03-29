"""AI分析API"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.analysis import (
    analyze_strength_weakness,
    summarize_unsummarized,
    score_unscored_articles,
)
from app.database import get_db
from app.models.analysis_result import AnalysisResult
from app.models.company import Company
from app.models.user import User
from app.services.auth import get_current_user, require_admin

logger = logging.getLogger(__name__)
router = APIRouter()


class AnalysisResponse(BaseModel):
    id: int
    company_id: int
    analysis_type: str
    content_json: dict
    analyzed_at: str

    model_config = {"from_attributes": True}


class RunAnalysisResponse(BaseModel):
    strength_weakness: dict | None = None
    news_summarized: int = 0
    articles_scored: int = 0


@router.post("/run/{company_id}", response_model=RunAnalysisResponse)
def run_analysis(
    company_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """企業のAI分析を手動実行（管理者のみ）"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="企業が見つかりません")

    result = RunAnalysisResponse()

    # 強み/弱み分析
    try:
        sw_result = analyze_strength_weakness(db, company_id)
        if sw_result:
            result.strength_weakness = sw_result.content_json
    except Exception as e:
        logger.error(f"強み/弱み分析失敗: {e}")

    # ニュース要約
    try:
        result.news_summarized = summarize_unsummarized(db, company_id)
    except Exception as e:
        logger.error(f"ニュース要約失敗: {e}")

    # 影響度スコアリング
    try:
        result.articles_scored = score_unscored_articles(db, company_id)
    except Exception as e:
        logger.error(f"影響度スコアリング失敗: {e}")

    return result


@router.post("/run-all")
def run_all_analysis(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """全企業のAI分析を実行（管理者のみ）"""
    companies = db.query(Company).filter(Company.is_active == True).all()  # noqa: E712
    results = {}

    for company in companies:
        try:
            sw_result = analyze_strength_weakness(db, company.id)
            summarized = summarize_unsummarized(db, company.id)
            scored = score_unscored_articles(db, company.id)
            results[company.name] = {
                "strength_weakness": bool(sw_result),
                "news_summarized": summarized,
                "articles_scored": scored,
            }
        except Exception as e:
            results[company.name] = {"error": str(e)}
            logger.error(f"分析失敗 ({company.name}): {e}")

    return {"companies": results}


@router.get("/results/{company_id}", response_model=list[AnalysisResponse])
def get_analysis_results(
    company_id: int,
    analysis_type: str | None = Query(None, description="分析タイプでフィルタ"),
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """企業の分析結果を取得"""
    query = db.query(AnalysisResult).filter(AnalysisResult.company_id == company_id)
    if analysis_type:
        query = query.filter(AnalysisResult.analysis_type == analysis_type)

    results = query.order_by(AnalysisResult.analyzed_at.desc()).limit(limit).all()
    return [
        AnalysisResponse(
            id=r.id,
            company_id=r.company_id,
            analysis_type=r.analysis_type,
            content_json=r.content_json,
            analyzed_at=r.analyzed_at.isoformat() if r.analyzed_at else "",
        )
        for r in results
    ]


@router.get("/latest/{company_id}")
def get_latest_analysis(
    company_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """企業の最新分析結果を種類別に取得"""
    types = ["strength_weakness", "positioning", "trend"]
    latest = {}

    for t in types:
        result = db.query(AnalysisResult).filter(
            AnalysisResult.company_id == company_id,
            AnalysisResult.analysis_type == t,
        ).order_by(AnalysisResult.analyzed_at.desc()).first()

        if result:
            latest[t] = {
                "id": result.id,
                "content_json": result.content_json,
                "analyzed_at": result.analyzed_at.isoformat() if result.analyzed_at else None,
            }

    return latest
