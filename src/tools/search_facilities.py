"""Tool 2: Search Facilities."""

import logging
from typing import List, Optional

from fastmcp import FastMCP

from ..models.facility import FacilityInfo
from ..client import FRSClient, EPAAPIError


logger = logging.getLogger(__name__)


async def search_facilities(
    facility_name: Optional[str] = None,
    naics_code: Optional[str] = None,
    state: Optional[str] = None,
    zip_code: Optional[str] = None,
    city: Optional[str] = None,
    limit: int = 100
) -> List[FacilityInfo]:
    """Search for EPA-regulated facilities using various filters.
    
    This tool allows searching for facilities in the EPA's Facility Registry Service (FRS)
    using facility name, NAICS code, state, ZIP code, or city. At least one search parameter
    must be provided.
    
    Args:
        facility_name: Partial or full facility name (uses contains matching)
        naics_code: NAICS industry code
        state: Two-letter state code (e.g., 'NY', 'CA')
        zip_code: 5-digit ZIP code
        city: City name
        limit: Maximum results to return (default: 100, max: 1000)
    
    Returns:
        List of FacilityInfo objects containing:
        - Registry ID and facility name
        - Address and location information
        - Active EPA programs (TRI, RCRA, etc.)
        - Industry codes and descriptions
        - Facility status
    
    Raises:
        ValueError: If no search parameters provided or invalid parameter format
        Exception: If EPA API query fails
    
    Example:
        >>> facilities = await search_facilities(facility_name="Chemical", state="NY")
        >>> print(f"Found {len(facilities)} facilities")
        >>> for facility in facilities[:3]:
        ...     print(f"{facility.name} - {facility.city}, {facility.state}")
    """
    # Validate input parameters
    if not any([facility_name, naics_code, state, zip_code, city]):
        raise ValueError("At least one search parameter must be provided")
    
    if not (1 <= limit <= 1000):
        raise ValueError("Limit must be between 1 and 1000")
    
    # Clean and validate individual parameters
    if facility_name:
        facility_name = facility_name.strip()
        if not facility_name:
            raise ValueError("Facility name cannot be empty")
    
    if naics_code:
        naics_code = naics_code.strip()
        if not naics_code:
            raise ValueError("NAICS code cannot be empty")
    
    if state:
        state = state.strip().upper()
        if len(state) != 2:
            raise ValueError(f"State code must be 2 letters, got: {state}")
    
    if zip_code:
        # Convert to string and strip whitespace
        zip_code_str = str(zip_code).strip()
        # Remove any non-digit characters
        zip_code_clean = ''.join(c for c in zip_code_str if c.isdigit())
        # Validate length
        if len(zip_code_clean) > 5:
            raise ValueError(f"ZIP code must be 5 digits or less, got: {zip_code_clean}")
        # Zero-pad to 5 digits
        zip_code = zip_code_clean.zfill(5)
    
    if city:
        city = city.strip()
        if not city:
            raise ValueError("City cannot be empty")
    
    try:
        logger.info(f"Searching facilities with filters: facility_name={facility_name}, "
                   f"naics_code={naics_code}, state={state}, zip_code={zip_code}, city={city}, limit={limit}")
        
        # Use FRS client to search facilities
        async with FRSClient() as client:
            facilities = await client.search_facilities(
                facility_name=facility_name,
                naics_code=naics_code,
                state=state,
                zip_code=zip_code,
                city=city,
                limit=limit
            )
        
        logger.info(f"Found {len(facilities)} facilities matching search criteria")
        return facilities
        
    except ValueError:
        # Re-raise validation errors
        raise
    except EPAAPIError as e:
        logger.error(f"EPA API error during facility search: {e}")
        raise Exception(f"Failed to search facilities: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during facility search: {e}")
        raise Exception(f"Failed to search facilities: {e}")


# Register the tool with FastMCP
def register_tool(mcp: FastMCP):
    """Register the search facilities tool with FastMCP.
    
    Args:
        mcp: FastMCP instance
    """
    @mcp.tool()
    async def search_facilities_tool(
        facility_name: Optional[str] = None,
        naics_code: Optional[str] = None,
        state: Optional[str] = None,
        zip_code: Optional[str] = None,
        city: Optional[str] = None,
        limit: int = 100
    ) -> List[FacilityInfo]:
        """Search for EPA-regulated facilities using various filters.
        
        Search for facilities in the EPA's Facility Registry Service using facility name,
        NAICS code, state, ZIP code, or city. At least one search parameter must be provided.
        
        Args:
            facility_name: Partial or full facility name (uses contains matching)
            naics_code: NAICS industry code
            state: Two-letter state code (e.g., 'NY', 'CA')
            zip_code: 5-digit ZIP code
            city: City name
            limit: Maximum results to return (default: 100)
            
        Returns:
            List of facilities with registry ID, name, address, coordinates,
            active programs, industry codes, and status information
        """
        return await search_facilities(
            facility_name=facility_name,
            naics_code=naics_code,
            state=state,
            zip_code=zip_code,
            city=city,
            limit=limit
        )
