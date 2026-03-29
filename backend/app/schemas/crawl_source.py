"""クロールソース関連スキーマ"""

from datetime import datetime

from pydantic import BaseModel


class CrawlSourceCreate(BaseModel):
    company_id: int
    source_type: str  # official / news / review / job
    url: str
    crawl_frequency: str = "daily"


class CrawlSourceUpdate(BaseModel):
    source_type: str | None = None
    url: str | None = None
    crawl_frequency: str | None = None
    is_active: bool | None = None


class CrawlSourceResponse(BaseModel):
    id: int
    company_id: int
    source_type: str
    url: str
    crawl_frequency: str
    last_crawled_at: datetime | None = None
    is_active: bool

    model_config = {"from_attributes": True}
