"""アラートモデル"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"))
    event_type: Mapped[str] = mapped_column(String(50))  # hiring_surge / reorg / new_service / score_change
    severity: Mapped[str] = mapped_column(String(10))  # 高 / 中 / 低
    title: Mapped[str] = mapped_column(String(300))
    message: Mapped[str] = mapped_column(Text)
    source_article_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("news_articles.id", ondelete="SET NULL"), nullable=True
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    notified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
