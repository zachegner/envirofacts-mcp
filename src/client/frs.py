"""FRS (Facility Registry Service) API client."""

import logging
from typing import List, Optional, Dict, Any

from .base import EPAClient, EPAAPIError
from ..models.facility import FacilityInfo, FacilityType
from ..models.common import BoundingBox


logger = logging.getLogger(__name__)


class FRSClient(EPAClient):
    """Client for FRS (Facility Registry Service) queries."""
    
    async def get_facilities_by_state(
        self,
        state: str,
        limit: int = 1000
    ) -> List[FacilityInfo]:
        """Get FRS facilities by state.
        
        Args:
            state: Two-letter state code (e.g., 'NY', 'CA')
            limit: Maximum results to return
            
        Returns:
            List of FacilityInfo objects
            
        Raises:
            EPAAPIError: If query fails
        """
        try:
            filters = {'state_code': {'equals': state.upper()}}
            
            data = await self.query_table('frs.frs_facility_site', filters=filters, limit=limit)
            
            facilities = []
            for record in data:
                try:
                    facility = self._parse_frs_record(record)
                    if facility:
                        facilities.append(facility)
                except Exception as e:
                    logger.warning(f"Failed to parse FRS record: {e}")
                    continue
            
            logger.info(f"Retrieved {len(facilities)} FRS facilities for state {state}")
            return facilities
            
        except Exception as e:
            logger.error(f"Failed to get FRS facilities for state {state}: {e}")
            raise EPAAPIError(f"FRS state query failed: {e}")
    
    async def get_facilities_in_bbox(
        self,
        bbox: BoundingBox,
        limit: int = 100
    ) -> List[FacilityInfo]:
        """Get FRS facilities within a bounding box.
        
        DEPRECATED: Use get_facilities_by_state() instead for better reliability.
        
        Args:
            bbox: Geographic bounding box
            limit: Maximum results to return
            
        Returns:
            List of FacilityInfo objects
            
        Raises:
            EPAAPIError: If query fails
        """
        logger.warning("get_facilities_in_bbox is deprecated. Use get_facilities_by_state instead.")
        try:
            filters = {
                'latitude': {
                    'greaterThan': bbox.min_latitude,
                    'lessThan': bbox.max_latitude
                },
                'longitude': {
                    'greaterThan': bbox.min_longitude,
                    'lessThan': bbox.max_longitude
                }
            }
            
            data = await self.query_table('frs.frs_facility_site', filters=filters, limit=limit)
            
            facilities = []
            for record in data:
                try:
                    facility = self._parse_frs_record(record)
                    if facility:
                        facilities.append(facility)
                except Exception as e:
                    logger.warning(f"Failed to parse FRS record: {e}")
                    continue
            
            logger.info(f"Retrieved {len(facilities)} FRS facilities")
            return facilities
            
        except Exception as e:
            logger.error(f"Failed to get FRS facilities: {e}")
            raise EPAAPIError(f"FRS query failed: {e}")
    
    async def get_facility_by_id(self, registry_id: str) -> Optional[FacilityInfo]:
        """Get single FRS facility by registry ID.
        
        Args:
            registry_id: FRS Registry ID
            
        Returns:
            FacilityInfo object or None if not found
            
        Raises:
            EPAAPIError: If query fails
        """
        try:
            filters = {'registry_id': {'equals': registry_id}}
            data = await self.query_table('frs.frs_facility_site', filters=filters, limit=1)
            
            if data:
                return self._parse_frs_record(data[0])
            return None
            
        except Exception as e:
            logger.error(f"Failed to get FRS facility {registry_id}: {e}")
            raise EPAAPIError(f"FRS facility query failed: {e}")
    
    async def search_facilities(
        self,
        facility_name: Optional[str] = None,
        naics_code: Optional[str] = None,
        state: Optional[str] = None,
        zip_code: Optional[str] = None,
        city: Optional[str] = None,
        limit: int = 100
    ) -> List[FacilityInfo]:
        """Search for FRS facilities using various filters.
        
        Args:
            facility_name: Partial or full facility name (uses contains matching)
            naics_code: NAICS industry code
            state: Two-letter state code
            zip_code: 5-digit ZIP code
            city: City name
            limit: Maximum results to return (default: 100)
            
        Returns:
            List of FacilityInfo objects
            
        Raises:
            EPAAPIError: If query fails
            ValueError: If no search parameters provided
        """
        # Validate that at least one search parameter is provided
        if not any([facility_name, naics_code, state, zip_code, city]):
            raise ValueError("At least one search parameter must be provided")
        
        try:
            # Build filters dictionary
            filters = {}
            
            if facility_name:
                filters['primary_name'] = {'contains': facility_name.strip()}
            
            if naics_code:
                filters['naics_code'] = {'equals': naics_code.strip()}
            
            if state:
                # Normalize state code to uppercase
                state_code = state.strip().upper()
                if len(state_code) != 2:
                    raise ValueError(f"State code must be 2 letters, got: {state_code}")
                filters['state_code'] = {'equals': state_code}
            
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
                filters['postal_code'] = {'equals': zip_code}
            
            if city:
                filters['city_name'] = {'contains': city.strip()}
            
            # Query the FRS facility_site table
            data = await self.query_table('frs.frs_facility_site', filters=filters, limit=limit)
            
            facilities = []
            for record in data:
                try:
                    facility = self._parse_frs_record(record)
                    if facility:
                        facilities.append(facility)
                except Exception as e:
                    logger.warning(f"Failed to parse FRS record: {e}")
                    continue
            
            logger.info(f"Retrieved {len(facilities)} facilities matching search criteria")
            return facilities
            
        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Failed to search FRS facilities: {e}")
            raise EPAAPIError(f"FRS search failed: {e}")
    
    def _parse_frs_record(self, record: Dict[str, Any]) -> Optional[FacilityInfo]:
        """Parse FRS API record to FacilityInfo model.
        
        Args:
            record: Raw FRS API record
            
        Returns:
            FacilityInfo object or None if invalid
        """
        try:
            # Extract coordinates if available (FRS facility_site doesn't have lat/lng directly)
            coordinates = None
            # Note: FRS facility_site table doesn't include lat/lng - would need separate lookup
            
            # Extract address components from FRS facility_site response
            address_parts = []
            if record.get('location_address'):
                address_parts.append(record['location_address'])
            if record.get('city_name'):
                address_parts.append(record['city_name'])
            if record.get('state_code'):
                address_parts.append(record['state_code'])
            if record.get('postal_code'):
                address_parts.append(record['postal_code'])
            
            address = ', '.join(address_parts) if address_parts else None
            
            return FacilityInfo(
                registry_id=str(record.get('registry_id', '')),
                name=record.get('primary_name') or 'Unknown Facility',
                address=address,
                city=record.get('city_name'),
                state=record.get('state_code'),
                zip_code=record.get('postal_code'),
                coordinates=coordinates,
                programs=[FacilityType.FRS],  # FRS facilities are in FRS program
                naics_code=record.get('naics_code'),
                naics_description=record.get('naics_description'),
                status=record.get('operating_status')
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse FRS record: {e}")
            return None
