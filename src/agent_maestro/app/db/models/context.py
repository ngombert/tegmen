from datetime import datetime
from sqlalchemy import DateTime, String, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from agent_maestro.app.db.base import Base


class Context(Base):
    __tablename__ = "contexts"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    agent: Mapped[str] = mapped_column(String(100), nullable=False)
    context_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=func.now(),
    )
