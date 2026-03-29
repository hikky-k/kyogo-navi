"""ダッシュボードAPIのテスト"""


def test_get_stats(client, admin_token):
    """統計情報取得"""
    res = client.get("/api/v1/dashboard/stats", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    data = res.json()
    assert "company_count" in data
    assert "news_count" in data
    assert "unread_alerts" in data
    assert "job_count" in data


def test_get_news_empty(client, admin_token):
    """ニュース一覧（空の場合）"""
    res = client.get("/api/v1/dashboard/news", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert res.json() == []


def test_get_alerts_empty(client, admin_token):
    """アラート一覧（空の場合）"""
    res = client.get("/api/v1/dashboard/alerts", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert res.json() == []


def test_get_alerts_unauthorized(client):
    """未認証でアラート取得不可"""
    res = client.get("/api/v1/dashboard/alerts")
    assert res.status_code == 401
