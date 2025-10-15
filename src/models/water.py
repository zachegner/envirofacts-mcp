"""Water system and violation data models."""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

from .common import Coordinates


class WaterSystem(BaseModel):
    """Safe Drinking Water Information System (SDWIS) water system."""
    
    system_id: str = Field(..., description="Water system ID")
    name: str = Field(..., description="Water system name")
    population_served: Optional[int] = Field(None, ge=0, description="Population served")
    coordinates: Optional[Coordinates] = Field(None, description="System coordinates")
    state: Optional[str] = Field(None, description="State abbreviation")
    county: Optional[str] = Field(None, description="County name")
    system_type: Optional[str] = Field(None, description="Type of water system")
    primary_source: Optional[str] = Field(None, description="Primary water source")
    distance_miles: Optional[float] = Field(None, ge=0, description="Distance from search center in miles")
    
    def __str__(self) -> str:
        return f"{self.name} ({self.system_id})"


class WaterViolation(BaseModel):
    """Safe Drinking Water Act violation."""
    
    violation_id: str = Field(..., description="Violation ID")
    system_id: str = Field(..., description="Water system ID")
    system_name: str = Field(..., description="Water system name")
    violation_type: str = Field(..., description="Type of violation (e.g., MCL, MONITORING)")
    contaminant: Optional[str] = Field(None, description="Contaminant name")
    violation_date: Optional[date] = Field(None, description="Date of violation")
    compliance_status: Optional[str] = Field(None, description="Current compliance status")
    is_current: bool = Field(default=False, description="Whether violation is currently active")
    enforcement_action: Optional[str] = Field(None, description="Enforcement action taken")
    population_affected: Optional[int] = Field(None, ge=0, description="Population affected")
    
    def __str__(self) -> str:
        return f"{self.violation_type} violation at {self.system_name}"
