"""Geocoding utilities for EPA Envirofacts MCP Server."""

import asyncio
import logging
from typing import Optional, Dict, Any
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

from config import settings
from ..models.common import Coordinates, LocationInfo


logger = logging.getLogger(__name__)


class GeocodingCache:
    """Simple in-memory cache for geocoding results."""
    
    def __init__(self, max_size: int = 1000):
        """Initialize geocoding cache.
        
        Args:
            max_size: Maximum number of cached results
        """
        self.cache: Dict[str, LocationInfo] = {}
        self.max_size = max_size
    
    def get(self, location: str) -> Optional[LocationInfo]:
        """Get cached location info for location.
        
        Args:
            location: Location string
            
        Returns:
            Cached LocationInfo or None
        """
        return self.cache.get(location.lower().strip())
    
    def set(self, location: str, location_info: LocationInfo):
        """Cache location info for location.
        
        Args:
            location: Location string
            location_info: LocationInfo to cache
        """
        if len(self.cache) >= self.max_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        self.cache[location.lower().strip()] = location_info
    
    def clear(self):
        """Clear all cached results."""
        self.cache.clear()


# Global geocoding cache
_geocoding_cache = GeocodingCache()


async def geocode_location(location: str) -> LocationInfo:
    """Geocode a location string to coordinates and state information.
    
    Args:
        location: Address, city, or ZIP code
        
    Returns:
        LocationInfo object with coordinates and state details
        
    Raises:
        ValueError: If geocoding fails
    """
    # Check cache first
    cached = _geocoding_cache.get(location)
    if cached:
        logger.debug(f"Using cached location info for {location}")
        return cached
    
    try:
        # Create Nominatim geocoder
        geocoder = Nominatim(
            user_agent=settings.geocoding_user_agent,
            timeout=10
        )
        
        logger.info(f"Geocoding location: {location}")
        
        # Geocode with rate limiting (1 request per second for Nominatim)
        await asyncio.sleep(1)  # Rate limiting
        
        # Run geocoding in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: geocoder.geocode(location, exactly_one=True, addressdetails=True)
        )
        
        if result is None:
            raise ValueError(f"Could not geocode location: {location}")
        
        # Extract coordinates
        coordinates = Coordinates(
            latitude=result.latitude,
            longitude=result.longitude
        )
        
        # Extract state information from address details
        address_details = result.raw.get('address', {})
        state_code = None
        state_name = None
        
        # Try to extract state code from ISO3166-2-lvl4 (e.g., "US-NY" -> "NY")
        iso_code = address_details.get('ISO3166-2-lvl4', '')
        if iso_code.startswith('US-'):
            state_code = iso_code[3:]  # Extract "NY" from "US-NY"
        
        # Fallback to state field
        if not state_code:
            state_name = address_details.get('state')
            if state_name:
                # Convert full state name to abbreviation (basic mapping)
                state_code = _get_state_abbreviation(state_name)
        
        # Extract other location details
        county = address_details.get('county')
        country = address_details.get('country')
        
        location_info = LocationInfo(
            coordinates=coordinates,
            state_code=state_code,
            state_name=state_name,
            county=county,
            country=country
        )
        
        # Cache the result
        _geocoding_cache.set(location, location_info)
        
        logger.info(f"Successfully geocoded {location} to {location_info}")
        return location_info
        
    except GeocoderTimedOut as e:
        logger.error(f"Geocoding timeout for {location}: {e}")
        raise ValueError(f"Geocoding timeout for {location}. Please try again.")
        
    except GeocoderServiceError as e:
        logger.error(f"Geocoding service error for {location}: {e}")
        raise ValueError(f"Geocoding service error for {location}. Please check your internet connection.")
        
    except Exception as e:
        logger.error(f"Unexpected geocoding error for {location}: {e}")
        raise ValueError(f"Failed to geocode {location}: {e}")


def _get_state_abbreviation(state_name: str) -> Optional[str]:
    """Convert full state name to 2-letter abbreviation.
    
    Args:
        state_name: Full state name
        
    Returns:
        2-letter state abbreviation or None
    """
    # Basic mapping for common states
    state_mapping = {
        'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA',
        'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'Florida': 'FL', 'Georgia': 'GA',
        'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA',
        'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
        'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO',
        'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ',
        'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH',
        'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
        'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT',
        'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY',
        'District of Columbia': 'DC'
    }
    
    return state_mapping.get(state_name)


def clear_geocoding_cache():
    """Clear the geocoding cache."""
    _geocoding_cache.clear()
    logger.info("Geocoding cache cleared")
