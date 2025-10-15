"""Base EPA API client with retry logic and error handling."""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urlencode

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import settings


logger = logging.getLogger(__name__)


class EPAAPIError(Exception):
    """Base exception for EPA API errors."""
    pass


class EPATimeoutError(EPAAPIError):
    """EPA API timeout error."""
    pass


class EPANetworkError(EPAAPIError):
    """EPA API network error."""
    pass


class EPAClient:
    """Base client for EPA Envirofacts API with retry logic."""
    
    def __init__(self, base_url: Optional[str] = None, timeout: Optional[int] = None):
        """Initialize EPA client.
        
        Args:
            base_url: EPA API base URL (defaults to settings)
            timeout: Request timeout in seconds (defaults to settings)
        """
        self.base_url = base_url or settings.epa_api_base_url.rstrip('/')
        self.timeout = timeout or settings.request_timeout
        
        # Create httpx client with timeout
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers={
                'User-Agent': 'epa-envirofacts-mcp/1.0',
                'Accept': 'application/json'
            }
        )
    
    def _build_query_url(
        self,
        table: str,
        filters: Optional[Dict[str, Any]] = None,
        joins: Optional[List[str]] = None,
        sort: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        format_type: str = "JSON"
    ) -> str:
        """Build EPA API query URL.
        
        Args:
            table: EPA table name (e.g., 'frs.frs_facilities')
            filters: Dictionary of filters {column: {operator: value}}
            joins: List of join tables
            sort: Sort column
            limit: Maximum results
            offset: Starting offset
            format_type: Response format (JSON, CSV, etc.)
            
        Returns:
            Complete EPA API URL
            
        Example:
            filters = {
                'state_abbr': {'equals': 'CA'},
                'facility_name': {'contains': 'Chemical'}
            }
        """
        # Start with base URL and table
        url_parts = [self.base_url, table]
        
        # Add filters
        if filters:
            for column, conditions in filters.items():
                for operator, value in conditions.items():
                    url_parts.extend([column, operator, str(value)])
        
        # Add joins
        if joins:
            for join_table in joins:
                url_parts.append('join')
                url_parts.append(join_table)
        
        # Add pagination
        url_parts.append(f"{offset + 1}:{offset + limit}")
        
        # Add sort
        if sort:
            url_parts.append(sort)
        
        # Add format
        url_parts.append(format_type)
        
        return '/'.join(url_parts)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError)),
        reraise=True
    )
    async def _execute_query(self, url: str) -> Dict[str, Any]:
        """Execute EPA API query with retry logic.
        
        Args:
            url: Complete EPA API URL
            
        Returns:
            Parsed JSON response
            
        Raises:
            EPATimeoutError: If request times out
            EPANetworkError: If network error occurs
            EPAAPIError: If API returns error
        """
        try:
            logger.debug(f"Executing EPA API query: {url}")
            
            response = await self.client.get(url)
            response.raise_for_status()
            
            # Parse JSON response
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                raise EPAAPIError(f"Invalid JSON response: {e}")
            
            logger.debug(f"EPA API query successful, returned {len(data)} records")
            return data
            
        except httpx.TimeoutException as e:
            logger.warning(f"EPA API timeout: {e}")
            raise EPATimeoutError(f"Request timed out after {self.timeout}s: {e}")
            
        except httpx.NetworkError as e:
            logger.warning(f"EPA API network error: {e}")
            raise EPANetworkError(f"Network error: {e}")
            
        except httpx.HTTPStatusError as e:
            logger.error(f"EPA API HTTP error {e.response.status_code}: {e}")
            if e.response.status_code == 429:
                raise EPAAPIError("Rate limit exceeded - please try again later")
            elif e.response.status_code >= 500:
                raise EPAAPIError(f"EPA API server error: {e.response.status_code}")
            else:
                raise EPAAPIError(f"EPA API error {e.response.status_code}: {e}")
    
    async def query_table(
        self,
        table: str,
        filters: Optional[Dict[str, Any]] = None,
        joins: Optional[List[str]] = None,
        sort: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Query EPA table with filters and pagination.
        
        Args:
            table: EPA table name
            filters: Dictionary of filters
            joins: List of join tables
            sort: Sort column
            limit: Maximum results
            offset: Starting offset
            
        Returns:
            List of records from EPA API
            
        Raises:
            EPAAPIError: If query fails
        """
        url = self._build_query_url(table, filters, joins, sort, limit, offset)
        
        try:
            data = await self._execute_query(url)
            
            # EPA API returns a list of records
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'results' in data:
                return data['results']
            else:
                logger.warning(f"Unexpected EPA API response format: {type(data)}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to query EPA table {table}: {e}")
            raise EPAAPIError(f"Query failed: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check EPA API connectivity.
        
        Returns:
            Health status information
        """
        try:
            # Simple test query to FRS facility_site table
            test_url = self._build_query_url('frs.frs_facility_site', limit=1)
            await self._execute_query(test_url)
            
            return {
                "status": "healthy",
                "api_reachable": True,
                "base_url": self.base_url,
                "timeout": self.timeout
            }
            
        except Exception as e:
            logger.error(f"EPA API health check failed: {e}")
            return {
                "status": "unhealthy",
                "api_reachable": False,
                "error": str(e),
                "base_url": self.base_url,
                "timeout": self.timeout
            }
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
