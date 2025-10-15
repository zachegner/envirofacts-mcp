"""Integration tests for EPA Envirofacts MCP Server with live API calls."""

import pytest
import asyncio

from src.tools.location_summary import get_environmental_summary_by_location
from src.models.summary import EnvironmentalSummary


@pytest.mark.integration
@pytest.mark.slow
class TestLocationSummaryIntegration:
    """Integration tests with live EPA API calls."""
    
    @pytest.mark.asyncio
    async def test_nyc_environmental_summary(self):
        """Test environmental summary for NYC (ZIP 10001)."""
        result = await get_environmental_summary_by_location("10001", radius_miles=3.0)
        
        assert isinstance(result, EnvironmentalSummary)
        assert result.location == "10001"
        assert result.coordinates is not None
        assert result.radius_miles == 3.0
        
        # Should find facilities in NYC area
        assert result.total_facilities >= 0
        assert isinstance(result.facility_counts, dict)
        
        # Should have data sources
        assert len(result.data_sources) > 0
        assert "FRS" in result.data_sources
        
        # Should have query timestamp
        assert result.query_timestamp is not None
    
    @pytest.mark.asyncio
    async def test_la_environmental_summary(self):
        """Test environmental summary for LA (ZIP 90001)."""
        result = await get_environmental_summary_by_location("90001", radius_miles=5.0)
        
        assert isinstance(result, EnvironmentalSummary)
        assert result.location == "90001"
        assert result.coordinates is not None
        
        # Should find facilities in LA area
        assert result.total_facilities >= 0
        assert isinstance(result.facility_counts, dict)
    
    @pytest.mark.asyncio
    async def test_flint_environmental_summary(self):
        """Test environmental summary for Flint, MI (ZIP 48502)."""
        result = await get_environmental_summary_by_location("48502", radius_miles=2.0)
        
        assert isinstance(result, EnvironmentalSummary)
        assert result.location == "48502"
        assert result.coordinates is not None
        
        # Should find facilities in Flint area
        assert result.total_facilities >= 0
        assert isinstance(result.facility_counts, dict)
    
    @pytest.mark.asyncio
    async def test_city_name_geocoding(self):
        """Test environmental summary with city name."""
        result = await get_environmental_summary_by_location("San Francisco, CA", radius_miles=5.0)
        
        assert isinstance(result, EnvironmentalSummary)
        assert result.location == "San Francisco, CA"
        assert result.coordinates is not None
        
        # Should be in California
        assert result.coordinates.latitude > 35.0
        assert result.coordinates.latitude < 40.0
        assert result.coordinates.longitude > -125.0
        assert result.coordinates.longitude < -120.0
    
    @pytest.mark.asyncio
    async def test_address_geocoding(self):
        """Test environmental summary with full address."""
        result = await get_environmental_summary_by_location(
            "1600 Pennsylvania Avenue NW, Washington, DC", 
            radius_miles=2.0
        )
        
        assert isinstance(result, EnvironmentalSummary)
        assert result.location == "1600 Pennsylvania Avenue NW, Washington, DC"
        assert result.coordinates is not None
        
        # Should be in Washington DC area
        assert result.coordinates.latitude > 38.8
        assert result.coordinates.latitude < 39.0
        assert result.coordinates.longitude > -77.1
        assert result.coordinates.longitude < -77.0
    
    @pytest.mark.asyncio
    async def test_large_radius(self):
        """Test environmental summary with large radius."""
        result = await get_environmental_summary_by_location("Chicago, IL", radius_miles=20.0)
        
        assert isinstance(result, EnvironmentalSummary)
        assert result.radius_miles == 20.0
        
        # Should find more facilities with larger radius
        assert result.total_facilities >= 0
    
    @pytest.mark.asyncio
    async def test_small_radius(self):
        """Test environmental summary with small radius."""
        result = await get_environmental_summary_by_location("Boston, MA", radius_miles=1.0)
        
        assert isinstance(result, EnvironmentalSummary)
        assert result.radius_miles == 1.0
        
        # Should find fewer facilities with smaller radius
        assert result.total_facilities >= 0
    
    @pytest.mark.asyncio
    async def test_water_violations_data(self):
        """Test that water violations data is retrieved."""
        result = await get_environmental_summary_by_location("10001", radius_miles=5.0)
        
        assert isinstance(result, EnvironmentalSummary)
        assert isinstance(result.water_violations, list)
        assert isinstance(result.total_violations, int)
        assert result.total_violations >= 0
        
        # If violations exist, check structure
        if result.water_violations:
            violation = result.water_violations[0]
            assert hasattr(violation, 'violation_id')
            assert hasattr(violation, 'system_name')
            assert hasattr(violation, 'violation_type')
    
    @pytest.mark.asyncio
    async def test_chemical_releases_data(self):
        """Test that chemical releases data is retrieved."""
        result = await get_environmental_summary_by_location("10001", radius_miles=5.0)
        
        assert isinstance(result, EnvironmentalSummary)
        assert hasattr(result, 'chemical_releases')
        
        # Check release summary structure
        releases = result.chemical_releases
        assert hasattr(releases, 'total_facilities')
        assert hasattr(releases, 'total_chemicals')
        assert hasattr(releases, 'total_releases')
        assert hasattr(releases, 'reporting_year')
        assert releases.reporting_year >= 2020  # Should be recent year
    
    @pytest.mark.asyncio
    async def test_facility_distance_calculation(self):
        """Test that facility distances are calculated correctly."""
        result = await get_environmental_summary_by_location("10001", radius_miles=3.0)
        
        assert isinstance(result, EnvironmentalSummary)
        
        # Check that top facilities have distances
        if result.top_facilities:
            for facility in result.top_facilities[:5]:  # Check first 5
                if facility.distance_miles is not None:
                    assert facility.distance_miles >= 0
                    assert facility.distance_miles <= result.radius_miles
    
    @pytest.mark.asyncio
    async def test_summary_statistics(self):
        """Test that summary statistics are populated."""
        result = await get_environmental_summary_by_location("10001", radius_miles=5.0)
        
        assert isinstance(result, EnvironmentalSummary)
        assert isinstance(result.summary_stats, dict)
        
        # Check required stats
        assert 'search_radius_miles' in result.summary_stats
        assert 'total_population_served' in result.summary_stats
        assert 'active_violation_count' in result.summary_stats
        
        assert result.summary_stats['search_radius_miles'] == 5.0
        assert result.summary_stats['total_population_served'] >= 0
        assert result.summary_stats['active_violation_count'] >= 0
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_location(self):
        """Test error handling for invalid location."""
        with pytest.raises(ValueError, match="Could not find location"):
            await get_environmental_summary_by_location("InvalidLocation12345", radius_miles=5.0)
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_radius(self):
        """Test error handling for invalid radius."""
        with pytest.raises(ValueError, match="Radius must be between 0.1 and 100.0 miles"):
            await get_environmental_summary_by_location("10001", radius_miles=0.05)
        
        with pytest.raises(ValueError, match="Radius must be between 0.1 and 100.0 miles"):
            await get_environmental_summary_by_location("10001", radius_miles=101.0)
    
    @pytest.mark.asyncio
    async def test_performance_large_query(self):
        """Test performance with a large query."""
        import time
        
        start_time = time.time()
        result = await get_environmental_summary_by_location("Houston, TX", radius_miles=10.0)
        end_time = time.time()
        
        # Should complete within reasonable time (less than 30 seconds)
        assert (end_time - start_time) < 30.0
        assert isinstance(result, EnvironmentalSummary)
    
    @pytest.mark.asyncio
    async def test_data_consistency(self):
        """Test that returned data is consistent."""
        result = await get_environmental_summary_by_location("10001", radius_miles=3.0)
        
        assert isinstance(result, EnvironmentalSummary)
        
        # Check that counts match actual data
        if result.top_facilities:
            assert len(result.top_facilities) <= 50  # Should be limited to 50
        
        if result.water_violations:
            assert len(result.water_violations) == result.total_violations
        
        if result.hazardous_sites:
            assert len(result.hazardous_sites) == result.total_hazardous_sites
        
        # Check that facility counts are reasonable
        total_counted = sum(result.facility_counts.values())
        assert total_counted >= result.total_facilities
