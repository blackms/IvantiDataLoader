"""Repository for interacting with Ivanti API."""
import time
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import httpx
from httpx import Response

from ..config.settings import IvantiConfig
from ..core.exceptions import (
    AuthenticationError,
    ConnectionError,
    IvantiAPIError,
    MessageProcessingError,
    RetryableAPIError,
    RetryableConnectionError
)
from ..core.models import Product, SyncResult
from ..adapters.product_adapter import ProductAdapter
from ..utils.logging import get_logger
from ..utils.retry import RetryConfig, retry_with_backoff
from .base import ProductRepository

logger = get_logger()


class IvantiRepository(ProductRepository):
    """Repository for interacting with Ivanti API."""

    def __init__(
        self,
        config: IvantiConfig,
        retry_config: Optional[RetryConfig] = None
    ):
        """
        Initialize Ivanti repository.

        Args:
            config: Ivanti API configuration
            retry_config: Retry configuration
        """
        super().__init__(retry_config)
        self.config = config
        self._access_token: Optional[str] = None
        self._token_expiry: float = 0
        self._client = self._create_client()

    def _create_client(self) -> httpx.Client:
        """
        Create HTTP client with default configuration.

        Returns:
            httpx.Client: Configured client
        """
        return httpx.Client(
            timeout=self.config.request_timeout,
            headers=self._get_default_headers(),
            verify=True,  # SSL verification
            http2=True
        )

    def _get_default_headers(self) -> Dict[str, str]:
        """
        Get default headers for API requests.

        Returns:
            Dict[str, str]: Headers dictionary
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-Key": self.config.api_key
        }
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        return headers

    def connect(self) -> None:
        """
        Establish connection by authenticating with Ivanti API.

        Raises:
            AuthenticationError: If authentication fails
            ConnectionError: If connection fails
        """
        self._authenticate()

    def disconnect(self) -> None:
        """Close the connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._access_token = None
            self._token_expiry = 0

    def is_connected(self) -> bool:
        """
        Check if connection is active and token is valid.

        Returns:
            bool: True if connected and authenticated
        """
        return (
            self._client is not None
            and self._access_token is not None
            and time.time() < self._token_expiry
        )

    def reconnect(self) -> None:
        """Re-establish connection."""
        self.disconnect()
        self.connect()

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
        """
        if self.is_connected():
            return

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
        except Exception as e:
            raise AuthenticationError(
                f"Authentication failed: {str(e)}"
            ) from e

    def _handle_response(
        self,
        response: Response,
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
        Retrieve a product from Ivanti.

        Args:
            product_id: Product ID

        Returns:
            Optional[Product]: Product if found

        Raises:
            ConnectionError: If connection fails
            IvantiAPIError: If API request fails
        """
        if not self.is_connected():
            self.connect()

        try:
            url = urljoin(self.config.api_url, f"/products/{product_id}")
            response = self._client.get(url)

            if response.status_code == 404:
                logger.debug("Product not found", product_id=product_id)
                return None

            self._handle_response(response, f"getting product {product_id}")
            return ProductAdapter.from_ivanti_response(response.json())

        except (RetryableConnectionError, RetryableAPIError):
            raise
        except Exception as e:
            raise IvantiAPIError(
                f"Failed to get product {product_id}: {str(e)}"
            ) from e

    @retry_with_backoff(
        retryable_exceptions=(RetryableConnectionError, RetryableAPIError),
        config=RetryConfig(max_attempts=3)
    )
    def create_product(self, product: Product) -> bool:
        """
        Create a new product in Ivanti.

        Args:
            product: Product to create

        Returns:
            bool: True if successful

        Raises:
            ConnectionError: If connection fails
            IvantiAPIError: If API request fails
        """
        if not self.is_connected():
            self.connect()

        try:
            url = urljoin(self.config.api_url, "/products")
            ivanti_product = ProductAdapter.to_ivanti_product(product)
            
            response = self._client.post(
                url,
                json=ivanti_product.model_dump()
            )
            
            self._handle_response(
                response,
                f"creating product {product.product_id}"
            )
            
            logger.info(
                "Product created successfully",
                product_id=product.product_id
            )
            return True

        except (RetryableConnectionError, RetryableAPIError):
            raise
        except Exception as e:
            raise IvantiAPIError(
                f"Failed to create product {product.product_id}: {str(e)}"
            ) from e

    @retry_with_backoff(
        retryable_exceptions=(RetryableConnectionError, RetryableAPIError),
        config=RetryConfig(max_attempts=3)
    )
    def update_product(self, product: Product) -> bool:
        """
        Update an existing product in Ivanti.

        Args:
            product: Product to update

        Returns:
            bool: True if successful

        Raises:
            ConnectionError: If connection fails
            IvantiAPIError: If API request fails
        """
        if not self.is_connected():
            self.connect()

        try:
            url = urljoin(
                self.config.api_url,
                f"/products/{product.product_id}"
            )
            ivanti_product = ProductAdapter.to_ivanti_product(product)
            
            response = self._client.put(
                url,
                json=ivanti_product.model_dump()
            )
            
            if response.status_code == 404:
                logger.warning(
                    "Product not found for update",
                    product_id=product.product_id
                )
                return False
                
            self._handle_response(
                response,
                f"updating product {product.product_id}"
            )
            
            logger.info(
                "Product updated successfully",
                product_id=product.product_id
            )
            return True

        except (RetryableConnectionError, RetryableAPIError):
            raise
        except Exception as e:
            raise IvantiAPIError(
                f"Failed to update product {product.product_id}: {str(e)}"
            ) from e

    @retry_with_backoff(
        retryable_exceptions=(RetryableConnectionError, RetryableAPIError),
        config=RetryConfig(max_attempts=3)
    )
    def delete_product(self, product_id: str) -> bool:
        """
        Delete a product from Ivanti.

        Args:
            product_id: Product ID

        Returns:
            bool: True if successful

        Raises:
            ConnectionError: If connection fails
            IvantiAPIError: If API request fails
        """
        if not self.is_connected():
            self.connect()

        try:
            url = urljoin(self.config.api_url, f"/products/{product_id}")
            response = self._client.delete(url)
            
            if response.status_code == 404:
                logger.warning(
                    "Product not found for deletion",
                    product_id=product_id
                )
                return False
                
            self._handle_response(
                response,
                f"deleting product {product_id}"
            )
            
            logger.info(
                "Product deleted successfully",
                product_id=product_id
            )
            return True

        except (RetryableConnectionError, RetryableAPIError):
            raise
        except Exception as e:
            raise IvantiAPIError(
                f"Failed to delete product {product_id}: {str(e)}"
            ) from e

    def batch_process_products(
        self,
        products: list[Product],
        operation: str
    ) -> SyncResult:
        """
        Process multiple products in batch.

        Args:
            products: Products to process
            operation: Operation type ('create' or 'update')

        Returns:
            SyncResult: Processing results
        """
        sync_result = SyncResult()
        
        for product in products:
            try:
                if operation == "create":
                    success = self.create_product(product)
                elif operation == "update":
                    success = self.update_product(product)
                else:
                    raise ValueError(f"Invalid operation: {operation}")

                if success:
                    sync_result.record_success()
                else:
                    sync_result.record_failure(
                        product.product_id,
                        f"Failed to {operation} product"
                    )

            except Exception as e:
                logger.exception(
                    f"Error during batch {operation}",
                    product_id=product.product_id,
                    error=str(e)
                )
                sync_result.record_failure(
                    product.product_id,
                    f"Error during {operation}: {str(e)}"
                )

        sync_result.complete()
        return sync_result

    def health_check(self) -> bool:
        """
        Check repository health.

        Returns:
            bool: True if healthy
        """
        try:
            if not self.is_connected():
                self.connect()
            return True
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return False

    def __enter__(self) -> 'IvantiRepository':
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.disconnect()