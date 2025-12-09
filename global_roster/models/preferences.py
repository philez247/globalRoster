"""Trader preferences model."""
from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from global_roster.models.base import Base


class TraderPreference(Base):
    """Generic preferences for traders."""
    
    __tablename__ = "trader_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    trader_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("traders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # e.g. "DAYS_OFF_GROUPING"
    category: Mapped[str] = mapped_column(String(50), nullable=False)

    # e.g. "PREFERENCE"
    key: Mapped[str] = mapped_column(String(50), nullable=False)

    # Preference weight; for DAYS_OFF_GROUPING:
    #   0  = no preference
    #  +2  = prefers back-to-back
    #  -2  = prefers split
    weight: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    trader: Mapped["Trader"] = relationship("Trader", backref="preferences")

    __table_args__ = (
        UniqueConstraint(
            "trader_id", "category", "key",
            name="uq_trader_preference_unique",
        ),
    )


class TraderDaySportPreference(Base):
    """Per-day sport preference (soft) for a trader."""

    __tablename__ = "trader_day_sport_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    trader_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("traders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    day_of_week: Mapped[str] = mapped_column(String(3), nullable=False)  # MON/TUE/...
    sport_code: Mapped[str | None] = mapped_column(String(20), nullable=True)

    trader: Mapped["Trader"] = relationship("Trader", backref="day_sport_preferences")

    __table_args__ = (
        UniqueConstraint(
            "trader_id",
            "day_of_week",
            name="uq_trader_day_sport_pref",
        ),
    )



