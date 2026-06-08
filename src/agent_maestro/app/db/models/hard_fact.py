from datetime import datetime
from sqlalchemy import DateTime, String, Float, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column
from agent_maestro.app.db.base import Base

class HardFact(Base):
    __tablename__ = "hard_facts"

    id: Mapped[int] = mapped_column(primary_key=True)
    family_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)  # "allergie", "preference", etc.
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str] = mapped_column(String(1024), nullable=False)
    source_agent: Mapped[str] = mapped_column(String(100), nullable=False)
    importance_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
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
