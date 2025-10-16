"""Unit tests for search facilities tool."""

import pytest
from unittest.mock import AsyncMock, patch

from src.tools.search_facilities import search_facilities
from src.models.facility import FacilityInfo, FacilityType
from src.client import EPAAPIError


class TestSearchFacilities:
    """Test cases for search_facilities function."""
    
    @pytest.mark.asyncio
    async def test_successful_search_by_facility_name(self):
        """Test successful search by facility name."""
        mock_facilities = [
            FacilityInfo(
                registry_id="12345",
                name="Test Chemical Plant",
                address="123 Main St, Test City, NY 12345",
                city="Test City",
                state="NY",
                zip_code="12345",
                programs=[FacilityType.FRS],
                naics_code="325199",
                naics_description="All Other Basic Organic Chemical Manufacturing"
            )
        ]
        
        with patch('src.tools.search_facilities.FRSClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.search_facilities = AsyncMock(
                return_value=mock_facilities
            )
            
            result = await search_facilities(facility_name="Chemical")
            
            assert len(result) == 1
            assert result[0].name == "Test Chemical Plant"
            assert result[0].state == "NY"
            
            # Verify the client was called with correct parameters
            mock_client.return_value.__aenter__.return_value.search_facilities.assert_called_once_with(
                facility_name="Chemical",
                naics_code=None,
                state=None,
                zip_code=None,
                city=None,
                limit=100
            )
    
    @pytest.mark.asyncio
    async def test_successful_search_by_state(self):
        """Test successful search by state."""
        mock_facilities = [
            FacilityInfo(
                registry_id="67890",
                name="NY Manufacturing Co",
                address="456 Oak Ave, Albany, NY 12201",
                city="Albany",
                state="NY",
                zip_code="12201",
                programs=[FacilityType.FRS]
            )
        ]
        
        with patch('src.tools.search_facilities.FRSClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.search_facilities = AsyncMock(
                return_value=mock_facilities
            )
            
            result = await search_facilities(state="NY")
            
            assert len(result) == 1
            assert result[0].state == "NY"
            
            mock_client.return_value.__aenter__.return_value.search_facilities.assert_called_once_with(
                facility_name=None,
                naics_code=None,
                state="NY",
                zip_code=None,
                city=None,
                limit=100
            )
    
    @pytest.mark.asyncio
    async def test_successful_search_by_zip_code(self):
        """Test successful search by ZIP code."""
        mock_facilities = [
            FacilityInfo(
                registry_id="11111",
                name="Local Facility",
                address="789 Pine St, Boston, MA 02101",
                city="Boston",
                state="MA",
                zip_code="02101",
                programs=[FacilityType.FRS]
            )
        ]
        
        with patch('src.tools.search_facilities.FRSClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.search_facilities = AsyncMock(
                return_value=mock_facilities
            )
            
            result = await search_facilities(zip_code="02101")
            
            assert len(result) == 1
            assert result[0].zip_code == "02101"
            
            mock_client.return_value.__aenter__.return_value.search_facilities.assert_called_once_with(
                facility_name=None,
                naics_code=None,
                state=None,
                zip_code="02101",
                city=None,
                limit=100
            )
    
    @pytest.mark.asyncio
    async def test_successful_search_by_city(self):
        """Test successful search by city."""
        mock_facilities = [
            FacilityInfo(
                registry_id="22222",
                name="Chicago Industrial",
                address="321 Lake St, Chicago, IL 60601",
                city="Chicago",
                state="IL",
                zip_code="60601",
                programs=[FacilityType.FRS]
            )
        ]
        
        with patch('src.tools.search_facilities.FRSClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.search_facilities = AsyncMock(
                return_value=mock_facilities
            )
            
            result = await search_facilities(city="Chicago")
            
            assert len(result) == 1
            assert result[0].city == "Chicago"
            
            mock_client.return_value.__aenter__.return_value.search_facilities.assert_called_once_with(
                facility_name=None,
                naics_code=None,
                state=None,
                zip_code=None,
                city="Chicago",
                limit=100
            )
    
    @pytest.mark.asyncio
    async def test_successful_search_by_naics_code(self):
        """Test successful search by NAICS code."""
        mock_facilities = [
            FacilityInfo(
                registry_id="33333",
                name="Chemical Manufacturer",
                address="555 Industrial Blvd, Houston, TX 77001",
                city="Houston",
                state="TX",
                zip_code="77001",
                programs=[FacilityType.FRS],
                naics_code="325199",
                naics_description="All Other Basic Organic Chemical Manufacturing"
            )
        ]
        
        with patch('src.tools.search_facilities.FRSClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.search_facilities = AsyncMock(
                return_value=mock_facilities
            )
            
            result = await search_facilities(naics_code="325199")
            
            assert len(result) == 1
            assert result[0].naics_code == "325199"
            
            mock_client.return_value.__aenter__.return_value.search_facilities.assert_called_once_with(
                facility_name=None,
                naics_code="325199",
                state=None,
                zip_code=None,
                city=None,
                limit=100
            )
    
    @pytest.mark.asyncio
    async def test_successful_search_multiple_parameters(self):
        """Test successful search with multiple parameters."""
        mock_facilities = [
            FacilityInfo(
                registry_id="44444",
                name="CA Chemical Plant",
                address="777 Sunset Blvd, Los Angeles, CA 90001",
                city="Los Angeles",
                state="CA",
                zip_code="90001",
                programs=[FacilityType.FRS]
            )
        ]
        
        with patch('src.tools.search_facilities.FRSClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.search_facilities = AsyncMock(
                return_value=mock_facilities
            )
            
            result = await search_facilities(facility_name="Chemical", state="CA", city="Los Angeles")
            
            assert len(result) == 1
            assert result[0].name == "CA Chemical Plant"
            
            mock_client.return_value.__aenter__.return_value.search_facilities.assert_called_once_with(
                facility_name="Chemical",
                naics_code=None,
                state="CA",
                zip_code=None,
                city="Los Angeles",
                limit=100
            )
    
    @pytest.mark.asyncio
    async def test_no_search_parameters(self):
        """Test validation error when no search parameters provided."""
        with pytest.raises(ValueError, match="At least one search parameter must be provided"):
            await search_facilities()
    
    @pytest.mark.asyncio
    async def test_empty_facility_name(self):
        """Test validation error with empty facility name."""
        with pytest.raises(ValueError, match="Facility name cannot be empty"):
            await search_facilities(facility_name="")
        
        with pytest.raises(ValueError, match="Facility name cannot be empty"):
            await search_facilities(facility_name="   ")
    
    @pytest.mark.asyncio
    async def test_empty_naics_code(self):
        """Test validation error with empty NAICS code."""
        with pytest.raises(ValueError, match="NAICS code cannot be empty"):
            await search_facilities(naics_code="")
        
        with pytest.raises(ValueError, match="NAICS code cannot be empty"):
            await search_facilities(naics_code="   ")
    
    @pytest.mark.asyncio
    async def test_empty_city(self):
        """Test validation error with empty city."""
        with pytest.raises(ValueError, match="City cannot be empty"):
            await search_facilities(city="")
        
        with pytest.raises(ValueError, match="City cannot be empty"):
            await search_facilities(city="   ")
    
    @pytest.mark.asyncio
    async def test_invalid_state_code(self):
        """Test validation error with invalid state code."""
        with pytest.raises(ValueError, match="State code must be 2 letters"):
            await search_facilities(state="CALIFORNIA")
        
        with pytest.raises(ValueError, match="State code must be 2 letters"):
            await search_facilities(state="C")
        
        with pytest.raises(ValueError, match="State code must be 2 letters"):
            await search_facilities(state="123")
    
    @pytest.mark.asyncio
    async def test_invalid_zip_code(self):
        """Test validation error with invalid ZIP code."""
        with pytest.raises(ValueError, match="ZIP code must be 5 digits or less"):
            await search_facilities(zip_code="123456")
        
        with pytest.raises(ValueError, match="ZIP code must be 5 digits or less"):
            await search_facilities(zip_code="123456789")
    
    @pytest.mark.asyncio
    async def test_invalid_limit(self):
        """Test validation error with invalid limit."""
        with pytest.raises(ValueError, match="Limit must be between 1 and 1000"):
            await search_facilities(facility_name="Test", limit=0)
        
        with pytest.raises(ValueError, match="Limit must be between 1 and 1000"):
            await search_facilities(facility_name="Test", limit=1001)
    
    @pytest.mark.asyncio
    async def test_state_normalization(self):
        """Test that state codes are normalized to uppercase."""
        with patch('src.tools.search_facilities.FRSClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.search_facilities = AsyncMock(
                return_value=[]
            )
            
            await search_facilities(state="ny")
            
            mock_client.return_value.__aenter__.return_value.search_facilities.assert_called_once_with(
                facility_name=None,
                naics_code=None,
                state="NY",
                zip_code=None,
                city=None,
                limit=100
            )
    
    @pytest.mark.asyncio
    async def test_parameter_trimming(self):
        """Test that parameters are trimmed of whitespace."""
        with patch('src.tools.search_facilities.FRSClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.search_facilities = AsyncMock(
                return_value=[]
            )
            
            await search_facilities(
                facility_name="  Chemical  ",
                naics_code="  325199  ",
                state="  NY  ",
                zip_code="  12345  ",
                city="  Test City  "
            )
            
            mock_client.return_value.__aenter__.return_value.search_facilities.assert_called_once_with(
                facility_name="Chemical",
                naics_code="325199",
                state="NY",
                zip_code="12345",
                city="Test City",
                limit=100
            )
    
    @pytest.mark.asyncio
    async def test_empty_results(self):
        """Test handling of empty results."""
        with patch('src.tools.search_facilities.FRSClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.search_facilities = AsyncMock(
                return_value=[]
            )
            
            result = await search_facilities(facility_name="Nonexistent Facility")
            
            assert result == []
    
    @pytest.mark.asyncio
    async def test_epa_api_error(self):
        """Test handling of EPA API errors."""
        with patch('src.tools.search_facilities.FRSClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.search_facilities = AsyncMock(
                side_effect=EPAAPIError("API connection failed")
            )
            
            with pytest.raises(Exception, match="Failed to search facilities"):
                await search_facilities(facility_name="Test")
    
    @pytest.mark.asyncio
    async def test_unexpected_error(self):
        """Test handling of unexpected errors."""
        with patch('src.tools.search_facilities.FRSClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.search_facilities = AsyncMock(
                side_effect=RuntimeError("Unexpected error")
            )
            
            with pytest.raises(Exception, match="Failed to search facilities"):
                await search_facilities(facility_name="Test")
    
    @pytest.mark.asyncio
    async def test_zip_code_with_leading_zeros(self):
        """Test ZIP codes with leading zeros."""
        mock_facilities = [
            FacilityInfo(
                registry_id="55555",
                name="MA Facility",
                address="123 Main St, Worcester, MA 01510",
                city="Worcester",
                state="MA",
                zip_code="01510",
                programs=[FacilityType.FRS]
            )
        ]
        
        with patch('src.tools.search_facilities.FRSClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.search_facilities = AsyncMock(
                return_value=mock_facilities
            )
            
            # Test with string ZIP code with leading zero
            result = await search_facilities(zip_code="01510")
            assert len(result) == 1
            assert result[0].zip_code == "01510"
            
            mock_client.return_value.__aenter__.return_value.search_facilities.assert_called_with(
                facility_name=None,
                naics_code=None,
                state=None,
                zip_code="01510",
                city=None,
                limit=100
            )
    
    @pytest.mark.asyncio
    async def test_numeric_zip_code_input(self):
        """Test numeric ZIP code input gets zero-padded."""
        mock_facilities = [
            FacilityInfo(
                registry_id="66666",
                name="Test Facility",
                address="456 Oak St, Test City, MA 01510",
                city="Test City",
                state="MA",
                zip_code="01510",
                programs=[FacilityType.FRS]
            )
        ]
        
        with patch('src.tools.search_facilities.FRSClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.search_facilities = AsyncMock(
                return_value=mock_facilities
            )
            
            # Test with numeric ZIP code (1510) - should become "01510"
            result = await search_facilities(zip_code=1510)
            assert len(result) == 1
            
            mock_client.return_value.__aenter__.return_value.search_facilities.assert_called_with(
                facility_name=None,
                naics_code=None,
                state=None,
                zip_code="01510",
                city=None,
                limit=100
            )
    
    @pytest.mark.asyncio
    async def test_zip_code_edge_cases(self):
        """Test ZIP code edge cases."""
        mock_facilities = []
        
        with patch('src.tools.search_facilities.FRSClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.search_facilities = AsyncMock(
                return_value=mock_facilities
            )
            
            # Test 4-digit ZIP code (should be padded to 5 digits)
            await search_facilities(zip_code="1234")
            mock_client.return_value.__aenter__.return_value.search_facilities.assert_called_with(
                facility_name=None,
                naics_code=None,
                state=None,
                zip_code="01234",
                city=None,
                limit=100
            )
            
            # Test single digit ZIP code
            await search_facilities(zip_code="1")
            mock_client.return_value.__aenter__.return_value.search_facilities.assert_called_with(
                facility_name=None,
                naics_code=None,
                state=None,
                zip_code="00001",
                city=None,
                limit=100
            )
            
            # Test ZIP code with non-digit characters
            await search_facilities(zip_code="123-45")
            mock_client.return_value.__aenter__.return_value.search_facilities.assert_called_with(
                facility_name=None,
                naics_code=None,
                state=None,
                zip_code="12345",
                city=None,
                limit=100
            )
    
    @pytest.mark.asyncio
    async def test_zip_code_00000(self):
        """Test edge case ZIP code 00000."""
        mock_facilities = []
        
        with patch('src.tools.search_facilities.FRSClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.search_facilities = AsyncMock(
                return_value=mock_facilities
            )
            
            await search_facilities(zip_code="00000")
            mock_client.return_value.__aenter__.return_value.search_facilities.assert_called_with(
                facility_name=None,
                naics_code=None,
                state=None,
                zip_code="00000",
                city=None,
                limit=100
            )
            
    @pytest.mark.asyncio
    async def test_custom_limit(self):
        """Test custom limit parameter."""
        with patch('src.tools.search_facilities.FRSClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.search_facilities = AsyncMock(
                return_value=[]
            )
            
            await search_facilities(facility_name="Test", limit=50)
            
            mock_client.return_value.__aenter__.return_value.search_facilities.assert_called_once_with(
                facility_name="Test",
                naics_code=None,
                state=None,
                zip_code=None,
                city=None,
                limit=50
            )
