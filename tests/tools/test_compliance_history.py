"""Unit tests for compliance history tool."""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import date, datetime

from src.tools.compliance_history import get_facility_compliance_history
from src.models.compliance import FacilityComplianceHistory, ComplianceRecord, ComplianceStatus
from src.models.facility import FacilityInfo, FacilityType
from src.client import EPAAPIError


class TestComplianceHistoryTool:
    """Test cases for compliance history tool."""
    
    @pytest.fixture
    def mock_facility_info(self):
        """Mock facility info for testing."""
        return FacilityInfo(
            registry_id="110000012345",
            name="Test Chemical Facility",
            address="123 Test St, Test City, TS",
            city="Test City",
            state="TS",
            zip_code="12345",
            programs=[FacilityType.FRS, FacilityType.TRI],
            naics_code="325199",
            naics_description="All Other Basic Organic Chemical Manufacturing"
        )
    
    @pytest.fixture
    def mock_compliance_record(self):
        """Mock compliance record for testing."""
        return ComplianceRecord(
            program="TRI",
            status=ComplianceStatus.COMPLIANT,
            violations=[],
            last_inspection_date=date(2023, 6, 15),
            last_enforcement_date=None,
            total_penalties=None,
            violation_count=0
        )
    
    @pytest.mark.asyncio
    async def test_basic_compliance_lookup(self, mock_facility_info, mock_compliance_record):
        """Test basic compliance lookup with registry_id."""
        with patch('src.tools.compliance_history.FRSClient') as mock_frs, \
             patch('src.tools.compliance_history.ComplianceClient') as mock_compliance:
            
            # Mock FRS client
            mock_frs_instance = AsyncMock()
            mock_frs_instance.get_facility_by_id.return_value = mock_facility_info
            mock_frs.return_value.__aenter__.return_value = mock_frs_instance
            
            # Mock compliance client
            mock_compliance_instance = AsyncMock()
            mock_compliance_instance.get_compliance_by_registry_id.return_value = [mock_compliance_record]
            mock_compliance.return_value.__aenter__.return_value = mock_compliance_instance
            
            result = await get_facility_compliance_history("110000012345")
            
            assert isinstance(result, FacilityComplianceHistory)
            assert result.facility_info.registry_id == "110000012345"
            assert result.facility_info.name == "Test Chemical Facility"
            assert len(result.compliance_records) == 1
            assert result.compliance_records[0].program == "TRI"
            assert result.overall_status == ComplianceStatus.COMPLIANT
            assert result.total_violations == 0
            assert result.years_analyzed == 5
    
    @pytest.mark.asyncio
    async def test_program_specific_filtering(self, mock_facility_info, mock_compliance_record):
        """Test program-specific filtering."""
        with patch('src.tools.compliance_history.FRSClient') as mock_frs, \
             patch('src.tools.compliance_history.ComplianceClient') as mock_compliance:
            
            # Mock FRS client
            mock_frs_instance = AsyncMock()
            mock_frs_instance.get_facility_by_id.return_value = mock_facility_info
            mock_frs.return_value.__aenter__.return_value = mock_frs_instance
            
            # Mock compliance client
            mock_compliance_instance = AsyncMock()
            mock_compliance_instance.get_compliance_by_registry_id.return_value = [mock_compliance_record]
            mock_compliance.return_value.__aenter__.return_value = mock_compliance_instance
            
            result = await get_facility_compliance_history("110000012345", program="TRI")
            
            # Verify compliance client was called with program filter
            mock_compliance_instance.get_compliance_by_registry_id.assert_called_once_with(
                registry_id="110000012345",
                program="TRI",
                years=5
            )
            
            assert result.overall_status == ComplianceStatus.COMPLIANT
    
    @pytest.mark.asyncio
    async def test_years_parameter_filtering(self, mock_facility_info, mock_compliance_record):
        """Test years parameter filtering."""
        with patch('src.tools.compliance_history.FRSClient') as mock_frs, \
             patch('src.tools.compliance_history.ComplianceClient') as mock_compliance:
            
            # Mock FRS client
            mock_frs_instance = AsyncMock()
            mock_frs_instance.get_facility_by_id.return_value = mock_facility_info
            mock_frs.return_value.__aenter__.return_value = mock_frs_instance
            
            # Mock compliance client
            mock_compliance_instance = AsyncMock()
            mock_compliance_instance.get_compliance_by_registry_id.return_value = [mock_compliance_record]
            mock_compliance.return_value.__aenter__.return_value = mock_compliance_instance
            
            result = await get_facility_compliance_history("110000012345", years=10)
            
            # Verify compliance client was called with years parameter
            mock_compliance_instance.get_compliance_by_registry_id.assert_called_once_with(
                registry_id="110000012345",
                program=None,
                years=10
            )
            
            assert result.years_analyzed == 10
    
    @pytest.mark.asyncio
    async def test_fallback_logic_frs_to_program_specific(self):
        """Test fallback logic when FRS lookup fails."""
        with patch('src.tools.compliance_history.FRSClient') as mock_frs, \
             patch('src.tools.compliance_history.ComplianceClient') as mock_compliance:
            
            # Mock FRS client to fail
            mock_frs_instance = AsyncMock()
            mock_frs_instance.get_facility_by_id.return_value = None
            mock_frs.return_value.__aenter__.return_value = mock_frs_instance
            
            # Mock compliance client
            mock_compliance_instance = AsyncMock()
            mock_compliance_instance.get_compliance_by_registry_id.return_value = []
            mock_compliance.return_value.__aenter__.return_value = mock_compliance_instance
            
            result = await get_facility_compliance_history("110000012345")
            
            # Should create basic facility info when FRS lookup fails
            assert result.facility_info.registry_id == "110000012345"
            assert result.facility_info.name == "Facility 110000012345"
            assert result.overall_status == ComplianceStatus.UNKNOWN
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_id(self):
        """Test error handling with invalid ID."""
        with patch('src.tools.compliance_history.FRSClient') as mock_frs, \
             patch('src.tools.compliance_history.ComplianceClient') as mock_compliance:
            
            # Mock FRS client
            mock_frs_instance = AsyncMock()
            mock_frs_instance.get_facility_by_id.return_value = None
            mock_frs.return_value.__aenter__.return_value = mock_frs_instance
            
            # Mock compliance client to raise error
            mock_compliance_instance = AsyncMock()
            mock_compliance_instance.get_compliance_by_registry_id.side_effect = EPAAPIError("API Error")
            mock_compliance.return_value.__aenter__.return_value = mock_compliance_instance
            
            with pytest.raises(Exception) as exc_info:
                await get_facility_compliance_history("invalid_id")
            
            assert "Failed to retrieve compliance data" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_empty_results(self, mock_facility_info):
        """Test handling of empty compliance results."""
        with patch('src.tools.compliance_history.FRSClient') as mock_frs, \
             patch('src.tools.compliance_history.ComplianceClient') as mock_compliance:
            
            # Mock FRS client
            mock_frs_instance = AsyncMock()
            mock_frs_instance.get_facility_by_id.return_value = mock_facility_info
            mock_frs.return_value.__aenter__.return_value = mock_frs_instance
            
            # Mock compliance client to return empty results
            mock_compliance_instance = AsyncMock()
            mock_compliance_instance.get_compliance_by_registry_id.return_value = []
            mock_compliance.return_value.__aenter__.return_value = mock_compliance_instance
            
            result = await get_facility_compliance_history("110000012345")
            
            assert result.facility_info.registry_id == "110000012345"
            assert len(result.compliance_records) == 0
            assert result.overall_status == ComplianceStatus.UNKNOWN
            assert result.total_violations == 0
    
    @pytest.mark.asyncio
    async def test_multiple_programs_compliance(self, mock_facility_info):
        """Test compliance history with multiple programs."""
        rcra_record = ComplianceRecord(
            program="RCRA",
            status=ComplianceStatus.VIOLATION,
            violations=[],
            last_inspection_date=date(2023, 3, 10),
            last_enforcement_date=date(2023, 4, 15),
            total_penalties=5000.0,
            violation_count=2
        )
        
        tri_record = ComplianceRecord(
            program="TRI",
            status=ComplianceStatus.COMPLIANT,
            violations=[],
            last_inspection_date=date(2023, 6, 15),
            last_enforcement_date=None,
            total_penalties=None,
            violation_count=0
        )
        
        with patch('src.tools.compliance_history.FRSClient') as mock_frs, \
             patch('src.tools.compliance_history.ComplianceClient') as mock_compliance:
            
            # Mock FRS client
            mock_frs_instance = AsyncMock()
            mock_frs_instance.get_facility_by_id.return_value = mock_facility_info
            mock_frs.return_value.__aenter__.return_value = mock_frs_instance
            
            # Mock compliance client
            mock_compliance_instance = AsyncMock()
            mock_compliance_instance.get_compliance_by_registry_id.return_value = [rcra_record, tri_record]
            mock_compliance.return_value.__aenter__.return_value = mock_compliance_instance
            
            result = await get_facility_compliance_history("110000012345")
            
            assert len(result.compliance_records) == 2
            assert result.overall_status == ComplianceStatus.VIOLATION  # Should be violation due to RCRA
            assert result.total_violations == 2
            assert result.total_penalties == 5000.0
    
    def test_parameter_validation(self):
        """Test parameter validation."""
        # Test empty registry_id
        with pytest.raises(ValueError) as exc_info:
            pytest.runner.run_async(get_facility_compliance_history(""))
        assert "Registry ID cannot be empty" in str(exc_info.value)
        
        # Test invalid years
        with pytest.raises(ValueError) as exc_info:
            pytest.runner.run_async(get_facility_compliance_history("123", years=0))
        assert "Years must be between 1 and 20" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            pytest.runner.run_async(get_facility_compliance_history("123", years=25))
        assert "Years must be between 1 and 20" in str(exc_info.value)
        
        # Test invalid program
        with pytest.raises(ValueError) as exc_info:
            pytest.runner.run_async(get_facility_compliance_history("123", program="INVALID"))
        assert "Program must be 'TRI' or 'RCRA'" in str(exc_info.value)
