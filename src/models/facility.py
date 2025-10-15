"""Facility-related data models."""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

from .common import Coordinates


class FacilityType(str, Enum):
    """Types of EPA-regulated facilities."""
    
    TRI = "TRI"  # Toxics Release Inventory
    RCRA = "RCRA"  # Resource Conservation and Recovery Act
    SDWIS = "SDWIS"  # Safe Drinking Water Information System
    FRS = "FRS"  # Facility Registry Service
    ICIS = "ICIS"  # Integrated Compliance Information System
    GHG = "GHG"  # Greenhouse Gas Reporting Program
    NEI = "NEI"  # National Emissions Inventory
    SEMS = "SEMS"  # Superfund Enterprise Management System


class FacilityInfo(BaseModel):
    """Information about an EPA-regulated facility."""
    
    registry_id: str = Field(..., description="FRS Registry ID")
    name: str = Field(..., description="Facility name")
    address: Optional[str] = Field(None, description="Facility address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State abbreviation")
    zip_code: Optional[str] = Field(None, description="ZIP code")
    coordinates: Optional[Coordinates] = Field(None, description="Facility coordinates")
    programs: List[FacilityType] = Field(default_factory=list, description="Active EPA programs")
    naics_code: Optional[str] = Field(None, description="NAICS industry code")
    naics_description: Optional[str] = Field(None, description="NAICS industry description")
    distance_miles: Optional[float] = Field(None, ge=0, description="Distance from search center in miles")
    status: Optional[str] = Field(None, description="Facility status")
    
    def __str__(self) -> str:
        return f"{self.name} ({self.registry_id})"
