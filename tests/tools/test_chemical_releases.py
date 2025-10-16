"""Unit tests for chemical release tool."""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from src.tools.chemical_releases import get_chemical_release_data
from src.models.releases import (
    ChemicalRelease, ChemicalReleaseData, FacilityReleaseInfo, 
    ChemicalAggregation
)


class TestChemicalReleaseTool:
    """Test cases for chemical release tool."""
    
    @pytest.fixture
    def sample_releases(self):
        """Sample chemical releases for testing."""
        return [
            ChemicalRelease(
                facility_id="110000123456",
                facility_name="Test Chemical Plant A",
                chemical_name="Benzene",
                cas_number="71-43-2",
                reporting_year=2022,
                air_release=1000.0,
                water_release=200.0,
                land_release=50.0,
                underground_injection=0.0,
                release_type="On-site",
                units="pounds"
            ),
            ChemicalRelease(
                facility_id="110000123456",
                facility_name="Test Chemical Plant A",
                chemical_name="Lead",
                cas_number="7439-92-1",
                reporting_year=2022,
                air_release=500.0,
                water_release=100.0,
                land_release=25.0,
                underground_injection=0.0,
                release_type="On-site",
                units="pounds"
            ),
            ChemicalRelease(
                facility_id="110000789012",
                facility_name="Test Chemical Plant B",
                chemical_name="Benzene",
                cas_number="71-43-2",
                reporting_year=2022,
                air_release=800.0,
                water_release=150.0,
                land_release=30.0,
                underground_injection=0.0,
                release_type="On-site",
                units="pounds"
            )
        ]
    
    @pytest.fixture
    def mock_tri_client(self):
        """Mock TRI client for testing."""
        mock_client = AsyncMock()
        return mock_client
    
    @pytest.mark.asyncio
    async def test_get_chemical_release_data_by_chemical_name(self, sample_releases, mock_tri_client):
        """Test chemical release search by chemical name."""
        mock_tri_client.get_chemical_releases.return_value = sample_releases
        
        with patch('src.tools.chemical_releases.TRIClient', return_value=mock_tri_client):
            result = await get_chemical_release_data(chemical_name="benzene")
        
        assert isinstance(result, ChemicalReleaseData)
        assert result.search_params['chemical_name'] == "benzene"
        assert result.total_facilities == 2
        assert result.total_chemicals == 2
        assert result.total_releases == 2855.0  # Sum of all releases
        assert result.air_releases == 2300.0
        assert result.water_releases == 450.0
        assert result.land_releases == 105.0
        assert result.underground_injections == 0.0
        
        # Check facility aggregation
        assert len(result.facilities) == 2
        facility_a = next(f for f in result.facilities if f.facility_id == "110000123456")
        assert facility_a.facility_name == "Test Chemical Plant A"
        assert len(facility_a.chemical_releases) == 2
        assert facility_a.total_releases == 1875.0
        assert facility_a.unique_chemicals == 2
        
        # Check chemical aggregation
        assert len(result.chemicals) == 2
        benzene_agg = next(c for c in result.chemicals if c.chemical_name == "Benzene")
        assert benzene_agg.cas_number == "71-43-2"
        assert len(benzene_agg.facilities_releasing) == 2
        assert benzene_agg.total_releases == 2230.0
        assert benzene_agg.facility_count == 2
        
        # Check top facilities and chemicals
        assert len(result.top_facilities) == 2
        assert len(result.top_chemicals) == 2
        assert result.top_facilities[0].facility_id == "110000123456"  # Higher total
        assert result.top_chemicals[0].chemical_name == "Benzene"  # Higher total
    
    @pytest.mark.asyncio
    async def test_get_chemical_release_data_by_cas_number(self, sample_releases, mock_tri_client):
        """Test chemical release search by CAS number."""
        mock_tri_client.get_chemical_releases.return_value = sample_releases[:1]  # Just benzene
        
        with patch('src.tools.chemical_releases.TRIClient', return_value=mock_tri_client):
            result = await get_chemical_release_data(cas_number="71-43-2")
        
        assert isinstance(result, ChemicalReleaseData)
        assert result.search_params['cas_number'] == "71-43-2"
        assert result.total_facilities == 1
        assert result.total_chemicals == 1
        assert result.total_releases == 1250.0
    
    @pytest.mark.asyncio
    async def test_get_chemical_release_data_by_state(self, sample_releases, mock_tri_client):
        """Test chemical release search by state."""
        mock_tri_client.get_chemical_releases.return_value = sample_releases
        
        with patch('src.tools.chemical_releases.TRIClient', return_value=mock_tri_client):
            result = await get_chemical_release_data(state="CA")
        
        assert isinstance(result, ChemicalReleaseData)
        assert result.search_params['state'] == "CA"
        assert result.total_facilities == 2
        assert result.total_chemicals == 2
    
    @pytest.mark.asyncio
    async def test_get_chemical_release_data_multiple_params(self, sample_releases, mock_tri_client):
        """Test chemical release search with multiple parameters."""
        mock_tri_client.get_chemical_releases.return_value = sample_releases[:1]
        
        with patch('src.tools.chemical_releases.TRIClient', return_value=mock_tri_client):
            result = await get_chemical_release_data(
                chemical_name="benzene",
                state="CA",
                year=2022
            )
        
        assert isinstance(result, ChemicalReleaseData)
        assert result.search_params['chemical_name'] == "benzene"
        assert result.search_params['state'] == "CA"
        assert result.search_params['year'] == 2022
        assert result.reporting_year == 2022
    
    @pytest.mark.asyncio
    async def test_get_chemical_release_data_no_params_raises_error(self):
        """Test that no search parameters raises ValueError."""
        with pytest.raises(ValueError, match="At least one search parameter must be provided"):
            await get_chemical_release_data()
    
    @pytest.mark.asyncio
    async def test_get_chemical_release_data_invalid_limit_raises_error(self):
        """Test that invalid limit raises ValueError."""
        with pytest.raises(ValueError, match="Limit must be between 1 and 1000"):
            await get_chemical_release_data(chemical_name="benzene", limit=0)
        
        with pytest.raises(ValueError, match="Limit must be between 1 and 1000"):
            await get_chemical_release_data(chemical_name="benzene", limit=1001)
    
    @pytest.mark.asyncio
    async def test_get_chemical_release_data_invalid_state_raises_error(self):
        """Test that invalid state code raises ValueError."""
        with pytest.raises(ValueError, match="State must be a two-letter code"):
            await get_chemical_release_data(state="California")
    
    @pytest.mark.asyncio
    async def test_get_chemical_release_data_empty_results(self, mock_tri_client):
        """Test handling of empty results."""
        mock_tri_client.get_chemical_releases.return_value = []
        
        with patch('src.tools.chemical_releases.TRIClient', return_value=mock_tri_client):
            result = await get_chemical_release_data(chemical_name="nonexistent")
        
        assert isinstance(result, ChemicalReleaseData)
        assert result.total_facilities == 0
        assert result.total_chemicals == 0
        assert result.total_releases == 0.0
        assert len(result.facilities) == 0
        assert len(result.chemicals) == 0
    
    
    
    
    
    def test_facility_release_info_properties(self):
        """Test FacilityReleaseInfo properties."""
        releases = [
            ChemicalRelease(
                facility_id="110000123456",
                facility_name="Test Plant",
                chemical_name="Benzene",
                cas_number="71-43-2",
                reporting_year=2022,
                air_release=1000.0,
                water_release=200.0,
                land_release=50.0,
                underground_injection=0.0,
                release_type="On-site",
                units="pounds"
            ),
            ChemicalRelease(
                facility_id="110000123456",
                facility_name="Test Plant",
                chemical_name="Lead",
                cas_number="7439-92-1",
                reporting_year=2022,
                air_release=500.0,
                water_release=100.0,
                land_release=25.0,
                underground_injection=0.0,
                release_type="On-site",
                units="pounds"
            )
        ]
        
        facility = FacilityReleaseInfo(
            facility_id="110000123456",
            facility_name="Test Plant",
            chemical_releases=releases
        )
        
        assert facility.total_releases == 1875.0
        assert facility.unique_chemicals == 2
    
    def test_chemical_aggregation_properties(self):
        """Test ChemicalAggregation properties."""
        releases = [
            ChemicalRelease(
                facility_id="110000123456",
                facility_name="Test Plant A",
                chemical_name="Benzene",
                cas_number="71-43-2",
                reporting_year=2022,
                air_release=1000.0,
                water_release=200.0,
                land_release=50.0,
                underground_injection=0.0,
                release_type="On-site",
                units="pounds"
            ),
            ChemicalRelease(
                facility_id="110000789012",
                facility_name="Test Plant B",
                chemical_name="Benzene",
                cas_number="71-43-2",
                reporting_year=2022,
                air_release=800.0,
                water_release=150.0,
                land_release=30.0,
                underground_injection=0.0,
                release_type="On-site",
                units="pounds"
            )
        ]
        
        chemical = ChemicalAggregation(
            chemical_name="Benzene",
            cas_number="71-43-2",
            facilities_releasing=releases
        )
        
        assert chemical.total_releases == 2230.0
        assert chemical.facility_count == 2


