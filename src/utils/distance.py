"""Distance calculation utilities for EPA Envirofacts MCP Server."""

import math
import logging
from typing import List, Tuple

from ..models.common import Coordinates, BoundingBox
from ..models.facility import FacilityInfo


logger = logging.getLogger(__name__)


def calculate_bounding_box(lat: float, lon: float, radius_miles: float) -> BoundingBox:
    """Calculate bounding box for area queries.
    
    Args:
        lat: Center latitude
        lon: Center longitude
        radius_miles: Radius in miles
        
    Returns:
        BoundingBox object
        
    Raises:
        ValueError: If coordinates are invalid
    """
    if not (-90 <= lat <= 90):
        raise ValueError(f"Invalid latitude: {lat}")
    if not (-180 <= lon <= 180):
        raise ValueError(f"Invalid longitude: {lon}")
    if radius_miles <= 0:
        raise ValueError(f"Radius must be positive: {radius_miles}")
    
    # Earth's radius in miles
    earth_radius_miles = 3959.0
    
    # Convert radius to degrees
    lat_delta = radius_miles / earth_radius_miles * (180 / math.pi)
    lon_delta = radius_miles / (earth_radius_miles * math.cos(math.radians(lat))) * (180 / math.pi)
    
    # Calculate bounding box
    min_lat = lat - lat_delta
    max_lat = lat + lat_delta
    min_lon = lon - lon_delta
    max_lon = lon + lon_delta
    
    # Ensure coordinates are within valid ranges
    min_lat = max(min_lat, -90)
    max_lat = min(max_lat, 90)
    min_lon = max(min_lon, -180)
    max_lon = min(max_lon, 180)
    
    return BoundingBox(
        min_latitude=min_lat,
        max_latitude=max_lat,
        min_longitude=min_lon,
        max_longitude=max_lon
    )


def haversine_distance(coord1: Coordinates, coord2: Coordinates) -> float:
    """Calculate distance between two coordinates using Haversine formula.
    
    Args:
        coord1: First coordinates
        coord2: Second coordinates
        
    Returns:
        Distance in miles
    """
    # Earth's radius in miles
    earth_radius_miles = 3959.0
    
    # Convert to radians
    lat1_rad = math.radians(coord1.latitude)
    lat2_rad = math.radians(coord2.latitude)
    delta_lat_rad = math.radians(coord2.latitude - coord1.latitude)
    delta_lon_rad = math.radians(coord2.longitude - coord1.longitude)
    
    # Haversine formula
    a = (math.sin(delta_lat_rad / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon_rad / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))
    
    return earth_radius_miles * c


def filter_by_distance(
    facilities: List[FacilityInfo],
    center: Coordinates,
    max_distance_miles: float
) -> List[FacilityInfo]:
    """Filter facilities by distance from center point.
    
    Args:
        facilities: List of facilities to filter
        center: Center coordinates
        max_distance_miles: Maximum distance in miles
        
    Returns:
        List of facilities within distance, sorted by distance
    """
    filtered_facilities = []
    
    for facility in facilities:
        if facility.coordinates:
            distance = haversine_distance(center, facility.coordinates)
            if distance <= max_distance_miles:
                # Update distance in facility object
                facility.distance_miles = distance
                filtered_facilities.append(facility)
    
    # Sort by distance
    filtered_facilities.sort(key=lambda f: f.distance_miles or float('inf'))
    
    return filtered_facilities


def calculate_distance_matrix(
    coordinates: List[Coordinates]
) -> List[List[float]]:
    """Calculate distance matrix between coordinates.
    
    Args:
        coordinates: List of coordinates
        
    Returns:
        Distance matrix (symmetric)
    """
    n = len(coordinates)
    matrix = [[0.0] * n for _ in range(n)]
    
    for i in range(n):
        for j in range(i + 1, n):
            distance = haversine_distance(coordinates[i], coordinates[j])
            matrix[i][j] = distance
            matrix[j][i] = distance
    
    return matrix
