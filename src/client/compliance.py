"""Compliance API client for EPA-regulated facilities."""

import logging
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta

from .base import EPAClient, EPAAPIError
from ..models.compliance import ComplianceRecord, ViolationInfo, ComplianceStatus
from ..models.facility import FacilityInfo, FacilityType


logger = logging.getLogger(__name__)


class ComplianceClient(EPAClient):
    """Client for compliance-related EPA API queries."""
    
    async def get_rcra_compliance_by_handler_id(
        self,
        handler_id: str,
        years: int = 5
    ) -> Optional[ComplianceRecord]:
        """Get RCRA compliance data by handler ID.
        
        Args:
            handler_id: RCRA Handler ID
            years: Number of years to look back
            
        Returns:
            ComplianceRecord for RCRA program or None if not found
            
        Raises:
            EPAAPIError: If query fails
        """
        try:
            # Query RCRA handler table for basic compliance info
            filters = {'handler_id': {'equals': handler_id}}
            data = await self.query_table('rcra.rcra_handler', filters=filters, limit=1)
            
            if not data:
                logger.info(f"No RCRA handler found for ID: {handler_id}")
                return None
            
            record = data[0]
            
            # Parse compliance information
            violations = []
            status = ComplianceStatus.UNKNOWN
            
            # Check for compliance indicators in the handler record
            compliance_status = record.get('compliance_status')
            if compliance_status:
                if compliance_status.upper() in ['COMPLIANT', 'IN_COMPLIANCE']:
                    status = ComplianceStatus.COMPLIANT
                elif compliance_status.upper() in ['NON_COMPLIANT', 'VIOLATION']:
                    status = ComplianceStatus.VIOLATION
            
            # Parse last inspection date
            last_inspection_date = None
            if record.get('last_inspection_date'):
                try:
                    last_inspection_date = datetime.strptime(
                        record['last_inspection_date'], '%Y-%m-%d'
                    ).date()
                except (ValueError, TypeError):
                    pass
            
            # Parse last enforcement date
            last_enforcement_date = None
            if record.get('last_enforcement_date'):
                try:
                    last_enforcement_date = datetime.strptime(
                        record['last_enforcement_date'], '%Y-%m-%d'
                    ).date()
                except (ValueError, TypeError):
                    pass
            
            # Filter by years if dates are available
            cutoff_date = date.today() - timedelta(days=years * 365)
            if last_inspection_date and last_inspection_date < cutoff_date:
                last_inspection_date = None
            if last_enforcement_date and last_enforcement_date < cutoff_date:
                last_enforcement_date = None
            
            compliance_record = ComplianceRecord(
                program="RCRA",
                status=status,
                violations=violations,
                last_inspection_date=last_inspection_date,
                last_enforcement_date=last_enforcement_date,
                total_penalties=None,  # Would need separate enforcement table
                violation_count=len(violations)
            )
            
            logger.info(f"Retrieved RCRA compliance for handler {handler_id}: {status}")
            return compliance_record
            
        except Exception as e:
            logger.error(f"Failed to get RCRA compliance for handler {handler_id}: {e}")
            raise EPAAPIError(f"RCRA compliance query failed: {e}")
    
    async def get_tri_compliance_by_facility_id(
        self,
        facility_id: str,
        years: int = 5
    ) -> Optional[ComplianceRecord]:
        """Get TRI compliance data by facility ID.
        
        Args:
            facility_id: TRI Facility ID or FRS Registry ID
            years: Number of years to look back
            
        Returns:
            ComplianceRecord for TRI program or None if not found
            
        Raises:
            EPAAPIError: If query fails
        """
        try:
            # Try TRI facility ID first, then FRS registry ID
            filters = {'tri_facility_id': {'equals': facility_id}}
            data = await self.query_table('tri.tri_facility', filters=filters, limit=1)
            
            # If not found by TRI ID, try FRS registry ID
            if not data:
                filters = {'registry_id': {'equals': facility_id}}
                data = await self.query_table('tri.tri_facility', filters=filters, limit=1)
            
            if not data:
                logger.info(f"No TRI facility found for ID: {facility_id}")
                return None
            
            record = data[0]
            
            # Parse compliance information
            violations = []
            status = ComplianceStatus.UNKNOWN
            
            # Check for compliance indicators
            compliance_status = record.get('compliance_status')
            if compliance_status:
                if compliance_status.upper() in ['COMPLIANT', 'IN_COMPLIANCE']:
                    status = ComplianceStatus.COMPLIANT
                elif compliance_status.upper() in ['NON_COMPLIANT', 'VIOLATION']:
                    status = ComplianceStatus.VIOLATION
            
            # Check facility closure status
            if record.get('fac_closed_ind') == 'Y':
                status = ComplianceStatus.COMPLIANT  # Closed facilities are considered compliant
            
            # Parse last inspection date
            last_inspection_date = None
            if record.get('last_inspection_date'):
                try:
                    last_inspection_date = datetime.strptime(
                        record['last_inspection_date'], '%Y-%m-%d'
                    ).date()
                except (ValueError, TypeError):
                    pass
            
            # Filter by years if date is available
            cutoff_date = date.today() - timedelta(days=years * 365)
            if last_inspection_date and last_inspection_date < cutoff_date:
                last_inspection_date = None
            
            compliance_record = ComplianceRecord(
                program="TRI",
                status=status,
                violations=violations,
                last_inspection_date=last_inspection_date,
                last_enforcement_date=None,  # TRI doesn't typically have enforcement dates
                total_penalties=None,
                violation_count=len(violations)
            )
            
            logger.info(f"Retrieved TRI compliance for facility {facility_id}: {status}")
            return compliance_record
            
        except Exception as e:
            logger.error(f"Failed to get TRI compliance for facility {facility_id}: {e}")
            raise EPAAPIError(f"TRI compliance query failed: {e}")
    
    async def get_compliance_by_registry_id(
        self,
        registry_id: str,
        program: Optional[str] = None,
        years: int = 5
    ) -> List[ComplianceRecord]:
        """Get compliance data by FRS registry ID across programs.
        
        Args:
            registry_id: FRS Registry ID
            program: Optional program filter ('TRI' or 'RCRA')
            years: Number of years to look back
            
        Returns:
            List of ComplianceRecord objects
            
        Raises:
            EPAAPIError: If query fails
        """
        compliance_records = []
        
        try:
            # If program is specified, only query that program
            if program:
                if program.upper() == 'RCRA':
                    # Try to find RCRA handler ID from registry ID
                    rcra_record = await self._get_rcra_handler_by_registry_id(registry_id)
                    if rcra_record:
                        compliance_record = await self.get_rcra_compliance_by_handler_id(
                            rcra_record['handler_id'], years
                        )
                        if compliance_record:
                            compliance_records.append(compliance_record)
                
                elif program.upper() == 'TRI':
                    compliance_record = await self.get_tri_compliance_by_facility_id(
                        registry_id, years
                    )
                    if compliance_record:
                        compliance_records.append(compliance_record)
            
            else:
                # Query both programs
                # Try RCRA first
                try:
                    rcra_record = await self._get_rcra_handler_by_registry_id(registry_id)
                    if rcra_record:
                        compliance_record = await self.get_rcra_compliance_by_handler_id(
                            rcra_record['handler_id'], years
                        )
                        if compliance_record:
                            compliance_records.append(compliance_record)
                except Exception as e:
                    logger.warning(f"RCRA compliance lookup failed for {registry_id}: {e}")
                
                # Try TRI
                try:
                    compliance_record = await self.get_tri_compliance_by_facility_id(
                        registry_id, years
                    )
                    if compliance_record:
                        compliance_records.append(compliance_record)
                except Exception as e:
                    logger.warning(f"TRI compliance lookup failed for {registry_id}: {e}")
            
            logger.info(f"Retrieved {len(compliance_records)} compliance records for registry {registry_id}")
            return compliance_records
            
        except Exception as e:
            logger.error(f"Failed to get compliance for registry {registry_id}: {e}")
            raise EPAAPIError(f"Compliance lookup failed: {e}")
    
    async def _get_rcra_handler_by_registry_id(
        self,
        registry_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get RCRA handler record by FRS registry ID.
        
        Args:
            registry_id: FRS Registry ID
            
        Returns:
            RCRA handler record or None if not found
        """
        try:
            # Query RCRA handler table by registry ID
            filters = {'registry_id': {'equals': registry_id}}
            data = await self.query_table('rcra.rcra_handler', filters=filters, limit=1)
            
            if data:
                return data[0]
            return None
            
        except Exception as e:
            logger.warning(f"Failed to get RCRA handler for registry {registry_id}: {e}")
            return None
