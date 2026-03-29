"""テスト共通設定"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.services.auth import hash_password
from app.models.user import User
from app.models.company import Company

# テスト用のインメモリSQLite
TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    """各テスト前にテーブルを作成し、テスト後に削除"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """テスト用HTTPクライアント"""
    return TestClient(app)


@pytest.fixture
def db():
    """テスト用DBセッション"""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def admin_user(db):
    """管理者ユーザーを作成"""
    user = User(
        name="テスト管理者",
        email="admin@test.com",
        password_hash=hash_password("password123"),
        role="admin",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def viewer_user(db):
    """閲覧者ユーザーを作成"""
    user = User(
        name="テスト閲覧者",
        email="viewer@test.com",
        password_hash=hash_password("password123"),
        role="viewer",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_token(client, admin_user):
    """管理者のJWTトークンを取得"""
    res = client.post("/api/v1/auth/login", json={"email": "admin@test.com", "password": "password123"})
    return res.json()["access_token"]


@pytest.fixture
def viewer_token(client, viewer_user):
    """閲覧者のJWTトークンを取得"""
    res = client.post("/api/v1/auth/login", json={"email": "viewer@test.com", "password": "password123"})
    return res.json()["access_token"]


@pytest.fixture
def sample_company(db):
    """テスト用企業を作成"""
    company = Company(name="テスト株式会社", category="総合系", website_url="https://example.com", description="テスト企業")
    db.add(company)
    db.commit()
    db.refresh(company)
    return company
