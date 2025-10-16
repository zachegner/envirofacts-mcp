"""Tool 3: Facility Compliance History."""

import logging
from typing import Optional
from datetime import date

from fastmcp import FastMCP

from ..models.compliance import FacilityComplianceHistory, ComplianceStatus
from ..models.facility import FacilityInfo, FacilityType
from ..client import ComplianceClient, FRSClient, EPAAPIError


logger = logging.getLogger(__name__)


async def get_facility_compliance_history(
    registry_id: str,
    program: Optional[str] = None,
    years: int = 5
) -> FacilityComplianceHistory:
    """Get compliance and enforcement history for an EPA-regulated facility.
    
    This tool retrieves compliance status, violations, and enforcement history
    for EPA-regulated facilities across RCRA and TRI programs. It supports both
    FRS registry IDs and program-specific IDs with intelligent fallback logic.
    
    Args:
        registry_id: FRS Registry ID or program-specific ID (RCRA Handler ID, TRI Facility ID)
        program: Optional program filter ('TRI' or 'RCRA')
        years: Historical years to include (default: 5, max: 20)
    
    Returns:
        FacilityComplianceHistory containing:
        - Facility information
        - Compliance records by program
        - Violations with dates and status
        - Overall compliance status
        - Summary statistics
    
    Raises:
        ValueError: If parameters are invalid
        Exception: If EPA API queries fail
    
    Example:
        >>> # By FRS registry ID
        >>> compliance = await get_facility_compliance_history("110000012345")
        >>> 
        >>> # By program-specific ID with filter
        >>> compliance = await get_facility_compliance_history("VAD000012345", program="RCRA")
        >>> 
        >>> # With custom timeframe
        >>> compliance = await get_facility_compliance_history("110000012345", years=10)
    """
    # Validate input parameters
    if not registry_id or not registry_id.strip():
        raise ValueError("Registry ID cannot be empty")
    
    if not (1 <= years <= 20):
        raise ValueError("Years must be between 1 and 20")
    
    if program and program.upper() not in ['TRI', 'RCRA']:
        raise ValueError("Program must be 'TRI' or 'RCRA'")
    
    registry_id = registry_id.strip()
    if program:
        program = program.strip().upper()
    
    try:
        logger.info(f"Getting compliance history for facility {registry_id} "
                   f"(program: {program or 'all'}, years: {years})")
        
        # Step 1: Get facility information from FRS
        facility_info = None
        try:
            async with FRSClient() as frs_client:
                facility_info = await frs_client.get_facility_by_id(registry_id)
        except Exception as e:
            logger.warning(f"Failed to get facility info from FRS for {registry_id}: {e}")
        
        # If FRS lookup failed, create a basic facility info
        if not facility_info:
            facility_info = FacilityInfo(
                registry_id=registry_id,
                name=f"Facility {registry_id}",
                programs=[FacilityType.FRS]
            )
        
        # Step 2: Get compliance records
        compliance_records = []
        try:
            async with ComplianceClient() as compliance_client:
                compliance_records = await compliance_client.get_compliance_by_registry_id(
                    registry_id=registry_id,
                    program=program,
                    years=years
                )
        except Exception as e:
            logger.error(f"Failed to get compliance records for {registry_id}: {e}")
            raise Exception(f"Failed to retrieve compliance data: {e}")
        
        # Step 3: Calculate overall status and statistics
        overall_status = ComplianceStatus.UNKNOWN
        total_violations = 0
        total_penalties = None
        
        if compliance_records:
            # Determine overall status based on individual program statuses
            statuses = [record.status for record in compliance_records]
            if ComplianceStatus.VIOLATION in statuses:
                overall_status = ComplianceStatus.VIOLATION
            elif ComplianceStatus.COMPLIANT in statuses:
                overall_status = ComplianceStatus.COMPLIANT
            
            # Calculate totals
            total_violations = sum(record.violation_count for record in compliance_records)
            
            # Sum penalties (if available)
            penalties = [record.total_penalties for record in compliance_records 
                        if record.total_penalties is not None]
            if penalties:
                total_penalties = sum(penalties)
        
        # Step 4: Build compliance history
        compliance_history = FacilityComplianceHistory(
            facility_info=facility_info,
            compliance_records=compliance_records,
            overall_status=overall_status,
            total_violations=total_violations,
            total_penalties=total_penalties,
            years_analyzed=years,
            last_updated=date.today()
        )
        
        logger.info(f"Compliance history complete for {registry_id}: "
                   f"{overall_status}, {total_violations} violations, "
                   f"{len(compliance_records)} programs")
        
        return compliance_history
        
    except ValueError:
        # Re-raise validation errors
        raise
    except Exception as e:
        logger.error(f"Failed to get compliance history for {registry_id}: {e}")
        raise Exception(f"Failed to retrieve compliance history: {e}")


# Register the tool with FastMCP
def register_tool(mcp: FastMCP):
    """Register the compliance history tool with FastMCP.
    
    Args:
        mcp: FastMCP instance
    """
    @mcp.tool()
    async def get_facility_compliance_history_tool(
        registry_id: str,
        program: Optional[str] = None,
        years: int = 5
    ) -> FacilityComplianceHistory:
        """Get compliance and enforcement history for an EPA-regulated facility.
        
        Retrieves compliance status, violations, and enforcement history for EPA-regulated
        facilities across RCRA and TRI programs. Supports both FRS registry IDs and 
        program-specific IDs with intelligent fallback logic.
        
        Args:
            registry_id: FRS Registry ID or program-specific ID (RCRA Handler ID, TRI Facility ID)
            program: Optional program filter ('TRI' or 'RCRA')
            years: Historical years to include (default: 5)
            
        Returns:
            Complete compliance history with facility information, compliance records,
            violations, and summary statistics
        """
        return await get_facility_compliance_history(registry_id, program, years)
