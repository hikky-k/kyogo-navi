"""競合ナビ バックエンド メインアプリケーション"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analysis, auth, companies, crawl, crawl_sources, dashboard, users

app = FastAPI(
    title="競合ナビ API",
    description="コンサルティング業界の競合インテリジェンスシステム",
    version="0.1.0",
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(auth.router, prefix="/api/v1/auth", tags=["認証"])
app.include_router(users.router, prefix="/api/v1/users", tags=["ユーザー"])
app.include_router(companies.router, prefix="/api/v1/companies", tags=["企業"])
app.include_router(crawl_sources.router, prefix="/api/v1/crawl-sources", tags=["クロールソース"])
app.include_router(crawl.router, prefix="/api/v1/crawl", tags=["クロール実行"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["AI分析"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["ダッシュボード"])


@app.get("/api/v1/health")
def health_check():
    """ヘルスチェック"""
    return {"status": "ok"}
