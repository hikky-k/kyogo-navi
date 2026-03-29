"""企業関連スキーマ"""

from datetime import datetime

from pydantic import BaseModel


class CompanyCreate(BaseModel):
    name: str
    category: str  # 総合系 / IT系 / ブティック系
    website_url: str | None = None
    logo_url: str | None = None
    description: str | None = None


class CompanyUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    website_url: str | None = None
    logo_url: str | None = None
    description: str | None = None
    is_active: bool | None = None


class CompanyResponse(BaseModel):
    id: int
    name: str
    category: str
    website_url: str | None = None
    logo_url: str | None = None
    description: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
