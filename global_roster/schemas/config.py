"""Configuration Pydantic schemas."""
from pydantic import BaseModel, ConfigDict, Field, field_validator


class LocationCreate(BaseModel):
    """Schema for creating a location."""
    code: str = Field(..., min_length=1, max_length=15)
    
    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Validate location code: trim, uppercase, no spaces."""
        v = v.strip().upper()
        if not v:
            raise ValueError("Location code cannot be empty")
        if " " in v:
            raise ValueError("Location code cannot contain spaces")
        if len(v) > 15:
            raise ValueError("Location code must be <= 15 characters")
        return v


class LocationRead(BaseModel):
    """Schema for reading a location."""
    id: int
    code: str
    
    model_config = ConfigDict(from_attributes=True)





