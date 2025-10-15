"""Unit tests for location summary tool."""

import pytest
from unittest.mock import AsyncMock, patch

from src.tools.location_summary import get_environmental_summary_by_location
from src.models.summary import EnvironmentalSummary
from src.models.common import Coordinates


class TestGetEnvironmentalSummaryByLocation:
    """Test cases for get_environmental_summary_by_location function."""
    
    @pytest.mark.asyncio
    async def test_successful_summary(self, sample_environmental_summary):
        """Test successful environmental summary generation."""
        with patch('src.tools.location_summary.geocode_location') as mock_geocode, \
             patch('src.tools.location_summary.calculate_bounding_box') as mock_bbox, \
             patch('src.tools.location_summary.FRSClient') as mock_frs, \
             patch('src.tools.location_summary.TRIClient') as mock_tri, \
             patch('src.tools.location_summary.SDWISClient') as mock_sdwis, \
             patch('src.tools.location_summary.RCRAClient') as mock_rcra, \
             patch('src.tools.location_summary.asyncio.gather') as mock_gather, \
             patch('src.tools.location_summary.filter_by_distance') as mock_filter, \
             patch('src.tools.location_summary.aggregate_facilities') as mock_aggregate, \
             patch('src.tools.location_summary.rank_facilities') as mock_rank, \
             patch('src.tools.location_summary.format_environmental_summary') as mock_format:
            
            # Setup mocks
            mock_geocode.return_value = Coordinates(latitude=40.7128, longitude=-74.0060)
            mock_bbox.return_value = "mock_bbox"
            mock_gather.return_value = [[], [], [], [], [], []]  # Empty results
            mock_filter.return_value = []
            mock_aggregate.return_value = []
            mock_rank.return_value = []
            mock_format.return_value = sample_environmental_summary
            
            # Mock context managers
            mock_frs.return_value.__aenter__.return_value = AsyncMock()
            mock_tri.return_value.__aenter__.return_value = AsyncMock()
            mock_sdwis.return_value.__aenter__.return_value = AsyncMock()
            mock_rcra.return_value.__aenter__.return_value = AsyncMock()
            
            result = await get_environmental_summary_by_location("New York, NY", 5.0)
            
            assert isinstance(result, EnvironmentalSummary)
            assert result.location == "New York, NY"
            
            # Verify geocoding was called
            mock_geocode.assert_called_once_with("New York, NY")
            
            # Verify bounding box calculation
            mock_bbox.assert_called_once_with(40.7128, -74.0060, 5.0)
    
    @pytest.mark.asyncio
    async def test_empty_location(self):
        """Test with empty location string."""
        with pytest.raises(ValueError, match="Location cannot be empty"):
            await get_environmental_summary_by_location("", 5.0)
        
        with pytest.raises(ValueError, match="Location cannot be empty"):
            await get_environmental_summary_by_location("   ", 5.0)
    
    @pytest.mark.asyncio
    async def test_invalid_radius(self):
        """Test with invalid radius values."""
        with pytest.raises(ValueError, match="Radius must be between 0.1 and 100.0 miles"):
            await get_environmental_summary_by_location("New York, NY", 0.05)
        
        with pytest.raises(ValueError, match="Radius must be between 0.1 and 100.0 miles"):
            await get_environmental_summary_by_location("New York, NY", 101.0)
    
    @pytest.mark.asyncio
    async def test_geocoding_failure(self):
        """Test with geocoding failure."""
        with patch('src.tools.location_summary.geocode_location') as mock_geocode:
            mock_geocode.side_effect = ValueError("Could not geocode location")
            
            with pytest.raises(ValueError, match="Could not find location"):
                await get_environmental_summary_by_location("Invalid Location", 5.0)
    
    @pytest.mark.asyncio
    async def test_api_failure_handling(self):
        """Test handling of API failures."""
        with patch('src.tools.location_summary.geocode_location') as mock_geocode, \
             patch('src.tools.location_summary.calculate_bounding_box') as mock_bbox, \
             patch('src.tools.location_summary.FRSClient') as mock_frs, \
             patch('src.tools.location_summary.TRIClient') as mock_tri, \
             patch('src.tools.location_summary.SDWISClient') as mock_sdwis, \
             patch('src.tools.location_summary.RCRAClient') as mock_rcra, \
             patch('src.tools.location_summary.asyncio.gather') as mock_gather, \
             patch('src.tools.location_summary.filter_by_distance') as mock_filter, \
             patch('src.tools.location_summary.aggregate_facilities') as mock_aggregate, \
             patch('src.tools.location_summary.rank_facilities') as mock_rank, \
             patch('src.tools.location_summary.format_environmental_summary') as mock_format:
            
            # Setup mocks
            mock_geocode.return_value = Coordinates(latitude=40.7128, longitude=-74.0060)
            mock_bbox.return_value = "mock_bbox"
            
            # Simulate some API failures
            mock_gather.return_value = [
                [],  # FRS success
                Exception("TRI API error"),  # TRI failure
                [],  # TRI releases success
                [],  # SDWIS systems success
                [],  # SDWIS violations success
                []   # RCRA success
            ]
            
            mock_filter.return_value = []
            mock_aggregate.return_value = []
            mock_rank.return_value = []
            mock_format.return_value = EnvironmentalSummary(
                location="Test",
                coordinates=Coordinates(latitude=40.7128, longitude=-74.0060),
                radius_miles=5.0
            )
            
            # Mock context managers
            mock_frs.return_value.__aenter__.return_value = AsyncMock()
            mock_tri.return_value.__aenter__.return_value = AsyncMock()
            mock_sdwis.return_value.__aenter__.return_value = AsyncMock()
            mock_rcra.return_value.__aenter__.return_value = AsyncMock()
            
            # Should not raise exception, should handle partial failures gracefully
            result = await get_environmental_summary_by_location("New York, NY", 5.0)
            
            assert isinstance(result, EnvironmentalSummary)
    
    @pytest.mark.asyncio
    async def test_default_radius(self):
        """Test with default radius value."""
        with patch('src.tools.location_summary.geocode_location') as mock_geocode, \
             patch('src.tools.location_summary.calculate_bounding_box') as mock_bbox, \
             patch('src.tools.location_summary.FRSClient') as mock_frs, \
             patch('src.tools.location_summary.TRIClient') as mock_tri, \
             patch('src.tools.location_summary.SDWISClient') as mock_sdwis, \
             patch('src.tools.location_summary.RCRAClient') as mock_rcra, \
             patch('src.tools.location_summary.asyncio.gather') as mock_gather, \
             patch('src.tools.location_summary.filter_by_distance') as mock_filter, \
             patch('src.tools.location_summary.aggregate_facilities') as mock_aggregate, \
             patch('src.tools.location_summary.rank_facilities') as mock_rank, \
             patch('src.tools.location_summary.format_environmental_summary') as mock_format:
            
            # Setup mocks
            mock_geocode.return_value = Coordinates(latitude=40.7128, longitude=-74.0060)
            mock_bbox.return_value = "mock_bbox"
            mock_gather.return_value = [[], [], [], [], [], []]
            mock_filter.return_value = []
            mock_aggregate.return_value = []
            mock_rank.return_value = []
            mock_format.return_value = EnvironmentalSummary(
                location="Test",
                coordinates=Coordinates(latitude=40.7128, longitude=-74.0060),
                radius_miles=5.0
            )
            
            # Mock context managers
            mock_frs.return_value.__aenter__.return_value = AsyncMock()
            mock_tri.return_value.__aenter__.return_value = AsyncMock()
            mock_sdwis.return_value.__aenter__.return_value = AsyncMock()
            mock_rcra.return_value.__aenter__.return_value = AsyncMock()
            
            # Call without radius parameter (should use default 5.0)
            await get_environmental_summary_by_location("New York, NY")
            
            # Verify bounding box was calculated with default radius
            mock_bbox.assert_called_once_with(40.7128, -74.0060, 5.0)
    
    @pytest.mark.asyncio
    async def test_unexpected_error(self):
        """Test handling of unexpected errors."""
        with patch('src.tools.location_summary.geocode_location') as mock_geocode:
            mock_geocode.side_effect = Exception("Unexpected error")
            
            with pytest.raises(Exception, match="Failed to retrieve environmental data"):
                await get_environmental_summary_by_location("New York, NY", 5.0)
