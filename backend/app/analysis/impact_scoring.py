"""影響度スコアリング（アラート判定）モジュール

各ニュースの採用市場への影響度を自動判定し、アラートを生成する。
APIキーがあればClaude API、なければローカル分析エンジンを使用。
"""

import json
import logging
import re
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.analysis.local_analyzer import score_impact_local
from app.models.alert import Alert
from app.models.company import Company
from app.models.news_article import NewsArticle

logger = logging.getLogger(__name__)


def score_article_impact(db: Session, article_id: int) -> dict | None:
    """ニュース記事の影響度を判定し、必要ならアラートを生成する"""
    article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
    if not article:
        return None

    if article.impact_score:
        existing_alert = db.query(Alert).filter(Alert.source_article_id == article_id).first()
        if existing_alert:
            return {"impact_score": article.impact_score, "already_processed": True}

    company = db.query(Company).filter(Company.id == article.company_id).first()
    company_name = company.name if company else "不明"

    if settings.ANTHROPIC_API_KEY:
        from app.analysis.claude_client import claude_client
        from app.analysis.prompts import IMPACT_SCORING_PROMPT

        prompt = IMPACT_SCORING_PROMPT.format(
            company_name=company_name, title=article.title,
            summary=article.summary or article.title,
        )
        logger.info(f"影響度スコアリング実行（Claude API）: {article.title}")
        response_text = claude_client.analyze(prompt)

        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                result = json.loads(json_match.group())
            else:
                return None
    else:
        logger.info(f"影響度スコアリング実行（ローカル）: {article.title}")
        result = score_impact_local(article.title, article.summary)

    # 記事の影響度を更新
    impact_score = result.get("impact_score", "低")
    article.impact_score = impact_score
    db.commit()

    # アラート生成判定
    if result.get("should_alert", False):
        alert_type = result.get("alert_type", "new_service")
        alert = Alert(
            company_id=article.company_id,
            event_type=alert_type or "new_service",
            severity=impact_score,
            title=f"[{company_name}] {article.title}",
            message=(result.get("reason", "") + "\n\n" + (result.get("recommended_action") or "")).strip(),
            source_article_id=article.id,
            is_read=False,
            notified_at=datetime.now(timezone.utc),
        )
        db.add(alert)
        db.commit()
        logger.info(f"アラート生成: {alert.title}")

    return result


def score_unscored_articles(db: Session, company_id: int | None = None, limit: int = 50) -> int:
    """未スコアの記事をまとめて影響度判定する"""
    query = db.query(NewsArticle).filter(NewsArticle.impact_score.is_(None))
    if company_id:
        query = query.filter(NewsArticle.company_id == company_id)

    articles = query.order_by(NewsArticle.created_at.desc()).limit(limit).all()
    count = 0

    for article in articles:
        try:
            result = score_article_impact(db, article.id)
            if result:
                count += 1
        except Exception as e:
            logger.error(f"スコアリング失敗: article_id={article.id} - {e}")

    return count
