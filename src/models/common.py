"""Common data models used across EPA Envirofacts tools."""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional


class Coordinates(BaseModel):
    """Geographic coordinates."""
    
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    
    def __str__(self) -> str:
        return f"({self.latitude:.6f}, {self.longitude:.6f})"


class BoundingBox(BaseModel):
    """Geographic bounding box for area queries."""
    
    min_latitude: float = Field(..., ge=-90, le=90, description="Minimum latitude")
    max_latitude: float = Field(..., ge=-90, le=90, description="Maximum latitude")
    min_longitude: float = Field(..., ge=-180, le=180, description="Minimum longitude")
    max_longitude: float = Field(..., ge=-180, le=180, description="Maximum longitude")
    
    @model_validator(mode='after')
    def validate_bounds(self):
        if self.max_latitude <= self.min_latitude:
            raise ValueError('max_latitude must be greater than min_latitude')
        if self.max_longitude <= self.min_longitude:
            raise ValueError('max_longitude must be greater than min_longitude')
        return self


class LocationInfo(BaseModel):
    """Enhanced location information with state details."""
    
    coordinates: Coordinates = Field(..., description="Geographic coordinates")
    state_code: Optional[str] = Field(None, description="2-letter state abbreviation (e.g., 'NY', 'CA')")
    state_name: Optional[str] = Field(None, description="Full state name (e.g., 'New York', 'California')")
    county: Optional[str] = Field(None, description="County name")
    country: Optional[str] = Field(None, description="Country name")
    
    def __str__(self) -> str:
        parts = [str(self.coordinates)]
        if self.state_code:
            parts.append(f"State: {self.state_code}")
        if self.county:
            parts.append(f"County: {self.county}")
        return ", ".join(parts)


class LocationParams(BaseModel):
    """Parameters for location-based queries."""
    
    location: str = Field(..., min_length=1, max_length=200, description="Address, city, or ZIP code")
    radius_miles: float = Field(default=5.0, ge=0.1, le=100.0, description="Search radius in miles")
    
    @field_validator('location')
    @classmethod
    def validate_location(cls, v):
        """Basic validation for location string."""
        if not v.strip():
            raise ValueError('Location cannot be empty')
        return v.strip()
