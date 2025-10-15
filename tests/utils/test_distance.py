"""Unit tests for distance calculation utilities."""

import pytest
import math

from src.utils.distance import (
    calculate_bounding_box,
    haversine_distance,
    filter_by_distance,
    calculate_distance_matrix
)
from src.models.common import Coordinates, BoundingBox
from src.models.facility import FacilityInfo, FacilityType


class TestCalculateBoundingBox:
    """Test cases for calculate_bounding_box function."""
    
    def test_valid_coordinates(self):
        """Test bounding box calculation with valid coordinates."""
        bbox = calculate_bounding_box(40.7128, -74.0060, 5.0)
        
        assert isinstance(bbox, BoundingBox)
        assert bbox.min_latitude < 40.7128 < bbox.max_latitude
        assert bbox.min_longitude < -74.0060 < bbox.max_longitude
        
        # Check that the box is roughly square (within reasonable bounds)
        lat_range = bbox.max_latitude - bbox.min_latitude
        lon_range = bbox.max_longitude - bbox.min_longitude
        assert abs(lat_range - lon_range) < 0.1  # Should be roughly equal
    
    def test_invalid_latitude(self):
        """Test bounding box calculation with invalid latitude."""
        with pytest.raises(ValueError, match="Invalid latitude"):
            calculate_bounding_box(91.0, -74.0060, 5.0)
        
        with pytest.raises(ValueError, match="Invalid latitude"):
            calculate_bounding_box(-91.0, -74.0060, 5.0)
    
    def test_invalid_longitude(self):
        """Test bounding box calculation with invalid longitude."""
        with pytest.raises(ValueError, match="Invalid longitude"):
            calculate_bounding_box(40.7128, 181.0, 5.0)
        
        with pytest.raises(ValueError, match="Invalid longitude"):
            calculate_bounding_box(40.7128, -181.0, 5.0)
    
    def test_invalid_radius(self):
        """Test bounding box calculation with invalid radius."""
        with pytest.raises(ValueError, match="Radius must be positive"):
            calculate_bounding_box(40.7128, -74.0060, 0.0)
        
        with pytest.raises(ValueError, match="Radius must be positive"):
            calculate_bounding_box(40.7128, -74.0060, -5.0)
    
    def test_coordinate_bounds(self):
        """Test that bounding box coordinates stay within valid ranges."""
        # Test near the poles
        bbox = calculate_bounding_box(89.0, 0.0, 10.0)
        assert bbox.max_latitude <= 90.0
        assert bbox.min_latitude >= -90.0
        
        # Test near the date line
        bbox = calculate_bounding_box(0.0, 179.0, 10.0)
        assert bbox.max_longitude <= 180.0
        assert bbox.min_longitude >= -180.0


class TestHaversineDistance:
    """Test cases for haversine_distance function."""
    
    def test_same_coordinates(self):
        """Test distance calculation with same coordinates."""
        coords = Coordinates(latitude=40.7128, longitude=-74.0060)
        distance = haversine_distance(coords, coords)
        
        assert distance == 0.0
    
    def test_known_distance(self):
        """Test distance calculation with known coordinates."""
        # Distance between NYC and LA should be approximately 2445 miles
        nyc = Coordinates(latitude=40.7128, longitude=-74.0060)
        la = Coordinates(latitude=34.0522, longitude=-118.2437)
        
        distance = haversine_distance(nyc, la)
        
        # Allow for some margin of error
        assert 2400 < distance < 2500
    
    def test_short_distance(self):
        """Test distance calculation for short distances."""
        # Two points about 1 mile apart
        point1 = Coordinates(latitude=40.7128, longitude=-74.0060)
        point2 = Coordinates(latitude=40.7200, longitude=-74.0060)
        
        distance = haversine_distance(point1, point2)
        
        # Should be approximately 0.5 miles
        assert 0.4 < distance < 0.6
    
    def test_opposite_sides_of_earth(self):
        """Test distance calculation for opposite sides of Earth."""
        # Points on opposite sides of Earth
        point1 = Coordinates(latitude=0.0, longitude=0.0)
        point2 = Coordinates(latitude=0.0, longitude=180.0)
        
        distance = haversine_distance(point1, point2)
        
        # Should be approximately half the Earth's circumference
        assert 12000 < distance < 13000


class TestFilterByDistance:
    """Test cases for filter_by_distance function."""
    
    @pytest.fixture
    def sample_facilities(self):
        """Sample facilities for testing."""
        center = Coordinates(latitude=40.7128, longitude=-74.0060)
        
        facilities = [
            FacilityInfo(
                registry_id="1",
                name="Nearby Facility",
                coordinates=Coordinates(latitude=40.7200, longitude=-74.0060),
                programs=[FacilityType.FRS]
            ),
            FacilityInfo(
                registry_id="2", 
                name="Far Facility",
                coordinates=Coordinates(latitude=41.0000, longitude=-74.0000),
                programs=[FacilityType.FRS]
            ),
            FacilityInfo(
                registry_id="3",
                name="No Coordinates",
                coordinates=None,
                programs=[FacilityType.FRS]
            )
        ]
        
        return facilities, center
    
    def test_filter_by_distance(self, sample_facilities):
        """Test filtering facilities by distance."""
        facilities, center = sample_facilities
        
        filtered = filter_by_distance(facilities, center, max_distance_miles=10.0)
        
        # Should include nearby facility and exclude far facility and no-coordinates facility
        assert len(filtered) == 1
        assert filtered[0].registry_id == "1"
        assert filtered[0].distance_miles is not None
        assert filtered[0].distance_miles <= 10.0
    
    def test_filter_by_distance_sorted(self, sample_facilities):
        """Test that filtered facilities are sorted by distance."""
        facilities, center = sample_facilities
        
        # Add another nearby facility
        facilities.append(
            FacilityInfo(
                registry_id="4",
                name="Closer Facility",
                coordinates=Coordinates(latitude=40.7150, longitude=-74.0060),
                programs=[FacilityType.FRS]
            )
        )
        
        filtered = filter_by_distance(facilities, center, max_distance_miles=10.0)
        
        # Should be sorted by distance
        assert len(filtered) == 2
        assert filtered[0].distance_miles <= filtered[1].distance_miles
    
    def test_filter_by_distance_empty(self, sample_facilities):
        """Test filtering with no facilities within distance."""
        facilities, center = sample_facilities
        
        filtered = filter_by_distance(facilities, center, max_distance_miles=0.1)
        
        assert len(filtered) == 0


class TestCalculateDistanceMatrix:
    """Test cases for calculate_distance_matrix function."""
    
    def test_distance_matrix(self):
        """Test distance matrix calculation."""
        coords = [
            Coordinates(latitude=40.7128, longitude=-74.0060),  # NYC
            Coordinates(latitude=34.0522, longitude=-118.2437),  # LA
            Coordinates(latitude=43.0125, longitude=-83.6875)   # Flint
        ]
        
        matrix = calculate_distance_matrix(coords)
        
        # Should be 3x3 matrix
        assert len(matrix) == 3
        assert all(len(row) == 3 for row in matrix)
        
        # Should be symmetric
        assert matrix[0][1] == matrix[1][0]
        assert matrix[0][2] == matrix[2][0]
        assert matrix[1][2] == matrix[2][1]
        
        # Diagonal should be zero
        assert matrix[0][0] == 0.0
        assert matrix[1][1] == 0.0
        assert matrix[2][2] == 0.0
        
        # All distances should be positive
        assert matrix[0][1] > 0
        assert matrix[0][2] > 0
        assert matrix[1][2] > 0
    
    def test_distance_matrix_single_point(self):
        """Test distance matrix with single point."""
        coords = [Coordinates(latitude=40.7128, longitude=-74.0060)]
        
        matrix = calculate_distance_matrix(coords)
        
        assert len(matrix) == 1
        assert matrix[0][0] == 0.0
    
    def test_distance_matrix_empty(self):
        """Test distance matrix with empty list."""
        coords = []
        
        matrix = calculate_distance_matrix(coords)
        
        assert len(matrix) == 0
