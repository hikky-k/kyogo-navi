# 競合ナビ（Kyogo Navi）

コンサルティング業界の競合インテリジェンスシステム。
中途採用担当者が競合他社の動向・強み・弱みを把握し、候補者への魅力づけに活用するためのWebアプリケーション。

---

## プロジェクト概要

### 解決する課題

コンサルティングファームの中途採用において、優秀な候補者は複数社から同時にオファーを受ける。
自社の魅力を的確に伝えるためには、競合他社の動向・強み・弱みをリアルタイムに把握し、差別化ポイントを明確にする必要がある。
現状は手作業での情報収集に頼っており、網羅性・即時性・分析の深さに課題がある。

### システム概要

- **システム名**: 競合ナビ（仮称）
- **形態**: Webアプリケーション（ブラウザベース）
- **対象業界**: コンサルティング業界（総合系・IT/デジタル系・ブティック系）
- **対象企業数**: 初期10社未満（主要競合）、段階的に拡大可能
- **情報更新**: 毎日自動更新（バッチ処理）

### 利用者

| 利用者 | 役割 | 主な利用シーン |
|--------|------|--------------|
| 採用担当者 | 主利用者 | 候補者への情報提供、競合分析、日常的な動向チェック |
| 面接官・現場マネージャー | 閲覧利用者 | 面接前の競合情報確認、自社の強みの説明材料 |
| 経営層・人事責任者 | 意思決定者 | 採用戦略の立案、競合環境の俯瞰 |

---

## 技術スタック

| レイヤー | 技術 | 備考 |
|---------|------|------|
| フロントエンド | Next.js (App Router) + Tailwind CSS | SSR対応、レスポンシブデザイン（PC・SP両対応） |
| バックエンドAPI | Python (FastAPI) | REST APIでフロントと通信 |
| データ収集 | Python (Playwright + BeautifulSoup) | クローラー、cronで毎日実行 |
| AI分析 | Claude API (Anthropic) | 要約・強み弱み分析・タグ付け・アラート判定 |
| データベース | PostgreSQL | 構造化データ保存 |
| キャッシュ | Redis | ダッシュボード高速表示用 |
| 通知 | SendGrid（メール） or Slack Webhook | アラート配信 |
| インフラ | Docker + クラウド（AWS or GCP） | コンテナ化で運用負荷軽減 |

---

## ディレクトリ構成

```
kyogo-navi/
├── CLAUDE.md
├── docker-compose.yml
├── frontend/                # Next.js フロントエンド
│   ├── src/
│   │   ├── app/             # App Router ページ
│   │   ├── components/      # UIコンポーネント
│   │   ├── lib/             # ユーティリティ・API クライアント
│   │   └── types/           # TypeScript型定義
│   ├── package.json
│   └── tailwind.config.ts
├── backend/                 # FastAPI バックエンド
│   ├── app/
│   │   ├── api/             # APIエンドポイント
│   │   ├── models/          # SQLAlchemyモデル
│   │   ├── schemas/         # Pydanticスキーマ
│   │   ├── services/        # ビジネスロジック
│   │   ├── crawlers/        # データ収集クローラー
│   │   └── analysis/        # AI分析モジュール
│   ├── migrations/          # Alembicマイグレーション
│   └── requirements.txt
├── docs/                    # ドキュメント
│   └── 01_requirements.md
└── tests/
    ├── frontend/
    └── backend/
```

---

## データベース設計

### 主要テーブル

```sql
-- 対象企業マスタ
companies: id, name, category(総合系/IT系/ブティック系), website_url, logo_url, description, is_active, created_at, updated_at

-- クロール対象ソース設定
crawl_sources: id, company_id(FK), source_type(official/news/review/job), url, crawl_frequency, last_crawled_at, is_active

-- 収集ニュース記事
news_articles: id, company_id(FK), source, source_url, title, content, summary, impact_score(高/中/低), tags(JSONB), published_at, created_at

-- AI分析結果
analysis_results: id, company_id(FK), analysis_type(strength_weakness/positioning/trend), content_json(JSONB), raw_data_refs(JSONB), analyzed_at

-- 口コミスコア履歴
review_scores: id, company_id(FK), source(openwork/glassdoor), overall_score, categories_json(JSONB), review_count, scraped_at

-- 求人情報
job_postings: id, company_id(FK), source(linkedin/bizreach), title, department, salary_range, requirements, posted_at, is_active, scraped_at

-- アラート履歴
alerts: id, company_id(FK), event_type(hiring_surge/reorg/new_service/score_change), severity(高/中/低), title, message, source_article_id(FK nullable), is_read, notified_at

-- ユーザー管理
users: id, name, email, password_hash, role(admin/viewer), notification_settings_json(JSONB), created_at

-- 手動入力メモ
manual_notes: id, company_id(FK), user_id(FK), content, created_at, updated_at
```

---

## 機能要件

### F1: データ収集（クローラー）

4つのソースから毎日自動収集する。各ソースごとにクローラーモジュールを独立実装し、企業ごとにURL・頻度を設定可能にする。

| ソース | 収集対象 | 収集項目 |
|--------|---------|---------|
| 公式サイト・プレスリリース | 各社コーポレートサイト、採用ページ、ニュースルーム | 組織再編・新サービス開始、経営陣交代・人事異動、採用強化情報・イベント |
| ニュースサイト・業界メディア | 日経・東洋経済・業界専門誌・ITメディア等 | 業界トレンド・市場動向、大型案件受注・アライアンス情報、決算・業績情報 |
| 口コミサイト | OpenWork, Glassdoor | 総合評価スコア推移、待遇・成長機会・ワークライフバランス、ポジティブ/ネガティブなレビュー傾向 |
| 求人サイト | LinkedIn, ビズリーチ等 | 募集ポジション・職種・年収レンジ、採用規模の変化（求人数の増減）、採用要件・待遇条件のトレンド |

**クローラー実装要件:**
- 各ソースのクローラーは `backend/app/crawlers/` 配下に独立モジュールとして実装
- `base_crawler.py` に共通インターフェースを定義し、各クローラーが継承
- クロール失敗時はリトライ（最大3回）+ エラーログ記録 + 管理者アラート
- robots.txt を尊重し、適切なリクエスト間隔（最低2秒）を設ける
- 収集データは `news_articles`, `review_scores`, `job_postings` テーブルに保存

### F2: AI分析

Claude APIを使って収集データを自動分析する。生データとAI分析結果の両方をダッシュボードで確認可能にする。

| 分析機能 | 説明 | 出力 |
|---------|------|------|
| 強み・弱み分析 | 公開情報・口コミから各社の強み・弱みを抽出・構造化 | 企業別カード形式（タグ付き） |
| ポジショニング分析 | 各社がどの領域・どの訴求軸で打ち出しているか | ポジショニングマップ |
| ニュース要約・タグ付け | 収集ニュースを自動要約し重要度タグを付与 | タイムライン表示 |
| トレンド検出 | 採用強化・組織再編・新規事業などの業界トレンドを検出 | トレンドレポート（週次/月次） |
| 影響度スコアリング | 各ニュースの採用市場への影響度を自動判定（高/中/低） | アラートのトリガーとして活用 |

**AI分析実装要件:**
- `backend/app/analysis/` 配下に分析モジュールを実装
- Claude APIへのプロンプトはテンプレート化し、`analysis/prompts/` に管理
- 分析結果は `analysis_results` テーブルにJSON形式で保存
- 分析は日次バッチで実行（新規データがある企業のみ）
- APIコスト最適化のためキャッシュを活用し、変更がないデータは再分析しない

### F3: ダッシュボード

以下の4ビューで構成する。利用者の役割に応じて表示をカスタマイズ可能。

| ビュー | 説明 | 主な表示要素 |
|--------|------|------------|
| 業界オーバービュー | 業界全体のトレンドを俯瞰 | 最新ニュースフィード、業界トレンドサマリー、アラート一覧 |
| 企業別詳細ビュー | 競合各社を個別に深掘り | 企業プロフィールカード、強み/弱み分析結果、最新ニュース、口コミスコア推移チャート、採用動向 |
| 比較ビュー | 複数社を横並びで比較 | 強み/弱み比較表、口コミスコア比較チャート、採用ポジション比較 |
| アラートビュー | 重要な変化を時系列で確認 | アラート履歴、対応ステータス、影響度フィルター |

**ダッシュボード実装要件:**
- ページ表示は3秒以内（Redisキャッシュ活用）
- チャートは Recharts を使用
- レスポンシブデザイン（PC・スマホ両対応）
- 企業カテゴリ（総合系/IT系/ブティック系）でのフィルタリング機能

### F4: アラート通知

競合他社に重要な動きがあった際に自動通知する。

- **対象イベント**: 大規模採用・採用凍結、組織再編・経営陣変更、新サービスライン立ち上げ、口コミスコアの大幅変動
- **通知チャネル**: ダッシュボード内通知 + メール通知（オプション）
- **通知設定**: ユーザーごとに対象企業・イベント種別をカスタマイズ可能
- **重要度判定**: AIによる影響度スコアリング（高/中/低）でノイズを排除

### F5: データ管理

- 対象企業の追加・削除・カテゴリ分類
- 企業ごとにURL・収集対象ページ・頻度を設定
- 収集データの履歴を保持し経時変化を追跡可能
- 自動収集できない情報（エージェント経由等）を手動追加
- 分析結果をCSV/PDFでエクスポート

### F6: ユーザー管理・認証

- メール/パスワードによるログイン認証
- 役割別アクセス制御（管理者: 全機能 / 閲覧者: ダッシュボード閲覧のみ）
- ユーザーごとの通知設定

---

## 画面一覧

| 画面ID | 画面名 | 概要 | パス |
|--------|--------|------|------|
| SCR-001 | ログイン | メール/パスワード認証 | `/login` |
| SCR-002 | 業界オーバービュー | 最新ニュース、トレンド、アラート一覧 | `/` (ホーム) |
| SCR-003 | 企業詳細 | 個社深掘り（強み/弱み・ニュース・口コミ・採用動向） | `/companies/[id]` |
| SCR-004 | 企業比較 | 複数社横並び比較 | `/compare` |
| SCR-005 | アラート管理 | アラート履歴・通知設定 | `/alerts` |
| SCR-006 | 管理画面 | 企業・ソース設定・ユーザー管理 | `/admin` |

---

## 非機能要件

| カテゴリ | 要件 | 詳細 |
|---------|------|------|
| パフォーマンス | レスポンス時間 | ダッシュボード表示: 3秒以内、日次バッチ処理: 30分以内で全社完了 |
| 可用性 | 稼働率 | 99.5%以上（営業日基準） |
| セキュリティ | 認証・認可 | ログイン認証必須、役割別アクセス制御 |
| スケーラビリティ | 拡張性 | 対象企業30社までの拡張に耐える設計 |
| 保守性 | ソース対応 | Webサイト構造変更時のクローラー修正が容易なモジュラー設計 |
| UI | レスポンシブ | PC・SP両対応 |

---

## 開発ルール

### 基本方針
1. この CLAUDE.md と上記の要件に従って段階的に開発する
2. Phase 1 から順番に進め、各Phase完了時に動作確認する
3. コメントとドキュメントは日本語で書く
4. コミットメッセージは日本語で、変更内容がわかるように書く

### コーディング規約
- **フロントエンド**: TypeScript 必須、ESLint + Prettier に従う、コンポーネントは関数コンポーネント + Hooks
- **バックエンド**: Python 3.11+、型ヒント必須、ruff でリント
- **API設計**: RESTful、エンドポイントは `/api/v1/` プレフィックス
- **エラーハンドリング**: 全APIエンドポイントで適切なエラーレスポンスを返す

### テスト方針
- バックエンド: pytest でユニットテスト
- フロントエンド: Jest + React Testing Library
- クローラー: モックを使ったテスト（実際のサイトにアクセスしない）

---

## 開発フェーズ

### Phase 1: 基盤構築（最初に実装）
- [ ] プロジェクトセットアップ（Next.js + FastAPI + PostgreSQL + Docker Compose）
- [ ] データベース設計・マイグレーション（Alembic）
- [ ] ユーザー認証基盤（JWT認証）
- [ ] 管理画面（企業・ソース登録）

### Phase 2: データ収集
- [ ] ベースクローラー実装（共通インターフェース）
- [ ] 公式サイトクローラー
- [ ] ニュースサイトクローラー
- [ ] 口コミサイトクローラー
- [ ] 求人サイトクローラー
- [ ] 日次バッチスケジューラー（cron）
- [ ] クロール失敗時のアラート

### Phase 3: AI分析
- [ ] Claude API連携モジュール
- [ ] 強み/弱み分析
- [ ] ニュース要約・タグ付け
- [ ] 影響度スコアリング（アラート判定）
- [ ] プロンプトテンプレート管理

### Phase 4: ダッシュボード
- [ ] 業界オーバービュー画面
- [ ] 企業詳細画面（強み/弱み・ニュース・口コミ・採用動向）
- [ ] 企業比較画面
- [ ] アラート通知機能（ダッシュボード内 + メール）
- [ ] チャート・グラフ（Recharts）

### Phase 5: テスト・改善
- [ ] 総合テスト
- [ ] ユーザーテスト・フィードバック反映
- [ ] パフォーマンス最適化
- [ ] 運用ドキュメント作成

---

## 環境変数

```env
# Database
DATABASE_URL=postgresql://user:pass@db:5432/kyogo_navi

# Redis
REDIS_URL=redis://redis:6379/0

# Claude API
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Auth
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Notification (optional)
SENDGRID_API_KEY=
SLACK_WEBHOOK_URL=
```
