"""プロンプトテンプレート管理

分析用プロンプトをテンプレートとして管理し、データを差し込んで利用する。
"""

STRENGTH_WEAKNESS_PROMPT = """あなたはコンサルティング業界の競合分析の専門家です。
以下の企業に関する情報を分析し、強みと弱みを構造化して抽出してください。

## 対象企業
企業���: {company_name}
カテゴリ: {category}

## 収集データ
### 最新ニュース
{news_data}

### 口コミ情報
{review_data}

### 求人情報
{job_data}

## 出力フォーマット（JSON）
以下のJSON形式で出力してください。JSONのみを出力し、他のテキストは含めないでください。

{{
  "strengths": [
    {{
      "category": "カテゴリ名（例: ブランド力、人材育成、技術力、報酬水準など）",
      "description": "具体的な強みの説明",
      "evidence": "根拠となる情報源"
    }}
  ],
  "weaknesses": [
    {{
      "category": "カテゴリ名",
      "description": "具体的な弱みの説明",
      "evidence": "根拠となる情報源"
    }}
  ],
  "summary": "全体的な分析サマリー（2-3文）"
}}
"""

NEWS_SUMMARY_PROMPT = """あなたはコンサルティング業界のニュースアナリストです。
以下のニュース記事を分析し、要約・タグ付け・影響度判定を行ってください。

## 対象企業
企業名: {company_name}

## ニュース記事
タイトル: {title}
ソース: {source}
本文:
{content}

## 出力フォーマット（JSON）
以下のJSON形式で出力してください。JSONのみを出力し、他のテキストは含めないでください。

{{
  "summary": "記事の要約（100-200文字）",
  "tags": ["タグ1", "タグ2"],
  "impact_score": "高/中/低",
  "impact_reason": "影響度の判定理由",
  "key_points": ["ポイント1", "ポイント2"]
}}

## 影響度の判定基準
- 高: 大規模採用・採用凍結、組織再編、経営陣変更、新サービスライン立ち上げ
- 中: 中規模な組織変更、新プロジェクト、業績に関する報道
- 低: 日常的なニュース、イベント参加、小規模な変更
"""

IMPACT_SCORING_PROMPT = """あなたはコンサルティング業界の採用市場アナリストです。
以下のニュース記事が採用市場に与える影響度を判定してください。

## 対象企業
企業名: {company_name}

## ニュース記事
タイトル: {title}
要約: {summary}

## 出力フォーマット（JSON）
以下のJSON形式で出力してください。JSONのみを出力し、他のテキストは含めないでください。

{{
  "impact_score": "高/中/低",
  "reason": "判定理由の説明",
  "should_alert": true/false,
  "alert_type": "hiring_surge/reorg/new_service/score_change/null",
  "recommended_action": "推奨アクション（候補者への説明ポイントなど）"
}}

## アラート判定基準
should_alert = true の場合:
- 大規模採用開始 or 採用凍結 → alert_type: "hiring_surge"
- 組織再編・経営陣変更 → alert_type: "reorg"
- 新サービスライン・大型案件 → alert_type: "new_service"
"""

TREND_ANALYSIS_PROMPT = """あなたはコンサルティング業界の市場アナリストです。
以下の複数企業のデータから、業界全体のトレンドを分析してください。

## 企業データ
{companies_data}

## 出力フォーマット（JSON）
以下のJSON形式で出力してください。JSONのみを出力し、他のテキストは含めないでください。

{{
  "trends": [
    {{
      "title": "トレンドタイトル",
      "description": "トレンドの詳細説明",
      "affected_companies": ["影響を受ける企業名"],
      "impact_on_hiring": "採用市場への影響"
    }}
  ],
  "market_summary": "市場全体のサマリー",
  "period": "{period}"
}}
"""
