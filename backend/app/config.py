"""アプリケーション設定"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # データベース
    DATABASE_URL: str = "postgresql://kyogo:kyogo_pass@db:5432/kyogo_navi"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # JWT認証
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # Claude API
    ANTHROPIC_API_KEY: str = ""

    # 通知（オプション）
    SENDGRID_API_KEY: str = ""
    SLACK_WEBHOOK_URL: str = ""

    model_config = {"env_file": ".env"}


settings = Settings()
