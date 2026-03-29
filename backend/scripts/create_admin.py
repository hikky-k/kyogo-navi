"""初期管理者ユーザーを作成するスクリプト

使い方: docker compose exec backend python -m scripts.create_admin
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.user import User
from app.services.auth import hash_password


def main():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == "admin@kyogo-navi.local").first()
        if existing:
            print("管理者ユーザーは既に存在します")
            return

        admin = User(
            name="管理者",
            email="admin@kyogo-navi.local",
            password_hash=hash_password("admin123"),
            role="admin",
        )
        db.add(admin)
        db.commit()
        print("管理者ユーザーを作成しました")
        print("  メール: admin@kyogo-navi.local")
        print("  パスワード: admin123")
    finally:
        db.close()


if __name__ == "__main__":
    main()
