"""Environmental summary response model."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict

from .common import Coordinates
from .facility import FacilityInfo
from .releases import ReleaseSummary
from .water import WaterSystem, WaterViolation


class EnvironmentalSummary(BaseModel):
    """Comprehensive environmental data summary for a location."""
    
    # Location information
    location: str = Field(..., description="Original location query")
    coordinates: Optional[Coordinates] = Field(None, description="Resolved coordinates")
    radius_miles: float = Field(..., description="Search radius used")
    
    # Facility counts by type
    facility_counts: Dict[str, int] = Field(default_factory=dict, description="Count of facilities by type")
    total_facilities: int = Field(default=0, ge=0, description="Total facilities found")
    
    # Top facilities (ranked by distance)
    top_facilities: List[FacilityInfo] = Field(default_factory=list, description="Top facilities within radius")
    
    # Water system information
    water_systems: List[WaterSystem] = Field(default_factory=list, description="Water systems in area")
    water_violations: List[WaterViolation] = Field(default_factory=list, description="Active water violations")
    total_violations: int = Field(default=0, ge=0, description="Total active violations")
    
    # Chemical release information
    chemical_releases: ReleaseSummary = Field(default_factory=lambda: ReleaseSummary(
        total_facilities=0,
        total_chemicals=0,
        total_releases=0.0,
        reporting_year=2023
    ), description="Chemical release summary")
    
    # Hazardous waste sites
    hazardous_sites: List[FacilityInfo] = Field(default_factory=list, description="RCRA hazardous waste sites")
    total_hazardous_sites: int = Field(default=0, ge=0, description="Total hazardous waste sites")
    
    # Summary statistics
    summary_stats: Dict[str, str | int | float | bool] = Field(default_factory=dict, description="Additional summary statistics")
    
    # Metadata
    query_timestamp: Optional[str] = Field(None, description="When the query was executed")
    data_sources: List[str] = Field(default_factory=list, description="EPA data sources queried")
    
    def __str__(self) -> str:
        return f"Environmental Summary for {self.location} ({self.total_facilities} facilities)"
