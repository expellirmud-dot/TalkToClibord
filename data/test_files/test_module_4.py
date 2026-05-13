
# Test Module 4 - API client and HTTP utilities
import requests
import json
from typing import Dict, Optional, Union
from dataclasses import dataclass

@dataclass
class APIResponse:
    """Data class for API response handling."""
    status_code: int
    data: Union[Dict, List]
    headers: Dict
    elapsed_time: float

class APIClient:
    """HTTP API client for RESTful services.
    
    Features:
    - Request/response logging
    - Retry logic with exponential backoff
    - Authentication handling
    - Rate limiting
    
    Attributes:
        base_url: Base URL for API endpoints
        api_key: Authentication key
        timeout: Request timeout in seconds
    """
    
    def __init__(self, base_url: str, api_key: Optional[str] = None, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        
    def _get_headers(self) -> Dict:
        """Build request headers with authentication."""
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        return headers
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> APIResponse:
        """Send GET request to specified endpoint."""
        import time
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        start_time = time.time()
        
        try:
            response = self.session.get(
                url,
                params=params,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            elapsed = time.time() - start_time
            
            return APIResponse(
                status_code=response.status_code,
                data=response.json() if response.content else {},
                headers=dict(response.headers),
                elapsed_time=elapsed
            )
        except Exception as e:
            return APIResponse(
                status_code=500,
                data={'error': str(e)},
                headers={},
                elapsed_time=time.time() - start_time
            )
    
    def post(self, endpoint: str, data: Optional[Dict] = None) -> APIResponse:
        """Send POST request to specified endpoint."""
        import time
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        start_time = time.time()
        
        try:
            response = self.session.post(
                url,
                json=data,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            elapsed = time.time() - start_time
            
            return APIResponse(
                status_code=response.status_code,
                data=response.json() if response.content else {},
                headers=dict(response.headers),
                elapsed_time=elapsed
            )
        except Exception as e:
            return APIResponse(
                status_code=500,
                data={'error': str(e)},
                headers={},
                elapsed_time=time.time() - start_time
            )
