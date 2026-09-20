from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseEntity
from app.models.user import User


class RefreshToken(BaseEntity):
    __tablename__ = "refresh_tokens"
    __table_args__ = (
        Index("ix_refresh_tokens_token", "token"),
        Index("ix_refresh_tokens_family_id", "family_id"),
    )

    token: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    family_id: Mapped[str] = mapped_column(String, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user: Mapped["User"] = relationship(lazy="joined")
    
