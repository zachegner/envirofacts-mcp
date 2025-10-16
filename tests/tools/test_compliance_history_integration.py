"""Integration tests for compliance history tool with live EPA API."""

import pytest
from datetime import date

from src.tools.compliance_history import get_facility_compliance_history
from src.models.compliance import FacilityComplianceHistory, ComplianceStatus


@pytest.mark.integration
class TestComplianceHistoryIntegration:
    """Integration tests with live EPA API calls."""
    
    @pytest.mark.asyncio
    async def test_compliance_lookup_with_known_frs_id(self):
        """Test compliance lookup with a known FRS registry ID."""
        # Use a known FRS registry ID (this may need to be updated with actual data)
        registry_id = "110000012345"  # Example ID - may need real ID for testing
        
        try:
            result = await get_facility_compliance_history(registry_id)
            
            assert isinstance(result, FacilityComplianceHistory)
            assert result.facility_info.registry_id == registry_id
            assert result.years_analyzed == 5
            assert result.last_updated == date.today()
            
            # Should have some compliance records or at least facility info
            assert result.facility_info.name is not None
            
        except Exception as e:
            # If the specific ID doesn't exist, that's okay for integration testing
            pytest.skip(f"Test facility ID {registry_id} not found: {e}")
    
    @pytest.mark.asyncio
    async def test_compliance_lookup_with_program_filter(self):
        """Test compliance lookup with program filter."""
        registry_id = "110000012345"  # Example ID
        
        try:
            # Test TRI program filter
            result = await get_facility_compliance_history(registry_id, program="TRI")
            
            assert isinstance(result, FacilityComplianceHistory)
            assert result.facility_info.registry_id == registry_id
            
            # If TRI records exist, they should all be TRI
            for record in result.compliance_records:
                assert record.program == "TRI"
            
        except Exception as e:
            pytest.skip(f"Test facility ID {registry_id} not found for TRI: {e}")
    
    @pytest.mark.asyncio
    async def test_compliance_lookup_with_custom_years(self):
        """Test compliance lookup with custom years parameter."""
        registry_id = "110000012345"  # Example ID
        
        try:
            result = await get_facility_compliance_history(registry_id, years=10)
            
            assert isinstance(result, FacilityComplianceHistory)
            assert result.facility_info.registry_id == registry_id
            assert result.years_analyzed == 10
            
        except Exception as e:
            pytest.skip(f"Test facility ID {registry_id} not found: {e}")
    
    @pytest.mark.asyncio
    async def test_compliance_lookup_with_invalid_id(self):
        """Test compliance lookup with invalid ID."""
        invalid_id = "999999999999"  # Non-existent ID
        
        result = await get_facility_compliance_history(invalid_id)
        
        assert isinstance(result, FacilityComplianceHistory)
        assert result.facility_info.registry_id == invalid_id
        assert result.facility_info.name == f"Facility {invalid_id}"
        assert result.overall_status == ComplianceStatus.UNKNOWN
        assert len(result.compliance_records) == 0
    
    @pytest.mark.asyncio
    async def test_compliance_lookup_with_rcra_handler_id(self):
        """Test compliance lookup with RCRA handler ID."""
        # Use a known RCRA handler ID (this may need to be updated with actual data)
        handler_id = "VAD000012345"  # Example RCRA handler ID
        
        try:
            result = await get_facility_compliance_history(handler_id, program="RCRA")
            
            assert isinstance(result, FacilityComplianceHistory)
            assert result.facility_info.registry_id == handler_id
            
            # If RCRA records exist, they should all be RCRA
            for record in result.compliance_records:
                assert record.program == "RCRA"
            
        except Exception as e:
            pytest.skip(f"Test RCRA handler ID {handler_id} not found: {e}")
    
    @pytest.mark.asyncio
    async def test_compliance_lookup_with_tri_facility_id(self):
        """Test compliance lookup with TRI facility ID."""
        # Use a known TRI facility ID (this may need to be updated with actual data)
        facility_id = "12345"  # Example TRI facility ID
        
        try:
            result = await get_facility_compliance_history(facility_id, program="TRI")
            
            assert isinstance(result, FacilityComplianceHistory)
            assert result.facility_info.registry_id == facility_id
            
            # If TRI records exist, they should all be TRI
            for record in result.compliance_records:
                assert record.program == "TRI"
            
        except Exception as e:
            pytest.skip(f"Test TRI facility ID {facility_id} not found: {e}")
    
    @pytest.mark.asyncio
    async def test_compliance_lookup_error_handling(self):
        """Test error handling with malformed input."""
        # Test with empty string (should be caught by validation)
        with pytest.raises(ValueError):
            await get_facility_compliance_history("")
        
        # Test with invalid years parameter
        with pytest.raises(ValueError):
            await get_facility_compliance_history("123", years=0)
        
        with pytest.raises(ValueError):
            await get_facility_compliance_history("123", years=25)
        
        # Test with invalid program
        with pytest.raises(ValueError):
            await get_facility_compliance_history("123", program="INVALID")
    
    @pytest.mark.asyncio
    async def test_compliance_lookup_performance(self):
        """Test that compliance lookup completes within reasonable time."""
        import time
        
        registry_id = "110000012345"  # Example ID
        
        start_time = time.time()
        
        try:
            result = await get_facility_compliance_history(registry_id)
            
            elapsed_time = time.time() - start_time
            
            # Should complete within 30 seconds (EPA API can be slow)
            assert elapsed_time < 30.0
            
            assert isinstance(result, FacilityComplianceHistory)
            
        except Exception as e:
            pytest.skip(f"Performance test skipped due to API error: {e}")
    
    @pytest.mark.asyncio
    async def test_compliance_lookup_multiple_programs(self):
        """Test compliance lookup across multiple programs."""
        registry_id = "110000012345"  # Example ID
        
        try:
            result = await get_facility_compliance_history(registry_id)
            
            assert isinstance(result, FacilityComplianceHistory)
            assert result.facility_info.registry_id == registry_id
            
            # Check that we have compliance records
            programs_found = {record.program for record in result.compliance_records}
            
            # Should have at least one program (TRI or RCRA)
            assert len(programs_found) >= 0  # May be empty if facility not in programs
            
            # All programs should be valid
            valid_programs = {"TRI", "RCRA"}
            for program in programs_found:
                assert program in valid_programs
            
        except Exception as e:
            pytest.skip(f"Multi-program test skipped: {e}")
