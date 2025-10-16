"""Integration tests for search facilities tool with live EPA API."""

import pytest

from src.tools.search_facilities import search_facilities


@pytest.mark.integration
class TestSearchFacilitiesIntegration:
    """Integration tests for search_facilities function with live EPA API."""
    
    @pytest.mark.asyncio
    async def test_search_by_facility_name_integration(self):
        """Test search by facility name with live EPA API."""
        facilities = await search_facilities(facility_name="Chemical", limit=10)
        
        # Should return some results
        assert isinstance(facilities, list)
        assert len(facilities) <= 10
        
        # Verify facility structure
        if facilities:
            facility = facilities[0]
            assert facility.registry_id
            assert facility.name
            assert "Chemical" in facility.name.lower()
            assert facility.state
            assert len(facility.state) == 2
            assert facility.programs == ["FRS"]
    
    @pytest.mark.asyncio
    async def test_search_by_state_integration(self):
        """Test search by state with live EPA API."""
        facilities = await search_facilities(state="NY", limit=5)
        
        # Should return some results
        assert isinstance(facilities, list)
        assert len(facilities) <= 5
        
        # Verify all facilities are in NY
        for facility in facilities:
            assert facility.state == "NY"
            assert facility.registry_id
            assert facility.name
    
    @pytest.mark.asyncio
    async def test_search_by_zip_code_integration(self):
        """Test search by ZIP code with live EPA API."""
        facilities = await search_facilities(zip_code="10001", limit=5)
        
        # Should return some results
        assert isinstance(facilities, list)
        assert len(facilities) <= 5
        
        # Verify all facilities are in the specified ZIP code
        for facility in facilities:
            assert facility.zip_code == "10001"
            assert facility.registry_id
            assert facility.name
    
    @pytest.mark.asyncio
    async def test_search_by_city_integration(self):
        """Test search by city with live EPA API."""
        facilities = await search_facilities(city="Los Angeles", limit=5)
        
        # Should return some results
        assert isinstance(facilities, list)
        assert len(facilities) <= 5
        
        # Verify all facilities are in Los Angeles
        for facility in facilities:
            assert facility.city == "Los Angeles"
            assert facility.registry_id
            assert facility.name
    
    @pytest.mark.asyncio
    async def test_search_by_naics_code_integration(self):
        """Test search by NAICS code with live EPA API."""
        # Use a common NAICS code for chemical manufacturing
        facilities = await search_facilities(naics_code="325199", limit=5)
        
        # Should return some results
        assert isinstance(facilities, list)
        assert len(facilities) <= 5
        
        # Verify all facilities have the specified NAICS code
        for facility in facilities:
            assert facility.naics_code == "325199"
            assert facility.registry_id
            assert facility.name
    
    @pytest.mark.asyncio
    async def test_search_multiple_parameters_integration(self):
        """Test search with multiple parameters with live EPA API."""
        facilities = await search_facilities(
            facility_name="Chemical",
            state="CA",
            limit=5
        )
        
        # Should return some results
        assert isinstance(facilities, list)
        assert len(facilities) <= 5
        
        # Verify all facilities match criteria
        for facility in facilities:
            assert facility.state == "CA"
            assert "Chemical" in facility.name.lower()
            assert facility.registry_id
    
    @pytest.mark.asyncio
    async def test_search_no_results_integration(self):
        """Test search with parameters that should return no results."""
        facilities = await search_facilities(
            facility_name="NonexistentFacilityName12345",
            limit=5
        )
        
        # Should return empty list
        assert isinstance(facilities, list)
        assert len(facilities) == 0
    
    @pytest.mark.asyncio
    async def test_search_large_result_set_integration(self):
        """Test search that should return many results."""
        facilities = await search_facilities(state="TX", limit=100)
        
        # Should return many results (Texas has many facilities)
        assert isinstance(facilities, list)
        assert len(facilities) <= 100
        
        # Verify all facilities are in Texas
        for facility in facilities:
            assert facility.state == "TX"
            assert facility.registry_id
            assert facility.name
    
    @pytest.mark.asyncio
    async def test_search_by_zip_code_leading_zero_integration(self):
        """Test search by ZIP code with leading zero (01510) with live EPA API."""
        facilities = await search_facilities(zip_code="01510", limit=5)
        
        # Should return some results
        assert isinstance(facilities, list)
        assert len(facilities) <= 5
        
        # Verify all facilities are in the specified ZIP code
        for facility in facilities:
            assert facility.zip_code == "01510"
            assert facility.registry_id
            assert facility.name
    
    @pytest.mark.asyncio
    async def test_search_by_numeric_zip_code_integration(self):
        """Test search with numeric ZIP code input (1510 -> 01510) with live EPA API."""
        facilities = await search_facilities(zip_code=1510, limit=5)
        
        # Should return some results
        assert isinstance(facilities, list)
        assert len(facilities) <= 5
        
        # Verify all facilities are in the zero-padded ZIP code
        for facility in facilities:
            assert facility.zip_code == "01510"
            assert facility.registry_id
            assert facility.name
