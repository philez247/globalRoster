"""Trader model."""
import enum
from datetime import date
from typing import Optional
from sqlalchemy import Boolean, Date, Enum as SAEnum, Integer, String, TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column, relationship

from global_roster.models.base import Base


class UserRole(str, enum.Enum):
    """User role enum for trader permissions."""
    USER = "USER"
    OWNER = "OWNER"
    MANAGER = "MANAGER"
    ADMIN = "ADMIN"


class UserRoleType(TypeDecorator):
    """Custom type for UserRole that works with SQLite (stores as string)."""
    impl = String
    cache_ok = True
    
    def __init__(self, length=20):
        super().__init__(length)
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, UserRole):
            return value.value
        return str(value)
    
    def process_result_value(self, value, dialect):
        if value is None:
            return None
        try:
            return UserRole(value)
        except ValueError:
            # Fallback to USER if invalid value
            return UserRole.USER


class Trader(Base):
    """Trader model representing a trader in the system."""
    
    __tablename__ = "traders"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    location: Mapped[str] = mapped_column(String(10), nullable=False)
    manager: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    primary_sport: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    secondary_sport: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    required_days_per_week: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    hours_per_week: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    alias: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, unique=True)
    user_role: Mapped[UserRole] = mapped_column(
        UserRoleType(20),
        nullable=False,
        default=UserRole.USER,
        server_default="USER",
    )

    # Relationships
    sport_skills = relationship(
        "TraderSportSkill",
        back_populates="trader",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

