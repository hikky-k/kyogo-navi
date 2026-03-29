"""AI分析 日次バッチスケジューラー

新規データがある企業のみ分析を実行する。
cronで毎日実行: 0 8 * * * docker compose exec backend python -m app.analysis.scheduler
（クロールバッチの2時間後を推奨）
"""

import logging
import sys

from app.analysis import analyze_strength_weakness, summarize_unsummarized, score_unscored_articles
from app.database import SessionLocal
from app.models.company import Company

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def run_all_analysis():
    """全企業のAI分析を実行する"""
    db = SessionLocal()
    try:
        companies = db.query(Company).filter(Company.is_active == True).all()  # noqa: E712
        total_sw = 0
        total_summary = 0
        total_scored = 0
        errors = 0

        for company in companies:
            logger.info(f"=== {company.name} の分析開始 ===")
            try:
                # 強み/弱み分析
                result = analyze_strength_weakness(db, company.id)
                if result:
                    total_sw += 1

                # ニュース要約
                summarized = summarize_unsummarized(db, company.id)
                total_summary += summarized

                # 影響度スコアリング
                scored = score_unscored_articles(db, company.id)
                total_scored += scored

                logger.info(f"=== {company.name} 完��: SW={bool(result)}, 要約={summarized}, スコア={scored} ===")
            except Exception as e:
                errors += 1
                logger.error(f"分析失敗 ({company.name}): {e}")

        logger.info(f"全分析完了: 強み弱み={total_sw}, 要約={total_summary}, スコアリング={total_scored}, エラー={errors}")
        return errors == 0

    finally:
        db.close()


def main():
    logger.info("===== AI分析バッチ開始 =====")
    success = run_all_analysis()
    logger.info("===== AI分析バッチ完了 =====")
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
