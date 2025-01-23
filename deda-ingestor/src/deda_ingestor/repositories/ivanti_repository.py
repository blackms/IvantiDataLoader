"""Repository for interacting with Ivanti API."""
import time
from typing import Dict, Optional
from urllib.parse import urljoin

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from ..config.settings import IvantiConfig
from ..core.models import Product, IvantiProduct
from ..adapters.product_adapter import ProductAdapter
from .base import ProductRepository


class IvantiRepository(ProductRepository):
    """Repository for interacting with Ivanti API."""

    def __init__(self, config: IvantiConfig):
        """
        Initialize Ivanti repository.

        Args:
            config: Ivanti API configuration
        """
        self.config = config
        self._access_token: Optional[str] = None
        self._token_expiry: float = 0
        self._client = httpx.Client(
            timeout=config.request_timeout,
            headers=self._get_default_headers()
        )

    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers for API requests."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-Key": self.config.api_key
        }
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        return headers

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(httpx.HTTPError)
    )
    def _authenticate(self) -> None:
        """
        Authenticate with Ivanti API using OAuth2.

        Raises:
            httpx.HTTPError: If authentication fails
        """
        if self._access_token and time.time() < self._token_expiry:
            return

        auth_data = {
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "grant_type": "client_credentials"
        }

        response = self._client.post(
            self.config.token_url,
            json=auth_data
        )
        response.raise_for_status()

        auth_response = response.json()
        self._access_token = auth_response["access_token"]
        # Set token expiry with a small buffer (5 minutes)
        self._token_expiry = time.time() + auth_response["expires_in"] - 300
        
        # Update client headers with new token
        self._client.headers.update(self._get_default_headers())

    def _ensure_authenticated(self) -> None:
        """Ensure we have a valid authentication token."""
        if not self._access_token or time.time() >= self._token_expiry:
            self._authenticate()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, ConnectionError))
    )
    def get_product(self, product_id: str) -> Optional[Product]:
        """
        Retrieve a product from Ivanti by ID.

        Args:
            product_id: The product ID to retrieve

        Returns:
            Optional[Product]: The product if found, None otherwise

        Raises:
            httpx.HTTPError: If API request fails
        """
        self._ensure_authenticated()

        url = urljoin(self.config.api_url, f"/products/{product_id}")
        response = self._client.get(url)

        if response.status_code == 404:
            return None

        response.raise_for_status()
        return ProductAdapter.from_ivanti_response(response.json())

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, ConnectionError))
    )
    def create_product(self, product: Product) -> bool:
        """
        Create a new product in Ivanti.

        Args:
            product: The product to create

        Returns:
            bool: True if creation successful, False otherwise

        Raises:
            httpx.HTTPError: If API request fails
        """
        self._ensure_authenticated()

        url = urljoin(self.config.api_url, "/products")
        ivanti_product = ProductAdapter.to_ivanti_product(product)
        
        response = self._client.post(url, json=ivanti_product.model_dump())
        response.raise_for_status()
        
        return response.status_code in (200, 201)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, ConnectionError))
    )
    def update_product(self, product: Product) -> bool:
        """
        Update an existing product in Ivanti.

        Args:
            product: The product to update

        Returns:
            bool: True if update successful, False otherwise

        Raises:
            httpx.HTTPError: If API request fails
        """
        self._ensure_authenticated()

        url = urljoin(self.config.api_url, f"/products/{product.product_id}")
        ivanti_product = ProductAdapter.to_ivanti_product(product)
        
        response = self._client.put(url, json=ivanti_product.model_dump())
        
        if response.status_code == 404:
            return False
            
        response.raise_for_status()
        return response.status_code == 200

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, ConnectionError))
    )
    def delete_product(self, product_id: str) -> bool:
        """
        Delete a product from Ivanti.

        Args:
            product_id: The ID of the product to delete

        Returns:
            bool: True if deletion successful, False otherwise

        Raises:
            httpx.HTTPError: If API request fails
        """
        self._ensure_authenticated()

        url = urljoin(self.config.api_url, f"/products/{product_id}")
        response = self._client.delete(url)
        
        if response.status_code == 404:
            return False
            
        response.raise_for_status()
        return response.status_code == 204

    def __enter__(self) -> 'IvantiRepository':
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self._client.close()