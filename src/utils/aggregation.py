"""Data aggregation utilities for EPA Envirofacts MCP Server."""

import logging
from typing import List, Dict, Any, Set, Optional
from collections import defaultdict, Counter
from datetime import datetime

from ..models.facility import FacilityInfo, FacilityType
from ..models.releases import ChemicalRelease, ReleaseSummary
from ..models.water import WaterSystem, WaterViolation
from ..models.summary import EnvironmentalSummary
from ..models.common import Coordinates


logger = logging.getLogger(__name__)


def aggregate_facilities(
    frs_facilities: List[FacilityInfo],
    tri_facilities: List[FacilityInfo],
    rcra_facilities: List[FacilityInfo],
    sdwis_systems: List[WaterSystem]
) -> List[FacilityInfo]:
    """Aggregate and deduplicate facilities from multiple sources.
    
    Args:
        frs_facilities: FRS facilities
        tri_facilities: TRI facilities
        rcra_facilities: RCRA facilities
        sdwis_systems: SDWIS water systems
        
    Returns:
        List of deduplicated facilities
    """
    # Use registry_id as primary key for deduplication
    facility_map: Dict[str, FacilityInfo] = {}
    
    # Process FRS facilities first (they have the most complete info)
    for facility in frs_facilities:
        if facility.registry_id:
            facility_map[facility.registry_id] = facility
    
    # Add TRI facilities, merging programs
    for facility in tri_facilities:
        if facility.registry_id in facility_map:
            # Merge programs
            existing = facility_map[facility.registry_id]
            programs = set(existing.programs)
            programs.update(facility.programs)
            existing.programs = list(programs)
        else:
            facility_map[facility.registry_id] = facility
    
    # Add RCRA facilities, merging programs
    for facility in rcra_facilities:
        if facility.registry_id in facility_map:
            # Merge programs
            existing = facility_map[facility.registry_id]
            programs = set(existing.programs)
            programs.update(facility.programs)
            existing.programs = list(programs)
        else:
            facility_map[facility.registry_id] = facility
    
    # Convert SDWIS systems to facilities (they don't have registry_id)
    for system in sdwis_systems:
        # Use system_id as registry_id for water systems
        facility = FacilityInfo(
            registry_id=system.system_id,
            name=system.name,
            address=None,
            city=None,
            state=system.state,
            zip_code=None,
            coordinates=system.coordinates,
            programs=[FacilityType.SDWIS],
            distance_miles=system.distance_miles
        )
        facility_map[system.system_id] = facility
    
    return list(facility_map.values())


def rank_facilities(facilities: List[FacilityInfo], limit: int = 50) -> List[FacilityInfo]:
    """Rank facilities by distance and limit results.
    
    Args:
        facilities: List of facilities
        limit: Maximum number of facilities to return
        
    Returns:
        Top facilities ranked by distance
    """
    # Sort by distance (None distances go to end)
    sorted_facilities = sorted(
        facilities,
        key=lambda f: f.distance_miles if f.distance_miles is not None else float('inf')
    )
    
    return sorted_facilities[:limit]


def summarize_releases(releases: List[ChemicalRelease]) -> ReleaseSummary:
    """Summarize chemical release data.
    
    Args:
        releases: List of chemical releases
        
    Returns:
        ReleaseSummary object
    """
    if not releases:
        return ReleaseSummary(
            total_facilities=0,
            total_chemicals=0,
            total_releases=0.0,
            reporting_year=2023
        )
    
    # Get unique facilities and chemicals
    facilities = set(r.facility_id for r in releases)
    chemicals = set(r.chemical_name for r in releases)
    
    # Calculate totals by medium
    air_total = sum(r.air_release or 0 for r in releases)
    water_total = sum(r.water_release or 0 for r in releases)
    land_total = sum(r.land_release or 0 for r in releases)
    underground_total = sum(r.underground_injection or 0 for r in releases)
    
    total_releases = air_total + water_total + land_total + underground_total
    
    # Get top chemicals by total release
    chemical_totals = defaultdict(float)
    for release in releases:
        chemical_totals[release.chemical_name] += release.total_release
    
    top_chemicals = [
        {"chemical": chem, "total_release": total}
        for chem, total in Counter(chemical_totals).most_common(10)
    ]
    
    # Get reporting year (use most common year)
    years = [r.reporting_year for r in releases]
    reporting_year = Counter(years).most_common(1)[0][0] if years else 2023
    
    return ReleaseSummary(
        total_facilities=len(facilities),
        total_chemicals=len(chemicals),
        total_releases=total_releases,
        air_releases=air_total,
        water_releases=water_total,
        land_releases=land_total,
        underground_injections=underground_total,
        top_chemicals=top_chemicals,
        reporting_year=reporting_year
    )


def format_environmental_summary(
    location: str,
    coordinates: Optional[Coordinates],
    radius_miles: float,
    facilities: List[FacilityInfo],
    water_systems: List[WaterSystem],
    water_violations: List[WaterViolation],
    chemical_releases: List[ChemicalRelease],
    hazardous_sites: List[FacilityInfo]
) -> EnvironmentalSummary:
    """Format comprehensive environmental summary.
    
    Args:
        location: Original location query
        coordinates: Resolved coordinates
        radius_miles: Search radius
        facilities: All facilities found
        water_systems: Water systems in area
        water_violations: Water violations
        chemical_releases: Chemical releases
        hazardous_sites: Hazardous waste sites
        
    Returns:
        EnvironmentalSummary object
    """
    # Count facilities by type
    facility_counts = defaultdict(int)
    for facility in facilities:
        for program in facility.programs:
            facility_counts[program.value] += 1
    
    # Count active violations
    active_violations = [v for v in water_violations if v.is_current]
    
    # Summarize chemical releases
    release_summary = summarize_releases(chemical_releases)
    
    # Create summary statistics
    summary_stats = {
        "search_radius_miles": radius_miles,
        "total_population_served": sum(ws.population_served or 0 for ws in water_systems),
        "active_violation_count": len(active_violations),
        "facilities_with_releases": len(set(r.facility_id for r in chemical_releases)),
        "unique_chemicals": len(set(r.chemical_name for r in chemical_releases)),
        "hazardous_waste_sites": len(hazardous_sites)
    }
    
    return EnvironmentalSummary(
        location=location,
        coordinates=coordinates,
        radius_miles=radius_miles,
        facility_counts=dict(facility_counts),
        total_facilities=len(facilities),
        top_facilities=facilities[:50],  # Already ranked by distance
        water_systems=water_systems,
        water_violations=active_violations,
        total_violations=len(active_violations),
        chemical_releases=release_summary,
        hazardous_sites=hazardous_sites,
        total_hazardous_sites=len(hazardous_sites),
        summary_stats=summary_stats,
        query_timestamp=datetime.utcnow().isoformat(),
        data_sources=["FRS", "TRI", "SDWIS", "RCRA"]
    )
