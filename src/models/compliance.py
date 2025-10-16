"""Compliance-related data models."""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import date

from .facility import FacilityInfo


class ComplianceStatus(str, Enum):
    """Compliance status enumeration."""
    
    COMPLIANT = "compliant"
    VIOLATION = "violation"
    UNKNOWN = "unknown"


class ViolationInfo(BaseModel):
    """Information about a compliance violation."""
    
    violation_id: Optional[str] = Field(None, description="Unique violation identifier")
    violation_type: str = Field(..., description="Type of violation")
    violation_date: Optional[date] = Field(None, description="Date of violation")
    status: str = Field(..., description="Current violation status")
    description: Optional[str] = Field(None, description="Description of violation")
    enforcement_action: Optional[str] = Field(None, description="Enforcement action taken")
    penalty_amount: Optional[float] = Field(None, description="Penalty amount in dollars")


class ComplianceRecord(BaseModel):
    """Compliance record for a specific EPA program."""
    
    program: str = Field(..., description="EPA program (TRI, RCRA, etc.)")
    status: ComplianceStatus = Field(..., description="Overall compliance status")
    violations: List[ViolationInfo] = Field(default_factory=list, description="List of violations")
    last_inspection_date: Optional[date] = Field(None, description="Date of last inspection")
    last_enforcement_date: Optional[date] = Field(None, description="Date of last enforcement action")
    total_penalties: Optional[float] = Field(None, description="Total penalties in dollars")
    violation_count: int = Field(0, description="Number of violations")


class FacilityComplianceHistory(BaseModel):
    """Complete compliance history for a facility."""
    
    facility_info: FacilityInfo = Field(..., description="Facility information")
    compliance_records: List[ComplianceRecord] = Field(default_factory=list, description="Compliance records by program")
    overall_status: ComplianceStatus = Field(..., description="Overall facility compliance status")
    total_violations: int = Field(0, description="Total violations across all programs")
    total_penalties: Optional[float] = Field(None, description="Total penalties across all programs")
    years_analyzed: int = Field(..., description="Number of years analyzed")
    last_updated: Optional[date] = Field(None, description="Date of last compliance update")
    
    def __str__(self) -> str:
        return f"Compliance History for {self.facility_info.name} ({self.facility_info.registry_id})"
