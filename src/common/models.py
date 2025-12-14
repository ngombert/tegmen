"""Database models for Tegmen."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.database import Base


class FamilyMember(Base):
    """Family member model."""

    __tablename__ = "family_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # parent, child, etc.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    preferences: Mapped[list["Preference"]] = relationship(
        back_populates="member", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<FamilyMember(id={self.id}, name='{self.name}', role='{self.role}')>"


class Preference(Base):
    """User preferences model."""

    __tablename__ = "preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("family_members.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # food, travel, school
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    member: Mapped["FamilyMember"] = relationship(back_populates="preferences")

    def __repr__(self) -> str:
        return f"<Preference(id={self.id}, category='{self.category}')>"


class ConversationLog(Base):
    """Conversation logs for tracking agent interactions."""

    __tablename__ = "conversation_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    agent: Mapped[str] = mapped_column(String(50), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant
    message: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    member_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("family_members.id"), nullable=True
    )

    def __repr__(self) -> str:
        return f"<ConversationLog(id={self.id}, agent='{self.agent}', role='{self.role}')>"
