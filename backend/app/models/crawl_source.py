"""クロールソースモデル"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CrawlSource(Base):
    __tablename__ = "crawl_sources"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"))
    source_type: Mapped[str] = mapped_column(String(50))  # official / news / review / job
    url: Mapped[str] = mapped_column(String(500))
    crawl_frequency: Mapped[str] = mapped_column(String(20), default="daily")  # daily / weekly
    last_crawled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # リレーション
    company = relationship("Company", back_populates="crawl_sources")
