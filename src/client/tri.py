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
    
    async def get_chemical_releases(
        self,
        chemical_name: Optional[str] = None,
        cas_number: Optional[str] = None,
        state: Optional[str] = None,
        county: Optional[str] = None,
        year: Optional[int] = None,
        limit: int = 1000
    ) -> List[ChemicalRelease]:
        """Get TRI chemical releases with flexible search parameters.
        
        Args:
            chemical_name: Chemical name (partial match)
            cas_number: CAS Registry Number (exact match)
            state: Two-letter state code (e.g., 'NY', 'CA')
            county: County name (filtered client-side)
            year: Reporting year (None for most recent available)
            limit: Maximum results to return
            
        Returns:
            List of ChemicalRelease objects
            
        Raises:
            EPAAPIError: If query fails
            ValueError: If no search parameters provided
        """
        # Validate that at least one search parameter is provided
        if not any([chemical_name, cas_number, state, county]):
            raise ValueError("At least one search parameter must be provided (chemical_name, cas_number, state, or county)")
        
        try:
            # Step 1: Query tri_reporting_form with joins if needed
            reporting_filters = {}
            joins = []
            
            if chemical_name:
                reporting_filters['cas_chem_name'] = {'contains': chemical_name}
            
            if cas_number:
                # Join with tri_chem_info to filter by CAS number
                joins.append('tri.tri_chem_info')
                reporting_filters['cas_registry_number'] = {'equals': cas_number}
            
            if year:
                reporting_filters['reporting_year'] = {'equals': year}
            
            # Note: We don't filter by state here because tri_reporting_form doesn't have state_abbr field
            # State filtering will be done later when we check facility information
            
            # Get reporting form records
            reporting_data = await self.query_table('tri.tri_reporting_form', filters=reporting_filters, joins=joins, limit=limit)
            
            if not reporting_data:
                logger.info("No reporting form records found")
                return []
            
            # Extract unique facility IDs and chemical IDs
            facility_ids = set()
            chemical_ids = set()
            doc_ctrl_nums = set()
            
            for record in reporting_data:
                if record.get('tri_facility_id'):
                    facility_ids.add(record['tri_facility_id'])
                if record.get('tri_chem_id'):
                    chemical_ids.add(record['tri_chem_id'])
                if record.get('doc_ctrl_num'):
                    doc_ctrl_nums.add(record['doc_ctrl_num'])
            
            # Step 2: Query tri_facility for facility information
            facility_data = {}
            if facility_ids:
                for facility_id in facility_ids:
                    try:
                        facility_filters = {'tri_facility_id': {'equals': facility_id}}
                        batch_data = await self.query_table('tri.tri_facility', filters=facility_filters, limit=1)
                        if batch_data:
                            facility_data[facility_id] = batch_data[0]
                    except Exception as e:
                        logger.warning(f"Failed to get facility {facility_id}: {e}")
                        continue
            
            # Step 3: Query tri_chem_info for chemical information (only if not already joined)
            chemical_data = {}
            if chemical_ids and not cas_number:  # Skip if we already joined
                for chemical_id in chemical_ids:
                    try:
                        chemical_filters = {'tri_chem_id': {'equals': chemical_id}}
                        batch_data = await self.query_table('tri.tri_chem_info', filters=chemical_filters, limit=1)
                        if batch_data:
                            chemical_data[chemical_id] = batch_data[0]
                    except Exception as e:
                        logger.warning(f"Failed to get chemical {chemical_id}: {e}")
                        continue
            
            # Step 4: Query tri_form_r for release quantities
            release_data = {}
            if doc_ctrl_nums:
                for doc_ctrl_num in doc_ctrl_nums:
                    try:
                        release_filters = {'doc_ctrl_num': {'equals': doc_ctrl_num}}
                        batch_data = await self.query_table('tri.tri_form_r', filters=release_filters, limit=1)
                        if batch_data:
                            release_data[doc_ctrl_num] = batch_data[0]
                    except Exception as e:
                        logger.warning(f"Failed to get release {doc_ctrl_num}: {e}")
                        continue
            
            # Step 5: Combine data and create ChemicalRelease objects
            releases = []
            for record in reporting_data:
                try:
                    # Extract chemical info from joined record if available
                    chemical_record = None
                    if cas_number and 'chem_name' in record:
                        # Chemical data is in the joined record
                        chemical_record = record
                    
                    release = self._parse_tri_release_record_combined(
                        record, 
                        facility_data.get(record.get('tri_facility_id')),
                        chemical_record or chemical_data.get(record.get('tri_chem_id')),
                        release_data.get(record.get('doc_ctrl_num'))
                    )
                    
                    if release:
                        # Apply additional filters
                        if cas_number and release.cas_number != cas_number:
                            continue
                        if state:
                            # Check if facility is in the specified state
                            facility_info = facility_data.get(record.get('tri_facility_id'))
                            if not facility_info or facility_info.get('state_abbr') != state.upper():
                                continue
                        
                        releases.append(release)
                        
                except Exception as e:
                    logger.warning(f"Failed to parse TRI release record: {e}")
                    continue
            
            logger.info(f"Retrieved {len(releases)} TRI chemical releases")
            return releases
            
        except Exception as e:
            logger.error(f"Failed to get TRI chemical releases: {e}")
            raise EPAAPIError(f"TRI chemical releases query failed: {e}")
    
    def _parse_tri_release_record_combined(
        self, 
        reporting_record: Dict[str, Any],
        facility_record: Optional[Dict[str, Any]] = None,
        chemical_record: Optional[Dict[str, Any]] = None,
        release_record: Optional[Dict[str, Any]] = None
    ) -> Optional[ChemicalRelease]:
        """Parse TRI release data from multiple tables into ChemicalRelease model.
        
        Args:
            reporting_record: Raw TRI reporting form record
            facility_record: Raw TRI facility record (optional)
            chemical_record: Raw TRI chemical info record (optional)
            release_record: Raw TRI form R record (optional)
            
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
            
            # Get chemical name and CAS number
            chemical_name = 'Unknown Chemical'
            cas_number = None
            
            if chemical_record:
                chemical_name = chemical_record.get('chem_name', chemical_name)
                cas_number = chemical_record.get('cas_registry_number')
            elif reporting_record.get('cas_chem_name'):
                chemical_name = reporting_record['cas_chem_name']
            
            # Get facility information
            facility_id = reporting_record.get('tri_facility_id', '')
            facility_name = 'Unknown Facility'
            
            if facility_record:
                facility_name = facility_record.get('facility_name', facility_name)
            
            # Get release quantities from form R
            air_release = None
            water_release = None
            land_release = None
            underground_injection = None
            
            if release_record:
                air_release = safe_float(release_record.get('air_total_release'))
                water_release = safe_float(release_record.get('water_total_release'))
                land_release = safe_float(release_record.get('land_total_release'))
                underground_injection = safe_float(release_record.get('uninj_total_release'))
            
            # Calculate total release
            total_release = 0.0
            if air_release:
                total_release += air_release
            if water_release:
                total_release += water_release
            if land_release:
                total_release += land_release
            if underground_injection:
                total_release += underground_injection
            
            return ChemicalRelease(
                facility_id=facility_id,
                facility_name=facility_name,
                chemical_name=chemical_name,
                cas_number=cas_number,
                reporting_year=int(reporting_record.get('reporting_year', 2023)),
                air_release=air_release,
                water_release=water_release,
                land_release=land_release,
                underground_injection=underground_injection,
                release_type='TRI',
                units='pounds'
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse combined TRI release record: {e}")
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
