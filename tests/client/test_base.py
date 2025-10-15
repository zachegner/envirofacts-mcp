"""Unit tests for base EPA client."""

import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock

from src.client.base import EPAClient, EPAAPIError, EPATimeoutError, EPANetworkError


class TestEPAClient:
    """Test cases for EPAClient base class."""
    
    @pytest.fixture
    def client(self):
        """Create EPAClient instance for testing."""
        return EPAClient()
    
    def test_init(self):
        """Test EPAClient initialization."""
        client = EPAClient()
        assert client.base_url == "https://data.epa.gov/efservice/"
        assert client.timeout == 300
        assert client.client is not None
    
    def test_init_custom_params(self):
        """Test EPAClient initialization with custom parameters."""
        client = EPAClient(base_url="https://test.epa.gov/", timeout=60)
        assert client.base_url == "https://test.epa.gov/"
        assert client.timeout == 60
    
    def test_build_query_url_simple(self, client):
        """Test URL building with simple filters."""
        url = client._build_query_url(
            table="frs.frs_facilities",
            filters={"state_abbr": {"equals": "CA"}},
            limit=10
        )
        expected = "https://data.epa.gov/efservice/frs.frs_facilities/state_abbr/equals/CA/1:10/JSON"
        assert url == expected
    
    def test_build_query_url_complex(self, client):
        """Test URL building with complex filters and joins."""
        filters = {
            "latitude": {"greaterThan": "40.0", "lessThan": "41.0"},
            "longitude": {"greaterThan": "-74.0", "lessThan": "-73.0"}
        }
        joins = ["tri.tri_reporting_form"]
        
        url = client._build_query_url(
            table="tri.tri_facility",
            filters=filters,
            joins=joins,
            sort="facility_name",
            limit=50,
            offset=100
        )
        
        expected = ("https://data.epa.gov/efservice/tri.tri_facility/"
                  "latitude/greaterThan/40.0/latitude/lessThan/41.0/"
                  "longitude/greaterThan/-74.0/longitude/lessThan/-73.0/"
                  "join/tri.tri_reporting_form/101:150/facility_name/JSON")
        assert url == expected
    
    @pytest.mark.asyncio
    async def test_execute_query_success(self, client):
        """Test successful query execution."""
        mock_response = AsyncMock()
        mock_response.json.return_value = [{"test": "data"}]
        mock_response.raise_for_status.return_value = None
        
        client.client.get = AsyncMock(return_value=mock_response)
        
        result = await client._execute_query("https://test.epa.gov/test")
        
        assert result == [{"test": "data"}]
        client.client.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_query_timeout(self, client):
        """Test query execution with timeout."""
        client.client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
        
        with pytest.raises(EPATimeoutError):
            await client._execute_query("https://test.epa.gov/test")
    
    @pytest.mark.asyncio
    async def test_execute_query_network_error(self, client):
        """Test query execution with network error."""
        client.client.get = AsyncMock(side_effect=httpx.NetworkError("Network error"))
        
        with pytest.raises(EPANetworkError):
            await client._execute_query("https://test.epa.gov/test")
    
    @pytest.mark.asyncio
    async def test_execute_query_http_error(self, client):
        """Test query execution with HTTP error."""
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error", request=MagicMock(), response=mock_response
        )
        
        client.client.get = AsyncMock(return_value=mock_response)
        
        with pytest.raises(EPAAPIError, match="EPA API server error"):
            await client._execute_query("https://test.epa.gov/test")
    
    @pytest.mark.asyncio
    async def test_execute_query_rate_limit(self, client):
        """Test query execution with rate limit error."""
        mock_response = AsyncMock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Rate limit", request=MagicMock(), response=mock_response
        )
        
        client.client.get = AsyncMock(return_value=mock_response)
        
        with pytest.raises(EPAAPIError, match="Rate limit exceeded"):
            await client._execute_query("https://test.epa.gov/test")
    
    @pytest.mark.asyncio
    async def test_execute_query_invalid_json(self, client):
        """Test query execution with invalid JSON response."""
        mock_response = AsyncMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status.return_value = None
        
        client.client.get = AsyncMock(return_value=mock_response)
        
        with pytest.raises(EPAAPIError, match="Invalid JSON response"):
            await client._execute_query("https://test.epa.gov/test")
    
    @pytest.mark.asyncio
    async def test_query_table_success(self, client):
        """Test successful table query."""
        mock_data = [{"id": 1, "name": "Test"}]
        client._execute_query = AsyncMock(return_value=mock_data)
        
        result = await client.query_table(
            table="test.table",
            filters={"id": {"equals": "1"}},
            limit=10
        )
        
        assert result == mock_data
        client._execute_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_query_table_with_results_key(self, client):
        """Test table query with results key in response."""
        mock_data = {"results": [{"id": 1, "name": "Test"}]}
        client._execute_query = AsyncMock(return_value=mock_data)
        
        result = await client.query_table("test.table")
        
        assert result == [{"id": 1, "name": "Test"}]
    
    @pytest.mark.asyncio
    async def test_query_table_unexpected_format(self, client):
        """Test table query with unexpected response format."""
        mock_data = {"unexpected": "format"}
        client._execute_query = AsyncMock(return_value=mock_data)
        
        result = await client.query_table("test.table")
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_query_table_error(self, client):
        """Test table query with error."""
        client._execute_query = AsyncMock(side_effect=Exception("Test error"))
        
        with pytest.raises(EPAAPIError, match="Query failed"):
            await client.query_table("test.table")
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, client):
        """Test successful health check."""
        client._execute_query = AsyncMock(return_value=[])
        
        result = await client.health_check()
        
        assert result["status"] == "healthy"
        assert result["api_reachable"] is True
        assert "base_url" in result
        assert "timeout" in result
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, client):
        """Test health check with API failure."""
        client._execute_query = AsyncMock(side_effect=Exception("API error"))
        
        result = await client.health_check()
        
        assert result["status"] == "unhealthy"
        assert result["api_reachable"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_close(self, client):
        """Test client close method."""
        client.client.aclose = AsyncMock()
        
        await client.close()
        
        client.client.aclose.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test client as async context manager."""
        with patch('src.client.base.EPAClient.close') as mock_close:
            async with EPAClient() as client:
                assert client is not None
            mock_close.assert_called_once()
