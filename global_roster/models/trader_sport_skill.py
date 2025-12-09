"""Trader sport skill model with per-sport level."""
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from global_roster.models.base import Base


class TraderSportSkill(Base):
    __tablename__ = "trader_sport_skill"

    id = Column(Integer, primary_key=True, index=True)
    trader_id = Column(Integer, ForeignKey("traders.id"), nullable=False)
    sport_code = Column(String, nullable=False)
    sport_level = Column(Integer, nullable=False, default=1, server_default="1")

    trader = relationship("Trader", back_populates="sport_skills")



