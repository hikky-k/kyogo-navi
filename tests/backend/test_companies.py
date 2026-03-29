"""企業管理APIのテスト"""


def test_create_company(client, admin_token):
    """企業登録（管理者）"""
    res = client.post("/api/v1/companies/", json={
        "name": "アクセンチュア", "category": "総合系",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 201
    assert res.json()["name"] == "アクセンチュア"


def test_create_company_viewer_forbidden(client, viewer_token):
    """閲覧者は企業登録できない"""
    res = client.post("/api/v1/companies/", json={
        "name": "テスト", "category": "IT系",
    }, headers={"Authorization": f"Bearer {viewer_token}"})
    assert res.status_code == 403


def test_list_companies(client, admin_token, sample_company):
    """企業一覧取得"""
    res = client.get("/api/v1/companies/", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_list_companies_filter_category(client, admin_token, sample_company):
    """カテゴリフィルタ"""
    res = client.get("/api/v1/companies/?category=総合系", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert all(c["category"] == "総合系" for c in res.json())


def test_get_company(client, admin_token, sample_company):
    """企業詳細取得"""
    res = client.get(f"/api/v1/companies/{sample_company.id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert res.json()["name"] == "テスト株式会社"


def test_get_company_not_found(client, admin_token):
    """存在しない企業"""
    res = client.get("/api/v1/companies/9999", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 404


def test_update_company(client, admin_token, sample_company):
    """企業更新"""
    res = client.patch(f"/api/v1/companies/{sample_company.id}", json={
        "description": "更新済み",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert res.json()["description"] == "更新済み"


def test_delete_company(client, admin_token, sample_company):
    """企業削除"""
    res = client.delete(f"/api/v1/companies/{sample_company.id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 204


def test_duplicate_company_name(client, admin_token, sample_company):
    """同名企業の登録は失敗"""
    res = client.post("/api/v1/companies/", json={
        "name": "テスト株式会社", "category": "IT系",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 400
