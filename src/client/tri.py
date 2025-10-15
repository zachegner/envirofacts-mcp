"""TRI (Toxics Release Inventory) API client."""

import logging
from typing import List, Optional, Dict, Any

from .base import EPAClient, EPAAPIError
from ..models.facility import FacilityInfo, FacilityType
from ..models.releases import ChemicalRelease
from ..models.common import BoundingBox, Coordinates


logger = logging.getLogger(__name__)


class TRIClient(EPAClient):
    """Client for TRI (Toxics Release Inventory) queries."""
    
    async def get_tri_facilities_by_state(
        self,
        state: str,
        year: int = 2022,
        limit: int = 1000
    ) -> List[FacilityInfo]:
        """Get TRI facilities by state.
        
        Args:
            state: Two-letter state code (e.g., 'NY', 'CA')
            year: Reporting year (default: 2022, latest available)
            limit: Maximum results to return
            
        Returns:
            List of FacilityInfo objects
            
        Raises:
            EPAAPIError: If query fails
        """
        try:
            filters = {'state_abbr': {'equals': state.upper()}}
            
            # Query TRI facility table directly (no joins to avoid 500 errors)
            data = await self.query_table('tri.tri_facility', filters=filters, limit=limit)
            
            facilities = []
            for record in data:
                try:
                    facility = self._parse_tri_facility_record(record)
                    if facility:
                        facilities.append(facility)
                except Exception as e:
                    logger.warning(f"Failed to parse TRI facility record: {e}")
                    continue
            
            logger.info(f"Retrieved {len(facilities)} TRI facilities for state {state}")
            return facilities
            
        except Exception as e:
            logger.error(f"Failed to get TRI facilities for state {state}: {e}")
            raise EPAAPIError(f"TRI facilities state query failed: {e}")
    
    async def get_tri_releases_by_state(
        self,
        state: str,
        year: int = 2022,
        limit: int = 1000
    ) -> List[ChemicalRelease]:
        """Get TRI chemical releases by state.
        
        Args:
            state: Two-letter state code (e.g., 'NY', 'CA')
            year: Reporting year (default: 2022, latest available)
            limit: Maximum results to return
            
        Returns:
            List of ChemicalRelease objects
            
        Raises:
            EPAAPIError: If query fails
        """
        try:
            filters = {'state_abbr': {'equals': state.upper()}}
            
            # Query TRI facility table directly (no joins to avoid 500 errors)
            data = await self.query_table('tri.tri_facility', filters=filters, limit=limit)
            
            releases = []
            for record in data:
                try:
                    release = self._parse_tri_release_record(record)
                    if release:
                        releases.append(release)
                except Exception as e:
                    logger.warning(f"Failed to parse TRI release record: {e}")
                    continue
            
            logger.info(f"Retrieved {len(releases)} TRI chemical releases for state {state}")
            return releases
            
        except Exception as e:
            logger.error(f"Failed to get TRI releases for state {state}: {e}")
            raise EPAAPIError(f"TRI releases state query failed: {e}")
    
    async def get_tri_facilities_in_bbox(
        self,
        bbox: BoundingBox,
        year: int = 2023,
        limit: int = 100
    ) -> List[FacilityInfo]:
        """Get TRI facilities within a bounding box.
        
        DEPRECATED: Use get_tri_facilities_by_state() instead for better reliability.
        
        Args:
            bbox: Geographic bounding box
            year: Reporting year
            limit: Maximum results to return
            
        Returns:
            List of FacilityInfo objects
            
        Raises:
            EPAAPIError: If query fails
        """
        logger.warning("get_tri_facilities_in_bbox is deprecated. Use get_tri_facilities_by_state instead.")
        try:
            filters = {
                'fac_latitude': {
                    'greaterThan': bbox.min_latitude,
                    'lessThan': bbox.max_latitude
                },
                'fac_longitude': {
                    'greaterThan': bbox.min_longitude,
                    'lessThan': bbox.max_longitude
                },
                'reporting_year': {'equals': year}
            }
            
            # Join with TRI reporting form to get facilities with releases
            joins = ['tri.tri_reporting_form']
            data = await self.query_table('tri.tri_facility', filters=filters, joins=joins, limit=limit)
            
            facilities = []
            for record in data:
                try:
                    facility = self._parse_tri_facility_record(record)
                    if facility:
                        facilities.append(facility)
                except Exception as e:
                    logger.warning(f"Failed to parse TRI facility record: {e}")
                    continue
            
            logger.info(f"Retrieved {len(facilities)} TRI facilities")
            return facilities
            
        except Exception as e:
            logger.error(f"Failed to get TRI facilities: {e}")
            raise EPAAPIError(f"TRI facilities query failed: {e}")
    
    async def get_tri_releases(
        self,
        bbox: BoundingBox,
        year: int = 2023,
        limit: int = 100
    ) -> List[ChemicalRelease]:
        """Get TRI chemical releases within a bounding box.
        
        DEPRECATED: Use get_tri_releases_by_state() instead for better reliability.
        
        Args:
            bbox: Geographic bounding box
            year: Reporting year
            limit: Maximum results to return
            
        Returns:
            List of ChemicalRelease objects
            
        Raises:
            EPAAPIError: If query fails
        """
        logger.warning("get_tri_releases is deprecated. Use get_tri_releases_by_state instead.")
        try:
            filters = {
                'fac_latitude': {
                    'greaterThan': bbox.min_latitude,
                    'lessThan': bbox.max_latitude
                },
                'fac_longitude': {
                    'greaterThan': bbox.min_longitude,
                    'lessThan': bbox.max_longitude
                },
                'reporting_year': {'equals': year}
            }
            
            # Join TRI facility with reporting form and chemical info
            joins = ['tri.tri_reporting_form', 'tri.tri_chem_info']
            data = await self.query_table('tri.tri_facility', filters=filters, joins=joins, limit=limit)
            
            releases = []
            for record in data:
                try:
                    release = self._parse_tri_release_record(record)
                    if release:
                        releases.append(release)
                except Exception as e:
                    logger.warning(f"Failed to parse TRI release record: {e}")
                    continue
            
            logger.info(f"Retrieved {len(releases)} TRI chemical releases")
            return releases
            
        except Exception as e:
            logger.error(f"Failed to get TRI releases: {e}")
            raise EPAAPIError(f"TRI releases query failed: {e}")
    
    def _parse_tri_facility_record(self, record: Dict[str, Any]) -> Optional[FacilityInfo]:
        """Parse TRI facility API record to FacilityInfo model.
        
        Args:
            record: Raw TRI API record
            
        Returns:
            FacilityInfo object or None if invalid
        """
        try:
            # Extract coordinates - use pref_latitude/pref_longitude (standardized decimal degrees)
            coordinates = None
            if record.get('pref_latitude') and record.get('pref_longitude'):
                coordinates = Coordinates(
                    latitude=float(record['pref_latitude']),
                    longitude=float(record['pref_longitude'])
                )
            elif record.get('fac_fac_latitude') and record.get('fac_fac_longitude'):
                # Fallback to fac_fac_latitude/fac_fac_longitude if pref_* not available
                coordinates = Coordinates(
                    latitude=float(record['fac_fac_latitude']),
                    longitude=float(record['fac_fac_longitude'])
                )
            
            # Extract address components
            address_parts = []
            if record.get('street_address'):
                address_parts.append(record['street_address'])
            if record.get('city_name'):
                address_parts.append(record['city_name'])
            if record.get('state_abbr'):
                address_parts.append(record['state_abbr'])
            if record.get('zip_code'):
                address_parts.append(record['zip_code'])
            
            address = ', '.join(address_parts) if address_parts else None
            
            return FacilityInfo(
                registry_id=str(record.get('tri_facility_id', '')),
                name=record.get('facility_name', 'Unknown TRI Facility'),
                address=address,
                city=record.get('city_name'),
                state=record.get('state_abbr'),
                zip_code=record.get('zip_code'),
                coordinates=coordinates,
                programs=[FacilityType.TRI],
                naics_code=record.get('naics_code'),
                naics_description=record.get('naics_description'),
                status=record.get('fac_closed_ind')
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse TRI facility record: {e}")
            return None
    
    def _parse_tri_release_record(self, record: Dict[str, Any]) -> Optional[ChemicalRelease]:
        """Parse TRI release API record to ChemicalRelease model.
        
        Args:
            record: Raw TRI API record with joins
            
        Returns:
            ChemicalRelease object or None if invalid
        """
        try:
            # Extract release quantities (convert to float, handle None)
            def safe_float(value):
                if value is None or value == '':
                    return None
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return None
            
            return ChemicalRelease(
                facility_id=str(record.get('registry_id', '')),
                facility_name=record.get('facility_name', 'Unknown Facility'),
                chemical_name=record.get('chemical_name', 'Unknown Chemical'),
                cas_number=record.get('cas_number'),
                reporting_year=int(record.get('reporting_year', 2023)),
                air_release=safe_float(record.get('total_air_release')),
                water_release=safe_float(record.get('total_water_release')),
                land_release=safe_float(record.get('total_land_release')),
                underground_injection=safe_float(record.get('total_underground_injection')),
                release_type=record.get('release_type'),
                units='pounds'
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse TRI release record: {e}")
            return None
