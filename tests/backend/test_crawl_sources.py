"""クロールソース管理APIのテスト"""


def test_create_crawl_source(client, admin_token, sample_company):
    """クロールソース登録"""
    res = client.post("/api/v1/crawl-sources/", json={
        "company_id": sample_company.id,
        "source_type": "official",
        "url": "https://example.com/news",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 201
    assert res.json()["source_type"] == "official"


def test_list_crawl_sources(client, admin_token, sample_company):
    """クロールソース一覧"""
    # まず1件登録
    client.post("/api/v1/crawl-sources/", json={
        "company_id": sample_company.id,
        "source_type": "news",
        "url": "https://news.example.com",
    }, headers={"Authorization": f"Bearer {admin_token}"})

    res = client.get(f"/api/v1/crawl-sources/?company_id={sample_company.id}",
                     headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_delete_crawl_source(client, admin_token, sample_company):
    """クロールソース削除"""
    create_res = client.post("/api/v1/crawl-sources/", json={
        "company_id": sample_company.id,
        "source_type": "review",
        "url": "https://review.example.com",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    source_id = create_res.json()["id"]

    res = client.delete(f"/api/v1/crawl-sources/{source_id}",
                        headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 204
