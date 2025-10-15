# EPA Envirofacts MCP Server

<div align="center">

[![MCP](https://img.shields.io/badge/MCP-Compatible-blue)](https://modelcontextprotocol.io)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Model Context Protocol (MCP) server that provides AI agents with structured access to U.S. EPA environmental data through the Envirofacts API.

[Features](#features) •
[Installation](#installation) •
[Usage](#usage) •
[Configuration](#configuration) •
[Contributing](#contributing)

</div>

---

## Features

- **Environmental Summary by Location**: Get comprehensive environmental data for any U.S. location including:
  - Nearby regulated facilities (TRI, RCRA, SDWIS, FRS)
  - Chemical release data from Toxics Release Inventory
  - Safe Drinking Water Act violations
  - Hazardous waste sites
  - Distance-based ranking and filtering
- **Geocoding Support**: Convert addresses, cities, and ZIP codes to coordinates
- **Robust Error Handling**: Retry logic, timeout handling, and graceful degradation
- **Modular Architecture**: Easy to extend with additional EPA data tools
- **Comprehensive Testing**: Unit tests with mocks and integration tests with live API

## Installation

### Quick Start (Recommended)

Install using [uv](https://github.com/astral-sh/uv) (fastest method):

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install
git clone https://github.com/zachegner/envirofacts-mcp
cd envirofacts-mcp
uv sync
```

### Alternative: Traditional Installation

**Prerequisites:**
- Python 3.11 or higher
- pip (Python package manager)

**Steps:**

```bash
# Clone the repository
git clone https://github.com/zachegner/envirofacts-mcp
cd envirofacts-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

### Using with Claude Desktop or Other MCP Clients

Add this configuration to your MCP client settings (e.g., `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "epa-envirofacts": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/envirofacts-mcp",
        "run",
        "python",
        "server.py"
      ]
    }
  }
}
```

Or with traditional installation:

```json
{
  "mcpServers": {
    "epa-envirofacts": {
      "command": "python",
      "args": ["/absolute/path/to/envirofacts-mcp/server.py"]
    }
  }
}
```

### Configuration (Optional)

Create a `.env` file for custom settings:

```bash
cp .env.example .env
# Edit .env with your preferred settings
```

## Configuration

The server can be configured through environment variables or a `.env` file:

```bash
# EPA API Configuration
EPA_API_BASE_URL=https://data.epa.gov/efservice/
REQUEST_TIMEOUT=300
RETRY_ATTEMPTS=3
MAX_RESULTS_PER_QUERY=1000

# Geocoding Configuration
GEOCODING_SERVICE=nominatim
GEOCODING_USER_AGENT=epa-envirofacts-mcp/1.0
GEOCODING_API_KEY=

# Logging Configuration
LOG_LEVEL=INFO
```

### Configuration Options

- `EPA_API_BASE_URL`: Base URL for EPA Envirofacts API (default: https://data.epa.gov/efservice/)
- `REQUEST_TIMEOUT`: Request timeout in seconds (default: 300)
- `RETRY_ATTEMPTS`: Number of retry attempts for failed requests (default: 3)
- `MAX_RESULTS_PER_QUERY`: Maximum results per API query (default: 1000)
- `GEOCODING_SERVICE`: Geocoding service to use (default: nominatim)
- `GEOCODING_USER_AGENT`: User agent string for geocoding requests
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## Usage

### Running the Server

#### With uv (Recommended)

```bash
uv run python server.py
```

#### Traditional Method

```bash
# Make sure your virtual environment is activated
source venv/bin/activate  # On Windows: venv\Scripts\activate
python server.py
```

The server will start and register the available tools. You can then connect to it using an MCP client (like Claude Desktop).

### Connecting to Claude Desktop

1. Open your Claude Desktop configuration file:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. Add the EPA Envirofacts MCP server:

```json
{
  "mcpServers": {
    "epa-envirofacts": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/yourusername/path/to/envirofacts-mcp",
        "run",
        "python",
        "server.py"
      ]
    }
  }
}
```

3. Restart Claude Desktop

4. Look for the 🔌 icon to confirm the server is connected

### Available Tools

#### 1. Environmental Summary by Location

Get comprehensive environmental data for any U.S. location.

**Parameters:**
- `location` (string): Address, city, or ZIP code (e.g., "New York, NY", "10001", "Los Angeles, CA")
- `radius_miles` (float, optional): Search radius in miles (default: 5.0, max: 100.0)

**Returns:**
- Location coordinates and search parameters
- Count of facilities by type (TRI, RCRA, SDWIS, FRS)
- Top facilities ranked by distance
- Water systems and active violations
- Chemical release summary with top chemicals
- Hazardous waste sites
- Summary statistics

**Example Usage:**
```python
# Get environmental summary for NYC
summary = await get_environmental_summary_by_location("10001", radius_miles=3.0)

print(f"Found {summary.total_facilities} facilities")
print(f"Active water violations: {summary.total_violations}")
print(f"Chemical releases: {summary.chemical_releases.total_releases} pounds")
```

#### 2. Health Check

Check system health and EPA API connectivity.

**Returns:**
- Server status and version
- EPA API connectivity status
- Configuration information

### Example Queries

```python
# Major cities
await get_environmental_summary_by_location("New York, NY", 5.0)
await get_environmental_summary_by_location("Los Angeles, CA", 5.0)
await get_environmental_summary_by_location("Chicago, IL", 5.0)

# ZIP codes
await get_environmental_summary_by_location("10001", 3.0)  # NYC
await get_environmental_summary_by_location("90001", 3.0)  # LA
await get_environmental_summary_by_location("48502", 2.0)  # Flint, MI

# Full addresses
await get_environmental_summary_by_location("1600 Pennsylvania Avenue NW, Washington, DC", 2.0)

# Different radius sizes
await get_environmental_summary_by_location("Houston, TX", 1.0)   # Small radius
await get_environmental_summary_by_location("Houston, TX", 20.0)  # Large radius
```

## Testing

### Unit Tests

Run unit tests with mocked responses:

```bash
# With uv
uv run pytest tests/ -v

# Traditional method
pytest tests/ -v
```

### Integration Tests

Run integration tests with live EPA API calls (slower):

```bash
# With uv
uv run pytest tests/ -v -m integration

# Traditional method
pytest tests/ -v -m integration
```

### Test Coverage

Generate test coverage report:

```bash
# With uv
uv run pytest tests/ --cov=src --cov-report=html

# Traditional method
pytest tests/ --cov=src --cov-report=html
```

### Test Categories

- **Unit Tests**: Fast tests with mocked dependencies
- **Integration Tests**: Slower tests with live EPA API calls (marked with `@pytest.mark.integration`)
- **Slow Tests**: Tests that may take longer (marked with `@pytest.mark.slow`)

## Project Structure

```
envirofacts-mcp/
├── server.py                    # FastMCP server entry point
├── config.py                    # Configuration settings
├── requirements.txt            # Python dependencies
├── .env.example                 # Example environment variables
├── .gitignore                   # Git ignore file
├── README.md                    # This file
├── src/
│   ├── __init__.py
│   ├── client/                  # EPA API clients
│   │   ├── __init__.py
│   │   ├── base.py             # Base client with retry logic
│   │   ├── frs.py              # FRS (Facility Registry) queries
│   │   ├── tri.py              # TRI (Toxics Release) queries
│   │   ├── sdwis.py            # SDWIS (Safe Drinking Water) queries
│   │   └── rcra.py             # RCRA (Hazardous Waste) queries
│   ├── models/                 # Pydantic data models
│   │   ├── __init__.py
│   │   ├── common.py           # Common models (LocationParams, Coordinates)
│   │   ├── facility.py         # Facility-related models
│   │   ├── releases.py         # Chemical release models
│   │   ├── water.py            # Water violation models
│   │   └── summary.py          # EnvironmentalSummary response model
│   ├── tools/                  # MCP tools
│   │   ├── __init__.py
│   │   └── location_summary.py # Tool 1: Environmental summary
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       ├── geocoding.py        # Geocoding functions
│       ├── distance.py         # Distance calculations
│       └── aggregation.py      # Data aggregation helpers
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── conftest.py            # Pytest fixtures and mocks
│   ├── client/                # Client tests
│   │   ├── test_base.py
│   │   ├── test_frs.py
│   │   ├── test_tri.py
│   │   ├── test_sdwis.py
│   │   └── test_rcra.py
│   ├── tools/                 # Tool tests
│   │   ├── test_location_summary.py
│   │   └── test_location_summary_integration.py
│   └── utils/                 # Utility tests
│       ├── test_geocoding.py
│       ├── test_distance.py
│       └── test_aggregation.py
└── epa-mcp-requirements.md    # Requirements document
```

## EPA Data Sources

The server integrates with multiple EPA data systems:

- **FRS (Facility Registry Service)**: Master facility database
- **TRI (Toxics Release Inventory)**: Chemical release data
- **SDWIS (Safe Drinking Water Information System)**: Water quality violations
- **RCRA (Resource Conservation and Recovery Act)**: Hazardous waste sites

## Error Handling

The server includes comprehensive error handling:

- **Network Errors**: Automatic retry with exponential backoff
- **API Timeouts**: Graceful handling of EPA API 15-minute timeout
- **Geocoding Failures**: Clear error messages with suggestions
- **Empty Results**: Informative messages instead of errors
- **Partial Failures**: Continue with available data, log warnings

## Performance

- **Parallel API Calls**: Uses `asyncio.gather()` for concurrent EPA API requests
- **Geocoding Cache**: In-memory cache to avoid repeated geocoding requests
- **Rate Limiting**: Respects Nominatim's 1 request/second rate limit
- **Pagination**: Limits results to prevent overwhelming responses
- **Distance Filtering**: Efficiently filters facilities by distance

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone <repository-url>
cd envirofacts-mcp

# Install with development dependencies
uv sync --all-extras

# Or with pip
pip install -e ".[dev]"
```

### Running Development Server

```bash
# With uv
uv run python server.py

# With auto-reload for development
uv run watchfiles "uv run python server.py" src/
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run the test suite: `uv run pytest tests/ -v`
5. Commit your changes: `git commit -am 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request

### Adding New Tools

To add a new EPA data tool:

1. Create a new tool file in `src/tools/`
2. Implement the tool function with proper error handling
3. Add unit tests in `tests/tools/`
4. Add integration tests if needed
5. Register the tool in `server.py`
6. Update documentation

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Include comprehensive docstrings
- Write tests for all new functionality
- Use meaningful variable and function names

## Troubleshooting

### Common Issues

**Installation Issues**:
- Make sure you have Python 3.11 or higher: `python --version`
- If using uv, ensure it's up to date: `uv self update`
- Try clearing uv cache: `uv cache clean`

**Geocoding Failures**:
- Check internet connectivity
- Verify location string format
- Try a different location format (ZIP code vs. city name)
- Rate limit: Nominatim allows 1 request/second

**API Timeouts**:
- Reduce search radius
- Check EPA API status at https://data.epa.gov/efservice/
- Increase timeout in configuration

**Empty Results**:
- Try a larger search radius
- Verify location is in the United States
- Check if area has EPA-regulated facilities

**MCP Connection Issues**:
- Verify the absolute path in your MCP client configuration
- Check that the server starts without errors: `uv run python server.py`
- Restart your MCP client (e.g., Claude Desktop)
- Check client logs for connection errors

### Debug Mode

Enable debug logging:

```bash
# With uv
LOG_LEVEL=DEBUG uv run python server.py

# Traditional method
export LOG_LEVEL=DEBUG
python server.py
```

### Logs Location

- Server logs: Check console output
- Claude Desktop logs:
  - **macOS**: `~/Library/Logs/Claude/mcp*.log`
  - **Windows**: `%APPDATA%\Claude\logs\mcp*.log`

## What is MCP?

The Model Context Protocol (MCP) is an open protocol that enables AI assistants like Claude to securely connect to external data sources and tools. This server implements MCP to provide access to EPA environmental data.

Learn more: [modelcontextprotocol.io](https://modelcontextprotocol.io)

## Available Data Sources

This server provides access to:

- **FRS (Facility Registry Service)**: Master facility database with 800,000+ facilities
- **TRI (Toxics Release Inventory)**: Chemical release data from industrial facilities
- **SDWIS (Safe Drinking Water Information System)**: Water quality and violations data
- **RCRA (Resource Conservation and Recovery Act)**: Hazardous waste sites and handlers

All data is sourced from the U.S. Environmental Protection Agency's public Envirofacts API.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- U.S. Environmental Protection Agency for providing the Envirofacts API
- [Anthropic](https://www.anthropic.com/) for the Model Context Protocol
- [FastMCP](https://github.com/jlowin/fastmcp) framework for MCP server implementation
- [Geopy](https://geopy.readthedocs.io/) library for geocoding functionality
- [Astral](https://astral.sh/) for the uv package manager

## Support

For questions, issues, or contributions:

1. Check the [troubleshooting section](#troubleshooting) above
2. Search [existing issues](https://github.com/yourusername/epa-envirofacts-mcp/issues) in the repository
3. Create a new issue with detailed information
4. Include error messages, configuration, and steps to reproduce

## Related Projects

- [Model Context Protocol](https://modelcontextprotocol.io)
- [MCP Servers Repository](https://github.com/modelcontextprotocol/servers)
- [FastMCP](https://github.com/jlowin/fastmcp)
- [EPA Envirofacts API Documentation](https://www.epa.gov/enviro/envirofacts-data-service-api)

---

**Note**: This server provides access to public EPA data. All data is publicly available through the EPA Envirofacts API. No API key is required for basic usage.

**Disclaimer**: This is an unofficial third-party implementation and is not affiliated with or endorsed by the U.S. Environmental Protection Agency.
