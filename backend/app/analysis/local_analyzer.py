"""ローカル分析エンジン（API不要・無料）

収集データをルールベースで分析し、採用担当者が面接で使える
具体的な魅力づけポイント・差別化トークまで生成する。
"""

import re
from collections import Counter
from datetime import datetime, timezone


# === 強み/弱み分析用キーワード辞書 ===

STRENGTH_PATTERNS = {
    "成長機会・キャリアパス": {
        "keywords": ["研修", "育成", "教育", "トレーニング", "成長", "キャリア", "スキル", "昇進", "キャリアパス", "MBA"],
        "talk_point": "入社後の具体的な成長ステップを伝える。研修プログラムや海外研修、資格取得支援の実績を具体的に。",
    },
    "プロジェクト・案件の質": {
        "keywords": ["大型", "大規模", "受注", "プロジェクト", "案件", "戦略", "経営", "トップマネジメント", "CEO"],
        "talk_point": "経営層と直接やりとりできる案件や、社会的インパクトの大きいプロジェクト事例を具体的に共有する。",
    },
    "報酬・待遇": {
        "keywords": ["高年収", "好待遇", "報酬", "給与", "年収", "ボーナス", "インセンティブ", "ストックオプション"],
        "talk_point": "年収レンジだけでなく、昇給ペースや評価に応じた報酬の伸び方を具体的に示す。",
    },
    "DX・テクノロジー投資": {
        "keywords": ["DX", "デジタル", "AI", "テクノロジー", "イノベーション", "先端", "技術", "クラウド", "データ"],
        "talk_point": "テクノロジー領域の投資額・人員拡大計画・具体的な導入事例を伝え、先進的な環境であることをアピール。",
    },
    "グローバル展開": {
        "keywords": ["海外", "グローバル", "国際", "拠点", "多国籍", "クロスボーダー", "アジア", "欧米"],
        "talk_point": "海外プロジェクトのアサイン率、駐在・出張の機会、グローバルチームとの協業体制を具体的に。",
    },
    "業界・領域の専門性": {
        "keywords": ["専門", "特化", "業界知見", "ノウハウ", "知見", "リーディング", "第一人者", "実績"],
        "talk_point": "特定業界での圧倒的な実績数や、他社にはない独自のフレームワーク・方法論を紹介する。",
    },
    "カルチャー・働きがい": {
        "keywords": ["カルチャー", "風土", "チーム", "協力", "フラット", "裁量", "挑戦", "自由", "ベンチャー"],
        "talk_point": "実際の社員の声やチームの雰囲気、意思決定スピード、若手への裁量の大きさを具体エピソードで。",
    },
    "ワークライフバランス": {
        "keywords": ["ワークライフバランス", "リモート", "フレックス", "柔軟", "働き方改革", "有給", "育休", "副業"],
        "talk_point": "平均残業時間、リモートワーク率、有給取得率などの数字を出す。制度だけでなく実態を伝える。",
    },
    "ブランド・市場地位": {
        "keywords": ["大手", "トップ", "リーディング", "実績", "信頼", "ブランド", "知名度", "No.1", "首位"],
        "talk_point": "ランキングや受賞歴、クライアントの顔ぶれ（Fortune 500企業の何割がクライアントか等）を示す。",
    },
    "新規事業・成長投資": {
        "keywords": ["新サービス", "新規事業", "ローンチ", "拡大", "投資", "ファンド", "スタートアップ", "M&A"],
        "talk_point": "新規事業への投資姿勢、社内起業制度、成長領域への積極的なリソース配分を伝える。",
    },
}

WEAKNESS_PATTERNS = {
    "長時間労働": {
        "keywords": ["激務", "残業", "長時間", "ハードワーク", "過重労働", "深夜", "休日出勤"],
        "counter_talk": "プロジェクト間の休暇制度や、働き方改革の具体的な取り組み・改善数値を準備しておく。",
    },
    "離職率・定着率": {
        "keywords": ["離職", "退職", "人材流出", "定着率", "転職"],
        "counter_talk": "平均在籍年数やアルムナイネットワークの強さ、卒業後のキャリアの広がりをポジティブに伝える。",
    },
    "評価・昇進の不透明さ": {
        "keywords": ["評価", "不公平", "不透明", "昇進", "年功序列", "政治的"],
        "counter_talk": "評価制度の具体的な仕組み（360度評価等）や、若手の昇進事例を準備する。",
    },
    "組織の硬直性": {
        "keywords": ["縦割り", "官僚的", "硬直", "風通し", "トップダウン", "保守的"],
        "counter_talk": "組織改革の取り組みや、新しいイニシアチブ、若手発信のプロジェクト事例を紹介する。",
    },
    "クライアント依存": {
        "keywords": ["下請け", "常駐", "派遣", "ベンダー", "受託"],
        "counter_talk": "自社発のソリューションや、クライアントとの対等な関係構築の事例を伝える。",
    },
}

# 影響度判定キーワード
IMPACT_KEYWORDS = {
    "高": ["大規模採用", "組織再編", "経営陣変更", "買収", "合併", "撤退", "大幅", "CEO", "社長",
           "リストラ", "事業売却", "戦略的提携", "上場", "採用凍結", "統合"],
    "中": ["新サービス", "新規事業", "提携", "受注", "決算", "業績", "拡大", "強化",
           "オフィス移転", "部門新設", "中途採用", "パートナー"],
    "低": ["イベント", "セミナー", "表彰", "受賞", "参加", "発表", "レポート"],
}

ALERT_PATTERNS = {
    "hiring_surge": ["大量採用", "採用強化", "積極採用", "採用拡大", "求人増", "採用凍結", "採用停止", "人員削減"],
    "reorg": ["組織再編", "経営陣", "社長交代", "CEO", "合併", "統合", "分社", "事業部新設"],
    "new_service": ["新サービス", "新規事業", "ローンチ", "サービス開始", "新設", "参入"],
}


def analyze_strength_weakness_local(company_name: str, category: str,
                                     news_texts: list[str], review_data: list[dict],
                                     job_data: list[dict]) -> dict:
    """ルールベースで強み/弱みを分析し、面接での魅力づけポイントまで生成する"""
    all_text = " ".join(news_texts)

    # 求人テキストも分析対象に
    job_texts = " ".join([
        f"{j.get('title', '')} {j.get('department', '')} {j.get('salary_range', '')} {j.get('requirements', '')}"
        for j in job_data
    ])
    all_text += " " + job_texts

    strengths = []
    weaknesses = []
    attraction_points = []  # 面接で使える魅力づけポイント
    differentiation_points = []  # 他社との差別化ポイント
    counter_arguments = []  # 弱みに対する切り返しトーク

    # === 強み検出 ===
    for cat, config in STRENGTH_PATTERNS.items():
        matches = [kw for kw in config["keywords"] if kw in all_text]
        if matches:
            strengths.append({
                "category": cat,
                "description": f"関連情報を{len(matches)}件検出（{', '.join(matches[:4])}）",
                "evidence": "収集ニュース・求人情報の分析",
            })
            attraction_points.append({
                "theme": cat,
                "what_to_say": config["talk_point"],
                "keywords_found": matches[:4],
            })

    # === 弱み検出 ===
    for cat, config in WEAKNESS_PATTERNS.items():
        matches = [kw for kw in config["keywords"] if kw in all_text]
        if matches:
            weaknesses.append({
                "category": cat,
                "description": f"関連情報を{len(matches)}件検出（{', '.join(matches[:3])}）",
                "evidence": "収集ニュース・口コミ情報の分析",
            })
            counter_arguments.append({
                "weakness": cat,
                "how_to_address": config["counter_talk"],
            })

    # === 口コミスコアからの分析 ===
    for review in review_data:
        score = review.get("overall_score", 0)
        source = review.get("source", "口コミサイト")
        cats = review.get("categories_json") or {}

        if score >= 4.0:
            strengths.append({
                "category": "従業員満足度",
                "description": f"{source}で高評価（{score}/5.0）",
                "evidence": f"{source}スコア",
            })
            attraction_points.append({
                "theme": "従業員満足度",
                "what_to_say": f"口コミサイトで{score}点の高評価。候補者に「実際に働いている社員の評価が高い」と伝えると効果的。",
                "keywords_found": [],
            })
        elif 0 < score < 3.0:
            weaknesses.append({
                "category": "従業員満足度",
                "description": f"{source}で低評価（{score}/5.0）",
                "evidence": f"{source}スコア",
            })
            counter_arguments.append({
                "weakness": "口コミスコア",
                "how_to_address": "直近の改善施策（制度変更、組織改革等）を具体的に伝え、「今は変わっている」ことを示す。",
            })

        # カテゴリ別の詳細分析
        for cat_name, cat_score in cats.items():
            if isinstance(cat_score, (int, float)):
                if cat_score >= 4.0:
                    attraction_points.append({
                        "theme": f"{cat_name}（高評価）",
                        "what_to_say": f"{cat_name}が{cat_score}点と高評価。この点を面接で積極的にアピールする。",
                        "keywords_found": [],
                    })

    # === 求人情報からの分析 ===
    if len(job_data) >= 10:
        strengths.append({
            "category": "積極的な事業拡大",
            "description": f"現在{len(job_data)}件の求人を公開中。積極的に人材を求めている。",
            "evidence": "求人サイト情報",
        })
        attraction_points.append({
            "theme": "成長機会の豊富さ",
            "what_to_say": f"現在{len(job_data)}件のポジションがオープン。事業拡大中で活躍の場が広いことを伝える。",
            "keywords_found": [],
        })

    # 年収情報の分析
    salary_mentions = [j.get("salary_range", "") for j in job_data if j.get("salary_range")]
    if salary_mentions:
        attraction_points.append({
            "theme": "報酬水準",
            "what_to_say": f"公開求人の年収レンジ: {', '.join(salary_mentions[:3])}。競合と比較した優位性を伝える。",
            "keywords_found": salary_mentions[:3],
        })

    # 募集職種の多様性
    departments = [j.get("department") for j in job_data if j.get("department")]
    if departments:
        unique_depts = list(set(departments))
        if len(unique_depts) >= 3:
            differentiation_points.append({
                "point": "多様なキャリアパス",
                "detail": f"{len(unique_depts)}の部門で募集中（{', '.join(unique_depts[:4])}等）。社内異動によるキャリアの幅広さをアピール。",
            })

    # === カテゴリ別のデフォルト魅力づけ ===
    if category == "総合系":
        differentiation_points.append({
            "point": "総合力による案件の幅広さ",
            "detail": "戦略からIT実装まで一気通貫で関われる。専門ファームと違い、キャリアの選択肢が豊富。",
        })
    elif category == "IT系":
        differentiation_points.append({
            "point": "テクノロジーの最前線",
            "detail": "最新技術に触れながらビジネス課題を解決できる。純粋なIT企業と違い、ビジネス視点も身につく。",
        })
    elif category == "ブティック系":
        differentiation_points.append({
            "point": "少数精鋭の専門性",
            "detail": "大手にはない経営層との距離の近さ、早期からの責任ある役割。成長スピードの速さをアピール。",
        })

    # === カテゴリ別のデフォルト弱み（業界構造に基づく一般的なリスク） ===
    # 口コミサイト等でよく指摘される、カテゴリ固有の典型的な弱みを必ず提示する
    category_weaknesses = {
        "総合系": [
            {
                "item": {"category": "長時間労働・プロジェクト負荷", "description": "大規模プロジェクトが多く、繁忙期のワークロードが高い傾向。口コミサイトでも頻出する指摘事項。", "evidence": "業界構造・口コミ傾向の分析"},
                "counter": {"weakness": "長時間労働・プロジェクト負荷", "how_to_address": "プロジェクト間の長期休暇制度、フレックス勤務の実態、直近の残業時間削減の数値を具体的に提示する。"},
            },
            {
                "item": {"category": "組織の大きさゆえの硬直性", "description": "意思決定のスピード感に欠ける場合がある。縦割り組織や官僚的な風土を指摘する口コミが散見される。", "evidence": "業界構造・口コミ傾向の分析"},
                "counter": {"weakness": "組織の硬直性", "how_to_address": "社内ベンチャー制度や若手の登用事例、フラットな議論の場（ハッカソン等）を紹介して払拭する。"},
            },
            {
                "item": {"category": "個人の裁量・成長実感", "description": "大組織の一員としてアサインされるため、自分の貢献が見えにくいと感じるケースがある。", "evidence": "業界構造・口コミ傾向の分析"},
                "counter": {"weakness": "個人の裁量", "how_to_address": "早期からリードを任されるプロジェクト例や、メンター制度、1on1の頻度を具体的に伝える。"},
            },
            {
                "item": {"category": "配属・アサインのミスマッチリスク", "description": "希望と異なる業界・領域にアサインされる可能性がある。特に入社直後はコントロールしにくい。", "evidence": "業界構造・口コミ傾向の分析"},
                "counter": {"weakness": "配属リスク", "how_to_address": "アサインの希望通過率、社内公募制度、異動リクエストの仕組みを説明する。"},
            },
        ],
        "IT系": [
            {
                "item": {"category": "実装寄り業務の比率", "description": "戦略系ファームと比べてシステム実装・運用保守のフェーズが長く、「上流だけやりたい」人にはギャップがある。", "evidence": "業界構造・口コミ傾向の分析"},
                "counter": {"weakness": "実装寄り業務の比率", "how_to_address": "実装フェーズでこそ得られるスキル（技術理解、PM力）の価値と、上流にシフトするキャリアパスを示す。"},
            },
            {
                "item": {"category": "クライアント常駐の働き方", "description": "プロジェクトによってはクライアント先への常駐が発生し、自社との帰属意識が薄れるとの口コミがある。", "evidence": "業界構造・口コミ傾向の分析"},
                "counter": {"weakness": "クライアント常駐", "how_to_address": "リモートワーク比率の改善状況、自社コミュニティ活動、社内勉強会の開催頻度を伝える。"},
            },
            {
                "item": {"category": "技術トレンドへの追従プレッシャー", "description": "技術変化が速く、常にキャッチアップが求められる。自己学習への投資が必須。", "evidence": "業界構造・口コミ傾向の分析"},
                "counter": {"weakness": "技術キャッチアップ", "how_to_address": "学習支援制度（資格取得補助、書籍購入、外部研修）の充実度を具体金額で示す。"},
            },
            {
                "item": {"category": "ワークライフバランス", "description": "デリバリー直前やリリース前は負荷が集中しやすい。口コミでも繁閑差が指摘される。", "evidence": "業界構造・口コミ傾向の分析"},
                "counter": {"weakness": "ワークライフバランス", "how_to_address": "プロジェクト終了後の連続休暇取得率、年間平均残業時間の推移を数字で伝える。"},
            },
        ],
        "ブティック系": [
            {
                "item": {"category": "ブランド認知度の低さ", "description": "大手と比べて知名度が低く、候補者の家族やエージェントに説明しにくい。転職市場での評価が見えにくい。", "evidence": "業界構造・口コミ傾向の分析"},
                "counter": {"weakness": "ブランド認知度", "how_to_address": "OB/OGの転職先実績や、特定業界での知名度の高さ、クライアントの具体名（公開可能なもの）を共有する。"},
            },
            {
                "item": {"category": "研修・育成体制の薄さ", "description": "少人数のため体系化された研修が少なく、OJT主体になりやすい。手厚い研修を求める人にはギャップ。", "evidence": "業界構造・口コミ傾向の分析"},
                "counter": {"weakness": "研修体制", "how_to_address": "OJTの質の高さ（パートナー直下で学べる等）、外部研修の活用実績、1人あたりの育成投資額を伝える。"},
            },
            {
                "item": {"category": "事業・収益の安定性", "description": "特定領域に依存するため、市場変動の影響を受けやすい。大手と比べて事業基盤が薄い。", "evidence": "業界構造・口コミ傾向の分析"},
                "counter": {"weakness": "事業安定性", "how_to_address": "直近の売上成長率、リピート率の高さ、複数業界への展開計画を示して成長性をアピール。"},
            },
            {
                "item": {"category": "キャリアパスの限定性", "description": "ポジションが限られるため、マネジメントへの昇進枠が少ない。長期的なキャリアパスが見えにくい。", "evidence": "業界構造・口コミ傾向の分析"},
                "counter": {"weakness": "キャリアパスの限定性", "how_to_address": "専門性の深化ルート、独立支援制度、アルムナイの多様なキャリア事例を紹介する。"},
            },
        ],
    }

    # カテゴリ別デフォルト弱みを追加（既にキーワード検出で入っていないもののみ）
    existing_weakness_cats = {w["category"] for w in weaknesses}
    for default_weakness in category_weaknesses.get(category, []):
        if default_weakness["item"]["category"] not in existing_weakness_cats:
            weaknesses.append(default_weakness["item"])
            counter_arguments.append(default_weakness["counter"])

    # === コンサルティング業界共通の弱み（全カテゴリ共通） ===
    common_weaknesses = [
        {
            "item": {"category": "Up or Out文化", "description": "一定期間で昇進できない場合に退職を促される文化がある。口コミサイトで頻繁に言及される。", "evidence": "業界共通の構造的特性"},
            "counter": {"weakness": "Up or Out文化", "how_to_address": "キャリアの多様化（専門職トラック等）の導入状況や、実態として厳格に運用しているかを正直に伝える。"},
        },
        {
            "item": {"category": "顧客業界の景気依存", "description": "クライアント企業の業績やIT投資動向に案件数が左右される。景気後退期にはプロジェクトが減少するリスク。", "evidence": "業界共通の構造的特性"},
            "counter": {"weakness": "景気依存リスク", "how_to_address": "不況期にも需要がある領域（コスト削減、PMI等）の強さや、業界分散戦略を説明する。"},
        },
    ]

    for common in common_weaknesses:
        if common["item"]["category"] not in existing_weakness_cats and len(weaknesses) < 6:
            weaknesses.append(common["item"])
            counter_arguments.append(common["counter"])

    # === サマリー生成 ===
    summary = f"{company_name}の分析結果: "
    if strengths:
        top_strengths = [s["category"] for s in strengths[:3]]
        summary += f"主な強みは{', '.join(top_strengths)}。"
    if weaknesses:
        top_weaknesses = [w["category"] for w in weaknesses[:2]]
        summary += f"留意点として{', '.join(top_weaknesses)}。"
    if attraction_points:
        summary += f"面接での魅力づけポイントを{len(attraction_points)}件生成しました。"

    return {
        "strengths": strengths[:6],
        "weaknesses": weaknesses[:6],
        "summary": summary,
        "attraction_points": attraction_points[:8],
        "differentiation_points": differentiation_points[:5],
        "counter_arguments": counter_arguments[:6],
        "interview_tips": _generate_interview_tips(strengths, weaknesses, category),
    }


def _generate_interview_tips(strengths: list, weaknesses: list, category: str) -> list[str]:
    """面接で使える具体的なTipsを生成"""
    tips = []

    if any(s["category"] == "成長機会・キャリアパス" for s in strengths):
        tips.append("「入社3年後にどんなスキルが身につくか」を具体的な先輩事例で説明する")

    if any(s["category"] == "プロジェクト・案件の質" for s in strengths):
        tips.append("NDA範囲内で、直近の注目プロジェクト（業界・規模感）を共有する")

    if any(s["category"] == "DX・テクノロジー投資" for s in strengths):
        tips.append("テクノロジー投資の具体的な数字や、社内ツール・環境の先進性を伝える")

    if any(w["category"] == "長時間労働" for w in weaknesses):
        tips.append("働き方改革の具体的な取り組みと数値改善を先回りして説明する")

    if any(w["category"] == "離職率・定着率" for w in weaknesses):
        tips.append("アルムナイの活躍事例を紹介し、「卒業後も価値あるキャリア」をポジティブに伝える")

    # カテゴリ別Tips
    if category == "総合系":
        tips.append("「大手ならではの安定感」と「挑戦できる環境」の両立を具体エピソードで示す")
    elif category == "IT系":
        tips.append("「ビジネス×テクノロジー」の両方が身につく唯一の環境であることを強調する")
    elif category == "ブティック系":
        tips.append("「少人数だからこそ得られる経験の密度」を大手との比較で具体的に説明する")

    # デフォルトTips
    tips.append("候補者の口コミサイトの閲覧状況を確認し、懸念点があれば先回りして切り返しを準備する")
    tips.append("候補者が他に受けている企業を確認し、その企業との差別化ポイントを重点的に説明する")
    tips.append("候補者のキャリア志向（専門性 vs 幅広さ、安定 vs 挑戦）に合わせてトークを調整する")

    return tips[:8]


def summarize_news_local(title: str, content: str | None) -> dict:
    """ルールベースでニュースを要約・タグ付けする"""
    text = f"{title} {content or ''}"

    # タグ抽出
    tag_keywords = {
        "採用動向": ["採用", "求人", "人材", "リクルート", "エントリー"],
        "組織変更": ["組織", "再編", "統合", "分社", "新設", "経営陣"],
        "業績・決算": ["決算", "業績", "売上", "利益", "成長", "増収", "減収"],
        "新サービス": ["新サービス", "新規事業", "ローンチ", "開始", "参入"],
        "提携・M&A": ["提携", "買収", "合併", "アライアンス", "パートナー", "出資"],
        "DX・テクノロジー": ["DX", "デジタル", "AI", "テクノロジー", "クラウド", "データ"],
        "働き方・福利厚生": ["働き方", "リモート", "オフィス", "福利厚生", "育休", "副業"],
        "業界動向": ["業界", "市場", "トレンド", "動向", "調査", "ランキング"],
        "受賞・表彰": ["受賞", "表彰", "認定", "ランキング", "選出"],
    }

    tags = []
    for tag, keywords in tag_keywords.items():
        if any(kw in text for kw in keywords):
            tags.append(tag)
    if not tags:
        tags = ["企業ニュース"]

    # 影響度判定
    impact_score = "低"
    for level, keywords in IMPACT_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            impact_score = level
            break

    # 要約生成
    summary = title
    if content and len(content) > 50:
        first_sentence = content.split("。")[0]
        if len(first_sentence) > 20:
            summary = first_sentence + "。"

    # 採用担当者向けの注目ポイント
    recruiter_note = None
    if impact_score in ("高", "中"):
        if any(kw in text for kw in ["採用", "求人", "人材"]):
            recruiter_note = "採用市場に直接影響。候補者への情報提供を検討してください。"
        elif any(kw in text for kw in ["組織", "再編", "新規事業"]):
            recruiter_note = "組織変更情報。候補者が気にするポイントなので面接で説明できるよう準備を。"

    return {
        "summary": summary[:300],
        "tags": tags[:4],
        "impact_score": impact_score,
        "recruiter_note": recruiter_note,
    }


def score_impact_local(title: str, summary: str | None) -> dict:
    """ルールベースで影響度スコアリング"""
    text = f"{title} {summary or ''}"

    impact_score = "低"
    for level, keywords in IMPACT_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            impact_score = level
            break

    should_alert = impact_score == "高"
    alert_type = None

    for atype, keywords in ALERT_PATTERNS.items():
        if any(kw in text for kw in keywords):
            should_alert = True
            alert_type = atype
            break

    # 採用担当者向けの具体的なアクション
    if impact_score == "高":
        reason = "採用市場に大きな影響を与える可能性があります。"
        action = "候補者への説明資料を更新し、次回面接で積極的に情報共有してください。"
    elif impact_score == "中":
        reason = "採用市場への間接的な影響が見込まれます。"
        action = "競合動向として把握し、候補者から質問があった場合に備えてください。"
    else:
        reason = "採用市場への直接的な影響は限定的です。"
        action = None

    return {
        "impact_score": impact_score,
        "reason": reason,
        "should_alert": should_alert,
        "alert_type": alert_type,
        "recommended_action": action,
    }
