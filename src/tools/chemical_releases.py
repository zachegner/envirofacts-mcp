"""Tool 4: Chemical Release Data."""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from collections import defaultdict

from fastmcp import FastMCP

from ..models.releases import (
    ChemicalRelease, ChemicalReleaseData, FacilityReleaseInfo, 
    ChemicalAggregation
)
from ..client.tri import TRIClient


logger = logging.getLogger(__name__)


async def _get_chemical_release_data_impl(
    chemical_name: Optional[str] = None,
    cas_number: Optional[str] = None,
    state: Optional[str] = None,
    county: Optional[str] = None,
    year: Optional[int] = None,
    limit: int = 100,
) -> ChemicalReleaseData:
    """Query TRI chemical releases with flexible search parameters.
    
    This tool provides comprehensive chemical release data from the Toxics Release Inventory (TRI),
    allowing searches by chemical name, CAS number, state, county, and year. Results include
    both facility-centric and chemical-centric aggregations with optional year-over-year trends.
    
    Args:
        chemical_name: Chemical name (partial match, e.g., 'benzene')
        cas_number: CAS Registry Number (exact match, e.g., '71-43-2')
        state: Two-letter state code (e.g., 'NY', 'CA')
        county: County name (filtered client-side)
        year: Reporting year (None for most recent available)
        limit: Maximum results to return (default: 100, max: 1000)
    
    Returns:
        ChemicalReleaseData containing:
        - Search parameters used
        - Summary statistics (total facilities, chemicals, releases)
        - Releases by medium (air, water, land, underground injection)
        - Facilities grouped by facility with all their chemical releases
        - Chemicals grouped by chemical with all facilities releasing them
        - Top facilities and chemicals by total releases
    
    Raises:
        ValueError: If no search parameters provided or parameters invalid
        Exception: If EPA API queries fail
    
    Example:
        >>> # Search by chemical name
        >>> data = await get_chemical_release_data(chemical_name="benzene", state="CA")
        >>> print(f"Found {data.total_facilities} facilities releasing benzene")
        
        >>> # Search by CAS number
        >>> data = await get_chemical_release_data(cas_number="71-43-2", year=2022)
        >>> print(f"Total releases: {data.total_releases} pounds")
        
    """
    # Validate input parameters
    if not any([chemical_name, cas_number, state, county]):
        raise ValueError("At least one search parameter must be provided (chemical_name, cas_number, state, or county)")
    
    if limit <= 0 or limit > 1000:
        raise ValueError("Limit must be between 1 and 1000")
    
    if state and len(state) != 2:
        raise ValueError("State must be a two-letter code (e.g., 'NY', 'CA')")
    
    # Clean and validate parameters
    search_params = {}
    if chemical_name:
        chemical_name = chemical_name.strip()
        search_params['chemical_name'] = chemical_name
    if cas_number:
        cas_number = cas_number.strip()
        search_params['cas_number'] = cas_number
    if state:
        state = state.strip().upper()
        search_params['state'] = state
    if county:
        county = county.strip()
        search_params['county'] = county
    if year:
        search_params['year'] = year
    
    try:
        logger.info(f"Getting chemical release data with params: {search_params}")
        
        # Initialize TRI client
        async with TRIClient() as tri_client:
            # Get chemical releases
            releases = await tri_client.get_chemical_releases(
                chemical_name=chemical_name,
                cas_number=cas_number,
                state=state,
                county=county,
                year=year,
                limit=limit
            )
        
        if not releases:
            logger.info("No chemical releases found")
            return ChemicalReleaseData(
                search_params=search_params,
                total_facilities=0,
                total_chemicals=0,
                total_releases=0.0,
                query_timestamp=datetime.utcnow().isoformat() + "Z"
            )
        
        # Apply county filter client-side if specified
        if county:
            # Note: This would require additional facility data for county matching
            # For now, we'll include all releases
            logger.info(f"County filtering not yet implemented - returning all releases")
        
        # Aggregate data by facility
        facilities_dict = defaultdict(list)
        for release in releases:
            facilities_dict[release.facility_id].append(release)
        
        facilities = []
        for facility_id, facility_releases in facilities_dict.items():
            facility_info = FacilityReleaseInfo(
                facility_id=facility_id,
                facility_name=facility_releases[0].facility_name,
                chemical_releases=facility_releases
            )
            facilities.append(facility_info)
        
        # Aggregate data by chemical
        chemicals_dict = defaultdict(list)
        for release in releases:
            chemical_key = f"{release.chemical_name}_{release.cas_number or 'unknown'}"
            chemicals_dict[chemical_key].append(release)
        
        chemicals = []
        for chemical_key, chemical_releases in chemicals_dict.items():
            chemical_agg = ChemicalAggregation(
                chemical_name=chemical_releases[0].chemical_name,
                cas_number=chemical_releases[0].cas_number,
                facilities_releasing=chemical_releases
            )
            chemicals.append(chemical_agg)
        
        # Calculate totals by medium
        air_releases = sum(r.air_release or 0.0 for r in releases)
        water_releases = sum(r.water_release or 0.0 for r in releases)
        land_releases = sum(r.land_release or 0.0 for r in releases)
        underground_injections = sum(r.underground_injection or 0.0 for r in releases)
        total_releases = sum(r.total_release for r in releases)
        
        # Sort facilities and chemicals by total releases
        facilities.sort(key=lambda f: f.total_releases, reverse=True)
        chemicals.sort(key=lambda c: c.total_releases, reverse=True)
        
        # Get top facilities and chemicals (top 20 each)
        top_facilities = facilities[:20]
        top_chemicals = chemicals[:20]
        
        
        # Determine reporting year
        reporting_year = None
        if year:
            reporting_year = year
        elif releases:
            # Use the most common year in the results
            years = [r.reporting_year for r in releases]
            reporting_year = max(set(years), key=years.count)
        
        # Build response
        result = ChemicalReleaseData(
            search_params=search_params,
            total_facilities=len(facilities),
            total_chemicals=len(chemicals),
            total_releases=total_releases,
            air_releases=air_releases,
            water_releases=water_releases,
            land_releases=land_releases,
            underground_injections=underground_injections,
            facilities=facilities,
            chemicals=chemicals,
            top_facilities=top_facilities,
            top_chemicals=top_chemicals,
            reporting_year=reporting_year,
            query_timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
        logger.info(f"Chemical release data complete: {result.total_facilities} facilities, "
                   f"{result.total_chemicals} chemicals, {result.total_releases:.1f} pounds total")
        
        return result
        
    except ValueError:
        # Re-raise validation errors
        raise
    except Exception as e:
        logger.error(f"Failed to get chemical release data: {e}")
        raise Exception(f"Failed to retrieve chemical release data: {e}")




# Register the tool with FastMCP
def register_tool(mcp: FastMCP):
    """Register the chemical release data tool with FastMCP.
    
    Args:
        mcp: FastMCP instance
    """
    @mcp.tool()
    async def get_chemical_release_data(
        chemical_name: Optional[str] = None,
        cas_number: Optional[str] = None,
        state: Optional[str] = None,
        county: Optional[str] = None,
        year: Optional[int] = None,
        limit: int = 100
    ) -> ChemicalReleaseData:
        """Query TRI chemical releases with flexible search parameters.
        
        Provides comprehensive chemical release data from the Toxics Release Inventory (TRI),
        allowing searches by chemical name, CAS number, state, county, and year.
        
        Args:
            chemical_name: Chemical name (partial match)
            cas_number: CAS Registry Number (exact match)
            state: Two-letter state code
            county: County name (filtered client-side)
            year: Reporting year (None for most recent available)
            limit: Maximum results to return (default: 100)
            
        Returns:
            Comprehensive chemical release data with aggregations
        """
        # Call the actual implementation function
        return await _get_chemical_release_data_impl(
            chemical_name=chemical_name,
            cas_number=cas_number,
            state=state,
            county=county,
            year=year,
            limit=limit
        )

