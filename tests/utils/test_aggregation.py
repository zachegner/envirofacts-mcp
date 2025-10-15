"""Unit tests for data aggregation utilities."""

import pytest
from datetime import date

from src.utils.aggregation import (
    aggregate_facilities,
    rank_facilities,
    summarize_releases,
    format_environmental_summary
)
from src.models.facility import FacilityInfo, FacilityType
from src.models.releases import ChemicalRelease, ReleaseSummary
from src.models.water import WaterSystem, WaterViolation
from src.models.summary import EnvironmentalSummary
from src.models.common import Coordinates


class TestAggregateFacilities:
    """Test cases for aggregate_facilities function."""
    
    @pytest.fixture
    def sample_facilities(self):
        """Sample facilities for testing."""
        frs_facility = FacilityInfo(
            registry_id="110000123456",
            name="Test Chemical Plant",
            programs=[FacilityType.FRS],
            coordinates=Coordinates(latitude=40.7128, longitude=-74.0060)
        )
        
        tri_facility = FacilityInfo(
            registry_id="110000123456",  # Same registry ID
            name="Test Chemical Plant",
            programs=[FacilityType.TRI],
            coordinates=Coordinates(latitude=40.7128, longitude=-74.0060)
        )
        
        rcra_facility = FacilityInfo(
            registry_id="110000789012",
            name="Test Waste Site",
            programs=[FacilityType.RCRA],
            coordinates=Coordinates(latitude=40.7200, longitude=-74.0100)
        )
        
        water_system = WaterSystem(
            system_id="NY1234567",
            name="Test Water System",
            coordinates=Coordinates(latitude=40.7150, longitude=-74.0050)
        )
        
        return [frs_facility], [tri_facility], [rcra_facility], [water_system]
    
    def test_aggregate_facilities_merge_programs(self, sample_facilities):
        """Test facility aggregation with program merging."""
        frs, tri, rcra, water = sample_facilities
        
        result = aggregate_facilities(frs, tri, rcra, water)
        
        # Should have 3 unique facilities (FRS+TRI merged, RCRA, Water)
        assert len(result) == 3
        
        # Find the merged facility
        merged_facility = next(f for f in result if f.registry_id == "110000123456")
        assert FacilityType.FRS in merged_facility.programs
        assert FacilityType.TRI in merged_facility.programs
        
        # Find RCRA facility
        rcra_facility = next(f for f in result if f.registry_id == "110000789012")
        assert FacilityType.RCRA in rcra_facility.programs
        
        # Find water system (converted to facility)
        water_facility = next(f for f in result if f.registry_id == "NY1234567")
        assert FacilityType.SDWIS in water_facility.programs
    
    def test_aggregate_facilities_empty_inputs(self):
        """Test facility aggregation with empty inputs."""
        result = aggregate_facilities([], [], [], [])
        assert result == []
    
    def test_aggregate_facilities_no_registry_id(self):
        """Test facility aggregation with facilities missing registry_id."""
        facility_no_id = FacilityInfo(
            registry_id="",
            name="No ID Facility",
            programs=[FacilityType.FRS]
        )
        
        result = aggregate_facilities([facility_no_id], [], [], [])
        
        # Should still include the facility
        assert len(result) == 1
        assert result[0].name == "No ID Facility"


class TestRankFacilities:
    """Test cases for rank_facilities function."""
    
    @pytest.fixture
    def sample_facilities_with_distance(self):
        """Sample facilities with distances for testing."""
        return [
            FacilityInfo(
                registry_id="1",
                name="Far Facility",
                distance_miles=10.0,
                programs=[FacilityType.FRS]
            ),
            FacilityInfo(
                registry_id="2",
                name="Near Facility",
                distance_miles=1.0,
                programs=[FacilityType.FRS]
            ),
            FacilityInfo(
                registry_id="3",
                name="No Distance",
                distance_miles=None,
                programs=[FacilityType.FRS]
            ),
            FacilityInfo(
                registry_id="4",
                name="Medium Facility",
                distance_miles=5.0,
                programs=[FacilityType.FRS]
            )
        ]
    
    def test_rank_facilities_by_distance(self, sample_facilities_with_distance):
        """Test facility ranking by distance."""
        result = rank_facilities(sample_facilities_with_distance, limit=10)
        
        # Should be sorted by distance (None goes to end)
        assert len(result) == 4
        assert result[0].distance_miles == 1.0  # Nearest first
        assert result[1].distance_miles == 5.0
        assert result[2].distance_miles == 10.0
        assert result[3].distance_miles is None  # No distance last
    
    def test_rank_facilities_with_limit(self, sample_facilities_with_distance):
        """Test facility ranking with limit."""
        result = rank_facilities(sample_facilities_with_distance, limit=2)
        
        assert len(result) == 2
        assert result[0].distance_miles == 1.0
        assert result[1].distance_miles == 5.0
    
    def test_rank_facilities_empty(self):
        """Test facility ranking with empty list."""
        result = rank_facilities([], limit=10)
        assert result == []


class TestSummarizeReleases:
    """Test cases for summarize_releases function."""
    
    @pytest.fixture
    def sample_releases(self):
        """Sample chemical releases for testing."""
        return [
            ChemicalRelease(
                facility_id="110000123456",
                facility_name="Plant A",
                chemical_name="Benzene",
                cas_number="71-43-2",
                reporting_year=2023,
                air_release=1000.0,
                water_release=200.0,
                land_release=50.0,
                underground_injection=0.0
            ),
            ChemicalRelease(
                facility_id="110000123456",
                facility_name="Plant A",
                chemical_name="Toluene",
                cas_number="108-88-3",
                reporting_year=2023,
                air_release=500.0,
                water_release=100.0,
                land_release=25.0,
                underground_injection=0.0
            ),
            ChemicalRelease(
                facility_id="110000789012",
                facility_name="Plant B",
                chemical_name="Benzene",
                cas_number="71-43-2",
                reporting_year=2023,
                air_release=800.0,
                water_release=150.0,
                land_release=30.0,
                underground_injection=0.0
            )
        ]
    
    def test_summarize_releases_success(self, sample_releases):
        """Test successful release summarization."""
        result = summarize_releases(sample_releases)
        
        assert isinstance(result, ReleaseSummary)
        assert result.total_facilities == 2  # Two unique facilities
        assert result.total_chemicals == 2  # Two unique chemicals
        assert result.total_releases == 1955.0  # Sum of all releases
        assert result.air_releases == 2300.0  # Sum of air releases
        assert result.water_releases == 450.0  # Sum of water releases
        assert result.land_releases == 105.0  # Sum of land releases
        assert result.underground_injections == 0.0
        assert result.reporting_year == 2023
        
        # Check top chemicals
        assert len(result.top_chemicals) == 2
        assert result.top_chemicals[0]["chemical"] == "Benzene"  # Highest total
        assert result.top_chemicals[0]["total_release"] == 1800.0
        assert result.top_chemicals[1]["chemical"] == "Toluene"
        assert result.top_chemicals[1]["total_release"] == 155.0
    
    def test_summarize_releases_empty(self):
        """Test release summarization with empty list."""
        result = summarize_releases([])
        
        assert isinstance(result, ReleaseSummary)
        assert result.total_facilities == 0
        assert result.total_chemicals == 0
        assert result.total_releases == 0.0
        assert result.reporting_year == 2023  # Default year
    
    def test_summarize_releases_none_values(self):
        """Test release summarization with None values."""
        releases = [
            ChemicalRelease(
                facility_id="1",
                facility_name="Test Plant",
                chemical_name="Test Chemical",
                reporting_year=2023,
                air_release=None,
                water_release=100.0,
                land_release=None,
                underground_injection=0.0
            )
        ]
        
        result = summarize_releases(releases)
        
        assert result.air_releases == 0.0  # None treated as 0
        assert result.water_releases == 100.0
        assert result.land_releases == 0.0
        assert result.total_releases == 100.0


class TestFormatEnvironmentalSummary:
    """Test cases for format_environmental_summary function."""
    
    @pytest.fixture
    def sample_data(self):
        """Sample data for environmental summary."""
        coordinates = Coordinates(latitude=40.7128, longitude=-74.0060)
        
        facilities = [
            FacilityInfo(
                registry_id="1",
                name="Test Facility",
                programs=[FacilityType.TRI, FacilityType.FRS],
                distance_miles=2.5
            )
        ]
        
        water_systems = [
            WaterSystem(
                system_id="NY1234567",
                name="Test Water System",
                population_served=1000000,
                distance_miles=1.0
            )
        ]
        
        water_violations = [
            WaterViolation(
                violation_id="V1",
                system_id="NY1234567",
                system_name="Test Water System",
                violation_type="MCL",
                is_current=True
            )
        ]
        
        chemical_releases = [
            ChemicalRelease(
                facility_id="1",
                facility_name="Test Facility",
                chemical_name="Benzene",
                reporting_year=2023,
                air_release=1000.0
            )
        ]
        
        hazardous_sites = [
            FacilityInfo(
                registry_id="2",
                name="Test Hazardous Site",
                programs=[FacilityType.RCRA],
                distance_miles=3.0
            )
        ]
        
        return (
            "New York, NY", coordinates, 5.0, facilities, water_systems,
            water_violations, chemical_releases, hazardous_sites
        )
    
    def test_format_environmental_summary_success(self, sample_data):
        """Test successful environmental summary formatting."""
        result = format_environmental_summary(*sample_data)
        
        assert isinstance(result, EnvironmentalSummary)
        assert result.location == "New York, NY"
        assert result.coordinates.latitude == 40.7128
        assert result.radius_miles == 5.0
        
        # Check facility counts
        assert result.facility_counts["TRI"] == 1
        assert result.facility_counts["FRS"] == 1
        assert result.facility_counts["RCRA"] == 1
        assert result.total_facilities == 1
        
        # Check water data
        assert len(result.water_systems) == 1
        assert len(result.water_violations) == 1
        assert result.total_violations == 1
        
        # Check chemical releases
        assert isinstance(result.chemical_releases, ReleaseSummary)
        assert result.chemical_releases.total_facilities == 1
        assert result.chemical_releases.total_chemicals == 1
        
        # Check hazardous sites
        assert len(result.hazardous_sites) == 1
        assert result.total_hazardous_sites == 1
        
        # Check summary stats
        assert result.summary_stats["search_radius_miles"] == 5.0
        assert result.summary_stats["total_population_served"] == 1000000
        assert result.summary_stats["active_violation_count"] == 1
        
        # Check metadata
        assert result.query_timestamp is not None
        assert "FRS" in result.data_sources
        assert "TRI" in result.data_sources
        assert "SDWIS" in result.data_sources
        assert "RCRA" in result.data_sources
    
    def test_format_environmental_summary_empty_data(self):
        """Test environmental summary formatting with empty data."""
        coordinates = Coordinates(latitude=40.7128, longitude=-74.0060)
        
        result = format_environmental_summary(
            "Test Location", coordinates, 5.0, [], [], [], [], []
        )
        
        assert result.total_facilities == 0
        assert result.total_violations == 0
        assert result.total_hazardous_sites == 0
        assert result.summary_stats["total_population_served"] == 0
        assert result.summary_stats["active_violation_count"] == 0
