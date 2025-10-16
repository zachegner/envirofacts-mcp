"""EPA Envirofacts MCP Server - Main entry point."""

import asyncio
import logging
import sys
from typing import Dict, Any

import structlog
from fastmcp import FastMCP

from config import settings
from src.tools.location_summary import register_tool
from src.tools.search_facilities import register_tool as register_search_tool
from src.tools.compliance_history import register_tool as register_compliance_tool


# Configure structured logging
def configure_logging():
    """Configure structured logging with structlog."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Set log level
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(message)s",
        stream=sys.stdout
    )


# Initialize FastMCP server with proper MCP configuration
mcp = FastMCP(
    name="epa-envirofacts",
    version="1.0.0"
)


@mcp.tool()
async def health_check() -> Dict[str, Any]:
    """System health and API connectivity check.
    
    Returns:
        Health status information including EPA API connectivity
    """
    try:
        from src.client import FRSClient
        
        # Test EPA API connectivity
        async with FRSClient() as client:
            health_status = await client.health_check()
        
        return {
            "status": "healthy",
            "version": "1.0.0",
            "server_name": "epa-envirofacts",
            "epa_api": health_status,
            "timestamp": structlog.get_logger().info("Health check completed")
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "version": "1.0.0", 
            "server_name": "epa-envirofacts",
            "error": str(e),
            "timestamp": structlog.get_logger().error(f"Health check failed: {e}")
        }


def main():
    """Main entry point for the EPA Envirofacts MCP Server."""
    # Configure logging
    configure_logging()
    logger = structlog.get_logger()
    
    logger.info("Starting EPA Envirofacts MCP Server", version="1.0.0")
    
    # Register tools
    register_tool(mcp)
    register_search_tool(mcp)
    register_compliance_tool(mcp)
    
    logger.info("Registered tools", tools=["environmental_summary_by_location", "search_facilities", "get_facility_compliance_history", "health_check"])
    
    # Run the server with proper MCP protocol support
    try:
        # FastMCP handles MCP protocol automatically
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error("Server error", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
