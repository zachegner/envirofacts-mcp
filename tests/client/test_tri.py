"""Unit tests for TRI client."""

import pytest
from unittest.mock import AsyncMock

from src.client.tri import TRIClient, EPAAPIError
from src.models.common import BoundingBox
from src.models.facility import FacilityInfo, FacilityType
from src.models.releases import ChemicalRelease


class TestTRIClient:
    """Test cases for TRIClient."""
    
    @pytest.fixture
    def client(self):
        """Create TRIClient instance for testing."""
        return TRIClient()
    
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
    async def test_get_tri_facilities_by_state_success(self, client, tri_api_response):
        """Test successful TRI facilities query by state."""
        client.query_table = AsyncMock(return_value=tri_api_response)
        
        result = await client.get_tri_facilities_by_state("NY", year=2022, limit=10)
        
        assert len(result) == 1
        assert isinstance(result[0], FacilityInfo)
        assert result[0].registry_id == "110000123456"
        assert FacilityType.TRI in result[0].programs
        
        # Verify query parameters
        call_args = client.query_table.call_args
        assert call_args[1]["table"] == "tri.tri_facility"
        assert call_args[1]["filters"]["state_abbr"]["equals"] == "NY"
        assert call_args[1]["limit"] == 10
    
    @pytest.mark.asyncio
    async def test_get_tri_releases_by_state_success(self, client, tri_api_response):
        """Test successful TRI releases query by state."""
        client.query_table = AsyncMock(return_value=tri_api_response)
        
        result = await client.get_tri_releases_by_state("NY", year=2022, limit=10)
        
        assert len(result) == 1
        assert isinstance(result[0], ChemicalRelease)
        assert result[0].facility_id == "110000123456"
        assert result[0].chemical_name == "Benzene"
        assert result[0].cas_number == "71-43-2"
        assert result[0].reporting_year == 2023
        assert result[0].air_release == 1500.5
        assert result[0].water_release == 250.0
        assert result[0].land_release == 100.0
        assert result[0].underground_injection == 0.0
        
        # Verify query parameters
        call_args = client.query_table.call_args
        assert call_args[1]["table"] == "tri.tri_facility"
        assert call_args[1]["filters"]["state_abbr"]["equals"] == "NY"
    
    @pytest.mark.asyncio
    async def test_get_tri_facilities_in_bbox_success(self, client, sample_bbox, tri_api_response):
        """Test successful TRI facilities query (deprecated bbox method)."""
        client.query_table = AsyncMock(return_value=tri_api_response)
        
        result = await client.get_tri_facilities_in_bbox(sample_bbox, year=2023, limit=10)
        
        assert len(result) == 1
        assert isinstance(result[0], FacilityInfo)
        assert result[0].registry_id == "110000123456"
        assert FacilityType.TRI in result[0].programs
        
        # Verify query parameters
        call_args = client.query_table.call_args
        assert call_args[1]["table"] == "tri.tri_facility"
        assert call_args[1]["joins"] == ["tri.tri_reporting_form"]
        assert call_args[1]["limit"] == 10
    
    @pytest.mark.asyncio
    async def test_get_tri_releases_success(self, client, sample_bbox, tri_api_response):
        """Test successful TRI releases query (deprecated bbox method)."""
        client.query_table = AsyncMock(return_value=tri_api_response)
        
        result = await client.get_tri_releases(sample_bbox, year=2023, limit=10)
        
        assert len(result) == 1
        assert isinstance(result[0], ChemicalRelease)
        assert result[0].facility_id == "110000123456"
        assert result[0].chemical_name == "Benzene"
        assert result[0].cas_number == "71-43-2"
        assert result[0].reporting_year == 2023
        assert result[0].air_release == 1500.5
        assert result[0].water_release == 250.0
        assert result[0].land_release == 100.0
        assert result[0].underground_injection == 0.0
        
        # Verify query parameters
        call_args = client.query_table.call_args
        assert call_args[1]["table"] == "tri.tri_facility"
        assert call_args[1]["joins"] == ["tri.tri_reporting_form", "tri.tri_chem_info"]
    
    def test_parse_tri_facility_record_success(self, client, sample_tri_facility):
        """Test successful TRI facility record parsing."""
        result = client._parse_tri_facility_record(sample_tri_facility)
        
        assert result is not None
        assert isinstance(result, FacilityInfo)
        assert result.registry_id == "110000123456"
        assert result.name == "Test Chemical Plant"
        assert FacilityType.TRI in result.programs
    
    def test_parse_tri_release_record_success(self, client, sample_tri_release):
        """Test successful TRI release record parsing."""
        result = client._parse_tri_release_record(sample_tri_release)
        
        assert result is not None
        assert isinstance(result, ChemicalRelease)
        assert result.facility_id == "110000123456"
        assert result.chemical_name == "Benzene"
        assert result.cas_number == "71-43-2"
        assert result.reporting_year == 2023
        assert result.air_release == 1500.5
        assert result.water_release == 250.0
        assert result.land_release == 100.0
        assert result.underground_injection == 0.0
        assert result.units == "pounds"
    
    def test_parse_tri_release_record_none_values(self, client):
        """Test TRI release record parsing with None values."""
        record = {
            "registry_id": "110000123456",
            "facility_name": "Test Facility",
            "chemical_name": "Test Chemical",
            "reporting_year": "2023",
            "total_air_release": "",
            "total_water_release": None,
            "total_land_release": "0",
            "total_underground_injection": "invalid"
        }
        
        result = client._parse_tri_release_record(record)
        
        assert result is not None
        assert result.air_release is None
        assert result.water_release is None
        assert result.land_release == 0.0
        assert result.underground_injection is None
