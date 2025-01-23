"""Tests for Ivanti repository integration."""
from datetime import datetime, UTC
from decimal import Decimal
import json
from unittest.mock import Mock, patch

import httpx
import pytest
from pytest_mock import MockerFixture

from deda_ingestor.core.exceptions import (
    AuthenticationError,
    IvantiAPIError,
    RetryableAPIError
)
from deda_ingestor.core.models import Product, ProductElement
from deda_ingestor.config.settings import IvantiConfig
from deda_ingestor.repositories.ivanti_repository import IvantiRepository


@pytest.fixture
def mock_auth_response() -> dict:
    """Fixture for mock authentication response."""
    return {
        "access_token": "test-token",
        "token_type": "Bearer",
        "expires_in": 3600
    }


@pytest.fixture
def mock_auth_success(mock_httpx_client: Mock, mock_auth_response: dict) -> Mock:
    """Fixture for successful authentication."""
    response = Mock(spec=httpx.Response)
    response.status_code = 200
    response.json.return_value = mock_auth_response
    response.raise_for_status = Mock()  # Add this line
    mock_httpx_client.post.return_value = response
    return response


@pytest.fixture
def ivanti_config() -> IvantiConfig:
    """Fixture for Ivanti configuration."""
    return IvantiConfig(
        api_url="https://ivanti-api.example.com",
        api_key="test-api-key",
        client_id="test-client-id",
        client_secret="test-client-secret",
        token_url="https://ivanti-api.example.com/oauth/token",
        request_timeout=30,
        max_retries=3,
        retry_delay=1
    )


@pytest.fixture
def mock_httpx_client(mocker: MockerFixture) -> Mock:
    """Fixture for mocked HTTPX client."""
    mock_client = Mock(spec=httpx.Client)
    mocker.patch("httpx.Client", return_value=mock_client)
    return mock_client


@pytest.fixture
def ivanti_repository(
    ivanti_config: IvantiConfig,
    mock_httpx_client: Mock,
    mock_auth_success: Mock
) -> IvantiRepository:
    """Fixture for Ivanti repository."""
    return IvantiRepository(ivanti_config)


@pytest.fixture
def sample_product() -> Product:
    """Fixture for sample product data."""
    return Product(
        product_id="PROD-123",
        product_name="Test Product",
        product_elements=[
            ProductElement(
                Lenght=50,
                **{
                    "Procuct Element": "Element 1",
                    "Type": "Hardware",
                    "GG Startup": 3,
                    "RU": "RU1",
                    "RU Qty": 10,
                    "RU Unit of measure": "Days",
                    "Q.ty min": 1,
                    "Q.ty MAX": 100,
                    "%Sconto MAX": Decimal("15"),
                    "Startup Costo": Decimal("500.0"),
                    "Startup Margine": Decimal("20"),
                    "Startup Prezzo": Decimal("600.0"),
                    "Canone Costo Mese": Decimal("100.0"),
                    "Canone Margine": Decimal("10"),
                    "Canone Prezzo Mese": Decimal("110.0"),
                    "Extended Description": "Test Description",
                    "Profit Center Prevalente": "PC001",
                    "Status": "Active",
                    "Note": "Test Note",
                    "Object": "REF001"
                }
            )
        ],
        created_at=datetime.now(UTC)
    )


@pytest.fixture
def mock_product_response() -> dict:
    """Fixture for mock product response from Ivanti API."""
    return {
        "id": "PROD-123",
        "name": "Test Product",
        "elements": [
            {
                "id": "ELEM-001",
                "name": "Element 1",
                "type": "Hardware",
                "startup_days": 3,
                "resource_unit": "RU1",
                "resource_unit_qty": 10,
                "resource_unit_measure": "Days",
                "quantity_min": 1,
                "quantity_max": 100,
                "max_discount_percentage": 15.0,
                "startup_cost": 500.0,
                "startup_margin": 20.0,
                "startup_price": 600.0,
                "monthly_fee_cost": 100.0,
                "monthly_fee_margin": 10.0,
                "monthly_fee_price": 110.0,
                "extended_description": "Test Description",
                "profit_center": "PC001",
                "status": "Active",
                "notes": "Test Note",
                "object_reference": "REF001"
            }
        ],
        "status": "Active",
        "created_at": "2024-01-23T12:00:00Z",
        "updated_at": "2024-01-23T12:00:00Z"
    }


def test_authentication_success(
    ivanti_repository: IvantiRepository,
    mock_httpx_client: Mock,
    mock_auth_response: dict
):
    """Test successful authentication."""
    # Setup
    mock_response = Mock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = mock_auth_response
    mock_response.raise_for_status = Mock()
    mock_httpx_client.post.return_value = mock_response

    # Execute
    ivanti_repository.connect()

    # Verify
    assert ivanti_repository._access_token == "test-token"
    mock_httpx_client.post.assert_called_once_with(
        ivanti_repository.config.token_url,
        json={
            "client_id": "test-client-id",
            "client_secret": "test-client-secret",
            "grant_type": "client_credentials"
        }
    )


def test_authentication_failure(
    ivanti_repository: IvantiRepository,
    mock_httpx_client: Mock
):
    """Test authentication failure."""
    # Setup
    mock_response = Mock(spec=httpx.Response)
    mock_response.status_code = 401
    mock_response.json.return_value = {"error": "Invalid credentials"}
    mock_response.raise_for_status = Mock(
        side_effect=httpx.HTTPStatusError(
            "Authentication failed",
            request=Mock(),
            response=mock_response
        )
    )
    mock_httpx_client.post.return_value = mock_response

    # Execute and verify
    with pytest.raises(AuthenticationError) as exc_info:
        ivanti_repository.connect()
    
    assert "Authentication failed" in str(exc_info.value)


def test_get_product_success(
    ivanti_repository: IvantiRepository,
    mock_httpx_client: Mock,
    mock_product_response: dict
):
    """Test successful product retrieval."""
    # Setup
    mock_response = Mock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = mock_product_response
    mock_response.raise_for_status = Mock()
    mock_httpx_client.get.return_value = mock_response

    # Execute
    product = ivanti_repository.get_product("PROD-123")

    # Verify
    assert product is not None
    assert product.product_id == "PROD-123"
    assert product.product_name == "Test Product"
    assert len(product.product_elements) == 1
    
    element = product.product_elements[0]
    assert element.product_element == "Element 1"
    assert element.type == "Hardware"
    assert element.startup_days == 3
    assert element.max_discount_percentage == Decimal("15.0")


def test_get_product_not_found(
    ivanti_repository: IvantiRepository,
    mock_httpx_client: Mock
):
    """Test product not found."""
    # Setup
    mock_response = Mock(spec=httpx.Response)
    mock_response.status_code = 404
    mock_response.json.return_value = {"error": "Product not found"}
    mock_response.raise_for_status = Mock(
        side_effect=httpx.HTTPStatusError(
            "Not Found",
            request=Mock(),
            response=mock_response
        )
    )
    mock_httpx_client.get.return_value = mock_response

    # Execute
    product = ivanti_repository.get_product("NONEXISTENT")

    # Verify
    assert product is None


def test_create_product_success(
    ivanti_repository: IvantiRepository,
    mock_httpx_client: Mock,
    sample_product: Product,
    mock_auth_success: Mock
):
    """Test successful product creation."""
    # Setup
    mock_response = Mock(spec=httpx.Response)
    mock_response.status_code = 201
    mock_response.json.return_value = {"id": "PROD-123"}
    mock_response.raise_for_status = Mock()
    mock_httpx_client.post.side_effect = [
        mock_auth_success,  # For authentication
        mock_response      # For product creation
    ]

    # Execute
    success = ivanti_repository.create_product(sample_product)

    # Verify
    assert success is True
    assert mock_httpx_client.post.call_count == 2
    create_call = mock_httpx_client.post.call_args_list[1]
    assert create_call[1]["json"]["id"] == "PROD-123"
    assert create_call[1]["json"]["name"] == "Test Product"


def test_update_product_success(
    ivanti_repository: IvantiRepository,
    mock_httpx_client: Mock,
    sample_product: Product
):
    """Test successful product update."""
    # Setup
    mock_response = Mock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "PROD-123"}
    mock_response.raise_for_status = Mock()
    mock_httpx_client.put.return_value = mock_response

    # Execute
    success = ivanti_repository.update_product(sample_product)

    # Verify
    assert success is True
    mock_httpx_client.put.assert_called_once()
    assert mock_httpx_client.put.call_args[1]["json"]["id"] == "PROD-123"
    assert mock_httpx_client.put.call_args[1]["json"]["name"] == "Test Product"


def test_retry_on_temporary_error(
    ivanti_repository: IvantiRepository,
    mock_httpx_client: Mock,
    sample_product: Product
):
    """Test retry mechanism on temporary errors."""
    # Setup responses: two failures followed by success
    error_response = Mock(spec=httpx.Response)
    error_response.status_code = 503
    error_response.json.return_value = {"error": "Service Unavailable"}
    error_response.raise_for_status = Mock(
        side_effect=httpx.HTTPStatusError(
            "Service Unavailable",
            request=Mock(),
            response=error_response
        )
    )

    success_response = Mock(spec=httpx.Response)
    success_response.status_code = 200
    success_response.json.return_value = {"id": "PROD-123"}
    success_response.raise_for_status = Mock()

    mock_httpx_client.put.side_effect = [
        error_response,
        error_response,
        success_response
    ]

    # Execute
    success = ivanti_repository.update_product(sample_product)

    # Verify
    assert success is True
    assert mock_httpx_client.put.call_count == 3


def test_rate_limit_handling(
    ivanti_repository: IvantiRepository,
    mock_httpx_client: Mock,
    sample_product: Product
):
    """Test handling of rate limit responses."""
    # Setup rate limit response
    rate_limit_response = Mock(spec=httpx.Response)
    rate_limit_response.status_code = 429
    rate_limit_response.headers = {"Retry-After": "2"}
    rate_limit_response.json.return_value = {"error": "Rate limit exceeded"}
    rate_limit_response.raise_for_status = Mock(
        side_effect=httpx.HTTPStatusError(
            "Rate limit exceeded",
            request=Mock(),
            response=rate_limit_response
        )
    )

    success_response = Mock(spec=httpx.Response)
    success_response.status_code = 200
    success_response.json.return_value = {"id": "PROD-123"}
    success_response.raise_for_status = Mock()

    mock_httpx_client.post.side_effect = [
        rate_limit_response,
        success_response
    ]

    # Execute
    success = ivanti_repository.create_product(sample_product)

    # Verify
    assert success is True
    assert mock_httpx_client.post.call_count == 2


def test_batch_process_products(
    ivanti_repository: IvantiRepository,
    mock_httpx_client: Mock,
    sample_product: Product
):
    """Test batch processing of products."""
    # Setup
    success_response = Mock(spec=httpx.Response)
    success_response.status_code = 201
    success_response.json.return_value = {"id": "PROD-123"}
    success_response.raise_for_status = Mock()
    
    error_response = Mock(spec=httpx.Response)
    error_response.status_code = 400
    error_response.json.return_value = {"error": "Invalid data"}
    error_response.raise_for_status = Mock(
        side_effect=httpx.HTTPStatusError(
            "Bad Request",
            request=Mock(),
            response=error_response
        )
    )

    mock_httpx_client.post.side_effect = [
        success_response,
        error_response,
        success_response
    ]

    products = [sample_product] * 3

    # Execute
    result = ivanti_repository.batch_process_products(products, "create")

    # Verify
    assert result.total_processed == 3
    assert result.successful_syncs == 2
    assert result.failed_syncs == 1
    assert len(result.errors) == 1