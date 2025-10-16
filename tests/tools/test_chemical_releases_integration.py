"""Integration tests for chemical release tool with live EPA API."""

import pytest
from datetime import datetime

from src.tools.chemical_releases import get_chemical_release_data


@pytest.mark.integration
class TestChemicalReleaseToolIntegration:
    """Integration tests for chemical release tool with live EPA API."""
    
    @pytest.mark.asyncio
    async def test_get_chemical_release_data_by_chemical_name(self):
        """Test chemical release search by chemical name with live API."""
        result = await get_chemical_release_data(
            chemical_name="benzene",
            limit=10
        )
        
        assert result.total_facilities > 0
        assert result.total_chemicals > 0
        assert result.total_releases > 0
        assert len(result.facilities) > 0
        assert len(result.chemicals) > 0
        
        # Check that benzene is in the results
        benzene_chemicals = [c for c in result.chemicals if "benzene" in c.chemical_name.lower()]
        assert len(benzene_chemicals) > 0
        
        # Check that all facilities have benzene releases
        for facility in result.facilities:
            benzene_releases = [r for r in facility.chemical_releases if "benzene" in r.chemical_name.lower()]
            assert len(benzene_releases) > 0
    
    @pytest.mark.asyncio
    async def test_get_chemical_release_data_by_cas_number(self):
        """Test chemical release search by CAS number with live API."""
        result = await get_chemical_release_data(
            cas_number="71-43-2",  # Benzene
            limit=10
        )
        
        assert result.total_facilities > 0
        assert result.total_chemicals > 0
        assert result.total_releases > 0
        
        # Check that all chemicals have the correct CAS number
        for chemical in result.chemicals:
            assert chemical.cas_number == "71-43-2"
        
        # Check that all releases have the correct CAS number
        for facility in result.facilities:
            for release in facility.chemical_releases:
                assert release.cas_number == "71-43-2"
    
    @pytest.mark.asyncio
    async def test_get_chemical_release_data_by_state(self):
        """Test chemical release search by state with live API."""
        result = await get_chemical_release_data(
            state="CA",
            limit=20
        )
        
        assert result.total_facilities > 0
        assert result.total_chemicals > 0
        assert result.total_releases > 0
        
        # Check that all facilities are in California
        # Note: This would require additional facility data to verify state
        # For now, we'll just check that we got results
    
    @pytest.mark.asyncio
    async def test_get_chemical_release_data_by_state_and_chemical(self):
        """Test chemical release search by state and chemical with live API."""
        result = await get_chemical_release_data(
            chemical_name="lead",
            state="TX",
            limit=15
        )
        
        assert result.total_facilities > 0
        assert result.total_chemicals > 0
        assert result.total_releases > 0
        
        # Check that lead is in the results
        lead_chemicals = [c for c in result.chemicals if "lead" in c.chemical_name.lower()]
        assert len(lead_chemicals) > 0
    
    @pytest.mark.asyncio
    async def test_get_chemical_release_data_by_year(self):
        """Test chemical release search by year with live API."""
        result = await get_chemical_release_data(
            chemical_name="benzene",
            year=2022,
            limit=10
        )
        
        assert result.total_facilities > 0
        assert result.total_chemicals > 0
        assert result.total_releases > 0
        assert result.reporting_year == 2022
        
        # Check that all releases are from 2022
        for facility in result.facilities:
            for release in facility.chemical_releases:
                assert release.reporting_year == 2022
    
    
    @pytest.mark.asyncio
    async def test_get_chemical_release_data_empty_search(self):
        """Test chemical release search with parameters that return no results."""
        result = await get_chemical_release_data(
            chemical_name="nonexistentchemical12345",
            limit=10
        )
        
        assert result.total_facilities == 0
        assert result.total_chemicals == 0
        assert result.total_releases == 0.0
        assert len(result.facilities) == 0
        assert len(result.chemicals) == 0
    
    @pytest.mark.asyncio
    async def test_get_chemical_release_data_aggregation_consistency(self):
        """Test that aggregation calculations are consistent."""
        result = await get_chemical_release_data(
            chemical_name="benzene",
            limit=20
        )
        
        # Check that total releases match sum of individual releases
        calculated_total = sum(r.total_release for facility in result.facilities for r in facility.chemical_releases)
        assert abs(result.total_releases - calculated_total) < 0.01
        
        # Check that air releases match sum of individual air releases
        calculated_air = sum(r.air_release or 0.0 for facility in result.facilities for r in facility.chemical_releases)
        assert abs(result.air_releases - calculated_air) < 0.01
        
        # Check that water releases match sum of individual water releases
        calculated_water = sum(r.water_release or 0.0 for facility in result.facilities for r in facility.chemical_releases)
        assert abs(result.water_releases - calculated_water) < 0.01
        
        # Check that land releases match sum of individual land releases
        calculated_land = sum(r.land_release or 0.0 for facility in result.facilities for r in facility.chemical_releases)
        assert abs(result.land_releases - calculated_land) < 0.01
        
        # Check that underground injections match sum of individual underground injections
        calculated_underground = sum(r.underground_injection or 0.0 for facility in result.facilities for r in facility.chemical_releases)
        assert abs(result.underground_injections - calculated_underground) < 0.01
    
    @pytest.mark.asyncio
    async def test_get_chemical_release_data_top_ranking(self):
        """Test that top facilities and chemicals are properly ranked."""
        result = await get_chemical_release_data(
            chemical_name="benzene",
            limit=30
        )
        
        if len(result.top_facilities) > 1:
            # Check that facilities are sorted by total releases (descending)
            for i in range(len(result.top_facilities) - 1):
                assert result.top_facilities[i].total_releases >= result.top_facilities[i + 1].total_releases
        
        if len(result.top_chemicals) > 1:
            # Check that chemicals are sorted by total releases (descending)
            for i in range(len(result.top_chemicals) - 1):
                assert result.top_chemicals[i].total_releases >= result.top_chemicals[i + 1].total_releases
    
    @pytest.mark.asyncio
    async def test_get_chemical_release_data_metadata(self):
        """Test that metadata is properly populated."""
        result = await get_chemical_release_data(
            chemical_name="benzene",
            state="CA",
            year=2022,
            limit=10
        )
        
        # Check search parameters
        assert "chemical_name" in result.search_params
        assert result.search_params["chemical_name"] == "benzene"
        assert "state" in result.search_params
        assert result.search_params["state"] == "CA"
        assert "year" in result.search_params
        assert result.search_params["year"] == 2022
        
        # Check timestamp
        assert result.query_timestamp is not None
        # Verify timestamp is in ISO format
        datetime.fromisoformat(result.query_timestamp.replace("Z", "+00:00"))
        
        # Check data sources
        assert "TRI" in result.data_sources
        
        # Check reporting year
        assert result.reporting_year == 2022


