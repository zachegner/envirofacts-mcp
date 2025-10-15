"""SDWIS (Safe Drinking Water Information System) API client."""

import logging
from typing import List, Optional, Dict, Any

from .base import EPAClient, EPAAPIError
from ..models.water import WaterSystem, WaterViolation
from ..models.common import BoundingBox


logger = logging.getLogger(__name__)


class SDWISClient(EPAClient):
    """Client for SDWIS (Safe Drinking Water Information System) queries."""
    
    async def get_water_systems_by_state(
        self,
        state: str,
        limit: int = 1000
    ) -> List[WaterSystem]:
        """Get water systems by state.
        
        Args:
            state: Two-letter state code (e.g., 'NY', 'CA')
            limit: Maximum results to return
            
        Returns:
            List of WaterSystem objects
            
        Raises:
            EPAAPIError: If query fails
        """
        try:
            filters = {'state_code': {'equals': state.upper()}}
            
            data = await self.query_table('sdwis.water_system', filters=filters, limit=limit)
            
            systems = []
            for record in data:
                try:
                    system = self._parse_water_system_record(record)
                    if system:
                        systems.append(system)
                except Exception as e:
                    logger.warning(f"Failed to parse water system record: {e}")
                    continue
            
            logger.info(f"Retrieved {len(systems)} water systems for state {state}")
            return systems
            
        except Exception as e:
            logger.error(f"Failed to get water systems for state {state}: {e}")
            raise EPAAPIError(f"SDWIS water systems state query failed: {e}")
    
    async def get_violations_by_state(
        self,
        state: str,
        active_only: bool = True,
        limit: int = 1000
    ) -> List[WaterViolation]:
        """Get water violations by state.
        
        Args:
            state: Two-letter state code (e.g., 'NY', 'CA')
            active_only: Only return current violations
            limit: Maximum results to return
            
        Returns:
            List of WaterViolation objects
            
        Raises:
            EPAAPIError: If query fails
        """
        try:
            filters = {'state_code': {'equals': state.upper()}}
            
            # Query violations table directly (no joins to avoid 500 errors)
            data = await self.query_table('sdwis.violation', filters=filters, limit=limit)
            
            violations = []
            for record in data:
                try:
                    violation = self._parse_violation_record(record)
                    if violation:
                        violations.append(violation)
                except Exception as e:
                    logger.warning(f"Failed to parse violation record: {e}")
                    continue
            
            logger.info(f"Retrieved {len(violations)} water violations for state {state}")
            return violations
            
        except Exception as e:
            logger.error(f"Failed to get water violations for state {state}: {e}")
            raise EPAAPIError(f"SDWIS violations state query failed: {e}")
    
    async def get_water_systems_in_bbox(
        self,
        bbox: BoundingBox,
        limit: int = 100
    ) -> List[WaterSystem]:
        """Get water systems within a bounding box.
        
        DEPRECATED: Use get_water_systems_by_state() instead for better reliability.
        
        Args:
            bbox: Geographic bounding box
            limit: Maximum results to return
            
        Returns:
            List of WaterSystem objects
            
        Raises:
            EPAAPIError: If query fails
        """
        logger.warning("get_water_systems_in_bbox is deprecated. Use get_water_systems_by_state instead.")
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
            
            data = await self.query_table('sdwis.water_system', filters=filters, limit=limit)
            
            systems = []
            for record in data:
                try:
                    system = self._parse_water_system_record(record)
                    if system:
                        systems.append(system)
                except Exception as e:
                    logger.warning(f"Failed to parse water system record: {e}")
                    continue
            
            logger.info(f"Retrieved {len(systems)} water systems")
            return systems
            
        except Exception as e:
            logger.error(f"Failed to get water systems: {e}")
            raise EPAAPIError(f"SDWIS water systems query failed: {e}")
    
    async def get_violations_in_bbox(
        self,
        bbox: BoundingBox,
        active_only: bool = True,
        limit: int = 100
    ) -> List[WaterViolation]:
        """Get water violations within a bounding box.
        
        DEPRECATED: Use get_violations_by_state() instead for better reliability.
        
        Args:
            bbox: Geographic bounding box
            active_only: Only return current violations
            limit: Maximum results to return
            
        Returns:
            List of WaterViolation objects
            
        Raises:
            EPAAPIError: If query fails
        """
        logger.warning("get_violations_in_bbox is deprecated. Use get_violations_by_state instead.")
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
            
            if active_only:
                filters['is_current_indicator'] = {'equals': 'Y'}
            
            # Join violations with water systems
            joins = ['sdwis.water_system']
            data = await self.query_table('sdwis.violation', filters=filters, joins=joins, limit=limit)
            
            violations = []
            for record in data:
                try:
                    violation = self._parse_violation_record(record)
                    if violation:
                        violations.append(violation)
                except Exception as e:
                    logger.warning(f"Failed to parse violation record: {e}")
                    continue
            
            logger.info(f"Retrieved {len(violations)} water violations")
            return violations
            
        except Exception as e:
            logger.error(f"Failed to get water violations: {e}")
            raise EPAAPIError(f"SDWIS violations query failed: {e}")
    
    def _parse_water_system_record(self, record: Dict[str, Any]) -> Optional[WaterSystem]:
        """Parse water system API record to WaterSystem model.
        
        Args:
            record: Raw SDWIS API record
            
        Returns:
            WaterSystem object or None if invalid
        """
        try:
            # Extract coordinates if available (SDWIS water_system doesn't have lat/lng directly)
            coordinates = None
            # Note: SDWIS water_system table doesn't include lat/lng - would need separate lookup
            
            return WaterSystem(
                system_id=str(record.get('pwsid', '')),
                name=record.get('pws_name') or 'Unknown Water System',
                population_served=self._safe_int(record.get('population_served_count')),
                coordinates=coordinates,
                state=record.get('state_code'),
                county=record.get('county_name'),
                system_type=record.get('pws_type_code'),
                primary_source=record.get('primary_source_code')
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse water system record: {e}")
            return None
    
    def _parse_violation_record(self, record: Dict[str, Any]) -> Optional[WaterViolation]:
        """Parse violation API record to WaterViolation model.
        
        Args:
            record: Raw SDWIS API record with joins
            
        Returns:
            WaterViolation object or None if invalid
        """
        try:
            # Parse violation date
            violation_date = None
            if record.get('violation_date'):
                try:
                    from datetime import datetime
                    violation_date = datetime.strptime(record['violation_date'], '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    pass
            
            return WaterViolation(
                violation_id=str(record.get('violation_id', '')),
                system_id=str(record.get('pwsid', '')),
                system_name=record.get('pws_name', 'Unknown System'),
                violation_type=record.get('violation_code', 'Unknown'),
                contaminant=record.get('contaminant_code'),
                violation_date=violation_date,
                compliance_status=record.get('compliance_status_code'),
                is_current=record.get('is_current_indicator') == 'Y',
                enforcement_action=record.get('enforcement_action_code'),
                population_affected=self._safe_int(record.get('population_served_count'))
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse violation record: {e}")
            return None
    
    def _safe_int(self, value) -> Optional[int]:
        """Safely convert value to integer."""
        if value is None or value == '':
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
