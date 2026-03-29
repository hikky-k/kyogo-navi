"""ニュース要約・タグ付けモジュール

収集ニュースを自動要約し重要度タグを付与する。
APIキーがあればClaude API、なければローカル分析エンジンを使用。
"""

import json
import logging
import re

from sqlalchemy.orm import Session

from app.config import settings
from app.analysis.local_analyzer import summarize_news_local
from app.models.company import Company
from app.models.news_article import NewsArticle

logger = logging.getLogger(__name__)


def summarize_article(db: Session, article_id: int) -> NewsArticle | None:
    """1つのニュース記事を要約・タグ付けする"""
    article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
    if not article:
        return None

    # 既に要約済みならスキップ
    if article.summary and article.tags:
        return article

    company = db.query(Company).filter(Company.id == article.company_id).first()
    company_name = company.name if company else "不明"

    if settings.ANTHROPIC_API_KEY:
        from app.analysis.claude_client import claude_client
        from app.analysis.prompts import NEWS_SUMMARY_PROMPT

        prompt = NEWS_SUMMARY_PROMPT.format(
            company_name=company_name, title=article.title,
            source=article.source, content=article.content or article.title,
        )
        logger.info(f"ニュース要約実行（Claude API）: {article.title}")
        response_text = claude_client.analyze(prompt)

        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                result = json.loads(json_match.group())
            else:
                return article
    else:
        logger.info(f"ニュース要約実行（ローカル）: {article.title}")
        result = summarize_news_local(article.title, article.content)

    article.summary = result.get("summary", article.summary)
    article.tags = result.get("tags", article.tags)
    article.impact_score = result.get("impact_score", article.impact_score)

    db.commit()
    db.refresh(article)
    return article


def summarize_unsummarized(db: Session, company_id: int | None = None, limit: int = 50) -> int:
    """未要約の記事をまとめて要約する"""
    query = db.query(NewsArticle).filter(NewsArticle.summary.is_(None))
    if company_id:
        query = query.filter(NewsArticle.company_id == company_id)

    articles = query.order_by(NewsArticle.created_at.desc()).limit(limit).all()
    count = 0

    for article in articles:
        try:
            result = summarize_article(db, article.id)
            if result and result.summary:
                count += 1
        except Exception as e:
            logger.error(f"要約失敗: article_id={article.id} - {e}")

    return count
