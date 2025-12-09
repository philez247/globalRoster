"""Configuration models for locations and sports."""
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from global_roster.models.base import Base


class LocationConfig(Base):
    """Location configuration model."""
    
    __tablename__ = "locations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(15), unique=True, nullable=False)  # e.g. DUB/MEL/NY
    name: Mapped[str] = mapped_column(String(50), nullable=False)  # human-readable name
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class SportConfig(Base):
    """Sport configuration model."""
    
    __tablename__ = "sports"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  # e.g. NBA/NFL
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)





