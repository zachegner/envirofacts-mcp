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
