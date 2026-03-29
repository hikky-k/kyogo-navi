"""強み/弱み分析モジュール

公開情報・口コミから各社の強み・弱みを抽出・構造化する。
APIキーがあればClaude API、なければローカル分析エンジンを使用。
"""

import json
import logging
import re
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.analysis.local_analyzer import analyze_strength_weakness_local
from app.models.analysis_result import AnalysisResult
from app.models.company import Company
from app.models.news_article import NewsArticle
from app.models.review_score import ReviewScore
from app.models.job_posting import JobPosting

logger = logging.getLogger(__name__)


def analyze_strength_weakness(db: Session, company_id: int) -> AnalysisResult | None:
    """企業の強み/弱み分析を実行する"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        logger.error(f"企業が見つかりません: company_id={company_id}")
        return None

    # 最新データを収集
    news = db.query(NewsArticle).filter(
        NewsArticle.company_id == company_id
    ).order_by(NewsArticle.created_at.desc()).limit(20).all()

    reviews = db.query(ReviewScore).filter(
        ReviewScore.company_id == company_id
    ).order_by(ReviewScore.scraped_at.desc()).limit(5).all()

    jobs = db.query(JobPosting).filter(
        JobPosting.company_id == company_id,
        JobPosting.is_active == True,  # noqa: E712
    ).order_by(JobPosting.scraped_at.desc()).limit(20).all()

    # Claude API が使える場合
    if settings.ANTHROPIC_API_KEY:
        from app.analysis.claude_client import claude_client
        from app.analysis.prompts import STRENGTH_WEAKNESS_PROMPT

        news_data = "\n".join([
            f"- [{n.source}] {n.title}" + (f"\n  {n.summary}" if n.summary else "")
            for n in news
        ]) or "データなし"

        review_data = "\n".join([
            f"- [{r.source}] 総合スコア: {r.overall_score}, レビュー数: {r.review_count}"
            + (f"\n  カテゴリ: {json.dumps(r.categories_json, ensure_ascii=False)}" if r.categories_json else "")
            for r in reviews
        ]) or "データなし"

        job_data = "\n".join([
            f"- {j.title}" + (f" ({j.department})" if j.department else "")
            + (f" 年収: {j.salary_range}" if j.salary_range else "")
            for j in jobs
        ]) or "データなし"

        prompt = STRENGTH_WEAKNESS_PROMPT.format(
            company_name=company.name, category=company.category,
            news_data=news_data, review_data=review_data, job_data=job_data,
        )

        logger.info(f"強み/弱み分析実行（Claude API）: {company.name}")
        response_text = claude_client.analyze(prompt)

        try:
            content = json.loads(response_text)
        except json.JSONDecodeError:
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                content = json.loads(json_match.group())
            else:
                content = {"error": "分析結果の解析に失敗しました"}
    else:
        # ローカル分析エンジン
        logger.info(f"強み/弱み分析実行（ローカル）: {company.name}")
        news_texts = [f"{n.title} {n.content or ''} {n.summary or ''}" for n in news]
        review_dicts = [{"overall_score": r.overall_score, "source": r.source,
                         "categories_json": r.categories_json} for r in reviews]
        job_dicts = [{"title": j.title, "department": j.department,
                      "salary_range": j.salary_range} for j in jobs]

        content = analyze_strength_weakness_local(
            company.name, company.category, news_texts, review_dicts, job_dicts
        )

    # DB保存
    result = AnalysisResult(
        company_id=company_id,
        analysis_type="strength_weakness",
        content_json=content,
        raw_data_refs={
            "news_ids": [n.id for n in news],
            "review_ids": [r.id for r in reviews],
            "job_ids": [j.id for j in jobs],
        },
        analyzed_at=datetime.now(timezone.utc),
    )
    db.add(result)
    db.commit()
    db.refresh(result)

    logger.info(f"強み/弱み分析完了: {company.name}")
    return result
