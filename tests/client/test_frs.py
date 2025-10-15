"""Unit tests for FRS client."""

import pytest
from unittest.mock import AsyncMock, patch

from src.client.frs import FRSClient, EPAAPIError
from src.models.common import BoundingBox
from src.models.facility import FacilityInfo, FacilityType


class TestFRSClient:
    """Test cases for FRSClient."""
    
    @pytest.fixture
    def client(self):
        """Create FRSClient instance for testing."""
        return FRSClient()
    
    @pytest.fixture
    def sample_bbox(self):
        """Sample bounding box for testing."""
        return BoundingBox(
            min_latitude=40.0,
            max_latitude=41.0,
            min_longitude=-74.0,
            max_longitude=-73.0
        )
    
    @pytest.mark.asyncio
    async def test_get_facilities_by_state_success(self, client, frs_api_response):
        """Test successful facilities query by state."""
        client.query_table = AsyncMock(return_value=frs_api_response)
        
        result = await client.get_facilities_by_state("NY", limit=10)
        
        assert len(result) == 1
        assert isinstance(result[0], FacilityInfo)
        assert result[0].registry_id == "110000123456"
        assert result[0].name == "Test Chemical Plant"
        assert FacilityType.FRS in result[0].programs
        
        # Verify query_table was called with correct parameters
        client.query_table.assert_called_once()
        call_args = client.query_table.call_args
        assert call_args[0][0] == "frs.frs_facility_site"  # table parameter
        assert call_args[1]["filters"]["state_code"]["equals"] == "NY"
        assert call_args[1]["limit"] == 10
    
    @pytest.mark.asyncio
    async def test_get_facilities_by_state_empty_response(self, client):
        """Test facilities query with empty response."""
        client.query_table = AsyncMock(return_value=[])
        
        result = await client.get_facilities_by_state("CA")
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_facilities_by_state_parse_error(self, client):
        """Test facilities query with parsing error."""
        # Invalid record that will cause parsing to fail
        invalid_record = {"invalid": "data"}
        client.query_table = AsyncMock(return_value=[invalid_record])
        
        result = await client.get_facilities_by_state("TX")
        
        # Should return empty list due to parsing failure
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_facilities_by_state_api_error(self, client):
        """Test facilities query with API error."""
        client.query_table = AsyncMock(side_effect=EPAAPIError("API error"))
        
        with pytest.raises(EPAAPIError, match="FRS state query failed"):
            await client.get_facilities_by_state("FL")
    
    @pytest.mark.asyncio
    async def test_get_facilities_in_bbox_success(self, client, sample_bbox, frs_api_response):
        """Test successful facilities query (deprecated bbox method)."""
        client.query_table = AsyncMock(return_value=frs_api_response)
        
        result = await client.get_facilities_in_bbox(sample_bbox, limit=10)
        
        assert len(result) == 1
        assert isinstance(result[0], FacilityInfo)
        assert result[0].registry_id == "110000123456"
        assert result[0].name == "Test Chemical Plant"
        assert FacilityType.FRS in result[0].programs
        
        # Verify query_table was called with correct parameters
        client.query_table.assert_called_once()
        call_args = client.query_table.call_args
        assert call_args[0][0] == "frs.frs_facility_site"  # table parameter
        assert "filters" in call_args[1]
        assert call_args[1]["limit"] == 10
    
    @pytest.mark.asyncio
    async def test_get_facilities_in_bbox_empty_response(self, client, sample_bbox):
        """Test facilities query with empty response (deprecated bbox method)."""
        client.query_table = AsyncMock(return_value=[])
        
        result = await client.get_facilities_in_bbox(sample_bbox)
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_facilities_in_bbox_parse_error(self, client, sample_bbox):
        """Test facilities query with parsing error (deprecated bbox method)."""
        # Invalid record that will cause parsing to fail
        invalid_record = {"invalid": "data"}
        client.query_table = AsyncMock(return_value=[invalid_record])
        
        result = await client.get_facilities_in_bbox(sample_bbox)
        
        # Should return empty list due to parsing failure
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_facilities_in_bbox_api_error(self, client, sample_bbox):
        """Test facilities query with API error (deprecated bbox method)."""
        client.query_table = AsyncMock(side_effect=EPAAPIError("API error"))
        
        with pytest.raises(EPAAPIError, match="FRS query failed"):
            await client.get_facilities_in_bbox(sample_bbox)
    
    @pytest.mark.asyncio
    async def test_get_facility_by_id_success(self, client, frs_api_response):
        """Test successful facility lookup by ID."""
        client.query_table = AsyncMock(return_value=frs_api_response)
        
        result = await client.get_facility_by_id("110000123456")
        
        assert result is not None
        assert isinstance(result, FacilityInfo)
        assert result.registry_id == "110000123456"
        
        # Verify query parameters
        call_args = client.query_table.call_args
        assert call_args[0][0] == "frs.frs_facility_site"  # table parameter
        assert call_args[1]["filters"]["registry_id"]["equals"] == "110000123456"
        assert call_args[1]["limit"] == 1
    
    @pytest.mark.asyncio
    async def test_get_facility_by_id_not_found(self, client):
        """Test facility lookup with no results."""
        client.query_table = AsyncMock(return_value=[])
        
        result = await client.get_facility_by_id("nonexistent")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_facility_by_id_api_error(self, client):
        """Test facility lookup with API error."""
        client.query_table = AsyncMock(side_effect=EPAAPIError("API error"))
        
        with pytest.raises(EPAAPIError, match="FRS facility query failed"):
            await client.get_facility_by_id("110000123456")
    
    def test_parse_frs_record_success(self, client, sample_frs_facility):
        """Test successful FRS record parsing."""
        result = client._parse_frs_record(sample_frs_facility)
        
        assert result is not None
        assert isinstance(result, FacilityInfo)
        assert result.registry_id == "110000123456"
        assert result.name == "Test Chemical Plant"
        assert result.address == "123 Industrial Blvd, New York, NY 10001"
        assert result.city == "New York"
        assert result.state == "NY"
        assert result.zip_code == "10001"
        assert result.coordinates is not None
        assert result.coordinates.latitude == 40.7128
        assert result.coordinates.longitude == -74.0060
        assert FacilityType.FRS in result.programs
        assert result.naics_code == "325199"
        assert result.status == "Active"
    
    def test_parse_frs_record_missing_coordinates(self, client):
        """Test FRS record parsing with missing coordinates."""
        record = {
            "registry_id": "110000123456",
            "facility_name": "Test Facility",
            "city_name": "New York",
            "state_abbr": "NY"
        }
        
        result = client._parse_frs_record(record)
        
        assert result is not None
        assert result.coordinates is None
    
    def test_parse_frs_record_invalid_data(self, client):
        """Test FRS record parsing with invalid data."""
        record = {"invalid": "data"}
        
        result = client._parse_frs_record(record)
        
        assert result is None
    
    def test_parse_frs_record_empty_name(self, client):
        """Test FRS record parsing with empty facility name."""
        record = {
            "registry_id": "110000123456",
            "facility_name": "",
            "city_name": "New York"
        }
        
        result = client._parse_frs_record(record)
        
        assert result is not None
        assert result.name == "Unknown Facility"
    
    def test_parse_frs_record_missing_address(self, client):
        """Test FRS record parsing with missing address components."""
        record = {
            "registry_id": "110000123456",
            "facility_name": "Test Facility"
        }
        
        result = client._parse_frs_record(record)
        
        assert result is not None
        assert result.address is None
        assert result.city is None
        assert result.state is None
        assert result.zip_code is None
