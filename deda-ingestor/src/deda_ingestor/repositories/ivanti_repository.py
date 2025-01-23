"""Repository for interacting with Ivanti API."""
import time
from datetime import datetime
from typing import Dict, List, Optional, Union

import httpx
from loguru import logger

from ..config.settings import IvantiConfig
from ..core.exceptions import (
    AuthenticationError,
    IvantiAPIError,
    RetryableAPIError,
    RetryableConnectionError
)
from ..core.models import Product, SyncResult
from ..utils.retry import RetryConfig, retry_with_backoff
from .base import BaseRepository


class IvantiRepository(BaseRepository):
    """Repository for Ivanti API operations."""

    def __init__(self, config: IvantiConfig):
        """
        Initialize repository.

        Args:
            config: Ivanti configuration
        """
        self.config = config
        self._access_token = None
        self._token_expiry = 0
        self._client = httpx.Client(
            base_url=config.api_url,
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

    def is_connected(self) -> bool:
        """Check if repository is connected and token is valid."""
        return (
            self._access_token is not None
            and self._token_expiry > time.time()
        )

    def connect(self) -> None:
        """
        Connect to Ivanti API.

        Raises:
            AuthenticationError: If authentication fails
        """
        if not self.is_connected():
            self._authenticate()

    @retry_with_backoff(
        retryable_exceptions=(RetryableConnectionError, RetryableAPIError),
        config=RetryConfig(max_attempts=3)
    )
    def _authenticate(self) -> None:
        """
        Authenticate with Ivanti API using OAuth2.

        Raises:
            AuthenticationError: If authentication fails
            RetryableConnectionError: If connection fails temporarily
            RetryableAPIError: If API returns retryable error
        """
        try:
            logger.info("Authenticating with Ivanti API")

            auth_data = {
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "grant_type": "client_credentials"
            }

            response = self._client.post(
                self.config.token_url,
                json=auth_data
            )

            self._handle_response(response, "authentication")

            auth_response = response.json()
            self._access_token = auth_response["access_token"]
            # Set token expiry with 5-minute buffer
            self._token_expiry = time.time() + auth_response["expires_in"] - 300

            # Update client headers with new token
            self._client.headers.update(self._get_default_headers())

            logger.info("Successfully authenticated with Ivanti API")

        except httpx.TransportError as e:
            raise RetryableConnectionError(
                f"Connection error during authentication: {str(e)}"
            ) from e
        except RetryableAPIError:
            raise  # Re-raise retryable errors for retry decorator
        except Exception as e:
            raise AuthenticationError(
                f"Authentication failed: {str(e)}"
            ) from e

    def _handle_response(
        self,
        response: httpx.Response,
        context: str,
        retryable_codes: tuple = (408, 429, 500, 502, 503, 504)
    ) -> None:
        """
        Handle API response and raise appropriate exceptions.

        Args:
            response: HTTP response
            context: Operation context
            retryable_codes: HTTP status codes that warrant retry

        Raises:
            RetryableAPIError: For temporary API issues
            IvantiAPIError: For API errors
        """
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            status_code = response.status_code
            error_detail = str(e)

            try:
                error_body = response.json()
                if isinstance(error_body, dict):
                    error_detail = error_body.get("message", error_detail)
            except Exception:
                error_body = response.text

            if status_code in retryable_codes:
                raise RetryableAPIError(
                    f"Retryable API error during {context}: {error_detail}",
                    status_code=status_code,
                    response_body=error_body
                ) from e

            raise IvantiAPIError(
                f"API error during {context}: {error_detail}",
                status_code=status_code,
                response_body=error_body
            ) from e

    @retry_with_backoff(
        retryable_exceptions=(RetryableConnectionError, RetryableAPIError),
        config=RetryConfig(max_attempts=3)
    )
    def get_product(self, product_id: str) -> Optional[Product]:
        """
        Get product from Ivanti.

        Args:
            product_id: Product ID

        Returns:
            Optional[Product]: Product if found, None otherwise

        Raises:
            IvantiAPIError: If API request fails
            RetryableAPIError: If API returns retryable error
        """
        try:
            self.connect()

            response = self._client.get(f"/products/{product_id}")

            try:
                self._handle_response(response, "get_product")
            except IvantiAPIError as e:
                if e.status_code == 404:
                    return None
                raise

            return Product.from_ivanti_response(response.json())

        except httpx.TransportError as e:
            raise RetryableConnectionError(
                f"Connection error during get_product: {str(e)}"
            ) from e

    @retry_with_backoff(
        retryable_exceptions=(RetryableConnectionError, RetryableAPIError),
        config=RetryConfig(max_attempts=3)
    )
    def create_product(self, product: Product) -> bool:
        """
        Create product in Ivanti.

        Args:
            product: Product to create

        Returns:
            bool: True if successful

        Raises:
            IvantiAPIError: If API request fails
            RetryableAPIError: If API returns retryable error
        """
        try:
            self.connect()

            response = self._client.post(
                "/products",
                json=product.to_ivanti_request()
            )

            self._handle_response(response, "create_product")
            return True

        except httpx.TransportError as e:
            raise RetryableConnectionError(
                f"Connection error during create_product: {str(e)}"
            ) from e

    @retry_with_backoff(
        retryable_exceptions=(RetryableConnectionError, RetryableAPIError),
        config=RetryConfig(max_attempts=3)
    )
    def update_product(self, product: Product) -> bool:
        """
        Update product in Ivanti.

        Args:
            product: Product to update

        Returns:
            bool: True if successful

        Raises:
            IvantiAPIError: If API request fails
            RetryableAPIError: If API returns retryable error
        """
        try:
            self.connect()

            response = self._client.put(
                f"/products/{product.product_id}",
                json=product.to_ivanti_request()
            )

            self._handle_response(response, "update_product")
            return True

        except httpx.TransportError as e:
            raise RetryableConnectionError(
                f"Connection error during update_product: {str(e)}"
            ) from e

    def batch_process_products(
        self,
        products: List[Product],
        operation: str = "create"
    ) -> SyncResult:
        """
        Process multiple products in batch.

        Args:
            products: List of products to process
            operation: Operation to perform ("create" or "update")

        Returns:
            SyncResult: Batch processing result
        """
        result = SyncResult(
            total_processed=len(products),
            start_time=datetime.utcnow()
        )

        for product in products:
            try:
                if operation == "create":
                    success = self.create_product(product)
                else:
                    success = self.update_product(product)

                if success:
                    result.successful_syncs += 1
                else:
                    result.failed_syncs += 1
                    result.errors[product.product_id] = "Operation failed"

            except Exception as e:
                result.failed_syncs += 1
                result.errors[product.product_id] = f"Error during {operation}: {str(e)}"
                logger.error(
                    f"Error during batch {operation}",
                    exc_info=True,
                    product_id=product.product_id
                )

        result.end_time = datetime.utcnow()
        return result

    def close(self) -> None:
        """Close repository connections."""
        if self._client:
            self._client.close()