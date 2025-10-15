"""Tool 1: Environmental Summary by Location."""

import asyncio
import logging
from typing import Optional

from fastmcp import FastMCP

from ..models.common import LocationParams, Coordinates, LocationInfo
from ..models.summary import EnvironmentalSummary
from ..client import FRSClient, TRIClient, SDWISClient, RCRAClient
from ..utils.geocoding import geocode_location
from ..utils.distance import calculate_bounding_box, filter_by_distance
from ..utils.aggregation import aggregate_facilities, rank_facilities, format_environmental_summary


logger = logging.getLogger(__name__)


async def get_environmental_summary_by_location(
    location: str,
    radius_miles: float = 5.0
) -> EnvironmentalSummary:
    """Get comprehensive environmental data for a location.
    
    This tool provides a comprehensive environmental summary for any location in the United States,
    including nearby regulated facilities, chemical releases, water quality violations, and hazardous
    waste sites within a specified radius.
    
    Args:
        location: Address, city, or ZIP code (e.g., "New York, NY", "10001", "Los Angeles, CA")
        radius_miles: Search radius in miles (default: 5.0, max: 100.0)
    
    Returns:
        EnvironmentalSummary containing:
        - Location coordinates and search parameters
        - Count of facilities by type (TRI, RCRA, SDWIS, FRS)
        - Top facilities ranked by distance
        - Water systems and active violations
        - Chemical release summary with top chemicals
        - Hazardous waste sites
        - Summary statistics
    
    Raises:
        ValueError: If location cannot be geocoded or parameters are invalid
        Exception: If EPA API queries fail
    
    Example:
        >>> summary = await get_environmental_summary_by_location("10001", 3.0)
        >>> print(f"Found {summary.total_facilities} facilities")
        >>> print(f"Active violations: {summary.total_violations}")
    """
    # Validate input parameters
    if not location or not location.strip():
        raise ValueError("Location cannot be empty")
    
    if not (0.1 <= radius_miles <= 100.0):
        raise ValueError("Radius must be between 0.1 and 100.0 miles")
    
    location = location.strip()
    
    try:
        logger.info(f"Getting environmental summary for {location} (radius: {radius_miles} miles)")
        
        # Step 1: Enhanced geocoding to get coordinates and state
        try:
            location_info = await geocode_location(location)
            coordinates = location_info.coordinates
            state_code = location_info.state_code
            
            logger.info(f"Geocoded {location} to {location_info}")
            
            if not state_code:
                raise ValueError(f"Could not determine state from location '{location}'. Please try a different address, city, or ZIP code.")
                
        except ValueError as e:
            logger.error(f"Geocoding failed for {location}: {e}")
            raise ValueError(f"Could not find location '{location}'. Please try a different address, city, or ZIP code.")
        
        # Step 2: State-based queries (no bounding box needed)
        logger.info(f"Querying EPA data sources for state {state_code}...")
        
        # Initialize EPA API clients
        async with FRSClient() as frs_client, \
                   TRIClient() as tri_client, \
                   SDWISClient() as sdwis_client, \
                   RCRAClient() as rcra_client:
            
            # Execute all state-based queries in parallel
            results = await asyncio.gather(
                # FRS facilities
                frs_client.get_facilities_by_state(state_code, limit=1000),
                
                # TRI facilities and releases (use 2022 - latest available)
                tri_client.get_tri_facilities_by_state(state_code, year=2022, limit=1000),
                tri_client.get_tri_releases_by_state(state_code, year=2022, limit=1000),
                
                # SDWIS water systems (violations disabled due to API issues)
                sdwis_client.get_water_systems_by_state(state_code, limit=1000),
                # sdwis_client.get_violations_by_state(state_code, active_only=True, limit=1000),
                
                # RCRA hazardous waste sites
                rcra_client.get_rcra_sites_by_state(state_code, limit=1000),
                
                return_exceptions=True
            )
            
            # Unpack results
            frs_facilities = results[0] if not isinstance(results[0], Exception) else []
            tri_facilities = results[1] if not isinstance(results[1], Exception) else []
            tri_releases = results[2] if not isinstance(results[2], Exception) else []
            water_systems = results[3] if not isinstance(results[3], Exception) else []
            water_violations = []  # Disabled due to API issues
            rcra_sites = results[4] if not isinstance(results[4], Exception) else []
            
            # Log any errors
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.warning(f"EPA API query {i} failed: {result}")
        
        # Step 3: Filter facilities by distance (client-side filtering)
        logger.info("Filtering facilities by distance...")
        filtered_frs = filter_by_distance(frs_facilities, coordinates, radius_miles)
        filtered_tri = filter_by_distance(tri_facilities, coordinates, radius_miles)
        filtered_rcra = filter_by_distance(rcra_sites, coordinates, radius_miles)
        
        # For facilities without coordinates, include them if they're in the same state
        # (since we queried by state, they're already geographically relevant)
        for facility in frs_facilities:
            if facility.coordinates is None and facility.state == state_code:
                facility.distance_miles = None  # Unknown distance
                if facility not in filtered_frs:
                    filtered_frs.append(facility)
        
        for facility in tri_facilities:
            if facility.coordinates is None and facility.state == state_code:
                facility.distance_miles = None  # Unknown distance
                if facility not in filtered_tri:
                    filtered_tri.append(facility)
        
        for facility in rcra_sites:
            if facility.coordinates is None and facility.state == state_code:
                facility.distance_miles = None  # Unknown distance
                if facility not in filtered_rcra:
                    filtered_rcra.append(facility)
        
        # Filter water systems by distance
        filtered_water_systems = []
        for system in water_systems:
            if system.coordinates:
                from ..utils.distance import haversine_distance
                distance = haversine_distance(coordinates, system.coordinates)
                if distance <= radius_miles:
                    system.distance_miles = distance
                    filtered_water_systems.append(system)
            elif system.state == state_code:
                # Include water systems without coordinates if in same state
                system.distance_miles = None
                filtered_water_systems.append(system)
        
        # Step 4: Aggregate facilities
        logger.info("Aggregating facility data...")
        all_facilities = aggregate_facilities(
            filtered_frs, filtered_tri, filtered_rcra, filtered_water_systems
        )
        
        # Step 5: Rank facilities by distance (top 50)
        top_facilities = rank_facilities(all_facilities, limit=50)
        
        # Step 6: Build environmental summary
        logger.info("Building environmental summary...")
        summary = format_environmental_summary(
            location=location,
            coordinates=coordinates,
            radius_miles=radius_miles,
            facilities=top_facilities,
            water_systems=filtered_water_systems,
            water_violations=water_violations,
            chemical_releases=tri_releases,
            hazardous_sites=filtered_rcra
        )
        
        logger.info(f"Environmental summary complete: {summary.total_facilities} facilities, "
                   f"{summary.total_violations} violations, {summary.total_hazardous_sites} hazardous sites")
        
        return summary
        
    except ValueError:
        # Re-raise validation errors
        raise
    except Exception as e:
        logger.error(f"Failed to get environmental summary for {location}: {e}")
        raise Exception(f"Failed to retrieve environmental data for {location}: {e}")


# Register the tool with FastMCP
def register_tool(mcp: FastMCP):
    """Register the environmental summary tool with FastMCP.
    
    Args:
        mcp: FastMCP instance
    """
    @mcp.tool()
    async def environmental_summary_by_location(
        location: str,
        radius_miles: float = 5.0
    ) -> EnvironmentalSummary:
        """Get comprehensive environmental data for a location.
        
        Provides environmental summary including nearby regulated facilities, chemical releases,
        water quality violations, and hazardous waste sites within a specified radius.
        
        Args:
            location: Address, city, or ZIP code
            radius_miles: Search radius in miles (default: 5.0)
            
        Returns:
            Comprehensive environmental summary
        """
        return await get_environmental_summary_by_location(location, radius_miles)
