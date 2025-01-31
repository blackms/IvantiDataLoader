"""Ivanti loader plugin."""
from datetime import datetime, UTC
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field, SecretStr

from ...core.base import DataLoader
from ...core.exceptions import LoaderError
from ..registry import PluginRegistry


class IvantiAuth(BaseModel):
    """Ivanti authentication configuration."""
    url: str = Field(..., description="Ivanti API base URL")
    username: str = Field(..., description="API username")
    password: SecretStr = Field(..., description="API password")
    tenant: Optional[str] = Field(None, description="Tenant identifier")


class IvantiLoaderConfig(BaseModel):
    """Configuration for Ivanti loader."""
    auth: IvantiAuth
    entity_type: str = Field(..., description="Type of entity to load (e.g., 'product')")
    batch_size: int = Field(
        default=50,
        description="Number of records to load in each batch"
    )
    timeout: int = Field(
        default=30,
        description="API request timeout in seconds"
    )
    retry_attempts: int = Field(
        default=3,
        description="Number of retry attempts for failed requests"
    )


@PluginRegistry.register_loader("ivanti")
class IvantiLoader(DataLoader[Dict[str, Any]]):
    """Loader plugin for Ivanti."""

    def __init__(self, config: IvantiLoaderConfig):
        """
        Initialize Ivanti loader.

        Args:
            config: Loader configuration
        """
        super().__init__(config)
        self.auth_token: Optional[str] = None
        self.auth_expiry: Optional[datetime] = None
        self._client = httpx.Client(
            base_url=config.auth.url,
            timeout=config.timeout,
            verify=True  # SSL verification
        )

    def _authenticate(self) -> None:
        """
        Authenticate with Ivanti API.

        Raises:
            LoaderError: If authentication fails
        """
        try:
            response = self._client.post(
                "/api/auth/token",
                json={
                    "username": self.config.auth.username,
                    "password": self.config.auth.password.get_secret_value(),
                    "tenant": self.config.auth.tenant
                }
            )
            response.raise_for_status()
            
            data = response.json()
            self.auth_token = data["token"]
            # Set token expiry (typically 1 hour from now)
            self.auth_expiry = datetime.now(UTC).replace(
                microsecond=0
            ) + datetime.timedelta(hours=1)
            
            self._client.headers.update({
                "Authorization": f"Bearer {self.auth_token}"
            })

        except Exception as e:
            raise LoaderError(f"Authentication failed: {str(e)}") from e

    def _ensure_authenticated(self) -> None:
        """Ensure valid authentication token exists."""
        if (
            not self.auth_token or
            not self.auth_expiry or
            datetime.now(UTC) >= self.auth_expiry
        ):
            self._authenticate()

    def _create_entity(self, data: Dict[str, Any]) -> bool:
        """
        Create new entity in Ivanti.

        Args:
            data: Entity data to create

        Returns:
            bool: True if successful

        Raises:
            LoaderError: If creation fails
        """
        try:
            response = self._client.post(
                f"/api/{self.config.entity_type}",
                json=data
            )
            response.raise_for_status()
            return True

        except Exception as e:
            raise LoaderError(
                f"Failed to create {self.config.entity_type}: {str(e)}"
            ) from e

    def _update_entity(self, entity_id: str, data: Dict[str, Any]) -> bool:
        """
        Update existing entity in Ivanti.

        Args:
            entity_id: ID of entity to update
            data: Updated entity data

        Returns:
            bool: True if successful

        Raises:
            LoaderError: If update fails
        """
        try:
            response = self._client.put(
                f"/api/{self.config.entity_type}/{entity_id}",
                json=data
            )
            response.raise_for_status()
            return True

        except Exception as e:
            raise LoaderError(
                f"Failed to update {self.config.entity_type} {entity_id}: {str(e)}"
            ) from e

    def _entity_exists(self, entity_id: str) -> bool:
        """
        Check if entity exists in Ivanti.

        Args:
            entity_id: ID of entity to check

        Returns:
            bool: True if exists

        Raises:
            LoaderError: If check fails
        """
        try:
            response = self._client.head(
                f"/api/{self.config.entity_type}/{entity_id}"
            )
            return response.status_code == 200

        except Exception as e:
            raise LoaderError(
                f"Failed to check {self.config.entity_type} existence: {str(e)}"
            ) from e

    def load(self, data: Dict[str, Any]) -> bool:
        """
        Load data into Ivanti.

        Args:
            data: Data to load

        Returns:
            bool: True if successful

        Raises:
            LoaderError: If load fails
        """
        try:
            self._ensure_authenticated()

            entity_id = data.get("id")
            if not entity_id:
                raise LoaderError("Data missing required 'id' field")

            # Determine if entity exists
            exists = self._entity_exists(entity_id)

            # Create or update entity
            for attempt in range(self.config.retry_attempts):
                try:
                    if exists:
                        return self._update_entity(entity_id, data)
                    else:
                        return self._create_entity(data)
                except LoaderError:
                    if attempt == self.config.retry_attempts - 1:
                        raise
                    # Re-authenticate and retry
                    self._authenticate()

            return False

        except Exception as e:
            if isinstance(e, LoaderError):
                raise
            raise LoaderError(f"Load operation failed: {str(e)}") from e

    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, '_client'):
            self._client.close()