"""Chemical release data models."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date


class ChemicalRelease(BaseModel):
    """Chemical release information from TRI."""
    
    facility_id: str = Field(..., description="Facility Registry ID")
    facility_name: str = Field(..., description="Facility name")
    chemical_name: str = Field(..., description="Chemical name")
    cas_number: Optional[str] = Field(None, description="CAS Registry Number")
    reporting_year: int = Field(..., ge=1987, le=2030, description="Reporting year")
    
    # Release quantities by medium (in pounds)
    air_release: Optional[float] = Field(None, ge=0, description="Air release quantity (pounds)")
    water_release: Optional[float] = Field(None, ge=0, description="Water release quantity (pounds)")
    land_release: Optional[float] = Field(None, ge=0, description="Land release quantity (pounds)")
    underground_injection: Optional[float] = Field(None, ge=0, description="Underground injection quantity (pounds)")
    
    # Additional information
    release_type: Optional[str] = Field(None, description="Type of release")
    units: str = Field(default="pounds", description="Units of measurement")
    
    @property
    def total_release(self) -> float:
        """Calculate total release across all media."""
        total = 0.0
        for release in [self.air_release, self.water_release, self.land_release, self.underground_injection]:
            if release is not None:
                total += release
        return total


class ReleaseSummary(BaseModel):
    """Summary of chemical releases for a location."""
    
    total_facilities: int = Field(..., ge=0, description="Total facilities with releases")
    total_chemicals: int = Field(..., ge=0, description="Total unique chemicals released")
    total_releases: float = Field(..., ge=0, description="Total releases across all media (pounds)")
    
    # Releases by medium
    air_releases: float = Field(default=0.0, ge=0, description="Total air releases (pounds)")
    water_releases: float = Field(default=0.0, ge=0, description="Total water releases (pounds)")
    land_releases: float = Field(default=0.0, ge=0, description="Total land releases (pounds)")
    underground_injections: float = Field(default=0.0, ge=0, description="Total underground injections (pounds)")
    
    # Top chemicals
    top_chemicals: List[Dict[str, Any]] = Field(default_factory=list, description="Top chemicals by release quantity")
    
    # Reporting year
    reporting_year: int = Field(..., ge=1987, le=2030, description="Year of data")
