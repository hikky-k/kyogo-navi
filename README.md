# 競合ナビ（Kyogo Navi）

コンサルティング業界の競合インテリジェンスシステム。
中途採用担当者が競合他社の動向・強み・弱みを把握し、候補者への魅力づけに活用するためのWebアプリケーション。

## 機能

- **業界オーバービュー**: 最新ニュース・アラート・統計を一覧表示
- **企業詳細**: 強み/弱み分析・口コミスコア推移・採用動向・面接での魅力づけガイド
- **企業比較**: 複数社の差別化ポイント・強み弱みマトリクス・1対1比較
- **アラート通知**: 競合の重要な動きを自動検知・通知
- **データ収集**: 公式サイト・ニュース・口コミ・求人から自動クロール
- **AI分析**: ローカル分析エンジン（無料）/ Claude API（オプション）

## 技術スタック

| レイヤー | 技術 |
|---------|------|
| フロントエンド | Next.js 15 (App Router) + Tailwind CSS + Recharts |
| バックエンドAPI | Python 3.11 + FastAPI |
| データベース | PostgreSQL 16 |
| キャッシュ | Redis 7 |
| コンテナ | Docker Compose |

## セットアップ

### 前提条件

- Docker Desktop がインストールされていること

### 起動手順

```bash
# 1. リポジトリをクローン
git clone https://github.com/hikky-k/kyogo-navi.git
cd kyogo-navi

# 2. 全サービスを起動
docker compose up --build -d

# 3. データベースのマイグレーション
docker compose exec backend alembic upgrade head

# 4. 初期管理者ユーザーを作成
docker compose exec backend python -m scripts.create_admin
```

### アクセス

| サービス | URL |
|---------|-----|
| フロントエンド | http://localhost:3000 |
| バックエンドAPI | http://localhost:8000 |
| API ドキュメント | http://localhost:8000/docs |

### ログイン情報（初期管理者）

- メール: `admin@kyogo-navi.com`
- パスワード: `admin123`

## 使い方

### 1. 企業を登録する

管理画面（`/admin`）で競合企業を登録します。
- 企業名・カテゴリ（総合系/IT系/ブティック系）・WebサイトURLを入力

### 2. クロールソースを設定する

登録した企業にクロール対象URLを追加します。
- ソースタイプ: 公式サイト / ニュースサイト / 口コミサイト / 求人サイト

### 3. データを収集する

管理画面の「実行」または「一括クロール」ボタンでデータ収集を実行します。

### 4. AI分析を実行する

企業詳細ページ（`/companies/[id]`）で「AI分析実行」ボタンを押すと、強み/弱み分析・面接での魅力づけガイドが生成されます。

### 5. 企業を比較する

企業比較ページ（`/compare`）で2社以上を選択し、差別化ポイント・比較マトリクスを確認できます。

## 日次バッチ処理

cronで以下を設定すると毎日自動でデータ収集・分析が実行されます。

```bash
# 毎朝6時にクロール実行
0 6 * * * docker compose exec backend python -m app.crawlers.scheduler

# 毎朝8時にAI分析実行
0 8 * * * docker compose exec backend python -m app.analysis.scheduler
```

## Claude API（オプション）

より高精度なAI分析を行う場合は、`.env` ファイルにAPIキーを設定します。

```bash
echo "ANTHROPIC_API_KEY=sk-ant-xxxxx" > .env
docker compose restart backend
```

未設定でもローカル分析エンジンで動作します。

## テスト

```bash
docker compose exec backend python -m pytest tests/ -v
```

## サービスの停止・再起動

```bash
# 停止
docker compose down

# 再起動
docker compose up -d

# ログ確認
docker compose logs -f backend
```

## トラブルシューティング

| 問題 | 対処法 |
|------|--------|
| ログインできない | `docker compose exec backend python -m scripts.create_admin` で管理者を再作成 |
| DBエラー | `docker compose exec backend alembic upgrade head` でマイグレーション実行 |
| フロントが表示されない | `docker compose logs frontend` でエラーを確認 |
| コンテナが起動しない | `docker compose down && docker compose up --build -d` で再ビルド |
