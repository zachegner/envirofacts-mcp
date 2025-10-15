"""RCRA (Resource Conservation and Recovery Act) API client."""

import logging
from typing import List, Optional, Dict, Any

from .base import EPAClient, EPAAPIError
from ..models.facility import FacilityInfo, FacilityType
from ..models.common import BoundingBox


logger = logging.getLogger(__name__)


class RCRAClient(EPAClient):
    """Client for RCRA (Resource Conservation and Recovery Act) queries."""
    
    async def get_rcra_sites_by_state(
        self,
        state: str,
        limit: int = 1000
    ) -> List[FacilityInfo]:
        """Get RCRA hazardous waste sites by state.
        
        Args:
            state: Two-letter state code (e.g., 'NY', 'CA')
            limit: Maximum results to return
            
        Returns:
            List of FacilityInfo objects
            
        Raises:
            EPAAPIError: If query fails
        """
        try:
            filters = {'activity_location': {'equals': state.upper()}}
            
            data = await self.query_table('rcra.br_gm_waste_code', filters=filters, limit=limit)
            
            sites = []
            for record in data:
                try:
                    site = self._parse_rcra_record(record)
                    if site:
                        sites.append(site)
                except Exception as e:
                    logger.warning(f"Failed to parse RCRA record: {e}")
                    continue
            
            logger.info(f"Retrieved {len(sites)} RCRA sites for state {state}")
            return sites
            
        except Exception as e:
            logger.error(f"Failed to get RCRA sites for state {state}: {e}")
            raise EPAAPIError(f"RCRA sites state query failed: {e}")
    
    async def get_rcra_sites_in_bbox(
        self,
        bbox: BoundingBox,
        limit: int = 100
    ) -> List[FacilityInfo]:
        """Get RCRA hazardous waste sites within a bounding box.
        
        DEPRECATED: Use get_rcra_sites_by_state() instead for better reliability.
        
        Args:
            bbox: Geographic bounding box
            limit: Maximum results to return
            
        Returns:
            List of FacilityInfo objects
            
        Raises:
            EPAAPIError: If query fails
        """
        logger.warning("get_rcra_sites_in_bbox is deprecated. Use get_rcra_sites_by_state instead.")
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
            
            data = await self.query_table('rcra.br_gm_waste_code', filters=filters, limit=limit)
            
            sites = []
            for record in data:
                try:
                    site = self._parse_rcra_record(record)
                    if site:
                        sites.append(site)
                except Exception as e:
                    logger.warning(f"Failed to parse RCRA record: {e}")
                    continue
            
            logger.info(f"Retrieved {len(sites)} RCRA sites")
            return sites
            
        except Exception as e:
            logger.error(f"Failed to get RCRA sites: {e}")
            raise EPAAPIError(f"RCRA sites query failed: {e}")
    
    async def get_rcra_site_by_id(self, handler_id: str) -> Optional[FacilityInfo]:
        """Get single RCRA site by handler ID.
        
        Args:
            handler_id: RCRA Handler ID
            
        Returns:
            FacilityInfo object or None if not found
            
        Raises:
            EPAAPIError: If query fails
        """
        try:
            filters = {'handler_id': {'equals': handler_id}}
            data = await self.query_table('rcra.br_gm_waste_code', filters=filters, limit=1)
            
            if data:
                return self._parse_rcra_record(data[0])
            return None
            
        except Exception as e:
            logger.error(f"Failed to get RCRA site {handler_id}: {e}")
            raise EPAAPIError(f"RCRA site query failed: {e}")
    
    def _parse_rcra_record(self, record: Dict[str, Any]) -> Optional[FacilityInfo]:
        """Parse RCRA API record to FacilityInfo model.
        
        Args:
            record: Raw RCRA API record
            
        Returns:
            FacilityInfo object or None if invalid
        """
        try:
            # Extract coordinates if available (RCRA br_gm_waste_code doesn't have lat/lng directly)
            coordinates = None
            # Note: RCRA br_gm_waste_code table doesn't include lat/lng - would need separate lookup
            
            # Extract address components from RCRA br_gm_waste_code response
            address_parts = []
            if record.get('activity_location'):
                address_parts.append(record['activity_location'])
            
            address = ', '.join(address_parts) if address_parts else None
            
            # Determine site type from waste code
            site_type = record.get('waste_code', 'Unknown')
            if site_type:
                site_type = f"RCRA Waste Code {site_type}"
            
            return FacilityInfo(
                registry_id=str(record.get('handler_id', '')),
                name=f"RCRA Handler {record.get('handler_id', 'Unknown')}",
                address=address,
                city=None,  # Not available in this table
                state=record.get('activity_location'),
                zip_code=None,  # Not available in this table
                coordinates=coordinates,
                programs=[FacilityType.RCRA],
                naics_code=None,  # Not available in this table
                naics_description=None,  # Not available in this table
                status=site_type
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse RCRA record: {e}")
            return None
