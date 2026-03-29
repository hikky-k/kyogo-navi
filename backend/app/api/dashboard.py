"""ダッシュボードAPI（Redisキャッシュ対応）"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.alert import Alert
from app.models.company import Company
from app.models.job_posting import JobPosting
from app.services.cache import cache_get, cache_set
from app.models.news_article import NewsArticle
from app.models.review_score import ReviewScore
from app.models.user import User
from app.services.auth import get_current_user

router = APIRouter()


@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """ダッシュボード統計情報（60秒キャッシュ）"""
    cached = cache_get("dashboard:stats")
    if cached:
        return cached

    result = {
        "company_count": db.query(Company).filter(Company.is_active == True).count(),  # noqa: E712
        "news_count": db.query(NewsArticle).count(),
        "unread_alerts": db.query(Alert).filter(Alert.is_read == False).count(),  # noqa: E712
        "job_count": db.query(JobPosting).filter(JobPosting.is_active == True).count(),  # noqa: E712
    }
    cache_set("dashboard:stats", result, ttl=60)
    return result


@router.get("/news")
def get_latest_news(
    company_id: int | None = Query(None),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """最新ニュース一覧"""
    query = db.query(NewsArticle)
    if company_id:
        query = query.filter(NewsArticle.company_id == company_id)

    articles = query.order_by(NewsArticle.created_at.desc()).limit(limit).all()
    return [
        {
            "id": a.id,
            "company_id": a.company_id,
            "company_name": db.query(Company.name).filter(Company.id == a.company_id).scalar(),
            "source": a.source,
            "source_url": a.source_url,
            "title": a.title,
            "summary": a.summary,
            "impact_score": a.impact_score,
            "tags": a.tags,
            "published_at": a.published_at.isoformat() if a.published_at else None,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in articles
    ]


@router.get("/alerts")
def get_alerts(
    severity: str | None = Query(None, description="高/中/低"),
    is_read: bool | None = Query(None),
    limit: int = Query(30, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """アラート一覧"""
    query = db.query(Alert)
    if severity:
        query = query.filter(Alert.severity == severity)
    if is_read is not None:
        query = query.filter(Alert.is_read == is_read)

    alerts = query.order_by(Alert.notified_at.desc()).limit(limit).all()
    return [
        {
            "id": a.id,
            "company_id": a.company_id,
            "company_name": db.query(Company.name).filter(Company.id == a.company_id).scalar(),
            "event_type": a.event_type,
            "severity": a.severity,
            "title": a.title,
            "message": a.message,
            "is_read": a.is_read,
            "notified_at": a.notified_at.isoformat() if a.notified_at else None,
        }
        for a in alerts
    ]


@router.patch("/alerts/{alert_id}/read")
def mark_alert_read(
    alert_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """アラートを既読にする"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if alert:
        alert.is_read = True
        db.commit()
    return {"ok": True}


@router.patch("/alerts/read-all")
def mark_all_alerts_read(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """全アラートを既読にする"""
    db.query(Alert).filter(Alert.is_read == False).update({"is_read": True})  # noqa: E712
    db.commit()
    return {"ok": True}


@router.get("/companies/{company_id}/reviews")
def get_company_reviews(
    company_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """企業の口コミスコア履歴"""
    reviews = db.query(ReviewScore).filter(
        ReviewScore.company_id == company_id
    ).order_by(ReviewScore.scraped_at.asc()).all()
    return [
        {
            "id": r.id,
            "source": r.source,
            "overall_score": r.overall_score,
            "categories_json": r.categories_json,
            "review_count": r.review_count,
            "scraped_at": r.scraped_at.isoformat() if r.scraped_at else None,
        }
        for r in reviews
    ]


@router.get("/companies/{company_id}/jobs")
def get_company_jobs(
    company_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """企業の求人情報"""
    jobs = db.query(JobPosting).filter(
        JobPosting.company_id == company_id
    ).order_by(JobPosting.scraped_at.desc()).limit(50).all()
    return [
        {
            "id": j.id,
            "source": j.source,
            "title": j.title,
            "department": j.department,
            "salary_range": j.salary_range,
            "requirements": j.requirements,
            "posted_at": j.posted_at.isoformat() if j.posted_at else None,
            "is_active": j.is_active,
        }
        for j in jobs
    ]


@router.get("/compare")
def get_compare_data(
    company_ids: str = Query(..., description="カンマ区切りの企業ID"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """企業比較データ（差分分析付き）"""
    ids = [int(x.strip()) for x in company_ids.split(",") if x.strip()]
    from app.models.analysis_result import AnalysisResult

    companies_data = []
    for cid in ids:
        company = db.query(Company).filter(Company.id == cid).first()
        if not company:
            continue

        sw = db.query(AnalysisResult).filter(
            AnalysisResult.company_id == cid,
            AnalysisResult.analysis_type == "strength_weakness",
        ).order_by(AnalysisResult.analyzed_at.desc()).first()

        review = db.query(ReviewScore).filter(
            ReviewScore.company_id == cid
        ).order_by(ReviewScore.scraped_at.desc()).first()

        job_count = db.query(JobPosting).filter(
            JobPosting.company_id == cid,
            JobPosting.is_active == True,  # noqa: E712
        ).count()

        # 最新ニュース数
        news_count = db.query(NewsArticle).filter(
            NewsArticle.company_id == cid
        ).count()

        companies_data.append({
            "company": {
                "id": company.id,
                "name": company.name,
                "category": company.category,
                "description": company.description,
            },
            "strength_weakness": sw.content_json if sw else None,
            "review": {
                "overall_score": review.overall_score if review else None,
                "categories_json": review.categories_json if review else None,
                "review_count": review.review_count if review else 0,
            },
            "job_count": job_count,
            "news_count": news_count,
        })

    # === 差分分析を生成 ===
    diff_analysis = _generate_comparison_analysis(companies_data)

    return {
        "companies": companies_data,
        "diff_analysis": diff_analysis,
    }


def _generate_comparison_analysis(companies_data: list[dict]) -> dict:
    """企業間の差分分析を生成する"""
    if len(companies_data) < 2:
        return {}

    # 各社の強み/弱みカテゴリを収集
    company_strengths: dict[str, set[str]] = {}
    company_weaknesses: dict[str, set[str]] = {}

    for d in companies_data:
        name = d["company"]["name"]
        sw = d.get("strength_weakness") or {}
        company_strengths[name] = {s["category"] for s in (sw.get("strengths") or [])}
        company_weaknesses[name] = {w["category"] for w in (sw.get("weaknesses") or [])}

    names = [d["company"]["name"] for d in companies_data]

    # === 比較マトリクス（項目ごとに各社の状況を比較） ===
    all_strength_cats = set()
    all_weakness_cats = set()
    for s_set in company_strengths.values():
        all_strength_cats |= s_set
    for w_set in company_weaknesses.values():
        all_weakness_cats |= w_set

    # 強み比較マトリクス
    strength_matrix = []
    for cat in sorted(all_strength_cats):
        row = {"category": cat, "type": "strength"}
        for name in names:
            row[name] = cat in company_strengths.get(name, set())
        strength_matrix.append(row)

    # 弱み比較マトリクス
    weakness_matrix = []
    for cat in sorted(all_weakness_cats):
        row = {"category": cat, "type": "weakness"}
        for name in names:
            row[name] = cat in company_weaknesses.get(name, set())
        weakness_matrix.append(row)

    # === 各社のユニークな強み・弱み ===
    unique_strengths: dict[str, list[str]] = {}
    unique_weaknesses: dict[str, list[str]] = {}

    for name in names:
        other_strengths = set()
        other_weaknesses = set()
        for other_name in names:
            if other_name != name:
                other_strengths |= company_strengths.get(other_name, set())
                other_weaknesses |= company_weaknesses.get(other_name, set())

        unique_strengths[name] = sorted(company_strengths.get(name, set()) - other_strengths)
        unique_weaknesses[name] = sorted(company_weaknesses.get(name, set()) - other_weaknesses)

    # === 各社ペアごとの差別化ポイント ===
    pairwise = []
    for i, d1 in enumerate(companies_data):
        for j, d2 in enumerate(companies_data):
            if i >= j:
                continue
            n1, n2 = d1["company"]["name"], d2["company"]["name"]

            advantages_1 = []  # d1がd2より優れている点
            advantages_2 = []  # d2がd1より優れている点

            # 強み差分
            only_1_strengths = company_strengths.get(n1, set()) - company_strengths.get(n2, set())
            only_2_strengths = company_strengths.get(n2, set()) - company_strengths.get(n1, set())
            for s in sorted(only_1_strengths):
                advantages_1.append({"area": s, "reason": f"{n1}のみに検出された強み"})
            for s in sorted(only_2_strengths):
                advantages_2.append({"area": s, "reason": f"{n2}のみに検出された強み"})

            # 弱み差分（相手にあって自分にない弱み = 自分の優位）
            only_2_weaknesses = company_weaknesses.get(n2, set()) - company_weaknesses.get(n1, set())
            only_1_weaknesses = company_weaknesses.get(n1, set()) - company_weaknesses.get(n2, set())
            for w in sorted(only_2_weaknesses):
                advantages_1.append({"area": f"{w}（相手の弱み）", "reason": f"{n2}で指摘されているが{n1}では未検出"})
            for w in sorted(only_1_weaknesses):
                advantages_2.append({"area": f"{w}（相手の弱み）", "reason": f"{n1}で指摘されているが{n2}では未検出"})

            # 口コミスコア差分
            s1 = d1["review"].get("overall_score")
            s2 = d2["review"].get("overall_score")
            if s1 and s2:
                if s1 > s2:
                    advantages_1.append({"area": "口コミスコア", "reason": f"{s1:.1f} vs {s2:.1f}（{s1 - s2:.1f}pt差）"})
                elif s2 > s1:
                    advantages_2.append({"area": "口コミスコア", "reason": f"{s2:.1f} vs {s1:.1f}（{s2 - s1:.1f}pt差）"})

            # 求人数差分
            j1, j2 = d1["job_count"], d2["job_count"]
            if j1 > j2 and j1 > 0:
                advantages_1.append({"area": "採用規模", "reason": f"求人{j1}件 vs {j2}件（積極採用中）"})
            elif j2 > j1 and j2 > 0:
                advantages_2.append({"area": "採用規模", "reason": f"求人{j2}件 vs {j1}件（積極採用中）"})

            # カテゴリ差分
            cat1, cat2 = d1["company"]["category"], d2["company"]["category"]
            if cat1 != cat2:
                advantages_1.append({"area": "ポジショニング", "reason": f"{cat1}としての特性（vs {cat2}）"})
                advantages_2.append({"area": "ポジショニング", "reason": f"{cat2}としての特性（vs {cat1}）"})

            pairwise.append({
                "company_1": n1,
                "company_2": n2,
                "advantages_1": advantages_1,
                "advantages_2": advantages_2,
            })

    # === 面接での使い方ガイド ===
    interview_guide = []
    for d in companies_data:
        name = d["company"]["name"]
        guide_points = []

        u_strengths = unique_strengths.get(name, [])
        if u_strengths:
            guide_points.append(f"他社にない強み: {', '.join(u_strengths[:3])}。この点を重点的にアピール。")

        u_weaknesses = unique_weaknesses.get(name, [])
        if u_weaknesses:
            guide_points.append(f"他社と比べた弱み: {', '.join(u_weaknesses[:3])}。切り返しを準備しておく。")

        if not u_strengths and not u_weaknesses:
            guide_points.append("他社と類似した特性。カルチャーや具体的なプロジェクト事例で差別化する。")

        interview_guide.append({"company": name, "points": guide_points})

    return {
        "strength_matrix": strength_matrix,
        "weakness_matrix": weakness_matrix,
        "unique_strengths": unique_strengths,
        "unique_weaknesses": unique_weaknesses,
        "pairwise": pairwise,
        "interview_guide": interview_guide,
    }
