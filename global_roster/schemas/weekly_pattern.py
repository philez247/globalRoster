"""Weekly pattern schemas."""
from typing import Literal

from pydantic import BaseModel, ConfigDict

ShiftType = Literal["FULL", "EARLY", "MID", "LATE"]
DaysOffPreference = Literal["NONE", "BACK_TO_BACK", "SPLIT"]


class WeeklyPatternCell(BaseModel):
    """A single cell in the weekly pattern grid."""
    day_of_week: int  # 0..6
    shift_type: ShiftType
    hard_block: bool
    weight: int  # -1, 0, +1 as per mapping


class DaySportPreference(BaseModel):
    """Preferred sport per day (soft)."""
    day_of_week: str  # MON, TUE, ... SUN
    sport_code: str | None = None


class WeeklyPatternUpdateRequest(BaseModel):
    """Request to update weekly pattern."""
    trader_id: int
    cells: list[WeeklyPatternCell]
    days_off_preference: DaysOffPreference = "NONE"
    day_sport_preferences: list[DaySportPreference] = []


class WeeklyPatternResponse(BaseModel):
    """Response containing weekly pattern data."""
    cells: list[WeeklyPatternCell]
    days_off_preference: DaysOffPreference
    day_sport_preferences: list[DaySportPreference] = []
    
    model_config = ConfigDict(from_attributes=True)

