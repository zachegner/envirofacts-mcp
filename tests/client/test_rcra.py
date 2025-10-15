"""Unit tests for RCRA client."""

import pytest
from unittest.mock import AsyncMock

from src.client.rcra import RCRAClient, EPAAPIError
from src.models.common import BoundingBox
from src.models.facility import FacilityInfo, FacilityType


class TestRCRAClient:
    """Test cases for RCRAClient."""
    
    @pytest.fixture
    def client(self):
        """Create RCRAClient instance for testing."""
        return RCRAClient()
    
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
    async def test_get_rcra_sites_in_bbox_success(self, client, sample_bbox, rcra_api_response):
        """Test successful RCRA sites query."""
        client.query_table = AsyncMock(return_value=rcra_api_response)
        
        result = await client.get_rcra_sites_in_bbox(sample_bbox, limit=10)
        
        assert len(result) == 1
        assert isinstance(result[0], FacilityInfo)
        assert result[0].registry_id == "NYD123456789"
        assert result[0].name == "Test Hazardous Waste Facility"
        assert FacilityType.RCRA in result[0].programs
        
        # Verify query parameters
        call_args = client.query_table.call_args
        assert call_args[1]["table"] == "rcra.rcra_handler"
        assert call_args[1]["limit"] == 10
    
    @pytest.mark.asyncio
    async def test_get_rcra_site_by_id_success(self, client, rcra_api_response):
        """Test successful RCRA site lookup by ID."""
        client.query_table = AsyncMock(return_value=rcra_api_response)
        
        result = await client.get_rcra_site_by_id("NYD123456789")
        
        assert result is not None
        assert isinstance(result, FacilityInfo)
        assert result.registry_id == "NYD123456789"
        
        # Verify query parameters
        call_args = client.query_table.call_args
        assert call_args[1]["table"] == "rcra.rcra_handler"
        assert call_args[1]["filters"]["handler_id"]["equals"] == "NYD123456789"
        assert call_args[1]["limit"] == 1
    
    @pytest.mark.asyncio
    async def test_get_rcra_site_by_id_not_found(self, client):
        """Test RCRA site lookup with no results."""
        client.query_table = AsyncMock(return_value=[])
        
        result = await client.get_rcra_site_by_id("nonexistent")
        
        assert result is None
    
    def test_parse_rcra_record_success(self, client, sample_rcra_site):
        """Test successful RCRA record parsing."""
        result = client._parse_rcra_record(sample_rcra_site)
        
        assert result is not None
        assert isinstance(result, FacilityInfo)
        assert result.registry_id == "NYD123456789"
        assert result.name == "Test Hazardous Waste Facility"
        assert result.address == "456 Waste Way, New York, NY 10001"
        assert result.city == "New York"
        assert result.state == "NY"
        assert result.zip_code == "10001"
        assert result.coordinates is not None
        assert result.coordinates.latitude == 40.7128
        assert result.coordinates.longitude == -74.0060
        assert FacilityType.RCRA in result.programs
        assert result.naics_code == "562211"
        assert result.status == "RCRA TSD"
    
    def test_parse_rcra_record_missing_data(self, client):
        """Test RCRA record parsing with missing data."""
        record = {
            "handler_id": "NYD123456789",
            "handler_name": "Test Site"
        }
        
        result = client._parse_rcra_record(record)
        
        assert result is not None
        assert result.registry_id == "NYD123456789"
        assert result.name == "Test Site"
        assert result.address is None
        assert result.coordinates is None
        assert result.status == "RCRA None"
    
    def test_parse_rcra_record_invalid_data(self, client):
        """Test RCRA record parsing with invalid data."""
        record = {"invalid": "data"}
        
        result = client._parse_rcra_record(record)
        
        assert result is None
