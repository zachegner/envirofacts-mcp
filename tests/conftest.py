"""Pytest fixtures and shared test utilities."""

import pytest
import asyncio
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock

from src.models.common import Coordinates, BoundingBox
from src.models.facility import FacilityInfo, FacilityType
from src.models.releases import ChemicalRelease
from src.models.water import WaterSystem, WaterViolation
from src.models.summary import EnvironmentalSummary


# Test coordinates for major cities
NYC_COORDS = Coordinates(latitude=40.7128, longitude=-74.0060)
LA_COORDS = Coordinates(latitude=34.0522, longitude=-118.2437)
FLINT_COORDS = Coordinates(latitude=43.0125, longitude=-83.6875)

# Test bounding boxes
NYC_BBOX = BoundingBox(
    min_latitude=40.7,
    max_latitude=40.8,
    min_longitude=-74.1,
    max_longitude=-73.9
)

LA_BBOX = BoundingBox(
    min_latitude=34.0,
    max_latitude=34.1,
    min_longitude=-118.3,
    max_longitude=-118.2
)


@pytest.fixture
def sample_frs_facility():
    """Sample FRS facility record."""
    return {
        "registry_id": "110000123456",
        "facility_name": "Test Chemical Plant",
        "street_address": "123 Industrial Blvd",
        "city_name": "New York",
        "state_abbr": "NY",
        "zip_code": "10001",
        "latitude": "40.7128",
        "longitude": "-74.0060",
        "naics_code": "325199",
        "naics_description": "All Other Basic Organic Chemical Manufacturing",
        "facility_status": "Active"
    }


@pytest.fixture
def sample_tri_facility():
    """Sample TRI facility record."""
    return {
        "registry_id": "110000123456",
        "facility_name": "Test Chemical Plant",
        "street_address": "123 Industrial Blvd",
        "city_name": "New York",
        "state_abbr": "NY",
        "zip_code": "10001",
        "latitude": "40.7128",
        "longitude": "-74.0060",
        "naics_code": "325199",
        "naics_description": "All Other Basic Organic Chemical Manufacturing",
        "facility_status": "Active",
        "reporting_year": "2023"
    }


@pytest.fixture
def sample_tri_release():
    """Sample TRI chemical release record."""
    return {
        "registry_id": "110000123456",
        "facility_name": "Test Chemical Plant",
        "chemical_name": "Benzene",
        "cas_number": "71-43-2",
        "reporting_year": "2023",
        "total_air_release": "1500.5",
        "total_water_release": "250.0",
        "total_land_release": "100.0",
        "total_underground_injection": "0.0",
        "release_type": "On-site"
    }


@pytest.fixture
def sample_water_system():
    """Sample SDWIS water system record."""
    return {
        "pws_id": "NY1234567",
        "pws_name": "New York City Water System",
        "population_served_count": "8000000",
        "latitude": "40.7128",
        "longitude": "-74.0060",
        "state_code": "NY",
        "county_served": "New York",
        "pws_type_code": "CWS",
        "primary_source_code": "SW"
    }


@pytest.fixture
def sample_water_violation():
    """Sample SDWIS water violation record."""
    return {
        "violation_id": "V123456789",
        "pws_id": "NY1234567",
        "pws_name": "New York City Water System",
        "violation_code": "MCL",
        "contaminant_code": "ARSENIC",
        "violation_date": "2023-06-15",
        "compliance_status_code": "Open",
        "is_current_indicator": "Y",
        "enforcement_action_code": "None",
        "population_served_count": "8000000"
    }


@pytest.fixture
def sample_rcra_site():
    """Sample RCRA site record."""
    return {
        "handler_id": "NYD123456789",
        "handler_name": "Test Hazardous Waste Facility",
        "street_address": "456 Waste Way",
        "city_name": "New York",
        "state_abbr": "NY",
        "zip_code": "10001",
        "latitude": "40.7128",
        "longitude": "-74.0060",
        "naics_code": "562211",
        "naics_description": "Hazardous Waste Treatment and Disposal",
        "handler_type": "TSD"
    }


@pytest.fixture
def sample_facility_info():
    """Sample FacilityInfo object."""
    return FacilityInfo(
        registry_id="110000123456",
        name="Test Chemical Plant",
        address="123 Industrial Blvd, New York, NY 10001",
        city="New York",
        state="NY",
        zip_code="10001",
        coordinates=NYC_COORDS,
        programs=[FacilityType.TRI, FacilityType.FRS],
        naics_code="325199",
        naics_description="All Other Basic Organic Chemical Manufacturing",
        distance_miles=2.5,
        status="Active"
    )


@pytest.fixture
def sample_chemical_release():
    """Sample ChemicalRelease object."""
    return ChemicalRelease(
        facility_id="110000123456",
        facility_name="Test Chemical Plant",
        chemical_name="Benzene",
        cas_number="71-43-2",
        reporting_year=2023,
        air_release=1500.5,
        water_release=250.0,
        land_release=100.0,
        underground_injection=0.0,
        release_type="On-site",
        units="pounds"
    )


@pytest.fixture
def sample_water_system_obj():
    """Sample WaterSystem object."""
    return WaterSystem(
        system_id="NY1234567",
        name="New York City Water System",
        population_served=8000000,
        coordinates=NYC_COORDS,
        state="NY",
        county="New York",
        system_type="CWS",
        primary_source="SW",
        distance_miles=1.2
    )


@pytest.fixture
def sample_water_violation_obj():
    """Sample WaterViolation object."""
    return WaterViolation(
        violation_id="V123456789",
        system_id="NY1234567",
        system_name="New York City Water System",
        violation_type="MCL",
        contaminant="ARSENIC",
        violation_date="2023-06-15",
        compliance_status="Open",
        is_current=True,
        enforcement_action="None",
        population_affected=8000000
    )


@pytest.fixture
def sample_environmental_summary():
    """Sample EnvironmentalSummary object."""
    return EnvironmentalSummary(
        location="New York, NY",
        coordinates=NYC_COORDS,
        radius_miles=5.0,
        facility_counts={"TRI": 5, "RCRA": 3, "SDWIS": 2, "FRS": 8},
        total_facilities=8,
        top_facilities=[sample_facility_info()],
        water_systems=[sample_water_system_obj()],
        water_violations=[sample_water_violation_obj()],
        total_violations=1,
        chemical_releases=sample_chemical_release(),
        hazardous_sites=[sample_facility_info()],
        total_hazardous_sites=1,
        summary_stats={
            "search_radius_miles": 5.0,
            "total_population_served": 8000000,
            "active_violation_count": 1
        },
        query_timestamp="2023-12-01T12:00:00Z",
        data_sources=["FRS", "TRI", "SDWIS", "RCRA"]
    )


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient for testing."""
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.json.return_value = []
    mock_response.raise_for_status.return_value = None
    mock_client.get.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_geocoder():
    """Mock geopy geocoder for testing."""
    mock_location = MagicMock()
    mock_location.latitude = 40.7128
    mock_location.longitude = -74.0060
    mock_location.raw = {
        'address': {
            'ISO3166-2-lvl4': 'US-NY',
            'state': 'New York',
            'county': 'New York County',
            'country': 'United States'
        }
    }
    
    mock_geocoder = MagicMock()
    mock_geocoder.geocode.return_value = mock_location
    return mock_geocoder


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# EPA API response fixtures
@pytest.fixture
def frs_api_response():
    """Sample FRS API response."""
    return [
        {
            "registry_id": "110000123456",
            "primary_name": "Test Chemical Plant",
            "location_address": "123 Industrial Blvd",
            "city_name": "New York",
            "state_code": "NY",
            "postal_code": "10001",
            "naics_code": "325199",
            "naics_description": "All Other Basic Organic Chemical Manufacturing",
            "operating_status": "Active"
        }
    ]


@pytest.fixture
def tri_api_response():
    """Sample TRI API response."""
    return [
        {
            "tri_facility_id": "110000123456",
            "facility_name": "Test Chemical Plant",
            "chemical_name": "Benzene",
            "cas_number": "71-43-2",
            "reporting_year": "2023",
            "total_air_release": "1500.5",
            "total_water_release": "250.0",
            "total_land_release": "100.0",
            "total_underground_injection": "0.0",
            "release_type": "On-site",
            "pref_latitude": "40.7128",
            "pref_longitude": "-74.0060",
            "street_address": "123 Industrial Blvd",
            "city_name": "New York",
            "state_abbr": "NY",
            "zip_code": "10001",
            "naics_code": "325199",
            "naics_description": "All Other Basic Organic Chemical Manufacturing"
        }
    ]


@pytest.fixture
def sdwis_api_response():
    """Sample SDWIS API response."""
    return [
        {
            "pws_id": "NY1234567",
            "pws_name": "New York City Water System",
            "population_served_count": "8000000",
            "latitude": "40.7128",
            "longitude": "-74.0060",
            "state_code": "NY",
            "county_served": "New York",
            "pws_type_code": "CWS",
            "primary_source_code": "SW"
        }
    ]


@pytest.fixture
def rcra_api_response():
    """Sample RCRA API response."""
    return [
        {
            "handler_id": "NYD123456789",
            "handler_name": "Test Hazardous Waste Facility",
            "street_address": "456 Waste Way",
            "city_name": "New York",
            "state_abbr": "NY",
            "zip_code": "10001",
            "latitude": "40.7128",
            "longitude": "-74.0060",
            "naics_code": "562211",
            "naics_description": "Hazardous Waste Treatment and Disposal",
            "handler_type": "TSD"
        }
    ]
