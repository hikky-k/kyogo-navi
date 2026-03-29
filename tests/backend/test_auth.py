"""認証APIのテスト"""


def test_register(client):
    """ユーザー登録"""
    res = client.post("/api/v1/auth/register", json={
        "name": "新規ユーザー",
        "email": "new@test.com",
        "password": "password123",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["access_token"]
    assert data["user"]["name"] == "新規ユーザー"
    assert data["user"]["role"] == "viewer"


def test_register_duplicate_email(client):
    """重複メールアドレスでの登録は失敗する"""
    client.post("/api/v1/auth/register", json={
        "name": "ユーザー1", "email": "dup@test.com", "password": "pass123",
    })
    res = client.post("/api/v1/auth/register", json={
        "name": "ユーザー2", "email": "dup@test.com", "password": "pass123",
    })
    assert res.status_code == 400


def test_login_success(client, admin_user):
    """正しい認証情報でログイン"""
    res = client.post("/api/v1/auth/login", json={
        "email": "admin@test.com", "password": "password123",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["access_token"]
    assert data["user"]["email"] == "admin@test.com"


def test_login_wrong_password(client, admin_user):
    """誤ったパスワードでログイン失敗"""
    res = client.post("/api/v1/auth/login", json={
        "email": "admin@test.com", "password": "wrongpass",
    })
    assert res.status_code == 401


def test_login_nonexistent_user(client):
    """存在しないユーザーでログイン失敗"""
    res = client.post("/api/v1/auth/login", json={
        "email": "nobody@test.com", "password": "pass123",
    })
    assert res.status_code == 401


def test_get_me(client, admin_token):
    """現在のユーザー情報を取得"""
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert res.json()["email"] == "admin@test.com"


def test_get_me_unauthorized(client):
    """トークンなしでアクセス不可"""
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
