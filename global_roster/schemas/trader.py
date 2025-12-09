"""Trader Pydantic schemas."""
from datetime import date
from pydantic import BaseModel, ConfigDict, Field

from global_roster.models.trader import UserRole


class TraderSportSkillBase(BaseModel):
    sport_code: str
    sport_level: int = 1


class TraderSportSkillUpdate(TraderSportSkillBase):
    id: int | None = None


class TraderSportSkillRead(TraderSportSkillBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class TraderBase(BaseModel):
    """Base trader schema with common fields."""
    name: str = Field(..., max_length=50)
    location: str = Field(..., max_length=15)
    alias: str = Field(..., max_length=100)
    manager: str | None = Field(None, max_length=50)
    level: int | None = None
    user_role: UserRole = UserRole.USER
    primary_sport: str | None = None
    secondary_sport: str | None = None
    required_days_per_week: int = 5
    hours_per_week: int | None = None
    start_date: date | None = None
    is_active: bool = True


class TraderCreate(TraderBase):
    """Schema for creating a trader."""
    name: str = Field(..., min_length=1)
    location: str = Field(..., min_length=1)
    alias: str = Field(..., min_length=1, max_length=100)
    manager: str | None = None
    level: int | None = None
    user_role: UserRole = UserRole.USER
    primary_sport: str | None = None
    secondary_sport: str | None = None
    required_days_per_week: int = 5
    hours_per_week: int | None = None
    start_date: date | None = None
    is_active: bool = True


class SportSkillInput(BaseModel):
    """Input for a sport skill (from frontend)."""
    sport: str
    level: str  # "1", "2", or "3"


class TraderUpdate(BaseModel):
    """Schema for updating a trader (all fields optional)."""
    name: str | None = None
    location: str | None = None
    alias: str | None = None
    manager: str | None = None
    level: int | None = None
    primary_sport: str | None = None
    primary_level: int | None = None
    secondary_sport: str | None = None
    secondary_level: int | None = None
    required_days_per_week: int | None = None
    hours_per_week: int | None = None
    start_date: date | None = None
    is_active: bool | None = None
    skills: list[SportSkillInput] | None = None


class TraderRead(TraderBase):
    """Schema for reading a trader (includes id)."""
    id: int
    sport_skills: list[TraderSportSkillRead] = []
    
    model_config = ConfigDict(from_attributes=True)

