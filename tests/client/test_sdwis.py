"""Unit tests for SDWIS client."""

import pytest
from unittest.mock import AsyncMock

from src.client.sdwis import SDWISClient, EPAAPIError
from src.models.common import BoundingBox
from src.models.water import WaterSystem, WaterViolation


class TestSDWISClient:
    """Test cases for SDWISClient."""
    
    @pytest.fixture
    def client(self):
        """Create SDWISClient instance for testing."""
        return SDWISClient()
    
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
    async def test_get_water_systems_in_bbox_success(self, client, sample_bbox, sdwis_api_response):
        """Test successful water systems query."""
        client.query_table = AsyncMock(return_value=sdwis_api_response)
        
        result = await client.get_water_systems_in_bbox(sample_bbox, limit=10)
        
        assert len(result) == 1
        assert isinstance(result[0], WaterSystem)
        assert result[0].system_id == "NY1234567"
        assert result[0].name == "New York City Water System"
        assert result[0].population_served == 8000000
        
        # Verify query parameters
        call_args = client.query_table.call_args
        assert call_args[1]["table"] == "sdwis.water_system"
        assert call_args[1]["limit"] == 10
    
    @pytest.mark.asyncio
    async def test_get_violations_in_bbox_success(self, client, sample_bbox, sample_water_violation):
        """Test successful violations query."""
        client.query_table = AsyncMock(return_value=[sample_water_violation])
        
        result = await client.get_violations_in_bbox(sample_bbox, active_only=True, limit=10)
        
        assert len(result) == 1
        assert isinstance(result[0], WaterViolation)
        assert result[0].violation_id == "V123456789"
        assert result[0].system_id == "NY1234567"
        assert result[0].violation_type == "MCL"
        assert result[0].is_current is True
        
        # Verify query parameters
        call_args = client.query_table.call_args
        assert call_args[1]["table"] == "sdwis.violation"
        assert call_args[1]["joins"] == ["sdwis.water_system"]
        assert call_args[1]["filters"]["is_current_indicator"]["equals"] == "Y"
    
    @pytest.mark.asyncio
    async def test_get_violations_in_bbox_all(self, client, sample_bbox):
        """Test violations query with active_only=False."""
        client.query_table = AsyncMock(return_value=[])
        
        await client.get_violations_in_bbox(sample_bbox, active_only=False)
        
        # Verify query parameters don't include current indicator filter
        call_args = client.query_table.call_args
        assert "is_current_indicator" not in call_args[1]["filters"]
    
    def test_parse_water_system_record_success(self, client, sample_water_system):
        """Test successful water system record parsing."""
        result = client._parse_water_system_record(sample_water_system)
        
        assert result is not None
        assert isinstance(result, WaterSystem)
        assert result.system_id == "NY1234567"
        assert result.name == "New York City Water System"
        assert result.population_served == 8000000
        assert result.coordinates is not None
        assert result.coordinates.latitude == 40.7128
        assert result.coordinates.longitude == -74.0060
        assert result.state == "NY"
        assert result.county == "New York"
        assert result.system_type == "CWS"
        assert result.primary_source == "SW"
    
    def test_parse_water_system_record_missing_coordinates(self, client):
        """Test water system record parsing with missing coordinates."""
        record = {
            "pws_id": "NY1234567",
            "pws_name": "Test System"
        }
        
        result = client._parse_water_system_record(record)
        
        assert result is not None
        assert result.coordinates is None
    
    def test_parse_violation_record_success(self, client, sample_water_violation):
        """Test successful violation record parsing."""
        result = client._parse_violation_record(sample_water_violation)
        
        assert result is not None
        assert isinstance(result, WaterViolation)
        assert result.violation_id == "V123456789"
        assert result.system_id == "NY1234567"
        assert result.system_name == "New York City Water System"
        assert result.violation_type == "MCL"
        assert result.contaminant == "ARSENIC"
        assert result.violation_date is not None
        assert result.violation_date.year == 2023
        assert result.violation_date.month == 6
        assert result.violation_date.day == 15
        assert result.compliance_status == "Open"
        assert result.is_current is True
        assert result.enforcement_action == "None"
        assert result.population_affected == 8000000
    
    def test_parse_violation_record_invalid_date(self, client):
        """Test violation record parsing with invalid date."""
        record = {
            "violation_id": "V123456789",
            "pws_id": "NY1234567",
            "pws_name": "Test System",
            "violation_code": "MCL",
            "violation_date": "invalid-date"
        }
        
        result = client._parse_violation_record(record)
        
        assert result is not None
        assert result.violation_date is None
    
    def test_safe_int_valid(self, client):
        """Test safe_int with valid values."""
        assert client._safe_int("123") == 123
        assert client._safe_int(456) == 456
        assert client._safe_int(0) == 0
    
    def test_safe_int_invalid(self, client):
        """Test safe_int with invalid values."""
        assert client._safe_int(None) is None
        assert client._safe_int("") is None
        assert client._safe_int("invalid") is None
        assert client._safe_int("12.5") is None
