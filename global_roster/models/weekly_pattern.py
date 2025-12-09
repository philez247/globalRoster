"""Trader weekly pattern model."""
from __future__ import annotations

from typing import Literal

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from global_roster.models.base import Base

ShiftType = Literal["FULL", "EARLY", "MID", "LATE"]


class TraderWeeklyPattern(Base):
    """Weekly pattern preferences for traders."""
    
    __tablename__ = "trader_weekly_patterns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    trader_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("traders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 0 = Monday, ..., 6 = Sunday
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)

    # "FULL", "EARLY", "MID", "LATE"
    shift_type: Mapped[str] = mapped_column(String(10), nullable=False)

    # True = Absolute No (cannot work this shift)
    hard_block: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Soft preference weight:
    #   +1 = Preferred Shift
    #    0 = Indifferent (or Absolute No if hard_block=True)
    #   -1 = Preferred Not Work
    weight: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    trader: Mapped["Trader"] = relationship("Trader", backref="weekly_patterns")

    __table_args__ = (
        UniqueConstraint(
            "trader_id", "day_of_week", "shift_type",
            name="uq_trader_weekly_pattern_cell",
        ),
    )





