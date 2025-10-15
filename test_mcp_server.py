#!/usr/bin/env python3
"""Test script to verify EPA Envirofacts MCP Server is working."""

import asyncio
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.tools.location_summary import get_environmental_summary_by_location


async def test_server():
    """Test the MCP server functionality."""
    print("🧪 Testing EPA Envirofacts MCP Server...")
    
    try:
        # Test with NYC ZIP code
        print("\n📍 Testing with NYC ZIP code (10001)...")
        result = await get_environmental_summary_by_location("10001", radius_miles=2.0)
        
        print(f"✅ Success! Found {result.total_facilities} facilities")
        print(f"   - Water violations: {result.total_violations}")
        print(f"   - Hazardous sites: {result.total_hazardous_sites}")
        print(f"   - Chemical releases: {result.chemical_releases.total_releases} pounds")
        
        if result.top_facilities:
            print(f"   - Nearest facility: {result.top_facilities[0].name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_server())
    sys.exit(0 if success else 1)
