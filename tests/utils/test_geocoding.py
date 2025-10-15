"""Unit tests for geocoding utilities."""

import pytest
import asyncio
from unittest.mock import patch, MagicMock

from src.utils.geocoding import geocode_location, GeocodingCache, clear_geocoding_cache
from src.models.common import Coordinates, LocationInfo


class TestGeocodingCache:
    """Test cases for GeocodingCache."""
    
    def test_init(self):
        """Test cache initialization."""
        cache = GeocodingCache(max_size=100)
        assert cache.max_size == 100
        assert len(cache.cache) == 0
    
    def test_set_and_get(self):
        """Test setting and getting cached values."""
        cache = GeocodingCache()
        coords = Coordinates(latitude=40.7128, longitude=-74.0060)
        location_info = LocationInfo(
            coordinates=coords,
            state_code="NY",
            state_name="New York",
            county="New York County"
        )
        
        cache.set("New York, NY", location_info)
        result = cache.get("New York, NY")
        
        assert result == location_info
        assert cache.get("new york, ny") == location_info  # Case insensitive
    
    def test_get_nonexistent(self):
        """Test getting non-existent cached value."""
        cache = GeocodingCache()
        result = cache.get("Nonexistent Location")
        
        assert result is None
    
    def test_max_size_limit(self):
        """Test cache size limit."""
        cache = GeocodingCache(max_size=2)
        coords1 = Coordinates(latitude=40.7128, longitude=-74.0060)
        coords2 = Coordinates(latitude=34.0522, longitude=-118.2437)
        coords3 = Coordinates(latitude=43.0125, longitude=-83.6875)
        
        location_info1 = LocationInfo(coordinates=coords1, state_code="NY")
        location_info2 = LocationInfo(coordinates=coords2, state_code="CA")
        location_info3 = LocationInfo(coordinates=coords3, state_code="MI")
        
        cache.set("Location 1", location_info1)
        cache.set("Location 2", location_info2)
        cache.set("Location 3", location_info3)
        
        # First location should be evicted
        assert cache.get("Location 1") is None
        assert cache.get("Location 2") == location_info2
        assert cache.get("Location 3") == location_info3
    
    def test_clear(self):
        """Test cache clearing."""
        cache = GeocodingCache()
        coords = Coordinates(latitude=40.7128, longitude=-74.0060)
        location_info = LocationInfo(coordinates=coords, state_code="NY")
        
        cache.set("Test Location", location_info)
        assert len(cache.cache) == 1
        
        cache.clear()
        assert len(cache.cache) == 0


class TestGeocodeLocation:
    """Test cases for geocode_location function."""
    
    @pytest.mark.asyncio
    async def test_geocode_success(self, mock_geocoder):
        """Test successful geocoding."""
        with patch('src.utils.geocoding.Nominatim', return_value=mock_geocoder):
            result = await geocode_location("New York, NY")
            
            assert isinstance(result, LocationInfo)
            assert result.coordinates.latitude == 40.7128
            assert result.coordinates.longitude == -74.0060
            assert result.state_code == "NY"
    
    @pytest.mark.asyncio
    async def test_geocode_cached(self, mock_geocoder):
        """Test geocoding with cached result."""
        with patch('src.utils.geocoding.Nominatim', return_value=mock_geocoder):
            # First call
            result1 = await geocode_location("New York, NY")
            
            # Second call should use cache
            result2 = await geocode_location("New York, NY")
            
            assert result1 == result2
            # Nominatim should only be called once
            assert mock_geocoder.geocode.call_count == 1
    
    @pytest.mark.asyncio
    async def test_geocode_timeout(self):
        """Test geocoding with timeout error."""
        mock_geocoder = MagicMock()
        mock_geocoder.geocode.side_effect = Exception("Timeout")
        
        with patch('src.utils.geocoding.Nominatim', return_value=mock_geocoder):
            with pytest.raises(ValueError, match="Failed to geocode"):
                await geocode_location("Test Location")
    
    @pytest.mark.asyncio
    async def test_geocode_no_result(self):
        """Test geocoding with no result."""
        mock_geocoder = MagicMock()
        mock_geocoder.geocode.return_value = None
        
        with patch('src.utils.geocoding.Nominatim', return_value=mock_geocoder):
            with pytest.raises(ValueError, match="Could not geocode location"):
                await geocode_location("Nonexistent Location")
    
    @pytest.mark.asyncio
    async def test_geocode_rate_limiting(self, mock_geocoder):
        """Test geocoding rate limiting."""
        with patch('src.utils.geocoding.Nominatim', return_value=mock_geocoder):
            with patch('asyncio.sleep') as mock_sleep:
                await geocode_location("Location 1")
                await geocode_location("Location 2")
                
                # Should have slept for rate limiting
                assert mock_sleep.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_geocode_empty_location(self):
        """Test geocoding with empty location."""
        with pytest.raises(ValueError, match="Location cannot be empty"):
            await geocode_location("")
        
        with pytest.raises(ValueError, match="Location cannot be empty"):
            await geocode_location("   ")


def test_clear_geocoding_cache():
    """Test global cache clearing."""
    from src.utils.geocoding import _geocoding_cache
    
    # Add something to cache
    coords = Coordinates(latitude=40.7128, longitude=-74.0060)
    location_info = LocationInfo(coordinates=coords, state_code="NY")
    _geocoding_cache.set("Test Location", location_info)
    assert len(_geocoding_cache.cache) == 1
    
    # Clear cache
    clear_geocoding_cache()
    assert len(_geocoding_cache.cache) == 0
