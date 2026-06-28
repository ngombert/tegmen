from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, String, JSON, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from agent_maestro.app.db.base import Base


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    family_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    session_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    active_agent: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    active_claim_check_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    context_summary: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("family_id", "user_id", name="uq_user_sessions_family_user"),
    )
