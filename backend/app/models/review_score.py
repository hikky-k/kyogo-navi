"""口コミスコアモデル"""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ReviewScore(Base):
    __tablename__ = "review_scores"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"))
    source: Mapped[str] = mapped_column(String(50))  # openwork / glassdoor
    overall_score: Mapped[float] = mapped_column(Float)
    categories_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
