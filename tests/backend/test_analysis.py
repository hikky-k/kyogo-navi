"""AI分析モジュールのテスト"""

from app.analysis.local_analyzer import (
    analyze_strength_weakness_local,
    summarize_news_local,
    score_impact_local,
)


def test_strength_weakness_local_with_category():
    """カテゴリに基づくデフォルト弱みが生成される"""
    result = analyze_strength_weakness_local(
        company_name="テスト社",
        category="総合系",
        news_texts=[],
        review_data=[],
        job_data=[],
    )
    assert "strengths" in result
    assert "weaknesses" in result
    assert len(result["weaknesses"]) > 0  # デフォルト弱みが必ずある
    assert "counter_arguments" in result
    assert len(result["counter_arguments"]) > 0
    assert "interview_tips" in result
    assert "attraction_points" in result
    assert "differentiation_points" in result


def test_strength_weakness_local_with_news():
    """ニュースからキーワード検出"""
    result = analyze_strength_weakness_local(
        company_name="テスト社",
        category="IT系",
        news_texts=["DXを推進する大規模プロジェクトを受注", "グローバル展開を加速"],
        review_data=[],
        job_data=[],
    )
    strength_cats = [s["category"] for s in result["strengths"]]
    assert any("DX" in c or "テクノロジー" in c for c in strength_cats)


def test_strength_weakness_local_with_reviews():
    """口コミスコアの分析"""
    result = analyze_strength_weakness_local(
        company_name="テスト社",
        category="ブティック系",
        news_texts=[],
        review_data=[{"overall_score": 4.5, "source": "openwork", "categories_json": {"待遇満足度": 4.2}}],
        job_data=[],
    )
    strength_cats = [s["category"] for s in result["strengths"]]
    assert "従業員満足度" in strength_cats


def test_strength_weakness_local_low_review_score():
    """低い口コミスコアは弱みに反映"""
    result = analyze_strength_weakness_local(
        company_name="テスト社",
        category="総合系",
        news_texts=[],
        review_data=[{"overall_score": 2.5, "source": "openwork", "categories_json": {}}],
        job_data=[],
    )
    weakness_cats = [w["category"] for w in result["weaknesses"]]
    assert "従業員満足度" in weakness_cats


def test_strength_weakness_all_categories():
    """全カテゴリでデフォルト弱みが出る"""
    for category in ["総合系", "IT系", "ブティック系"]:
        result = analyze_strength_weakness_local(
            company_name="テスト社",
            category=category,
            news_texts=[],
            review_data=[],
            job_data=[],
        )
        assert len(result["weaknesses"]) >= 3, f"{category}でデフォルト弱みが不足"
        assert len(result["counter_arguments"]) >= 3, f"{category}で切り返しが不足"


def test_summarize_news_local():
    """ニュース要約"""
    result = summarize_news_local("アクセンチュアが大規模採用を開始", "コンサ���ティング部門で200名の中途採用を計画")
    assert result["summary"]
    assert result["tags"]
    assert result["impact_score"] in ("高", "中", "低")


def test_summarize_news_local_tags():
    """タグの正確性"""
    result = summarize_news_local("DX推進のための新サービスをローンチ", None)
    assert "DX・テクノロジー" in result["tags"] or "新サービス" in result["tags"]


def test_score_impact_high():
    """高影響度の判定"""
    result = score_impact_local("大規模な組織再編を実施", "経営陣変更を伴う大幅な組織再編")
    assert result["impact_score"] == "高"
    assert result["should_alert"] is True


def test_score_impact_low():
    """低影響度の判定"""
    result = score_impact_local("業界セミナーに参加", "年次イベントに登壇")
    assert result["impact_score"] == "低"
    assert result["should_alert"] is False


def test_score_impact_alert_type():
    """アラートタイプの正確性"""
    result = score_impact_local("大量採用を開始", "積極採用を開始する計画")
    assert result["alert_type"] == "hiring_surge"
